"""Image-to-video through fal.ai's queue API, with a hard spend cap.

fal is prepaid, so the balance is the last line of defence; this module keeps its
own ledger (ledger_fal.json) so a run stops well before that. The worst-case cost
of each clip is reserved BEFORE submitting; it is settled down to the expected
price when fal returns a video, refunded only when fal reports the request failed
(fal bills successful outputs only), and kept in full on any crash or timeout.

fal's list prices are not what it bills (Wan 3.0 lists $0.05/s but bills 720p
at 2x and 1080p at 4x), so with a billing key (FAL_BILLING_KEY) the ledger is
reconciled against fal's own usage records before and after every clip, and
the real figure wins whenever it is higher.
Every clip is logged with its prompt in generation_log.jsonl for the disclosure.
"""
import math
import base64
import io
import json
import os
import time
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv
from PIL import Image

from cutaway import meta

ROOT = Path(__file__).resolve().parent.parent
QUEUE = "https://queue.fal.run"
HARD_CAP_USD = 45.00  # the user's own money; never exceeded; .env may only lower it
LEDGER = ROOT / "ledger_fal.json"

load_dotenv(ROOT / ".env")
BUDGET = min(HARD_CAP_USD, float(os.environ.get("CUTAWAY_FAL_BUDGET_USD", HARD_CAP_USD)))

STYLE_GUARD = ("Keep the painterly 2D anime look of the first frame exactly: flat cel shading, "
               "the same character design, no text.")
NEGATIVE = "3D render, CGI, photorealistic, morphing, extra legs, extra limbs, deformed beak, text, blur, low quality"

# USD per output second as fal actually billed them (usage records, 2026-11-01). `pad_s` covers
# billing that rounds the clip up (H3 billed 6 s for a 5 s clip); `margin` scales the upfront
# reservation for anything not yet confirmed.
MODELS = {
    "h3": {"endpoint": "minimax/h3/image-to-video", "usd_per_s": 0.05, "pad_s": 1, "margin": 1.25,
           "args": lambda img, prompt, dur, res: {"image_url": img, "prompt": f"{prompt} {STYLE_GUARD}",
                                                  "duration": dur, "resolution": "768P"}},
    "kling26": {"endpoint": "fal-ai/kling-video/v2.6/pro/image-to-video", "usd_per_s": 0.07, "margin": 1.25,
                "durations": (5, 10),
                "args": lambda img, prompt, dur, res: {"start_image_url": img, "prompt": f"{prompt} {STYLE_GUARD}",
                                                       "duration": str(dur), "generate_audio": False,
                                                       "negative_prompt": NEGATIVE}},
    # Billed 10 units for 5 s at 720p and 20 at 1080p; 480p assumed to be the $0.05 list rate.
    "wan30": {"endpoint": "alibaba/wan-3.0/image-to-video",
              "usd_per_s": {"480p": 0.05, "720p": 0.10, "1080p": 0.20}, "resolution": "720p", "margin": 1.25,
              "args": lambda img, prompt, dur, res: {"start_image_url": img, "prompt": f"{prompt} {STYLE_GUARD}",
                                                     "duration": dur, "resolution": res, "aspect_ratio": "16:9",
                                                     "audio": False}},
}


class BudgetError(RuntimeError):
    pass


def _key():
    key = os.environ.get("FAL_KEY", "")
    if not key:
        raise RuntimeError("FAL_KEY missing: put it in .env.")
    return key


def spent():
    if not LEDGER.exists():
        return 0.0
    return float(json.loads(LEDGER.read_text())["spent_usd"])


def _reserve(cost, limit=None):
    """Add `cost` to the ledger, or refuse if it would pass the budget (or a stage `limit`
    on the ledger total). A negative cost settles an earlier reservation."""
    lock = LEDGER.with_suffix(".lock")
    for _ in range(300):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            time.sleep(0.1)
    else:
        raise RuntimeError(f"Ledger lock {lock.name} stuck; delete it if nothing else is running.")
    try:
        total = round(spent() + cost, 6)
        cap = min(BUDGET, limit) if limit is not None else BUDGET
        if cost > 0 and total > cap + 1e-9:
            raise BudgetError(f"Budget stop: fal spent ${spent():.2f}, clip needs ${cost:.2f}, cap ${cap:.2f}.")
        LEDGER.write_text(json.dumps({"spent_usd": total, "updated": datetime.now().isoformat()}, indent=2))
    finally:
        os.close(fd)
        os.remove(lock)


def real_spent():
    """Total fal has billed this account, from its usage records; None without a billing key."""
    key = os.environ.get("FAL_BILLING_KEY") or os.environ.get("FAL_READONLY_KEY")
    if not key:
        return None
    try:
        r = httpx.get("https://api.fal.ai/v1/models/usage", headers={"Authorization": f"Key {key}"}, timeout=60,
                      params={"start": "2026-10-01", "expand": "summary", "timeframe": "day"})
        r.raise_for_status()
        return round(sum(x["cost"] for x in r.json().get("summary", [])), 6)
    except (httpx.HTTPError, ValueError, KeyError):
        return None


