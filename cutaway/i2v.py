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
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from PIL import Image

from cutaway import meta

ROOT = Path(__file__).resolve().parent.parent
QUEUE = "https://queue.fal.run"
load_dotenv(ROOT / ".env")

# One ledger and hard cap per fal account. "dodo": the user's own money, finished. "bootcamp": $60 pooled by
# three students on a new account (docs/BOOTCAMP.md); the cap leaves $2 of headroom and must never be raised
# without the user's word. `since`: where fal's usage records for that account start.
PROFILES = {
    "dodo": {"ledger": "ledger_fal.json", "cap": 45.00, "since": "2026-10-01"},
    "bootcamp": {"ledger": "ledger_fal_bootcamp.json", "cap": 58.00, "since": "2026-11-20"},
}
PROFILE = os.environ.get("CUTAWAY_FAL_PROFILE", "bootcamp")
HARD_CAP_USD = PROFILES[PROFILE]["cap"]  # never exceeded; .env may only lower it
LEDGER = ROOT / PROFILES[PROFILE]["ledger"]
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
    # FLUX 3 Max (Black Forest Labs, commercial licence): 5-20 s, sound generated in the same pass, 1080p only
    # an upscale of 720p. Half price until 23 Nov 00:00 UTC. margin 2.0 until a usage record confirms the bill
    # (Wan billed 2x its list price). Prompting: docs/FLUX3_PLAYBOOK.md.
    "flux3": {"endpoint": "blackforestlabs/flux-3-max/image-to-video", "usd_per_s": lambda res: _flux_rate(res),
              "resolution": "720p", "margin": 1.15, "durations": tuple(range(5, 21)), "max_side": 1280,
              "args": lambda img, prompt, dur, res: {"image_url": img, "prompt": prompt, "duration": dur,
                                                     "resolution": res, "aspect_ratio": "16:9",
                                                     "generate_audio": True}},
    "flux3_kf": {"endpoint": "blackforestlabs/flux-3-max/keyframes-to-video", "usd_per_s": lambda res: _flux_rate(res),
                 "resolution": "720p", "margin": 1.15, "durations": tuple(range(5, 21)), "max_side": 1280},
}


def _flux_rate(resolution):
    full = {"720p": 0.17, "1080p": 0.29}[resolution]
    return full / 2 if datetime.now(timezone.utc) < datetime(2026, 11, 23, tzinfo=timezone.utc) else full


