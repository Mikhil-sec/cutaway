"""The bootcamp pipeline: a 3-4 minute film inside one 80-minute AI session (docs/BOOTCAMP.md).

    python -m cutaway.bootcamp plan                         # Muse Spark: story -> films/bootcamp/film.json
    python -m cutaway.bootcamp sheets                       # Muse Image: character sheets, in parallel
    python -m cutaway.bootcamp keyframes [--shots s01,s05]  # Muse Image keyframes in dependency waves, Spark checks
    python -m cutaway.bootcamp quote [--shots ...]          # what the next takes would cost; spends nothing
    python -m cutaway.bootcamp video --yes [--shots ...] [--revised]   # FLUX 3 Max, all clips in parallel
    python -m cutaway.bootcamp review [--shots ...]         # Muse Spark watches every new take
    python -m cutaway.bootcamp cut                          # rough cut with the clips' own sound
    python -m cutaway.bootcamp score --yes                  # ElevenLabs Music to the cut (Spark writes the plan)
    python -m cutaway.bootcamp mix                          # rough cut + score -> film_final.mp4
    python -m cutaway.bootcamp status | statement

Everything lives in films/bootcamp/. film.json is the plan; each shot keeps its own state file
(shots/<id>/state.json), so parallel threads never share mutable state. Nothing is deleted: a repainted keyframe
keeps its earlier versions as <name>_vN.png and every take is kept. `video` and `score` spend fal money and refuse
to run without --yes; the $58 cap in i2v.py applies on top.

film.json:
{
 "title": "...", "look": "style sentence prefixed to every Muse Image prompt",
 "characters": [{"name": "wei14", "prompt": "character sheet prompt", "refs": ["refs/bootcamp/x.jpg"]}],
 "shots": [{
   "id": "s01", "seconds": 10, "mode": "i2v" | "keyframes",
   "frames": [{"name": "start", "at": 0, "prompt": "...", "refs": ["@wei14", "@s00.end", "refs/bootcamp/y.jpg"]},
              {"name": "end", "at": "end", "prompt": "...", "refs": ["@s01.start"]}],
   "motion": "the FLUX prompt (camera, action, environment, light, Sound: ... No music.)",
   "audio": true, "reasoning": "high", "flash_out": false, "trim": [0, 9.5]}]
}
refs: "@name" is a character sheet, "@sid.frame" another shot's keyframe (painted first), anything else a file.
i2v uses the first frame as the start and a frame with "at": "end" as the end image; keyframes mode pins every
frame at round(at*24) (or the last frame for "end").
"""
import argparse
import json
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from cutaway import i2v, meta

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT / "films" / "bootcamp"
SPARK = "muse-spark-1.3"
ACCEPT = 7
WORKERS = 6
CANDIDATES = 3  # Muse Image paintings per keyframe; Muse Spark picks the best
_print_lock = threading.Lock()


def say(*a):
    with _print_lock:
        print(*a, flush=True)


# ---------------------------------------------------------------- state

def film():
    return json.loads((FILM / "film.json").read_text(encoding="utf-8"))


def shot_dir(sid):
    d = FILM / "shots" / sid
    d.mkdir(parents=True, exist_ok=True)
    return d


def state(sid):
    p = shot_dir(sid) / "state.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_state(sid, st):
    (shot_dir(sid) / "state.json").write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")


def sheet_path(name):
    return FILM / "shots" / "_sheets" / f"{name}.png"


def frame_path(sid, name):
    return shot_dir(sid) / f"{name}.png"


def resolve(ref):
    if ref.startswith("@"):
        if "." in ref:
            sid, name = ref[1:].split(".", 1)
            return frame_path(sid, name)
        return sheet_path(ref[1:])
    p = Path(ref)
    return p if p.is_absolute() else ROOT / p


def pick(shots, only):
    return [s for s in shots if not only or s["id"] in only]


