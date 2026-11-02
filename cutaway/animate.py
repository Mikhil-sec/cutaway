"""Animate the keyframes with an image-to-video model (Wan 3.0 on fal), directed by Muse Spark.

    python -m cutaway.director films/dodo motion           # Muse Spark plans every shot's motion, as one film
    python -m cutaway.director films/dodo i2v [--shots ..]  # takes, reviews, retakes, within the budget
    python -m cutaway.director films/dodo upscale           # chosen takes to 1920x1080 with Real-ESRGAN

Division of labour, as in the rest of the director: Muse Spark writes the motion prompts (seeing every
keyframe and the story, so shots lead into each other) and judges every take against its keyframe;
the video model only animates; code holds the budget and decides what gets re-done.

Spending rules (the user's own money, see i2v.py for the hard cap and fal reconciliation):
- PRODUCTION_CEILING_USD is an absolute fal ledger total, so running this in pieces cannot add up to more.
- Phase 1 gives every shot one take before phase 2 spends anything on retakes, and retakes always leave
  enough for the first takes of shots not yet made, so a budget stop never leaves a shot with no clip.
- Retakes go to the worst-reviewed shots first: WAN_TAKES with Wan, then FALLBACK_TAKES with Kling 2.6 Pro.
"""
import json
import math
import shutil
import subprocess
from pathlib import Path

from . import i2v, meta

SPARK = "muse-spark-1.3"
MODEL = "wan30"
# fal ledger total. 2026-11-01: $4.45 tests + production, raised from 30.50 at the user's request to use
# what is loaded ($35) and stop cleanly at it; the $45 hard cap in i2v.py sits above.
PRODUCTION_CEILING_USD = 44.00
WAN_TAKES = 2    # per shot; then the fallback model (the user's call, 2026-11-01)
FALLBACK = "kling26"  # Kling 2.6 Pro: the most faithful in the bake-off, $0.07/s exact, native 1080p
FALLBACK_TAKES = 2
ACCEPT_SCORE = 7
FPS = 24
TRANSITIONS = ["cut", "crossfade", "fade_from_black"]


def _schema(props):
    return {"type": "object", "additionalProperties": False, "properties": props, "required": list(props)}


S, I, B = {"type": "string"}, {"type": "integer"}, {"type": "boolean"}

MOTION_PLAN = _schema({
    "flow_notes": S,
    "shots": {"type": "array", "items": _schema({
        "shot_id": S,
        "motion_prompt": S,
        "ends_on": S,
        "transition_in": {"type": "string", "enum": TRANSITIONS},
    })},
})

TAKE_REVIEW = _schema({
    "score": I,
    "on_model": B,
    "same_place": B,
    "beat_delivered": B,
    "problems": {"type": "array", "items": S},
    "revised_prompt": S,
})


def painted(film, only=None):
    return [s for s in film.shots(only) if s["kind"] == "painted"]


def seconds(shot, model=MODEL):
    if model == FALLBACK:  # Kling makes 5 or 10 s clips; a 5 s clip for a shot up to 6 s just ends it sooner
        return 5 if shot["duration_s"] <= 6 else 10
    return max(2, math.ceil(shot["duration_s"]))


def next_model(st):
    """Which model the shot's next retake uses, or None when it has had all its takes."""
    used = [t.get("model", MODEL) for t in st.get("i2v_takes", [])]
    if used.count(MODEL) < WAN_TAKES:
        return MODEL
    if used.count(FALLBACK) < FALLBACK_TAKES:
        return FALLBACK
    return None


def motion_path(film):
    return film.root / "motion.json"


def load_motion(film):
    p = motion_path(film)
    return {s["shot_id"]: s for s in json.loads(p.read_text(encoding="utf-8"))["shots"]} if p.exists() else {}


# ---------------------------------------------------------------- motion plan