def _strip(v):
    """args for the log: image data URLs replaced by a marker, at any depth."""
    if isinstance(v, str) and v.startswith("data:"):
        return "<image>"
    if isinstance(v, dict):
        return {k: _strip(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_strip(x) for x in v]
    return v


# Audio, through the same ledger. `media` is where the file is in fal's result. ElevenLabs Music lists $0.60 a
# minute; until a usage record shows whether part-minutes are billed whole, a whole minute is reserved.
AUDIO = {
    "music_el": {"endpoint": "fal-ai/elevenlabs/music", "usd_per_s": 0.01, "media": "audio",
                 "reserve": lambda s: 0.60 * math.ceil(s / 60) * 1.25},
    "sfx_el": {"endpoint": "fal-ai/elevenlabs/sound-effects/v2", "usd_per_s": 0.002, "media": "audio",
               "reserve": lambda s: 0.002 * math.ceil(s) * 2},
    # ElevenLabs v3 TTS: $0.10 per 1000 characters; audio() is called with seconds = len(text).
    "tts_el": {"endpoint": "fal-ai/elevenlabs/tts/eleven-v3", "usd_per_s": 0.0001, "media": "audio",
               "reserve": lambda chars: max(0.01, 0.0001 * chars * 2)},
    "mmaudio": {"endpoint": "fal-ai/mmaudio-v2", "usd_per_s": 0.001, "media": "video",
                "reserve": lambda s: 0.001 * math.ceil(s) * 2},
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
                      params={"start": PROFILES[PROFILE]["since"], "expand": "summary", "timeframe": "day"})
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
    if callable(rate):
        rate = rate(resolution or m["resolution"])
    elif isinstance(rate, dict):
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


def keyframes(frames, prompt, out, seconds, model="flux3_kf", extra=None, limit=None, timeout_s=1800,
              resolution=None):
    """FLUX 3 Max keyframes-to-video: frames = [(image_path, frame_index)], 24 fps, up to 10, unique indices,
    each at most seconds*24. Same reserve/collect behaviour as generate()."""
    m = MODELS[model]
    if seconds not in m["durations"]:
        raise ValueError(f"{model} takes durations {m['durations'][0]}-{m['durations'][-1]}, not {seconds}")
    idx = [int(i) for _, i in frames]
    if not 1 <= len(frames) <= 10 or len(set(idx)) != len(idx) or max(idx) > seconds * 24 or min(idx) < 0:
        raise ValueError(f"keyframe indices {idx} must be 1-10 unique values in 0..{seconds * 24}")
    out = Path(out)
    if out.with_suffix(".pending.json").exists():
        return _run(out)
    resolution = resolution or m["resolution"]
    price, reserved = quote(model, seconds, resolution)
    body = {"prompt": prompt, "duration": seconds, "resolution": resolution, "aspect_ratio": "16:9",
            "generate_audio": True,
            "keyframes": [{"image_url": image_data_url(p, m["max_side"]), "frame_index": int(i)} for p, i in frames],
            **(extra or {})}
    return _run(out, model, m["endpoint"], body, price, reserved, limit, timeout_s, "video",
                {"prompt": prompt, "image": [f"{p}@{i}" for p, i in frames], "seconds": seconds})


def generate(model, image, prompt, out, seconds=5, limit=None, timeout_s=1800, resolution=None, end_image=None,
             extra=None):
    """Animate `image` into a clip at `out` with one of MODELS. Returns the result dict, with the prompt
    actually used under "_prompt". end_image: the last frame (FLUX 3 Max); extra: more endpoint inputs
    (e.g. {"seed": 7, "reasoning_level": "low", "generate_audio": False}).

    The request is written to <out>.pending.json as soon as fal accepts it. If a run dies while waiting
    (a crash, the laptop hibernating), calling this again for the same `out` collects that paid request
    instead of submitting and paying for a new one.
    """
    m = MODELS[model]
    if "durations" in m and seconds not in m["durations"]:
        raise ValueError(f"{model} takes durations {m['durations']}, not {seconds}")
    out = Path(out)
    if out.with_suffix(".pending.json").exists():
        return _run(out)
    resolution = resolution or m.get("resolution")
    price, reserved = quote(model, seconds, resolution)
    side = m.get("max_side", 1920)
    body = m["args"](image_data_url(image, side), prompt, seconds, resolution)
    if end_image:
        body["end_image_url"] = image_data_url(end_image, side)
    body.update(extra or {})
    return _run(out, model, m["endpoint"], body, price, reserved, limit, timeout_s, "video",
                {"prompt": prompt, "image": str(image), "seconds": seconds})


def audio(model, body, out, seconds, limit=None, timeout_s=1800):
    """Generate audio with one of AUDIO (body: the endpoint's own input). `seconds` sets the price. A data URL
    may stand in for any input file. Returns fal's result dict."""
    m = AUDIO[model]
    out = Path(out)
    if out.with_suffix(".pending.json").exists():
        return _run(out)
    return _run(out, model, m["endpoint"], body, m["usd_per_s"] * seconds, m["reserve"](seconds), limit,
                timeout_s, m["media"], {"prompt": body.get("prompt") or body.get("text") or "", "seconds": seconds,
                                         "kind": "audio"})


def _run(out, model=None, endpoint=None, body=None, price=None, reserved=None, limit=None, timeout_s=1800,
         media="video", record=None):
    """Reserve, submit, wait, download and settle one paid request (or, with only `out`, collect the request an
    earlier run left in <out>.pending.json)."""
    pending = out.with_suffix(".pending.json")
    headers = {"Authorization": f"Key {_key()}"}
    if pending.exists():  # already submitted and reserved by an earlier run: just collect it
        job = json.loads(pending.read_text(encoding="utf-8"))
        print(f"  resuming fal request {job['request_id']} for {out.name}", flush=True)
    else:
        record = record or {}
        reconcile()
        bal = balance()
        if bal is not None and bal < price:
            raise BudgetError(f"fal balance ${bal:.2f} is below this clip's ${price:.2f}; top up or stop.")
        _reserve(reserved, limit)
        r = httpx.post(f"{QUEUE}/{endpoint}", json=body, headers=headers, timeout=120)
        if r.status_code in (400, 401, 403, 404, 422):  # rejected before any work: not billed
            _reserve(-reserved)
            raise RuntimeError(f"fal rejected {model}: HTTP {r.status_code}: {r.text[:600]}")
        r.raise_for_status()
        sub = r.json()
        job = {"request_id": sub["request_id"], "status_url": sub["status_url"], "response_url": sub["response_url"],
               "model": model, "endpoint": endpoint, "prompt": record.get("prompt", ""), "image": record.get("image"),
               "seconds": record.get("seconds"), "price": price, "reserved": reserved, "media": media, "kind": record.get("kind", "video"),
               "args": _strip(body)}
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
                raise TimeoutError(f"{job['model']} request {rid} still {st}; kept in {pending.name} for the next run")
            time.sleep(5)
        res = c.get(job["response_url"])
        if res.status_code != 200:  # fal does not bill failed requests
            _reserve(-job["reserved"])
            pending.unlink()
            raise RuntimeError(f"{job['model']} request {rid} failed: HTTP {res.status_code}: {res.text[:600]}")
        result = res.json()
        with c.stream("GET", result[job.get("media", "video")]["url"], timeout=600) as v:
            v.raise_for_status()
            with out.open("wb") as f:
                for chunk in v.iter_bytes():
                    f.write(chunk)
    _reserve(job["price"] - job["reserved"])
    meta._log(kind=job.get("kind", "video"), model=job["model"], endpoint=job["endpoint"], request_id=rid, prompt=job["prompt"],
              args=job["args"], image=job["image"], seconds=job["seconds"], cost_usd=round(job["price"], 4),
              out=str(out), expanded_prompt=result.get("expanded_prompt") or result.get("actual_prompt"))
    pending.unlink()
    reconcile()  # fal's records can lag a minute; the next clip's reconcile catches anything missed here
    result["_prompt"] = job["prompt"]
    return result