def run_parallel(jobs, workers=WORKERS):
    """jobs: [(label, fn)]. Runs them in threads; one failure never stops the others."""
    results = {}
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(fn): label for label, fn in jobs}
        for f in as_completed(futs):
            try:
                results[futs[f]] = f.result()
            except Exception as e:  # noqa: BLE001 - report and carry on; the step can be re-run
                results[futs[f]] = e
                say(f"  ! {futs[f]}: {type(e).__name__}: {str(e)[:300]}")
    return results


# ---------------------------------------------------------------- Muse Image with checks

CHECK = {"type": "object", "additionalProperties": False,
         "required": ["score", "problems", "revised_prompt"],
         "properties": {"score": {"type": "integer"}, "problems": {"type": "array", "items": {"type": "string"}},
                        "revised_prompt": {"type": "string"}}}
REWORD = {"type": "object", "additionalProperties": False, "required": ["prompt"],
          "properties": {"prompt": {"type": "string"}}}


def paint(prompt, out, refs, label):
    """One Muse Image call; on a content-filter refusal, Muse Spark rewords the prompt once."""
    meta.thread_context(shot=label)
    try:
        return meta.image(prompt, out, refs=refs), prompt
    except RuntimeError as e:
        if "HTTP 4" not in str(e):
            raise
        r = meta.chat(SPARK, [{"role": "system", "content":
                               "An image generator refused this prompt. Rewrite it so it is clearly harmless and "
                               "keeps every visual element, the mood and the composition. Return only the prompt."},
                              {"role": "user", "content": prompt}], schema=REWORD, max_tokens=3000,
                      reasoning_effort="low", timeout=120)
        say(f"  {label}: refused, reworded by Muse Spark")
        return meta.image(r["prompt"], out, refs=refs), r["prompt"]


def check(img, prompt, sheets, label):
    """Muse Spark compares a painting with its prompt and the character sheets it should match."""
    meta.thread_context(shot=label)
    content = [{"type": "text", "text": f"Prompt it was painted from:\n{prompt}\n\nThe last image is the "
                                        "painting; any images before it are character sheets it must match."}]
    content += [{"type": "image_url", "image_url": {"url": str(s)}} for s in sheets]
    content += [{"type": "image_url", "image_url": {"url": str(img)}}]
    return meta.chat(SPARK, [
        {"role": "system", "content":
            "You check keyframes for an AI film before they are animated. Score 0-10 (7 = usable): does it show "
            "what the prompt asks, are characters on-model with their sheets (face, age, hair, clothes), is it "
            "free of garbled text, extra limbs and broken hands, is it a strong cinematic 16:9 frame? problems: "
            "short and specific. revised_prompt: the whole prompt rewritten as one consistent description that "
            "fixes the problems (repeat it unchanged if none)."},
        {"role": "user", "content": content}], schema=CHECK, max_tokens=4000, reasoning_effort="low", timeout=180)


def _candidate(prompt, path, refs, sheets, label):
    _, used = paint(prompt, path, refs, label)
    try:
        v = check(path, used, sheets, label)
    except Exception as e:  # noqa: BLE001 - a slow or failed check must not block the session
        say(f"  {label}: check skipped ({type(e).__name__})")
        v = {"score": -1, "problems": ["check failed"], "revised_prompt": used}
    return {"file": path.name, "prompt": used, "check": v}


def paint_checked(prompt, out, refs, sheets, label, repaints=1, candidates=None):
    """Paint `candidates` versions at once; Muse Spark scores each and the best is copied to `out`. Below ACCEPT,
    one more round from the best one's revised prompt. Every candidate is kept as <name>_rRcK.png."""
    candidates = candidates or CANDIDATES
    out = Path(out)
    history = []
    for rnd in range(1, repaints + 2):
        if out.exists():  # keep the earlier version
            n = len(list(out.parent.glob(f"{out.stem}_v*.png"))) + 1
            out.rename(out.with_name(f"{out.stem}_v{n}.png"))
        paths = [out.with_name(f"{out.stem}_r{rnd}c{k}.png") for k in range(1, candidates + 1)]
        res = run_parallel([(f"{label}#c{k}", lambda p=p: _candidate(prompt, p, refs, sheets, label))
                            for k, p in enumerate(paths, 1)], workers=candidates)
        got = [r for r in res.values() if not isinstance(r, Exception)]
        if not got:
            raise RuntimeError(f"{label}: every candidate failed")
        history += got
        best = max(history, key=lambda h: h["check"]["score"])
        shutil.copyfile(out.with_name(best["file"]), out)
        say(f"  {label}: round {rnd} scores {[h['check']['score'] for h in got]}, best {best['check']['score']} "
            f"{best['check']['problems'][:2]}")
        if best["check"]["score"] >= ACCEPT or best["check"]["score"] < 0:
            break
        prompt = best["check"]["revised_prompt"]
    return history