def plan_motion(film, force=False):
    """One Muse Spark call sees the story and every keyframe and writes each shot's motion prompt, so the
    shots are directed as one film: what each shot ends on sets up the cut into the next."""
    if motion_path(film).exists() and not force:
        return load_motion(film)
    meta.CONTEXT.pop("shot", None)
    shots = painted(film)
    content = [{"type": "text", "text":
                f"Story brief:\n{(film.root / 'story.md').read_text(encoding='utf-8')}\n\nThe shots, in order, "
                f"each followed by its keyframe (the painted first frame the video model will animate):"}]
    for s in shots:
        content.append({"type": "text", "text":
                        f"\n{s['id']} (beat {s['beat']}, {s['duration_s']} s, planned camera {s['camera_move']} "
                        f"{s['intensity']}, action {s['action']}, atmosphere {s['atmosphere']}, transition in "
                        f"{s['transition_in']}). Frame: {s['keyframe_prompt'][:400]}"})
        content.append({"type": "image_url", "image_url": {"url": str(film.shot_dir(s) / "keyframe.png")}})
    r = meta.chat(SPARK, [
        {"role": "system", "content":
            "You are the director of a wordless animated short. Each shot will be animated from its painted "
            "keyframe by an image-to-video model that follows a short motion prompt. Write the prompts so the "
            "film flows like a movie, not a slideshow: purposeful character acting, natural secondary motion "
            "(people, traffic, cloth, mist, light), and a camera that moves with intent. Think across cuts: "
            "what each shot ends on (a look, a movement, a direction of travel) should lead into the next "
            "shot, and pick each transition_in (cut for action and shocks, crossfade for time passing or "
            "dreamlike links, fade_from_black only to open). Rules for every motion_prompt: present tense, "
            "40-80 words; describe only motion and camera, not the style; the dodo is the one in the "
            "keyframe and stays exactly that bird (no new birds unless the frame already has several); stay "
            "in the place shown, with no new buildings, streets or landscapes entering the frame; keep the "
            "camera move moderate so the painted place stays recognisable; no text, no speech, no faces in "
            "close-up; the motion must fit within the shot's duration. ends_on: one sentence describing the "
            "final moment. Return one entry per shot, in order, with the same shot ids."},
        {"role": "user", "content": content},
    ], schema=MOTION_PLAN, max_tokens=16000, reasoning_effort="medium")
    ids = [s["id"] for s in shots]
    got = [x["shot_id"] for x in r["shots"]]
    if got != ids:
        raise RuntimeError(f"motion plan shot ids {got} do not match the film's {ids}")
    motion_path(film).write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"motion plan: {r['flow_notes']}")
    return load_motion(film)


def revise_motion(film, ids, lesson):
    """Muse Spark rewrites the motion prompts of shots not yet animated, given what the reviews of the
    shots so far taught us about the video model. Ends, transitions and the film's flow are kept."""
    motion = json.loads(motion_path(film).read_text(encoding="utf-8"))
    by_id = {s["shot_id"]: s for s in motion["shots"]}
    shots = [s for s in painted(film) if s["id"] in ids]
    rejected = [f"{s['id']}: {t['review']['problems']}" for s in painted(film)
                for t in film.state(s).get("i2v_takes", []) if t.get("review") and not accepted(t["review"])]
    content = [{"type": "text", "text": f"Lesson from this production: {lesson}\nRejected takes so far:\n"
                                        + "\n".join(rejected) + "\n\nRewrite these shots' motion prompts:"}]
    for s in shots:
        m = by_id[s["id"]]
        content.append({"type": "text", "text": f"\n{s['id']} ({s['duration_s']} s). Current prompt: "
                                                f"{m['motion_prompt']}\nIt must still end on: {m['ends_on']}"})
        content.append({"type": "image_url", "image_url": {"url": str(film.shot_dir(s) / "keyframe.png")}})
    meta.CONTEXT.pop("shot", None)
    r = meta.chat(SPARK, [
        {"role": "system", "content":
            "You direct an image-to-video model animating painted keyframes for a wordless short film. Rewrite "
            "each motion prompt (present tense, 40-80 words, one consistent description) to follow the lesson, "
            "keep the shot's story beat and the moment it ends on, and keep the life in the shot through the "
            "character's acting and secondary motion (people, traffic, water, cloth, mist, light). Return one "
            "entry per shot, same ids, in order."},
        {"role": "user", "content": content},
    ], schema=_schema({"shots": {"type": "array", "items": _schema({"shot_id": S, "motion_prompt": S})}}),
        max_tokens=12000, reasoning_effort="medium")
    got = [x["shot_id"] for x in r["shots"]]
    if got != [s["id"] for s in shots]:
        raise RuntimeError(f"revised ids {got} do not match {[s['id'] for s in shots]}")
    for x in r["shots"]:
        m = by_id[x["shot_id"]]
        m.setdefault("previous_prompts", []).append(m["motion_prompt"])
        m["motion_prompt"] = x["motion_prompt"]
        m["revised_by"] = f"Muse Spark, after reviews: {lesson[:120]}"
    motion_path(film).write_text(json.dumps(motion, indent=2, ensure_ascii=False), encoding="utf-8")
    return r