def reconcile():
    """Raise the ledger to fal's real billed total if that is higher. Returns (ledger, real)."""
    real = real_spent()
    if real is not None and real > spent() + 1e-6:
        _reserve(real - spent())
    return spent(), real


def balance():
    key = os.environ.get("FAL_BILLING_KEY") or os.environ.get("FAL_READONLY_KEY")
    if not key:
        return None
    r = httpx.get("https://api.fal.ai/v1/account/billing", headers={"Authorization": f"Key {key}"},
                  params={"expand": "credits"}, timeout=60)
    return r.json()["credits"]["current_balance"] if r.status_code == 200 else None


def quote(model, seconds, resolution=None):
    """(expected price, worst-case reservation) in USD for one clip."""
    m = MODELS[model]
    rate = m["usd_per_s"]
    if isinstance(rate, dict):
        rate = rate[resolution or m["resolution"]]
    price = rate * math.ceil(seconds + m.get("pad_s", 0))
    return price, price * m["margin"]


def image_data_url(path, max_side=1920):
    """The keyframe as a JPEG data URL: a full PNG is several MB of JSON for no visible gain."""
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((max_side, max_side), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=94)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"


def generate(model, image, prompt, out, seconds=5, limit=None, timeout_s=1800, resolution=None):
    """Animate `image` into a clip at `out` with one of MODELS. Returns the result dict, with the prompt
    actually used under "_prompt".

    The request is written to <out>.pending.json as soon as fal accepts it. If a run dies while waiting
    (a crash, the laptop hibernating), calling this again for the same `out` collects that paid request
    instead of submitting and paying for a new one.
    """
    m = MODELS[model]
    if "durations" in m and seconds not in m["durations"]:
        raise ValueError(f"{model} takes durations {m['durations']}, not {seconds}")
    out = Path(out)
    pending = out.with_suffix(".pending.json")
    headers = {"Authorization": f"Key {_key()}"}
    if pending.exists():  # already submitted and reserved by an earlier run: just collect it
        job = json.loads(pending.read_text(encoding="utf-8"))
        print(f"  resuming fal request {job['request_id']} for {out.name}", flush=True)
    else:
        resolution = resolution or m.get("resolution")
        price, reserved = quote(model, seconds, resolution)
        body = m["args"](image_data_url(image), prompt, seconds, resolution)
        reconcile()
        bal = balance()
        if bal is not None and bal < price:
            raise BudgetError(f"fal balance ${bal:.2f} is below this clip's ${price:.2f}; top up or stop.")
        _reserve(reserved, limit)
        r = httpx.post(f"{QUEUE}/{m['endpoint']}", json=body, headers=headers, timeout=120)
        if r.status_code in (400, 401, 403, 404, 422):  # rejected before any work: not billed
            _reserve(-reserved)
            raise RuntimeError(f"fal rejected {model}: HTTP {r.status_code}: {r.text[:600]}")
        r.raise_for_status()
        sub = r.json()
        job = {"request_id": sub["request_id"], "status_url": sub["status_url"], "response_url": sub["response_url"],
               "model": model, "endpoint": m["endpoint"], "prompt": prompt, "image": str(image), "seconds": seconds,
               "price": price, "reserved": reserved,
               "args": {k: v for k, v in body.items() if "image" not in k}}
        out.parent.mkdir(parents=True, exist_ok=True)
        pending.write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
    rid = job["request_id"]
    with httpx.Client(headers=headers, timeout=120) as c:
        # Only answered polls count toward the timeout: time asleep or offline must not abandon a paid clip.
        waited, errors = 0, 0
        while True:
            try:
                st = c.get(job["status_url"]).json().get("status")
                errors = 0
            except (httpx.HTTPError, ValueError):
                st, errors = None, errors + 1
            if st == "COMPLETED":
                break
            if st is not None:
                waited += 5
            if waited > timeout_s or errors > 360:
                raise TimeoutError(f"{model} request {rid} still {st}; kept in {pending.name} for the next run")
            time.sleep(5)
        res = c.get(job["response_url"])
        if res.status_code != 200:  # fal does not bill failed requests
            _reserve(-job["reserved"])
            pending.unlink()
            raise RuntimeError(f"{model} request {rid} failed: HTTP {res.status_code}: {res.text[:600]}")
        result = res.json()
        with c.stream("GET", result["video"]["url"], timeout=600) as v:
            v.raise_for_status()
            with out.open("wb") as f:
                for chunk in v.iter_bytes():
                    f.write(chunk)
    _reserve(job["price"] - job["reserved"])
    meta._log(kind="video", model=model, endpoint=job["endpoint"], request_id=rid, prompt=job["prompt"],
              args=job["args"], image=job["image"], seconds=job["seconds"], cost_usd=round(job["price"], 4),
              out=str(out), expanded_prompt=result.get("expanded_prompt") or result.get("actual_prompt"))
    pending.unlink()
    reconcile()  # fal's records can lag a minute; the next clip's reconcile catches anything missed here
    result["_prompt"] = job["prompt"]
    return result