# ---------------------------------------------------------------- stages

PLAN = {
    "type": "object", "additionalProperties": False, "required": ["title", "look", "characters", "shots"],
    "properties": {
        "title": {"type": "string"}, "look": {"type": "string"},
        "characters": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["name", "prompt"],
            "properties": {"name": {"type": "string"}, "prompt": {"type": "string"}}}},
        "shots": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "seconds", "mode", "frames", "motion", "flash_out"],
            "properties": {
                "id": {"type": "string"}, "seconds": {"type": "integer"},
                "mode": {"type": "string", "enum": ["i2v", "keyframes"]},
                "flash_out": {"type": "boolean"}, "motion": {"type": "string"},
                "frames": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False, "required": ["name", "at", "prompt", "refs"],
                    "properties": {"name": {"type": "string"}, "at": {"type": "string"}, "prompt": {"type": "string"},
                                   "refs": {"type": "array", "items": {"type": "string"}}}}}}}}}}


def plan(brief_files):
    """Muse Spark turns the story and the playbook into film.json. Review and edit it before painting."""
    meta.thread_context(shot="plan")
    brief = "\n\n".join(Path(f).read_text(encoding="utf-8") for f in brief_files)
    r = meta.chat(SPARK, [
        {"role": "system", "content":
            "You are the director of a 3-4 minute AI film. Write the production plan as JSON. characters: one "
            "entry per character AND per age they appear at (e.g. wei14, wei26, wei50), each a full character-sheet "
            "prompt (front view, neutral background, full body, consistent outfit). shots: 5-20 s each, totalling "
            "200-240 s. frames: the start frame (at '0'), optionally an end frame (at 'end'), or for mode "
            "'keyframes' up to 10 frames at seconds like '6.5'. Each frame prompt is a complete Muse Image prompt; "
            "refs use '@name' for character sheets and '@sid.frame' for an earlier keyframe the frame must match "
            "(same place, same light), plus file paths for reference photos if given. motion is the FLUX 3 Max "
            "prompt and follows the playbook: camera move first, ordered action beats with 'then'/'as', "
            "environment motion, light, what stays still, then 'Sound: <named sources>. No music.' Short quoted "
            "dialogue must name the speaker. flash_out marks the Spring Festival photo shots."},
        {"role": "user", "content": brief}], schema=PLAN, max_tokens=60000, reasoning_effort="medium", timeout=900)
    for s in r["shots"]:
        for f in s["frames"]:
            f["at"] = "end" if f["at"] == "end" else float(f["at"] or 0)
    FILM.mkdir(parents=True, exist_ok=True)
    out = FILM / "film.json"
    if out.exists():
        out.rename(out.with_name(f"film_v{len(list(FILM.glob('film_v*.json'))) + 1}.json"))
    out.write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
    say(f"wrote {out}: {len(r['characters'])} characters, {len(r['shots'])} shots, "
        f"{sum(s['seconds'] for s in r['shots'])} s")