# ---------------------------------------------------------------- takes and reviews

class Stopped(RuntimeError):
    pass


def make_take(film, shot, prompt, model=MODEL):
    # The clean way to stop a run: create <film>/i2v.stop; it finishes the clip in hand and stops before the
    # next. Killing the process can leave a request sent but never collected (paid for nothing).
    if (film.root / "i2v.stop").exists():
        raise Stopped(f"{film.root / 'i2v.stop'} exists")
    st = film.state(shot)
    takes = st.setdefault("i2v_takes", [])
    n = len(takes) + 1
    out = film.shot_dir(shot) / f"take_{n}.mp4"
    waiting = sorted(film.shot_dir(shot).glob("take_*.pending.json"))
    if waiting:  # a paid request an earlier run never collected: collect it under its own take number
        out = waiting[0].with_name(waiting[0].name.replace(".pending.json", ".mp4"))
        n = int(out.stem.split("_")[1])
    meta.CONTEXT["shot"] = shot["id"]
    meta.CONTEXT["stage"] = "i2v"
    if waiting:
        model = json.loads(waiting[0].read_text(encoding="utf-8")).get("model", model)
    res = i2v.generate(model, film.shot_dir(shot) / "keyframe.png", prompt, out, seconds=seconds(shot, model),
                       limit=PRODUCTION_CEILING_USD)
    takes.append({"take": n, "file": out.name, "model": model, "prompt": res["_prompt"],
                  "seconds": seconds(shot, model)})
    film.save_state(shot)
    return takes[-1]


def review_take(film, shot, take, motion):
    """Muse Spark watches the take next to its keyframe. Returns the review, or None if it stays invalid."""
    from .director import shot_brief
    meta.CONTEXT["shot"] = shot["id"]
    d = film.shot_dir(shot)
    messages = lambda: [  # built fresh per call: meta.chat inlines media into the dicts it is given
        {"role": "system", "content":
            "You are the director reviewing one take from an image-to-video model for a wordless animated "
            "short. The first image is the approved keyframe; the video should animate it. Judge: does it "
            "work as a film shot and deliver its story beat; is the dodo the same bird as in the keyframe "
            "throughout (shape, colours, beak; no morphing, extra limbs or second dodo appearing); does it stay "
            "in the same place (no invented buildings or landscapes replacing the painting); is the motion "
            "natural; any flicker, melting or broken anatomy. score is an integer 0-10 (7 means usable in the "
            "film). problems: specific, short. revised_prompt: a complete rewritten motion prompt (40-80 words, "
            "one consistent description, not the old prompt plus corrections) that would fix the problems; "
            "repeat the current prompt if nothing needs fixing."},
        {"role": "user", "content": [
            {"type": "text", "text": f"{shot_brief(film, shot)}\nPlanned motion: {motion['motion_prompt']}\n"
                                     f"Should end on: {motion['ends_on']}\nPrompt used for this take: "
                                     f"{take['prompt']}"},
            {"type": "image_url", "image_url": {"url": str(d / "keyframe.png")}},
            {"type": "video_url", "video_url": {"url": str(d / take["file"]), "fps": 3}},
        ]},
    ]
    for effort in ("low", "medium"):  # a review that leaves its scale or names no reason is retried, then ignored
        r = meta.chat(SPARK, messages(), schema=TAKE_REVIEW, max_tokens=8000, reasoning_effort=effort)
        if 0 <= r["score"] <= 10 and r["revised_prompt"].strip() and (r["score"] >= ACCEPT_SCORE or r["problems"]):
            return r
    return None


