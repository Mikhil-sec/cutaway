"""Client for the Meta Model API (Muse Image, SAM 3.1), with a hard spend cap.

Meta has no hard spend cap, so this module enforces one. The cost of each call
is reserved in ledger.json BEFORE the request goes out and is never refunded:
a crash or timeout can only make the ledger overestimate spending. Every call
is logged with its prompt in generation_log.jsonl, which also serves as the
AI-disclosure record the film competition may ask for.
"""
import base64
import json
import mimetypes
import os
import time
from datetime import datetime
from pathlib import Path

import httpx
import numpy as np
from dotenv import load_dotenv
from meta_sam_parser import CompletedOutcome, decode_mask_to_raster, image_segmentation_format
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://api.meta.ai/v1"
HARD_CAP_USD = 120.00  # never exceeded; .env may only lower it
PRICES = {  # USD per call, rounded up so the ledger overestimates
    "muse-image-1.0": 0.01,
    "sam-3.1": 0.01,  # listed at $2.50 per 1,000 images; reserve 4x until billing confirms
}
LEDGER = ROOT / "ledger.json"
LOG = ROOT / "generation_log.jsonl"

load_dotenv(ROOT / ".env")
BUDGET = min(HARD_CAP_USD, float(os.environ.get("CUTAWAY_BUDGET_USD", HARD_CAP_USD)))


class BudgetError(RuntimeError):
    pass


def _key():
    key = os.environ.get("MODEL_API_KEY", "")
    if not key or key == "paste_your_key_here":
        raise RuntimeError("MODEL_API_KEY missing: put it in .env (see .env.example).")
    return key


def spent():
    if not LEDGER.exists():
        return 0.0
    return float(json.loads(LEDGER.read_text())["spent_usd"])


def _reserve(model, n=1):
    lock = LEDGER.with_suffix(".lock")
    for _ in range(100):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            time.sleep(0.1)
    else:
        raise RuntimeError(f"Ledger lock {lock.name} stuck; delete it if nothing else is running.")
    try:
        cost = PRICES[model] * n
        total = round(spent() + cost, 4)
        if total > BUDGET + 1e-9:
            raise BudgetError(f"Budget stop: spent ${spent():.2f}, call needs ${cost:.2f}, cap ${BUDGET:.2f}.")
        LEDGER.write_text(json.dumps({"spent_usd": total, "updated": datetime.now().isoformat()}, indent=2))
    finally:
        os.close(fd)
        os.remove(lock)


def _log(**entry):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"time": datetime.now().isoformat(), **entry}, ensure_ascii=False) + "\n")


def data_url(path):
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"


def _client():
    return httpx.Client(base_url=BASE_URL, headers={"Authorization": f"Bearer {_key()}"}, timeout=300)


def _post(path, body, **kw):
    """POST, retrying only on 429/503 (not billed). Never retries a timeout,
    since a timed-out request may already have been billed."""
    for attempt in range(4):
        with _client() as c:
            r = c.post(path, json=body, **kw)
        if r.status_code == 200:
            return r
        if r.status_code in (429, 503) and attempt < 3:
            time.sleep(float(r.headers.get("retry-after", 5 * 2**attempt)))
            continue
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:800]}")


def image(prompt, out, size="1536x864", refs=()):
    """Generate one still with Muse Image; with refs, edit/condition on them."""
    model = "muse-image-1.0"
    body = {"model": model, "prompt": prompt, "n": 1, "size": size, "output_format": "png"}
    path = "/images/generations"
    if refs:
        body["images"] = [{"image_url": data_url(r)} for r in refs]
        path = "/images/edits"
    _reserve(model)
    r = _post(path, body)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(r.json()["data"][0]["b64_json"]))
    _log(kind="image", model=model, prompt=prompt, refs=[str(x) for x in refs], size=size, out=str(out))
    return out


def segment(image_path, concept):
    """Segment every instance of `concept` with SAM 3.1.

    Returns a list of (confidence, full-frame boolean mask) sorted by confidence.
    """
    model = "sam-3.1"
    body = {
        "model": model,
        "input": [{"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": concept},
            {"type": "input_image", "image_url": data_url(image_path)},
        ]}],
        "stream": False,
        "metadata": {"mask_encoding": "one_bit"},
    }
    _reserve(model)
    r = _post("/responses", body)
    text = _output_text(r.json())
    parser = image_segmentation_format().create_parser()
    parser.push(text)
    result = parser.finish(CompletedOutcome()).result

    with Image.open(image_path) as im:
        W, H = im.size
    found = []
    for rec in result.records:
        if rec.kind != "mask":
            continue
        m = rec.mask
        local = np.frombuffer(decode_mask_to_raster(m), dtype=np.uint8).reshape(m.height, m.width)
        full = _place(local, rec.bounds, W, H)
        found.append((rec.confidence if rec.confidence is not None else 1.0, full))
    found.sort(key=lambda t: -t[0])
    _log(kind="segment", model=model, prompt=concept, image=str(image_path), matches=len(found))
    return found


def _output_text(resp):
    if resp.get("output_text"):
        return resp["output_text"]
    parts = []
    for item in resp.get("output", []):
        for c in item.get("content", []) or []:
            if c.get("type") == "output_text":
                parts.append(c.get("text", ""))
    return "".join(parts)


def _place(local, b, W, H):
    """Resize a box-local mask raster into its box on a full W x H frame."""
    x0, y0 = int(round(b.left)), int(round(b.top))
    x1, y1 = int(round(b.right)), int(round(b.bottom))
    bw, bh = max(1, x1 - x0), max(1, y1 - y0)
    patch = Image.fromarray(local * 255).resize((bw, bh), Image.BILINEAR)
    full = np.zeros((H, W), dtype=bool)
    full[y0:y0 + bh, x0:x0 + bw] = np.asarray(patch)[: H - y0, : W - x0] > 127
    return full