def sheets(force=False, only=()):
    """Character sheets in dependency waves: a sheet whose refs name another sheet ("@wei14") waits for it."""
    f = film()
    todo = [c for c in f["characters"] if (not only or c["name"] in only)
            and (force or not sheet_path(c["name"]).exists())]
    wave = 0
    while todo:
        ready = [c for c in todo if all(resolve(r).exists() for r in c.get("refs", []))]
        if not ready:
            say(f"  blocked sheets: {[c['name'] for c in todo]}")
            break
        wave += 1
        jobs = []
        for c in ready:
            out = sheet_path(c["name"])
            out.parent.mkdir(parents=True, exist_ok=True)
            refs = [resolve(r) for r in c.get("refs", [])]
            prev = [p for r, p in zip(c.get("refs", []), refs) if r.startswith("@")]
            jobs.append((c["name"], lambda c=c, out=out, refs=refs, prev=prev: paint_checked(
                f"{f.get('sheet_look', f['look'])} Character reference sheet: {c['prompt']}", out, refs, prev,
                f"sheet:{c['name']}")))
        say(f"sheets wave {wave}: {len(jobs)} to paint")
        results = run_parallel(jobs, workers=4)
        for name, res in results.items():
            if not isinstance(res, Exception):
                sheet_path(name).with_suffix(".json").write_text(json.dumps(res, indent=1, ensure_ascii=False),
                                                                 encoding="utf-8")
        todo = [c for c in todo if c["name"] not in results]


def keyframes(only=(), force=False):
    """Paint every frame whose @references exist, in parallel waves, until all are done or blocked."""
    f = film()
    todo = [(s, fr) for s in pick(f["shots"], only) for fr in s["frames"]
            if force or not frame_path(s["id"], fr["name"]).exists()]
    wave = 0
    while todo:
        ready = [(s, fr) for s, fr in todo if all(resolve(r).exists() for r in fr.get("refs", []))]
        if not ready:
            for s, fr in todo:
                missing = [r for r in fr.get("refs", []) if not resolve(r).exists()]
                say(f"  blocked {s['id']}.{fr['name']}: missing {missing}")
            break
        wave += 1
        say(f"keyframes wave {wave}: {len(ready)} frames")
        jobs = []
        for s, fr in ready:
            refs = [resolve(r) for r in fr.get("refs", [])][:10]
            sheets_ = [p for r, p in zip(fr.get("refs", []), refs) if r.startswith("@") and "." not in r]
            out = frame_path(s["id"], fr["name"])
            jobs.append((f"{s['id']}.{fr['name']}", lambda fr=fr, out=out, refs=refs, sh=sheets_, sid=s["id"]:
                         paint_checked(f"{f['look']} {fr['prompt']}", out, refs, sh, f"{sid}.{fr['name']}")))
        results = run_parallel(jobs, workers=6)
        for label, res in results.items():
            if isinstance(res, Exception):
                continue
            sid, name = label.split(".", 1)
            st = state(sid)
            st.setdefault("frames", {})[name] = res
            save_state(sid, st)
        done = {lbl for lbl, res in results.items() if not isinstance(res, Exception)}
        todo = [(s, fr) for s, fr in todo if f"{s['id']}.{fr['name']}" not in done
                and f"{s['id']}.{fr['name']}" not in results]  # failures are dropped; re-run the stage for them


def _clip_plan(s, revised=False):
    st = state(s["id"])
    prompt = f"{film().get('motion_style', '')} {s['motion']}".strip()
    if revised:
        reviewed = [t for t in st.get("takes", []) if t.get("review")]
        if reviewed:
            prompt = max(reviewed, key=lambda t: t["review"]["score"])["review"]["revised_prompt"]
    extra = {"generate_audio": s.get("audio", True), "reasoning_level": s.get("reasoning", "high")}
    if "seed" in s:
        extra["seed"] = s["seed"]
    return prompt, extra


def quote(only=()):
    f = film()
    total = 0.0
    for s in pick(f["shots"], only):
        model = "flux3_kf" if s["mode"] == "keyframes" else "flux3"
        price, reserved = i2v.quote(model, s["seconds"])
        total += price
        say(f"  {s['id']}: {s['seconds']} s  ${price:.2f} (reserves ${reserved:.2f})")
    ledger, real = i2v.reconcile()
    say(f"next takes: ${total:.2f} | fal ledger ${ledger:.2f}, real ${real}, balance ${i2v.balance()}, "
        f"cap ${i2v.BUDGET:.2f}")
    return total