def accepted(review):
    return bool(review) and review["score"] >= ACCEPT_SCORE and review["on_model"] and review["same_place"]


def best(st):
    reviewed = [t for t in st.get("i2v_takes", []) if t.get("review")]
    return max(reviewed, key=lambda t: t["review"]["score"], default=None)


def choose(film, shot):
    """Copy the best take, trimmed to the shot's length at 24 fps, to shot_i2v_1280.mp4."""
    st = film.state(shot)
    pick = best(st) or next((t for t in reversed(st.get("i2v_takes", [])) if t.get("file")), None)
    if not pick:
        return None
    d = film.shot_dir(shot)
    sizes = [(1280, 720)] + ([(1920, 1080)] if pick.get("model") == FALLBACK else [])  # Kling is native 1080p
    for w, h in sizes:  # the 1080p copy is written last, so upscale() sees it as current and skips it
        out = d / f"shot_i2v_{w}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(d / pick["file"]), "-t", str(shot["duration_s"]),
                        "-vf", f"fps={FPS},scale={w}:{h}:flags=lanczos,setsar=1", "-an", "-c:v", "libx264", "-crf",
                        "16", "-pix_fmt", "yuv420p", str(out)], check=True)
    out = d / "shot_i2v_1280.mp4"
    st["i2v_choice"] = pick["take"]
    film.save_state(shot)
    return out


def _review_pending(film, shot, motion):
    st = film.state(shot)
    for t in st.get("i2v_takes", []):
        if "review" not in t:
            r = review_take(film, shot, t, motion)
            t["review"] = r or {"score": -1, "on_model": False, "same_place": False, "beat_delivered": False,
                                "problems": ["review invalid twice"], "revised_prompt": t["prompt"]}
            film.save_state(shot)
            print(f"  {shot['id']} take {t['take']}: {t['review']['score']}/10 "
                  f"{'ACCEPT' if accepted(t['review']) else 'retake?'} {t['review']['problems'][:2]}", flush=True)


def reset_takes(film, shot, why):
    """Start a shot's takes over (after its keyframe or motion changed). Nothing is deleted: the old takes
    stay on record, and their files are renamed so new takes can't overwrite them."""
    st = film.state(shot)
    old = st.pop("i2v_takes", [])
    d = film.shot_dir(shot)
    n = len(st.get("i2v_takes_prev", []))
    for t in old:
        if t.get("file") and (d / t["file"]).exists():
            new = f"prev{n}_{t['file']}"
            (d / t["file"]).rename(d / new)
            t["file"] = new
    st.setdefault("i2v_takes_prev", []).append({"why": why, "takes": old})
    st.pop("i2v_choice", None)
    film.save_state(shot)


def first_takes_reserve(film, exclude=()):
    """What the first takes of shots that have none would cost: retakes must leave this much."""
    return sum(i2v.quote(MODEL, seconds(s))[1] for s in painted(film)
               if s["id"] not in exclude and not film.state(s).get("i2v_takes"))