def video(only=(), revised=False):
    f = film()
    jobs = []
    for s in pick(f["shots"], only):
        frames = s["frames"]
        paths = [frame_path(s["id"], fr["name"]) for fr in frames]
        if not all(p.exists() for p in paths):
            say(f"  skip {s['id']}: keyframes missing")
            continue
        prompt, extra = _clip_plan(s, revised)
        n = len(state(s["id"]).get("takes", [])) + 1
        out = shot_dir(s["id"]) / f"take_{n}.mp4"

        def job(s=s, frames=frames, paths=paths, prompt=prompt, extra=extra, out=out, n=n):
            meta.thread_context(shot=s["id"])
            if s["mode"] == "keyframes":
                last = s["seconds"] * 24
                pins = [(p, last if fr["at"] == "end" else min(last, round(float(fr["at"]) * 24)))
                        for fr, p in zip(frames, paths)]
                i2v.keyframes(pins, prompt, out, s["seconds"], extra=extra)
            else:
                end = next((p for fr, p in zip(frames, paths) if fr["at"] == "end"), None)
                i2v.generate("flux3", paths[0], prompt, out, seconds=s["seconds"], end_image=end, extra=extra)
            st = state(s["id"])
            st.setdefault("takes", []).append({"take": n, "file": out.name, "prompt": prompt, "extra": extra})
            save_state(s["id"], st)
            say(f"  {s['id']} take {n} done")
        jobs.append((s["id"], job))
    say(f"video: {len(jobs)} clips submitted together")
    run_parallel(jobs, workers=8)
    say(f"fal: ledger/real {i2v.reconcile()}, balance ${i2v.balance()}")


TAKE_REVIEW = {"type": "object", "additionalProperties": False,
               "required": ["score", "problems", "revised_prompt"],
               "properties": {"score": {"type": "integer"},
                              "problems": {"type": "array", "items": {"type": "string"}},
                              "revised_prompt": {"type": "string"}}}


def review(only=()):
    f = film()
    jobs = []
    for s in pick(f["shots"], only):
        for t in state(s["id"]).get("takes", []):
            if "review" in t:
                continue

            def job(s=s, t=t):
                meta.thread_context(shot=s["id"])
                d = shot_dir(s["id"])
                r = meta.chat(SPARK, [
                    {"role": "system", "content":
                        "You review one take from a video model for a cinematic short. The image is the planned "
                        "first frame. Score 0-10 (7 = usable): does the shot deliver its action and camera move, do "
                        "faces, hands and bodies stay intact and on-model, does the place stay the same, is motion "
                        "smooth, is there unwanted text or music? problems: short. revised_prompt: a complete "
                        "rewritten motion prompt fixing them (same structure, ends with a Sound line and 'No music')."},
                    {"role": "user", "content": [
                        {"type": "text", "text": f"Prompt used:\n{t['prompt']}"},
                        {"type": "image_url", "image_url": {"url": str(frame_path(s['id'], s['frames'][0]['name']))}},
                        {"type": "video_url", "video_url": {"url": str(d / t["file"]), "fps": 2}}]}],
                    schema=TAKE_REVIEW, max_tokens=6000, reasoning_effort="low", timeout=240)
                st = state(s["id"])
                for x in st["takes"]:
                    if x["take"] == t["take"]:
                        x["review"] = r
                save_state(s["id"], st)
                say(f"  {s['id']} take {t['take']}: {r['score']}/10 {r['problems'][:2]}")
            jobs.append((f"{s['id']}#{t['take']}", job))
    say(f"review: {len(jobs)} takes")
    run_parallel(jobs)


def best_take(sid):
    st = state(sid)
    if "choice" in st:
        return next(t for t in st["takes"] if t["take"] == st["choice"])
    takes = [t for t in st.get("takes", []) if (shot_dir(sid) / t["file"]).exists()]
    return max(takes, key=lambda t: (t.get("review") or {}).get("score", 0), default=None)


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], check=True)