def produce(film, only=None):
    motion = plan_motion(film)
    shots = painted(film, only)
    print(f"fal: ledger/real {i2v.reconcile()}, balance ${i2v.balance()}, production ceiling "
          f"${PRODUCTION_CEILING_USD:.2f}; one pass of these shots = "
          f"${sum(i2v.quote(MODEL, seconds(s))[0] for s in shots):.2f}", flush=True)
    halted = False
    # Phase 1: one take for every shot (and any paid request an earlier run left uncollected).
    for shot in shots:
        st = film.state(shot)
        if not st.get("i2v_takes") or list(film.shot_dir(shot).glob("take_*.pending.json")):
            try:
                make_take(film, shot, motion[shot["id"]]["motion_prompt"])
            except (i2v.BudgetError, Stopped) as e:
                print(f"STOP before {shot['id']}: {e}")
                halted = True
                break
            except TimeoutError as e:  # offline or asleep: stop; the next run collects the paid request
                print(f"STOP (timeout) at {shot['id']}: {e}", flush=True)
                halted = True
                break
            except Exception as e:  # one failed clip must not stop the film
                print(f"FAILED {shot['id']}: {e}", flush=True)
                continue
        _review_pending(film, shot, motion[shot["id"]])
    # Phase 2: retakes, worst shots first, never eating into first takes still owed elsewhere.
    while not halted:
        todo = [s for s in shots if film.state(s).get("i2v_takes") and not accepted((best(film.state(s)) or {}).get("review"))
                and next_model(film.state(s))]
        if not todo:
            break
        shot = min(todo, key=lambda s: best(film.state(s))["review"]["score"] if best(film.state(s)) else -1)
        model = next_model(film.state(shot))
        cost = i2v.quote(model, seconds(shot, model))[1]
        headroom = PRODUCTION_CEILING_USD - i2v.spent() - first_takes_reserve(film)
        if cost > headroom:
            print(f"retakes stop: ${headroom:.2f} headroom after reserving first takes; {shot['id']} needs ${cost:.2f}")
            break
        prev = best(film.state(shot))
        prompt = prev["review"]["revised_prompt"] if prev else motion[shot["id"]]["motion_prompt"]
        try:
            make_take(film, shot, prompt, model)
        except (i2v.BudgetError, Stopped) as e:
            print(f"STOP: {e}")
            break
        except TimeoutError as e:
            print(f"STOP (timeout) at {shot['id']}: {e}", flush=True)
            break
        except Exception as e:
            print(f"FAILED retake {shot['id']}: {e}", flush=True)
            film.state(shot)["i2v_takes"].append({"take": len(film.state(shot)["i2v_takes"]) + 1, "failed": str(e),
                                                  "model": model, "review": None})  # counts, so it can't loop
            film.save_state(shot)
            continue
        _review_pending(film, shot, motion[shot["id"]])
    for shot in shots:
        if choose(film, shot):
            b = best(film.state(shot))
            print(f"  {shot['id']}: take {film.state(shot)['i2v_choice']} chosen "
                  f"({b['review']['score'] if b else '?'}/10)")
    print(f"fal: ledger/real {i2v.reconcile()}, balance ${i2v.balance()}")


# ---------------------------------------------------------------- upscale

ESRGAN = meta.ROOT / "tools" / "realesrgan" / "realesrgan-ncnn-vulkan.exe"


def upscale(film, only=None):
    """Real-ESRGAN's anime video model, 2x, then down to 1920x1080: free, on the local GPU (~3 s a frame)."""
    for shot in painted(film, only):
        d = film.shot_dir(shot)
        src, out = d / "shot_i2v_1280.mp4", d / "shot_i2v_1920.mp4"
        if not src.exists() or (out.exists() and out.stat().st_mtime > src.stat().st_mtime):
            continue
        tmp = d / "_upscale"
        shutil.rmtree(tmp, ignore_errors=True)
        (tmp / "in").mkdir(parents=True)
        (tmp / "out").mkdir()
        subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(src), str(tmp / "in" / "%04d.png")], check=True)
        subprocess.run([str(ESRGAN), "-i", str(tmp / "in"), "-o", str(tmp / "out"), "-n", "realesr-animevideov3",
                        "-s", "2", "-f", "png"], check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "out" / "%04d.png"),
                        "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                        str(out)], check=True)
        shutil.rmtree(tmp)
        print(f"  {shot['id']} upscaled", flush=True)