def has_audio(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return bool(r.stdout.strip())


def duration(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def cut():
    """Every shot's best take, trimmed, 1280x720 24 fps, with its own sound; flash_out shots end on white."""
    f = film()
    parts = []
    tmp = FILM / "cut_parts"
    tmp.mkdir(exist_ok=True)
    for s in f["shots"]:
        t = best_take(s["id"])
        if not t:
            say(f"  {s['id']}: no take, left out")
            continue
        src = shot_dir(s["id"]) / t["file"]
        a, b = s.get("trim") or [0, min(s["seconds"], duration(src))]
        vf = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24,setsar=1"
        if s.get("flash_out"):
            vf += f",fade=out:st={max(b - a - 0.35, 0):.2f}:d=0.35:color=white"
        out = tmp / f"{s['id']}.mp4"
        inputs = ["-ss", a, "-t", b - a, "-i", src]
        if has_audio(src):
            ff(*inputs, "-vf", vf, "-af", "aresample=48000", "-c:v", "libx264", "-crf", 18, "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-ac", 2, out)
        else:
            ff(*inputs, "-f", "lavfi", "-t", b - a, "-i", "anullsrc=r=48000:cl=stereo", "-vf", vf, "-map", "0:v",
               "-map", "1:a", "-c:v", "libx264", "-crf", 18, "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", out)
        parts.append(out)
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    out = FILM / "rough_cut.mp4"
    ff("-f", "concat", "-safe", 0, "-i", lst, "-c", "copy", out)
    timeline, t0 = [], 0.0
    for p in parts:
        d = duration(p)
        timeline.append([p.stem, round(t0, 3), round(t0 + d, 3)])
        t0 += d
    (FILM / "timeline.json").write_text(json.dumps(timeline, indent=1), encoding="utf-8")
    say(f"wrote {out} ({t0:.1f} s, {len(parts)} shots)")


SCORE_PLAN = {"type": "object", "additionalProperties": False,
              "required": ["positive_global_styles", "negative_global_styles", "sections"],
              "properties": {
                  "positive_global_styles": {"type": "array", "items": {"type": "string"}},
                  "negative_global_styles": {"type": "array", "items": {"type": "string"}},
                  "sections": {"type": "array", "items": {
                      "type": "object", "additionalProperties": False,
                      "required": ["section_name", "starts_at_shot", "positive_local_styles",
                                   "negative_local_styles"],
                      "properties": {"section_name": {"type": "string"}, "starts_at_shot": {"type": "string"},
                                     "positive_local_styles": {"type": "array", "items": {"type": "string"}},
                                     "negative_local_styles": {"type": "array", "items": {"type": "string"}}}}}}}


def score():
    """Muse Spark writes the composition plan to the cut; ElevenLabs Music performs it (one fal call)."""
    f = film()
    timeline = json.loads((FILM / "timeline.json").read_text(encoding="utf-8"))
    shots = {s["id"]: s for s in f["shots"]}
    desc = "\n".join(f"{sid} {t0:.1f}-{t1:.1f}s: {shots[sid]['motion'][:220]}" for sid, t0, t1 in timeline)
    meta.thread_context(shot="score")
    plan_ = meta.chat(SPARK, [
        {"role": "system", "content":
            "Write the film score's composition plan for an instrumental music model. 4-8 sections, each starting "
            "at a shot id from the timeline, following the story's emotion: quiet where it breathes, building into "
            "action, landing on the ending. Instruments and mood only; no vocals, no lyrics. The clips carry their "
            "own sound effects, so leave room for them."},
        {"role": "user", "content": f"Title: {f['title']}\nTimeline:\n{desc}"}],
        schema=SCORE_PLAN, max_tokens=8000, reasoning_effort="low", timeout=240)
    starts = {sid: t0 for sid, t0, _ in timeline}
    total = timeline[-1][2]
    secs = [s for s in plan_["sections"] if s["starts_at_shot"] in starts]
    secs.sort(key=lambda s: starts[s["starts_at_shot"]])
    secs[0]["starts_at_shot"] = timeline[0][0]
    bounds = [starts[s["starts_at_shot"]] for s in secs] + [total]
    sections = []
    for s, a, b in zip(secs, bounds, bounds[1:]):
        if b - a < 3:
            continue
        sections.append({"section_name": s["section_name"], "duration_ms": int(min(120000, (b - a) * 1000)),
                         "lines": [], "positive_local_styles": s["positive_local_styles"],
                         "negative_local_styles": s["negative_local_styles"]})
    body = {"composition_plan": {"positive_global_styles": plan_["positive_global_styles"],
                                 "negative_global_styles": plan_["negative_global_styles"] + ["vocals", "lyrics"],
                                 "sections": sections},
            "respect_sections_durations": True, "output_format": "mp3_44100_192"}
    (FILM / "score.plan.json").write_text(json.dumps(body, indent=1, ensure_ascii=False), encoding="utf-8")
    out = FILM / f"score_v{len(list(FILM.glob('score_v*.mp3'))) + 1}.mp3"
    i2v.audio("music_el", body, out, total)
    say(f"wrote {out}")


def voice(only=()):
    """ElevenLabs v3 TTS for each shot's "voice" lines ({"text", "voice", "at"}), one fal call per line."""
    f = film()
    jobs = []
    for s in pick(f["shots"], only):
        for k, line in enumerate(s.get("voice", []), 1):
            out = shot_dir(s["id"]) / f"voice_{k}.mp3"
            if out.exists():
                continue
            body = {"text": line["text"], "voice": line.get("voice", "Brian"),
                    "stability": line.get("stability", 0.5), "language_code": "en"}

            def job(s=s, body=body, out=out):
                meta.thread_context(shot=s["id"])
                i2v.audio("tts_el", body, out, len(body["text"]))
            jobs.append((f"{s['id']}.{out.stem}", job))
    say(f"voice: {len(jobs)} lines")
    run_parallel(jobs, workers=4)
    say(f"fal: ledger/real {i2v.reconcile()}, balance ${i2v.balance()}")


def _voice_lines():
    """[(file, film time in s, gain dB)] for every generated voice line of a shot in the cut."""
    timeline = json.loads((FILM / "timeline.json").read_text(encoding="utf-8"))
    shots = {s["id"]: s for s in film()["shots"]}
    out = []
    for sid, t0, _ in timeline:
        s = shots[sid]
        a = (s.get("trim") or [0])[0]
        for k, line in enumerate(s.get("voice", []), 1):
            p = shot_dir(sid) / f"voice_{k}.mp3"
            if p.exists():
                out.append((p, t0 + max(0.0, float(line.get("at", 0)) - a), line.get("gain_db", 0)))
    return out


def mix(score_db=-9.0):
    """The rough cut's own sound with the score under it, levelled to -16 LUFS."""
    scores = sorted(FILM.glob("score_v*.mp3"), key=lambda p: p.stat().st_mtime)
    src = FILM / "rough_cut.mp4"
    out = FILM / "film_final.mp4"
    if not scores:
        say("no score yet: run score, or put a licensed track in films/bootcamp/score_v1.mp3")
        return
    lines = _voice_lines()
    ins, chain = [], ""
    for i, (p, t, g) in enumerate(lines, 2):
        ins += ["-i", p]
        chain += f"[{i}:a]aresample=48000,volume={g}dB,adelay={int(t * 1000)}:all=1[v{i}];"
    pads = "[0:a][m]" + "".join(f"[v{i}]" for i in range(2, len(lines) + 2))
    ff("-i", src, "-i", scores[-1], *ins, "-filter_complex",
       f"[1:a]volume={score_db}dB,afade=out:st={duration(src) - 3:.2f}:d=3[m];{chain}"
       f"{pads}amix=inputs={len(lines) + 2}:normalize=0:duration=first,loudnorm=I=-16:TP=-1.5:LRA=11,"
       "aresample=48000[a]",
       "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out)
    say(f"wrote {out} (score {scores[-1].name} at {score_db} dB)")


def status():
    f = film()
    for s in f["shots"]:
        st = state(s["id"])
        frames = sum(frame_path(s["id"], fr["name"]).exists() for fr in s["frames"])
        takes = st.get("takes", [])
        b = best_take(s["id"])
        sc = (b or {}).get("review", {}).get("score") if b else None
        say(f"  {s['id']}: frames {frames}/{len(s['frames'])}, takes {len(takes)}, best {sc}")
    ledger, real = i2v.reconcile()
    say(f"fal ledger ${ledger:.2f} (real ${real}), balance ${i2v.balance()}, cap ${i2v.BUDGET:.2f}; "
        f"Meta ledger ${meta.spent():.2f}")


def statement():
    """Draft of the AI Creation Statement from the generation log (docs/BOOTCAMP.md has the form)."""
    entries = [json.loads(l) for l in meta.LOG.read_text(encoding="utf-8").splitlines()
               if '"film": "bootcamp"' in l]
    by = {}
    for e in entries:
        m = by.setdefault(e.get("model", "?"), [0, 0.0])
        m[0] += 1
        m[1] += e.get("cost_usd") or meta.PRICES.get(e.get("model"), 0.0)
    roles = {"muse-image-1.0": "Meta Muse Image: character sheets and every keyframe",
             "muse-spark-1.3": "Meta Muse Spark: shot plan, keyframe and take reviews, prompt rewrites, score plan",
             "muse-wonder-1.0": "Meta Muse Wonder: critique of the cut",
             "flux3": "FLUX 3 Max (Black Forest Labs, via fal.ai): image-to-video with sound effects",
             "flux3_kf": "FLUX 3 Max keyframes-to-video (via fal.ai): the time-lapse shot",
             "music_el": "ElevenLabs Music (via fal.ai): the score",
             "tts_el": "ElevenLabs v3 text-to-speech (via fal.ai): off-screen English dialogue"}
    lines = [f"# AI Creation Statement draft: {film()['title']}", "", "| Tool | Purpose | Calls | Cost (USD) | Online/Offline |",
             "|---|---|---|---|---|"]
    for m, (n, c) in sorted(by.items()):
        lines.append(f"| {m} | {roles.get(m, '')} | {n} | {c:.2f} | Online |")
    lines += ["| Claude (Anthropic) | Pipeline code, story adaptation with the team | - | - | Online |",
              "| ffmpeg | Editing, assembly, audio mix | - | - | Offline |", ""]
    out = FILM / "AI_CREATION_STATEMENT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    say(f"wrote {out} ({len(entries)} logged calls)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["plan", "sheets", "keyframes", "quote", "video", "review", "cut", "score",
                                      "voice", "mix", "status", "statement"])
    ap.add_argument("--shots", default="")
    ap.add_argument("--brief", default="docs/BOOTCAMP_FILM.md,docs/FLUX3_PLAYBOOK.md")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--revised", action="store_true", help="video: use Muse Spark's revised prompt from the review")
    ap.add_argument("--yes", action="store_true", help="video/score: allow fal spending")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    meta.CONTEXT["film"] = "bootcamp"
    only = set(filter(None, a.shots.split(",")))
    if a.stage in ("video", "score", "voice") and not a.yes:
        quote(only) if a.stage == "video" else None
        sys.exit(f"{a.stage} spends fal money: add --yes once the team has agreed.")
    {"plan": lambda: plan([ROOT / p for p in a.brief.split(",")]),
     "sheets": lambda: sheets(a.force, only), "keyframes": lambda: keyframes(only, a.force), "quote": lambda: quote(only),
     "video": lambda: video(only, a.revised), "review": lambda: review(only), "cut": cut, "score": score, "voice": lambda: voice(only),
     "mix": mix, "status": status, "statement": statement}[a.stage]()


if __name__ == "__main__":
    main()
