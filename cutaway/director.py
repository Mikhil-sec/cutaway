"""The director agent: story -> shot list -> keyframes -> layers -> shot specs -> renders -> cut.

    python -m cutaway.director films/dodo plan
    python -m cutaway.director films/dodo keyframes [--shots s01,s02]
    python -m cutaway.director films/dodo layers    [--shots ...]
    python -m cutaway.director films/dodo specs     [--shots ...]
    python -m cutaway.director films/dodo render    [--shots ...] [--preview] [--final]
    python -m cutaway.director films/dodo storyboard

Every stage is idempotent: it skips work whose outputs exist, and all state
lives in <film>/plan.json, so a crash or a budget stop resumes where it left off.

Division of labour: Muse Spark makes the creative choices, always inside a
JSON schema (named camera moves, actions, atmospheres); code does the
geometry, checks the results and decides what gets re-done.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from . import camera, keyframes, meta, puppet
from .sheet import contact_sheet

SPARK = "muse-spark-1.3"
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
ATMOSPHERES = ["none", "mist", "dust", "rain", "flashes", "light_shafts"]
TRANSITIONS = ["cut", "crossfade", "fade_from_black"]
FOCUS = ["foreground", "subject", "background"]
BACK_DEPTH, FG_DEPTH, SUBJECT_DEPTH = 40.0, 5.0, 12.0
ASPECT = 16 / 9


# ---------------------------------------------------------------- state

class Film:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.repo = meta.ROOT
        self.refs = json.loads((self.root / "refs.json").read_text(encoding="utf-8"))
        self.plan_path = self.root / "plan.json"
        self.plan = json.loads(self.plan_path.read_text(encoding="utf-8")) if self.plan_path.exists() else None
        if self.plan:  # each shot's revisions are the source of truth: parallel runs may overwrite plan.json
            for shot in self.plan["shots"]:
                for rev in self.state(shot).get("revisions", []):
                    shot.update(rev["changes"])

    def save(self):
        """Writes the plan itself; per-shot progress lives in shots/<id>/state.json (see state())."""
        plan = {**self.plan, "shots": [{k: v for k, v in s.items() if k not in ("state", "_state")}
                                       for s in self.plan["shots"]]}
        self.plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    def shot_dir(self, shot):
        d = self.root / "shots" / shot["id"]
        d.mkdir(parents=True, exist_ok=True)
        return d

    def state(self, shot):
        """A shot's progress, in its own file so stages can run on different shots in parallel."""
        if "_state" not in shot:
            path = self.shot_dir(shot) / "state.json"
            shot["_state"] = (json.loads(path.read_text(encoding="utf-8-sig")) if path.exists()
                              else shot.get("state", {}))
        return shot["_state"]

    def save_state(self, shot):
        (self.shot_dir(shot) / "state.json").write_text(
            json.dumps(self.state(shot), indent=2, ensure_ascii=False), encoding="utf-8")

    def shots(self, only=None):
        return [s for s in self.plan["shots"] if not only or s["id"] in only]

    def ref_path(self, rel):
        return self.repo / rel


def strict(props, **kw):
    """A strict JSON-schema object: every property required, nothing extra."""
    return {"type": "object", "additionalProperties": False, "properties": props, "required": list(props), **kw}


S, I, N, B = {"type": "string"}, {"type": "integer"}, {"type": "number"}, {"type": "boolean"}


def enum(values):
    return {"type": "string", "enum": values}


def arr(items):
    return {"type": "array", "items": items}


# ---------------------------------------------------------------- 1. plan

def plan(film):
    if film.plan:
        print("plan exists; delete plan.json to replan")
        return
    chars = list(film.refs["characters"])
    places = [p["file"] for p in film.refs["places"]]
    shot = strict({
        "id": S,
        "beat": I,
        "kind": enum(["painted", "end_card"]),
        "duration_s": N,
        "keyframe_prompt": S,
        "characters": arr(enum(chars)),
        "place_refs": arr(enum(places)),
        "subjects": arr(S),
        "ground": S,
        "foreground": S,
        "camera_move": enum(camera.MOVES),
        "intensity": enum(list(camera.INTENSITY)),
        "focus_from": enum(FOCUS),
        "focus_to": enum(FOCUS),
        "action": enum(puppet.ACTIONS),
        "atmosphere": enum(ATMOSPHERES),
        "transition_in": enum(TRANSITIONS),
        "sound": S,
        "end_card_text": S,
    })
    schema = strict({"title": S, "logline": S, "style": S, "shots": arr(shot)})
    places_text = "\n".join(f"- {p['file']}: {p['place']} ({p['shows']})" for p in film.refs["places"])
    chars_text = "\n".join(f"- {k}: {v['description']}" for k, v in film.refs["characters"].items())
    system = f"""You are the director of a short animated film made in 2.5D: each shot is ONE painted still
that is cut into depth layers (background, ground, characters, foreground) and filmed with a moving
virtual camera. Characters can breathe and move their heads, and hop slightly; they cannot walk, run
or change pose within a shot. Show movement through cuts between shots instead.

Write the shot list for the story below.
- Total duration 140-165 seconds; 18-26 shots; painted shots last 4-9 seconds; vary shot sizes
  (wide, medium, close) and camera moves like a real film. Use strong moves for key moments only.
- keyframe_prompt: a complete description of the single painted frame: shot size, composition,
  where each character is in the frame (left/centre/right third), full body visible and standing on
  visible ground, what they are doing, the setting with specific Mauritian details, light and mood.
  Characters must not overlap each other. No legible text, logos or brand names anywhere.
- characters: which named characters appear (only these exist):
{chars_text}
- place_refs: 0-2 reference photos of the real place this shot shows (only from this list):
{places_text}
- subjects: short noun phrases a segmentation model can find for every character in the frame that
  should move on its own, e.g. "dodo". Humans in the background are not subjects. Empty for shots
  without characters.
- ground: short noun phrase for the surface the main character stands on (e.g. "mossy rock",
  "pavement"), or "" if not useful. foreground: a noun phrase for near-camera elements at the frame's
  bottom or sides (e.g. "fern leaves", "umbrellas"), or "".
- action: what the main character's head does. atmosphere: one effect. focus_from/focus_to: where
  the focus starts and ends (rack focus when they differ).
- The last shot is an end card: kind "end_card", end_card_text set, keyframe_prompt "".
- style: one sentence describing the visual style, prefixed to every keyframe prompt."""
    print("planning with Muse Spark...")
    result = meta.chat(SPARK, [
        {"role": "system", "content": system},
        {"role": "user", "content": (film.root / "story.md").read_text(encoding="utf-8")},
    ], schema=schema, max_tokens=24000, reasoning_effort="high")
    film.plan = validate_plan(result, film)
    film.save()
    total = sum(s["duration_s"] for s in film.plan["shots"])
    print(f"{len(film.plan['shots'])} shots, {total:.0f} s: {film.plan['title']}")


def validate_plan(p, film):
    """Code-side checks the schema can't express; fixes what it can."""
    seen = set()
    for i, s in enumerate(p["shots"]):
        if s["id"] in seen or not s["id"]:
            s["id"] = f"s{i + 1:02d}"
        seen.add(s["id"])
        s["duration_s"] = float(min(max(s["duration_s"], 3.0), 10.0))
        s["place_refs"] = s["place_refs"][:2]
    total = sum(s["duration_s"] for s in p["shots"])
    if not 95 <= total <= 175:  # keep well inside the competition's 90-180 s
        k = 150 / total
        for s in p["shots"]:
            s["duration_s"] = round(s["duration_s"] * k, 1)
    return p


# ---------------------------------------------------------------- 2. keyframes

CHECK_SCHEMA = strict({
    "character_score": I,
    "character_fully_visible": B,
    "matches_shot": B,
    "has_legible_text_or_logos": B,
    "style_match": B,
    "problems": arr(S),
})


def keyframe(film, shot):
    if shot["kind"] != "painted":
        return
    d = film.shot_dir(shot)
    out = d / "keyframe.png"
    st = film.state(shot)
    if out.exists() and st.get("keyframe_ok"):
        return
    chars = shot["characters"]
    sheets = [film.ref_path(film.refs["characters"][c]["sheet"]) for c in chars]
    places = [film.ref_path(p) for p in shot["place_refs"]]
    matches = [film.root / "shots" / sid / "keyframe.png" for sid in shot.get("match_shots", [])]
    base = f"{film.plan['style']} {shot['keyframe_prompt']}"
    if chars:
        base += (" Every " + ", ".join(chars) + " must match the character reference sheet exactly: same design, "
                 "colours and proportions.")
    if places:
        base += (" Use the reference photographs only for the real architecture and layout of this place in "
                 "Port Louis, Mauritius; repaint everything in the film's style.")
    if matches:  # a shot that continues another: same place, light and palette, seen from the new framing
        base += (" The last reference image is an earlier shot of the film in the same place: show the same "
                 "setting, surfaces, light and colours, from this shot's framing, so the cut reads as continuous.")
    base += " No legible text, logos or brand names."
    if st.get("repaint_notes"):  # why the previous painting was rejected by a review or critique
        base += " This repaint must fix: " + " ".join(st["repaint_notes"])
    notes = ""
    for attempt in range(3):
        prompt = base + (f" Avoid these problems from a previous attempt: {notes}" if notes else "")
        _, used = keyframes.generate(prompt, out, refs=sheets + places + matches)
        verdict = check_keyframe(film, shot, out, sheets)
        st.setdefault("keyframe_attempts", []).append({"prompt": used, "verdict": verdict})
        ok = (verdict["matches_shot"] and not verdict["has_legible_text_or_logos"] and verdict["style_match"]
              and (not chars or (verdict["character_score"] >= 7 and verdict["character_fully_visible"])))
        film.save_state(shot)
        print(f"  {shot['id']} keyframe attempt {attempt + 1}: {'ok' if ok else 'redo'} {verdict['problems'][:2]}")
        if ok:
            st["keyframe_ok"] = True
            film.save_state(shot)
            return
        notes = "; ".join(verdict["problems"])
    st["keyframe_ok"] = True  # best effort after 3 tries; the problems stay on record for review
    st["keyframe_flagged"] = True
    film.save_state(shot)


def check_keyframe(film, shot, img, sheets):
    content = [{"type": "text", "text": f"Shot description: {shot['keyframe_prompt']}"}]
    for c, sheet in zip(shot["characters"], sheets):
        content += [{"type": "text", "text": f"Reference sheet for '{c}':"},
                    {"type": "image_url", "image_url": {"url": str(sheet)}}]
    content += [{"type": "text", "text": "Generated keyframe:"}, {"type": "image_url", "image_url": {"url": str(img)}}]
    return meta.chat(SPARK, [
        {"role": "system", "content":
            "You are the continuity supervisor of an animated film. Check the generated keyframe. "
            "character_score: 0-10, how exactly each character matches its reference sheet in design "
            "(shape, beak, colours, markings, proportions; ignore pose and size); 10 if there are no "
            "characters. character_fully_visible: every character is entirely in frame and not cut off. "
            "matches_shot: the frame shows what the description asks for. has_legible_text_or_logos: any "
            "readable words, brand names or logos. style_match: painterly anime style, consistent with "
            "the sheets. problems: short, specific fixes for anything wrong."},
        {"role": "user", "content": content},
    ], schema=CHECK_SCHEMA, max_tokens=6000, reasoning_effort="low")


# ---------------------------------------------------------------- 3. layers

ALT_SCHEMA = strict({"phrases": arr(S)})


def find(img, phrase, min_conf=0.35):
    """SAM masks for a phrase; if none, ask Muse Spark for other phrasings and try those."""
    found = [(c, m) for c, m in meta.segment(img, phrase) if c >= min_conf]
    if found:
        return found, phrase
    alts = meta.chat(SPARK, [
        {"role": "system", "content": "A segmentation model found nothing for this noun phrase in a painted "
                                      "film frame. Give 3 alternative short noun phrases (1-3 words) for the "
                                      "same thing, most likely to work first."},
        {"role": "user", "content": phrase},
    ], schema=ALT_SCHEMA, max_tokens=3000, reasoning_effort="low")["phrases"]
    for alt in alts[:3]:
        found = [(c, m) for c, m in meta.segment(img, alt) if c >= min_conf]
        if found:
            return found, alt
    return [], phrase


def save_rgba(rgb, mask, path, feather=1.2):
    im = rgb.copy()
    im.putalpha(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(feather)))
    im.save(path)


def depth_for(feet_y, height):
    """Lower in the frame = nearer the camera."""
    return float(np.clip(SUBJECT_DEPTH * (0.78 * height) / max(feet_y, 1), 7.0, 24.0))


def layers(film, shot):
    if shot["kind"] != "painted":
        return
    d = film.shot_dir(shot)
    st = film.state(shot)
    if st.get("layers"):
        return
    kf = d / "keyframe.png"
    rgb = Image.open(kf).convert("RGB")
    W, H = rgb.size
    out = {"plate": None, "ground": None, "subjects": [], "foreground": None}

    # Characters, one puppet per instance (largest first, at most 6).
    instances = []
    for phrase in dict.fromkeys(shot["subjects"]):  # the planner sometimes lists one phrase per instance
        found, used = find(kf, phrase)
        heads = [m for _, m in meta.segment(kf, f"{used} head")] if found else []
        for conf, m in sorted(found, key=lambda t: -t[1].sum())[:6]:
            head = max(heads, key=lambda h: (h & m).sum(), default=np.zeros_like(m))
            instances.append((used, m, head if (head & m).any() else np.zeros_like(m)))
    occupied = np.zeros((H, W), dtype=bool)
    for n, (phrase, m, head) in enumerate(instances):
        occupied |= m
        name = f"{phrase.replace(' ', '_')}_{n}"
        img = d / f"{name}.png"
        save_rgba(rgb, m, img)
        pivots = puppet.build(m, head, d / f"{name}_weights.npy")
        out["subjects"].append({
            "name": name, "image": str(img), "weights": str(d / f"{name}_weights.npy"),
            "pivots": pivots, "facing": puppet.facing_from_mask(m, head),
            "depth": depth_for(pivots["feet"][1], H), "has_head": bool(head.any()),
            "bbox": [int(v) for v in Image.fromarray(m.astype(np.uint8) * 255).getbbox()],
        })

    # Clean plate: the frame with the characters removed, checked with SAM.
    plate = d / "plate.png"
    if instances:
        names = ", ".join(sorted({p for p, _, _ in instances}))
        for attempt in range(2):
            keyframes.generate(
                f"Remove every {names} from this image completely and fill in what was behind them. Keep "
                "everything else exactly the same: composition, colours, light and painting style.",
                plate, refs=[kf])
            with Image.open(plate) as p:
                if p.size != (W, H):
                    p.convert("RGB").resize((W, H), Image.LANCZOS).save(plate)
            leftovers = [m for p_ in sorted({p for p, _, _ in instances}) for c, m in meta.segment(plate, p_)
                         if c >= 0.5 and (m & occupied).sum() > 0.3 * m.sum()]
            if not leftovers:
                break
            print(f"  {shot['id']} plate still shows a character; retrying")
    else:
        rgb.save(plate)
    out["plate"] = str(plate)
    plate_rgb = Image.open(plate).convert("RGB")

    # Ground under the main character, at the character's depth so it doesn't slide.
    if shot["ground"] and out["subjects"]:
        main = out["subjects"][0]
        fx, fy = main["pivots"]["feet"]
        found, _ = find(plate, shot["ground"])
        ground = np.zeros((H, W), dtype=bool)
        for _, m in found:
            if m[min(fy + 12, H - 1), min(fx, W - 1)]:
                ground |= m
        if 0 < ground.mean() < 0.45:
            save_rgba(plate_rgb, ground, d / "ground.png")
            out["ground"] = {"image": str(d / "ground.png"), "depth": main["depth"] + 0.2}

    # Foreground: elements touching the bottom or side edges.
    if shot["foreground"]:
        found, _ = find(plate, shot["foreground"])
        fg = np.zeros((H, W), dtype=bool)
        for _, m in found:
            ys, xs = np.nonzero(m)
            if len(ys) and m.mean() < 0.3 and (ys.max() > 0.9 * H or xs.min() < 0.03 * W or xs.max() > 0.97 * W):
                fg |= m
        if fg.any():
            save_rgba(plate_rgb, fg, d / "foreground.png")
            out["foreground"] = {"image": str(d / "foreground.png"), "depth": FG_DEPTH}

    st["layers"] = out
    film.save_state(shot)
    print(f"  {shot['id']} layers: {len(out['subjects'])} characters, ground={bool(out['ground'])}, "
          f"foreground={bool(out['foreground'])}")


# ---------------------------------------------------------------- 4. specs

def touches_border(image, band=6):
    """Whether a layer's visible content reaches the frame border (its plane's edge would then show)."""
    a = np.asarray(Image.open(image).getchannel("A")) > 127
    return bool(a[:band].any() or a[-band:].any() or a[:, :band].any() or a[:, -band:].any())


def atmosphere(kind, subject_depth):
    """Fog cards and effects for a shot's planned atmosphere. Every shot gets a little air."""
    fog = [{"depth": 28, "opacity": 0.12, "speed": 0.08}]
    effects = [{"type": "motes", "depth": subject_depth * 0.7, "opacity": 0.25, "scale": 22}]
    if kind == "mist":
        fog = [{"depth": 28, "opacity": 0.22, "speed": 0.14}, {"depth": 8, "opacity": 0.06, "speed": 0.2}]
    elif kind in ("dust", "light_shafts"):
        effects = [{"type": "motes", "depth": subject_depth * 0.65, "opacity": 0.55, "scale": 20},
                   {"type": "motes", "depth": subject_depth * 1.6, "opacity": 0.35, "scale": 34,
                    "drift": [0.012, -0.006]}]
        if kind == "light_shafts":
            effects.append({"type": "shafts", "depth": subject_depth * 1.25, "opacity": 0.32})
    elif kind == "flashes":
        effects.append({"type": "flashes", "depth": subject_depth * 0.55, "count": 7, "rate": 0.3, "peak": 0.95})
    return fog, effects


def spec(film, shot, resolution=(960, 540)):
    if shot["kind"] != "painted":
        return None
    d = film.shot_dir(shot)
    L = film.state(shot)["layers"]
    with Image.open(L["plate"]) as p:
        image_size = list(p.size)
    spec_layers = [{"name": "plate", "image": L["plate"], "depth": BACK_DEPTH}]
    # Two cut-out cards in the same plane make dithered transparency fight over pixels (a camouflage
    # pattern), so keep characters at least GAP apart, nearest first, and the ground behind all of them.
    GAP = 0.08
    depths_sorted = sorted(range(len(L["subjects"])), key=lambda i: L["subjects"][i]["depth"])
    sdepths, last = {}, -1e9
    for i in depths_sorted:
        sdepths[i] = max(L["subjects"][i]["depth"], last + GAP)
        last = sdepths[i]
    if L["ground"]:
        g = dict(L["ground"])
        if sdepths:
            g["depth"] = max(g["depth"], max(sdepths.values()) + 0.2)
        spec_layers.append({"name": "ground", **g})
    for n, s in enumerate(L["subjects"]):
        s = {**s, "depth": sdepths[n]}
        anim = puppet.motion(shot["action"] if n == 0 else "idle", shot["duration_s"], seed=n + 1,
                             facing=s["facing"])
        if not s["has_head"]:
            anim.pop("bend", None)
        spec_layers.append({"name": s["name"], "image": s["image"], "depth": s["depth"],
                            "puppet": {"weights": s["weights"], "pivot": s["pivots"]["neck"],
                                       "feet": s["pivots"]["feet"]}, "anim": anim})
    if L["foreground"]:
        spec_layers.append({"name": "foreground", **L["foreground"], "wind": {"amp": 1.0, "period": 3.4}})
    shadows = [{"feet": s["pivots"]["feet"], "width_px": s["bbox"][2] - s["bbox"][0], "depth": sdepths[i]}
               for i, s in enumerate(L["subjects"])]

    main = {**L["subjects"][0], "depth": sdepths[0]} if L["subjects"] else None
    if main:
        x0, y0, x1, y1 = main["bbox"]
        wx, _, wz = camera.pixel_to_world((x0 + x1) / 2, (y0 + y1) / 2, main["depth"], image_size, ASPECT)
        sdepth = main["depth"]
    else:
        wx, wz, sdepth = 0.0, 0.0, SUBJECT_DEPTH

    def focus_name(f):
        if f == "foreground" and L["foreground"]:
            return "foreground"
        if f == "background" or not main:
            return "plate"
        return main["name"]

    keys = camera.move_keys(shot["camera_move"], shot["intensity"], shot["duration_s"], (wx, wz), sdepth,
                            focus_name(shot["focus_from"]), focus_name(shot["focus_to"]))
    subject = None
    if main:  # frame all the characters, not only the main one (the reveal has four dodos)
        bx0 = min(s["bbox"][0] for s in L["subjects"])
        by0 = min(s["bbox"][1] for s in L["subjects"])
        bx1 = max(s["bbox"][2] for s in L["subjects"])
        by1 = max(s["bbox"][3] for s in L["subjects"])
        ax, _, az = camera.pixel_to_world(bx0, by1, main["depth"], image_size, ASPECT)  # bottom-left
        bx, _, bz = camera.pixel_to_world(bx1, by0, main["depth"], image_size, ASPECT)  # top-right
        subject = ((ax, az, bx, bz), main["depth"])
    # Only the foreground needs its edges protected: the ground layer sits on the same painting it was
    # cut from, so its edge reveals the same pavement behind it, while a cut-off character is obvious.
    edge_depths = [L["foreground"]["depth"]] if L["foreground"] and touches_border(L["foreground"]["image"]) else []
    # Less margin (overscan) means less room for the move but less of the painting's edge cropped:
    # step it down until the characters stay in frame.
    for overscan in (1.25, 1.12, 1.05):
        camera.use_overscan(overscan)
        if subject:
            (x0, z0, x1, z1), sd = subject
            # The box was computed at the default margin; layer sizes scale with the margin.
            k = overscan / 1.25
            # One character needs room around it; a group only needs everyone in frame.
            margin = 0.12 if len(L["subjects"]) == 1 else 0.02
            fitted_subject = ((x0 * k, z0 * k, x1 * k, z1 * k), sd, margin)
        else:
            fitted_subject = None
        keys_o = [dict(k_) for k_ in keys]
        fitted, scale, framed = camera.fit_keys(keys_o, BACK_DEPTH, ASPECT, fitted_subject, edge_depths)
        if framed:
            break
    keys = fitted
    camera.use_overscan(1.25)
    fog, effects = atmosphere(shot["atmosphere"], sdepth)
    sp = {"name": shot["id"], "fps": 24, "seconds": shot["duration_s"], "resolution": list(resolution),
          "image_size": image_size, "layers": spec_layers, "fog": fog, "shadows": shadows, "effects": effects,
          # Scene units are metres and layers sit 5-40 m away, so a real f/2.4 blurs by under a pixel;
          # f/0.35 gives the shallow focus of a long lens on a large sensor.
          "camera": {"fstop": 0.35, "shake": {"deg": 0.12, "units": 0.008, "hz": 0.5}, "keys": keys}}
    if overscan != 1.25:  # only when it differs, so unchanged shots keep their spec (and their frames)
        sp["overscan"] = overscan
    path = d / f"spec_{resolution[0]}.json"
    path.write_text(json.dumps(sp, indent=2))
    film.state(shot)["camera_scale"] = scale
    film.save_state(shot)
    return path


# ---------------------------------------------------------------- 5. render

def render(film, shot, resolution=(960, 540), stills=None):
    if shot["kind"] != "painted":
        return None
    d = film.shot_dir(shot)
    sp = spec(film, shot, resolution)
    tag = f"{resolution[0]}"
    if stills:
        out = d / f"preview_{tag}"
        args = [str(sp), str(out), "--stills", ",".join(map(str, stills))]
    else:
        out = d / f"frames_{tag}"
        mp4 = d / f"shot_{tag}.mp4"
        # A clip is current only if it was made from exactly this spec; frames from an older spec (or empty
        # placeholders from an interrupted render) must not be reused either.
        stamp = out / ".spec"
        current = sp.read_text()
        stale = not stamp.exists() or stamp.read_text() != current
        if mp4.exists() and not stale:
            return mp4
        mp4.unlink(missing_ok=True)
        for f in out.glob("*.png"):
            if stale or f.stat().st_size == 0:
                f.unlink()
        out.mkdir(parents=True, exist_ok=True)
        stamp.write_text(current)
        args = [str(sp), str(out)]
    r = subprocess.run([BLENDER, "-b", "--factory-startup", "-P", str(film.repo / "cutaway" / "blender_shot.py"),
                        "--", *args], capture_output=True, text=True)
    if r.returncode or "Traceback" in r.stdout:
        raise RuntimeError(f"Blender failed on {shot['id']}:\n{r.stdout[-2500:]}\n{r.stderr[-1500:]}")
    if stills:
        return out
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", str(out / "frame_%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(mp4)], check=True)
    return mp4


# ---------------------------------------------------------------- 6. review (the critic loop)

INTENSITIES = list(camera.INTENSITY)
SHOT_REVIEW = strict({
    "score": I,
    "notes": arr(S),
    "camera_move": enum(camera.MOVES + ["keep"]),
    "intensity": enum(INTENSITIES + ["keep"]),
    "action": enum(puppet.ACTIONS + ["keep"]),
    "atmosphere": enum(ATMOSPHERES + ["keep"]),
    "duration": enum(["keep", "shorter", "longer"]),
    "redo_keyframe": B,
})


def shot_brief(film, shot):
    return (f"Film: {film.plan['title']}: {film.plan['logline']}\nShot {shot['id']} (story beat {shot['beat']}), "
            f"{shot['duration_s']} s. Intended frame: {shot['keyframe_prompt']}\nCamera: {shot['camera_move']} "
            f"({shot['intensity']}), focus {shot['focus_from']} -> {shot['focus_to']}. Character action: "
            f"{shot['action']}. Atmosphere: {shot['atmosphere']}.")


def review(film, shot, res=(960, 540), force=False):
    """Muse Spark watches the rendered shot; if it falls short, apply its changes once and re-render."""
    if shot["kind"] != "painted":
        return
    st = film.state(shot)
    mp4 = film.shot_dir(shot) / f"shot_{res[0]}.mp4"
    if (st.get("reviewed") and not force) or not mp4.exists():
        return
    meta.CONTEXT["shot"] = shot["id"]
    r = meta.chat(SPARK, [
        {"role": "system", "content":
            "You are the director reviewing a rendered shot of a 2.5D animated short (a painted still cut into "
            "depth layers, filmed with a virtual camera; characters can only breathe, bend their neck and hop). "
            "Judge whether it works as a film shot and serves its story beat: camera motion, character "
            "performance, atmosphere, timing, and anything that breaks the illusion. score 0-10. Then choose "
            "changes ONLY from the allowed values, or 'keep'. redo_keyframe only if the painted frame itself is "
            "wrong for the story (wrong place, character off-model, bad composition)."},
        {"role": "user", "content": [
            {"type": "text", "text": shot_brief(film, shot)},
            {"type": "video_url", "video_url": {"url": str(mp4), "fps": 3}},
        ]},
    ], schema=SHOT_REVIEW, max_tokens=8000, reasoning_effort="low")
    st.setdefault("reviews", []).append(r)
    st["reviewed"] = True
    changes = {k: r[k] for k in ("camera_move", "intensity", "action", "atmosphere") if r[k] not in ("keep", shot[k])}
    if r["duration"] != "keep":
        changes["duration_s"] = round(min(10, max(3, shot["duration_s"] * (0.8 if r["duration"] == "shorter" else 1.2))), 1)
    print(f"  {shot['id']} review {r['score']}/10 {r['notes'][:1]} changes={changes} redo_keyframe={r['redo_keyframe']}")
    # Repainting is costly: only for clearly failed frames, and never a keyframe the human director locked.
    redo = r["redo_keyframe"] and r["score"] <= 4 and not st.get("keyframe_locked")
    if r["score"] < 7 and (changes or redo):
        apply_changes(film, shot, changes, redo_keyframe=redo, why=r["notes"])
    elif r["score"] < 7 and r["redo_keyframe"]:
        st["repaint_suggested"] = r["notes"]  # kept for a human or a later round to decide
    film.save_state(shot)


def apply_changes(film, shot, changes, redo_keyframe=False, why=()):
    """Change a shot's plan and throw away the outputs that depend on what changed."""
    st = film.state(shot)
    st.setdefault("revisions", []).append({"changes": changes, "redo_keyframe": redo_keyframe, "why": list(why)})
    shot.update(changes)
    film.save()
    # Nothing is deleted: renders are stamped with their spec and redo themselves when it changes, so a
    # reverted change costs nothing. A replaced keyframe is archived, not lost.
    d = film.shot_dir(shot)
    if redo_keyframe:  # a new painting deserves a fresh review, and must know what to fix
        st.pop("keyframe_ok", None)
        st.pop("layers", None)
        st.pop("reviewed", None)
        st["repaint_notes"] = list(why)
        kf = d / "keyframe.png"
        if kf.exists():
            n = len(list(d.glob("keyframe_prev*.png")))
            kf.rename(d / f"keyframe_prev{n}.png")
    film.save_state(shot)


FILM_REVIEW = strict({
    "score": I,
    "overall": S,
    "strengths": arr(S),
    "weaknesses": arr(S),
    "pacing": arr(S),
    "shots": arr(strict({
        "shot_id": S,
        "problem": S,
        "duration": enum(["keep", "shorter", "longer"]),
        "intensity": enum(INTENSITIES + ["keep"]),
        "action": enum(puppet.ACTIONS + ["keep"]),
        "redo_keyframe": B,
    })),
})


def critique(film, cut, timeline):
    """Muse Wonder watches the whole cut against the shot timeline and returns shot-level fixes."""
    meta.CONTEXT.pop("shot", None)
    lines = "\n".join(f"{t0:6.1f}-{t1:6.1f} s  {sid}: {desc}" for sid, t0, t1, desc in timeline)
    messages = [
        {"role": "system", "content":
            "You are a film director and editor giving notes on the rough cut of a wordless 2.5D animated short "
            "(painted stills cut into depth layers and filmed with a virtual camera; characters can only breathe, "
            "bend their neck and hop). Watch the whole cut and judge story clarity, emotional arc, pacing, "
            "continuity of the character and places, and visual quality. score is an integer from 0 to 10. "
            "strengths and weaknesses: at least three specific observations each, citing shot ids from the "
            "timeline. In shots, list only shots that need a change, with the problem in a sentence and only the "
            "allowed values."},
        {"role": "user", "content": [
            {"type": "text", "text": f"Story brief:\n{(film.root / 'story.md').read_text(encoding='utf-8')}\n\n"
                                     f"Timeline of the cut:\n{lines}"},
            {"type": "video_url", "video_url": {"url": str(cut), "fps": 1}},
        ]},
    ]
    for effort in ("medium", "high"):
        r = meta.chat("muse-wonder-1.0", json.loads(json.dumps(messages)), schema=FILM_REVIEW, max_tokens=24000,
                      reasoning_effort=effort)
        problems = [n for n in r["shots"] if n["problem"].strip().lower() not in ("", "none", "n/a")]
        # A real review stays on its scale and engages with the film; anything else is a degenerate answer.
        if 0 <= r["score"] <= 10 and len(r["weaknesses"]) >= 2 and (problems or r["score"] >= 8):
            r["shots"] = problems
            break
        print(f"  critique rejected (score {r['score']}, {len(r['weaknesses'])} weaknesses); retrying deeper")
    else:
        r["unreliable"] = True
        r["shots"] = []
    (film.root / "critique.json").write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
    return r


I2V_REVIEW = strict({
    "score": I,
    "overall": S,
    "strengths": arr(S),
    "weaknesses": arr(S),
    "can_hear_audio": B,
    "sound": arr(S),
    "shots": arr(strict({"shot_id": S, "problem": S, "fix": S})),
})


def critique_i2v(film, cut, timeline):
    """Muse Wonder watches the image-to-video cut. Notes only: nothing is applied, because the 2.5D fixes
    (actions, intensity) mean nothing to a video model, and a retake costs the user's money."""
    from . import edit
    meta.CONTEXT.pop("shot", None)
    proxy = Path(cut).with_name("critique_proxy.mp4")  # a small copy: the whole film goes up as one data URL
    edit.ff("-i", cut, "-vf", "scale=960:-2", "-c:v", "libx264", "-crf", 30, "-preset", "slow", "-c:a", "aac",
            "-b:a", "96k", proxy)
    has_sound = bool(edit.subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                                          "stream=index", "-of", "csv=p=0", str(proxy)],
                                         capture_output=True, text=True).stdout.strip())
    lines = "\n".join(f"{t0:6.1f}-{t1:6.1f} s  {sid}: {desc}" for sid, t0, t1, desc in timeline)
    messages = [
        {"role": "system", "content":
            "You are a film director and editor giving notes on the cut of a wordless animated short. Each shot "
            "began as a painted keyframe that an image-to-video model animated; sparse text cards stand in for "
            "narration. " + ("It has a soundtrack: an instrumental score, synced sound effects and a few calls "
            "from the dodo. can_hear_audio: whether you actually received and heard the audio track; only if "
            "true, judge the sound in sound (at least three observations citing shot ids), and include sound "
            "in the score. " if has_sound else "There is no sound yet; set can_hear_audio false and leave sound "
            "empty. ") + "Watch the whole cut and judge story clarity, emotional arc, "
            "flow between shots, pacing, continuity of the character and places, and visual quality (morphing, "
            "flicker, off-model frames). score is an integer from 0 to 10. strengths and weaknesses: at least "
            "three specific observations each, citing shot ids from the timeline. In shots, list only shots "
            "that need a change: the problem in one sentence, and the cheapest fix in one sentence (trim, "
            "reorder, a different transition, a retake with a named change, or a repainted keyframe)."},
        {"role": "user", "content": [
            {"type": "text", "text": f"Story brief:\n{(film.root / 'story.md').read_text(encoding='utf-8')}\n\n"
                                     f"Timeline of the cut:\n{lines}"},
            {"type": "video_url", "video_url": {"url": str(proxy), "fps": 1}},
        ]},
    ]
    for effort in ("medium", "high"):
        try:  # a runaway answer (tens of thousands of lines) arrives as broken JSON: retry deeper
            r = meta.chat("muse-wonder-1.0", json.loads(json.dumps(messages)), schema=I2V_REVIEW,
                          max_tokens=24000, reasoning_effort=effort)
        except json.JSONDecodeError:
            print(f"  critique came back malformed at {effort} effort; retrying")
            r = {"score": -1, "strengths": [], "weaknesses": [], "shots": [], "overall": ""}
            continue
        if 0 <= r["score"] <= 10 and len(r["strengths"]) >= 2 and len(r["weaknesses"]) >= 2:
            break
        print(f"  critique rejected (score {r['score']}, {len(r['weaknesses'])} weaknesses); retrying deeper")
    else:
        r["unreliable"] = True
    (film.root / "critique_i2v.json").write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
    return r


REPAINT_CHECK = strict({"repaint": B, "reason": S})


def confirm_repaint(film, shot, problem):
    """A second model must agree before a painted keyframe is thrown away: Muse Spark looks at the frame
    and the note, and says whether repainting the still would actually fix it (rather than timing,
    camera or editing)."""
    kf = film.shot_dir(shot) / "keyframe.png"
    if not kf.exists():
        return True
    r = meta.chat(SPARK, [
        {"role": "system", "content":
            "An editor's note asks for this film keyframe to be repainted. Repainting is expensive and loses an "
            "approved image. Say repaint=true only if the problem is in the painted still itself (wrong place, "
            "missing or wrong characters or props, composition that contradicts the story beat) and a new "
            "painting would fix it. Say false if the note is praise, asks to keep the frame, or is about "
            "timing, camera, sound or editing."},
        {"role": "user", "content": [
            {"type": "text", "text": f"Shot {shot['id']}: {shot['keyframe_prompt']}\nEditor's note: {problem}"},
            {"type": "image_url", "image_url": {"url": str(kf)}},
        ]},
    ], schema=REPAINT_CHECK, max_tokens=4000, reasoning_effort="low")
    print(f"    repaint check for {shot['id']}: {r['repaint']} ({r['reason'][:90]})")
    return r["repaint"]


MAX_CRITIQUE_CHANGES = 5  # one critique round may change at most this many shots, in the order it lists them


def apply_critique(film, r):
    by_id = {s["id"]: s for s in film.plan["shots"]}
    changed = 0
    for note in r["shots"]:
        if changed >= MAX_CRITIQUE_CHANGES:
            print(f"  change budget spent; not applying the note on {note['shot_id']}")
            continue
        shot = by_id.get(note["shot_id"])
        if not shot or shot["kind"] != "painted":
            continue
        changes = {}
        if note["duration"] != "keep":
            changes["duration_s"] = round(min(10, max(3, shot["duration_s"] * (0.8 if note["duration"] == "shorter" else 1.2))), 1)
        for k in ("intensity", "action"):
            if note[k] not in ("keep", shot[k]):
                changes[k] = note[k]
        redo = (note["redo_keyframe"] and not film.state(shot).get("keyframe_locked")
                and confirm_repaint(film, shot, note["problem"]))
        if changes or redo:
            print(f"  {shot['id']}: {note['problem']} -> {changes} redo_keyframe={redo}")
            apply_changes(film, shot, changes, redo_keyframe=redo, why=[f"Muse Wonder: {note['problem']}"])
            changed += 1


NOTE_CHANGES = strict({
    "understood": S,
    "changes": arr(strict({
        "shot_id": S,
        "camera_move": enum(camera.MOVES + ["keep"]),
        "intensity": enum(INTENSITIES + ["keep"]),
        "action": enum(puppet.ACTIONS + ["keep"]),
        "atmosphere": enum(ATMOSPHERES + ["keep"]),
        "duration": enum(["keep", "shorter", "longer"]),
        "redo_keyframe": B,
        "keyframe_addition": S,
    })),
})


def voice_notes(film, audio):
    """The human director speaks; Muse Voice Transcribe hears it; Muse Spark turns it into shot changes."""
    meta.CONTEXT.pop("shot", None)
    words = {"Cutaway", "keyframe", "dolly zoom", "rack focus", *film.refs["characters"]}
    for p in film.refs["places"]:
        words.update(w.strip() for w in p["place"].replace(" with ", ",").replace(" and ", ",").split(","))
    words.update(("Caudan", "Le Pouce", "Port Louis", "Champ de Mars", "Moka", "Dodo Park"))
    text = meta.transcribe(audio, keywords=sorted(w for w in words if w))
    print(f"heard: {text}")
    shots = "\n".join(f"{s['id']}: {s['keyframe_prompt'][:120] or s['end_card_text']} | {s['camera_move']} "
                      f"{s['intensity']}, {s['action']}, {s['atmosphere']}, {s['duration_s']} s"
                      for s in film.plan["shots"])
    r = meta.chat(SPARK, [
        {"role": "system", "content":
            "You are the assistant director. Turn the director's spoken notes into concrete changes to specific "
            "shots, using only the allowed values ('keep' for anything not mentioned). Apply a general note to "
            "every shot it concerns. keyframe_addition: extra words for the painted frame's prompt if the note "
            "asks for different content (this redoes the keyframe), else ''. understood: one sentence restating "
            "the notes."},
        {"role": "user", "content": f"Shots:\n{shots}\n\nDirector's notes (transcribed speech):\n{text}"},
    ], schema=NOTE_CHANGES, max_tokens=12000, reasoning_effort="medium")
    print(f"understood: {r['understood']}")
    by_id = {s["id"]: s for s in film.plan["shots"]}
    for c in r["changes"]:
        shot = by_id.get(c["shot_id"])
        if not shot:
            continue
        changes = {k: c[k] for k in ("camera_move", "intensity", "action", "atmosphere") if c[k] not in ("keep", shot[k])}
        if c["duration"] != "keep":
            changes["duration_s"] = round(min(10, max(3, shot["duration_s"] * (0.8 if c["duration"] == "shorter" else 1.2))), 1)
        redo = c["redo_keyframe"] or bool(c["keyframe_addition"])
        if c["keyframe_addition"]:
            changes["keyframe_prompt"] = shot["keyframe_prompt"] + " " + c["keyframe_addition"]
        if changes or redo:
            print(f"  {shot['id']}: {changes} redo_keyframe={redo}")
            apply_changes(film, shot, changes, redo_keyframe=redo, why=[f"director's voice note: {text}"])
    return r


# ---------------------------------------------------------------- 7. cut and disclosure

def cut(film, res=(960, 540), source="render"):
    """source "render": the Blender 2.5D shots; "i2v": the chosen video-model takes, with the transitions
    from Muse Spark's motion plan."""
    from . import animate, edit
    motion = animate.load_motion(film) if source == "i2v" else {}
    clips, timeline, t = [], [], 0.0
    for shot in film.plan["shots"]:
        d = film.shot_dir(shot)
        if source == "i2v" and motion.get(shot["id"], {}).get("omit"):  # an editor's cut; the shot is kept
            continue
        trans = motion.get(shot["id"], {}).get("transition_in", shot["transition_in"])
        if shot["kind"] == "end_card":
            clip = edit.end_card(shot["end_card_text"], shot["duration_s"], d / f"end_{res[0]}.mp4", res)
            desc = f"end card: {shot['end_card_text']}"
        else:
            clip = d / (f"shot_i2v_{res[0]}.mp4" if source == "i2v" else f"shot_{res[0]}.mp4")
            if not clip.exists():
                raise RuntimeError(f"{shot['id']} has no {clip.name} yet")
            trim = motion.get(shot["id"], {}).get("trim") if source == "i2v" else None
            if trim:  # an editor's trim [in_s, out_s] of the chosen take; the take itself stays whole
                part = clip.with_name(f"{clip.stem}_trim.mp4")
                edit.ff("-ss", trim[0], "-to", trim[1], "-i", clip, "-an", "-c:v", "libx264", "-crf", 16,
                        "-pix_fmt", "yuv420p", part)
                clip = part
            desc = shot["keyframe_prompt"][:140]
        dur = edit.duration(clip)
        overlap = edit.XFADE_S if (clips and trans == "crossfade") else 0.0
        timeline.append((shot["id"], t - overlap, t - overlap + dur, desc))
        t += dur - overlap
        clips.append((clip, trans))
    out, length = edit.assemble(clips, film.root / f"cut_{res[0]}.mp4")
    cap_path = film.root / "captions.json"  # the author's text cards (story.md, "Text cards")
    if cap_path.exists():
        starts = {sid: t0 for sid, t0, _, _ in timeline}
        caps = [(c["text"], round(starts[c["shot"]] + c["offset_s"], 3), c["seconds"])
                for c in json.loads(cap_path.read_text(encoding="utf-8"))["captions"] if c["shot"] in starts]
        plain = out.with_name(f"cut_{res[0]}_nocaptions.mp4")
        out.replace(plain)
        edit.add_captions(plain, caps, out, res)
        timeline = [(sid, t0, t1, desc + "".join(f' [text card: "{c[0]}"]' for c in caps
                                                 if t0 <= c[1] < t1)) for sid, t0, t1, desc in timeline]
    (film.root / "timeline.json").write_text(json.dumps(timeline, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"cut: {out} ({length:.1f} s)")
    if not 90 <= length <= 180:
        print("WARNING: the cut is outside the competition's 90-180 s")
    return out, timeline


def soundtrack(film, res=(960, 540)):
    """Muse Spark writes the sound cue sheet from each shot's notes; code mixes it and muxes it onto the cut."""
    from . import edit, sound
    cut_path = film.root / f"cut_{res[0]}.mp4"
    timeline = json.loads((film.root / "timeline.json").read_text(encoding="utf-8"))
    cues_path = film.root / "sound_cues.json"
    if not cues_path.exists():
        meta.CONTEXT.pop("shot", None)
        ids = [s["id"] for s in film.plan["shots"]]
        notes = "\n".join(f"{s['id']}: {s['sound']} (scene: {(s['keyframe_prompt'] or s['end_card_text'])[:100]})"
                          for s in film.plan["shots"])
        r = meta.chat(SPARK, [
            {"role": "system", "content":
                "You are the sound designer of a wordless short film. For every shot choose the ambience bed "
                "that fits the place (forest, city street, crowd, harbour, indoor room, wind, or silence), how loud "
                "it sits (low, mid, high), and how many camera-shutter clicks are heard (0 unless people are taking "
                "photos; 2-8 when they are). Music is handled separately; leave space for it in quiet, emotional "
                "shots by choosing low levels or silence."},
            {"role": "user", "content": notes},
        ], schema=sound.cue_schema(ids), max_tokens=10000, reasoning_effort="low")
        cues_path.write_text(json.dumps(r, indent=2), encoding="utf-8")
    cues = {c["shot_id"]: c for c in json.loads(cues_path.read_text(encoding="utf-8"))["cues"]}
    music = next(iter(sorted((film.root / "music").glob("*.*"))), None) if (film.root / "music").exists() else None
    total = edit.duration(cut_path)
    wav = sound.mix(timeline, cues, film.root / f"soundtrack_{res[0]}.wav", total, music)
    out = film.root / f"film_{res[0]}.mp4"
    edit.ff("-i", cut_path, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", out)
    print(f"film with sound: {out} (music: {music.name if music else 'none yet'})")
    return out


DISCLOSURE_ROLES = {
    "muse-image-1.0": "painting every keyframe from the character sheet and reference photos",
    "muse-spark-1.3": "shot list, keyframe continuity checks, motion plan, review of every video take, prompt "
                      "rewording, sound design",
    "muse-wonder-1.0": "critique of the whole film with its soundtrack (editor's notes)",
    "muse-voice-transcribe-1.0": "the director's spoken notes",
    "sam-3.1": "depth layers for the earlier Blender version (not in the final film)",
    "wan30": "animating the keyframes (Wan 3.0 image-to-video, Alibaba, via fal.ai)",
    "kling26": "animating keyframes where Wan 3.0 failed twice (Kling 2.6 Pro, Kuaishou, via fal.ai)",
    "h3": "model bake-off only, not in the film (MiniMax H3, via fal.ai)",
    "music_el": "the score, from a composition plan written by Muse Spark (ElevenLabs Music, via fal.ai)",
    "mmaudio": "each shot's sound effects, generated from the shot's video (MMAudio v2, via fal.ai)",
    "sfx_el": "the dodo's calls (ElevenLabs Sound Effects v2, via fal.ai)",
}


def disclosure(film):
    """The AI-use record the MFDC rules ask for: extent, tools, what AI made and how, and every shot's prompts,
    takes and reviews. Describes the film as edited (timeline.json); raw calls go to generation_records.jsonl."""
    from . import i2v
    from .makingof import LIST_PRICES  # per-call list prices for models billed per image or per call
    entries = [json.loads(line) for line in meta.LOG.read_text(encoding="utf-8").splitlines()
               if f'"film": "{film.root.name}"' in line]
    by_model = {}
    for e in entries:
        m = by_model.setdefault(e.get("model", "?"), {"calls": 0, "cost_usd": 0.0, "kind": e.get("kind")})
        m["calls"] += 1
        m["cost_usd"] += e.get("cost_usd", LIST_PRICES.get(e.get("model"), 0.0))
    paid_media = ("video", "audio")
    meta_usd = sum(m["cost_usd"] for m in by_model.values() if m["kind"] not in paid_media)
    fal_logged = sum(m["cost_usd"] for m in by_model.values() if m["kind"] in paid_media)
    fal_billed = i2v.real_spent()
    timeline = json.loads((film.root / "timeline.json").read_text(encoding="utf-8"))
    motion = {m["shot_id"]: m for m in json.loads((film.root / "motion.json").read_text(encoding="utf-8"))["shots"]}
    sound = json.loads((film.root / "sound_design.json").read_text(encoding="utf-8"))
    cards = json.loads((film.root / "captions.json").read_text(encoding="utf-8"))["captions"]
    shots = {s["id"]: s for s in film.plan["shots"]}
    in_film = [t[0] for t in timeline]
    left_out = [s for s in shots if s not in in_film]
    end_card = next((s.get("end_card_text") for s in shots.values() if s.get("kind") == "end_card"), None)
    texts = ", ".join(f'"{c["text"]}"' for c in cards) + (f' and the end card "{end_card}"' if end_card else "")

    lines = [f"# AI disclosure: {film.plan['title']}", "",
             f"Category B (AI) · {timeline[-1][2]:.0f} seconds · {len(in_film)} shots", "",
             "## Extent of AI use", "",
             "Approximately 100% of the picture and the sound is AI-generated. The author's contribution is the "
             "story, its direction and the choice of the final cut.", "",
             "- **Images:** every frame starts from a keyframe painted by Muse Image (Meta). Real places in "
             "Port Louis were painted from reference photographs (see Third-party material); no photograph "
             "appears in the film as it was taken.",
             "- **Motion:** each keyframe was animated by an image-to-video model (Wan 3.0, or Kling 2.6 where "
             "Wan failed twice), from a motion prompt written by Muse Spark (Meta). Muse Spark watched every "
             "take and accepted or rejected it. 720p takes were upscaled to 1080p locally with Real-ESRGAN "
             "(an AI upscaler, run on the author's laptop).",
             "- **Sound:** the score (ElevenLabs Music), the effects (MMAudio) and the dodo's calls "
             "(ElevenLabs Sound Effects) are AI-generated, from a sound design written by Muse Spark. "
             "No recorded music or sound is used.",
             f"- **Text:** {texts}, drafted with an AI assistant, chosen by the author and set in "
             "EB Garamond.",
             "- **Editing:** cutting, transitions, trims, the sound mix and loudness were done by the Cutaway "
             "software (ffmpeg), following Muse Spark's plan, Muse Wonder's critiques and the author's notes.", "",
             "## Human and AI authorship", "",
             "- The story idea is the author's own: a dodo wakes in modern Port Louis, becomes an attraction and "
             "ends in an enclosure with many dodos. The written brief (story.md) was drafted from that idea with "
             "an AI assistant (Claude, Anthropic) and approved by the author.",
             "- The author directed through notes on each version. For example: an evening forest; the capture "
             "scene; the dodo waking on its own rock rather than in the road; a frightened escape instead of a "
             "calm walk after the startle; dodo calls as it wanders; an enclosure, not a real forest, at the end.",
             "- The Cutaway software, which runs the Meta models and the video and audio models, was written with "
             "the same AI assistant. Choices that overruled the models (choosing between tied takes, overruling a "
             "critique, trims) are recorded per shot below as made by the director: the AI assistant acting on "
             "the author's behalf.",
             "- The author reviewed every version and chose the final cut (version 7 of 7).", "",
             "## AI tools used", "",
             "| Model | Role | Calls | Cost (USD) |", "|---|---|---|---|"]
    for model, m in sorted(by_model.items(), key=lambda kv: (kv[1]["kind"] in paid_media, kv[0])):
        lines.append(f"| {model} | {DISCLOSURE_ROLES.get(model, '')} | {m['calls']} | {m['cost_usd']:.2f} |")
    billed = f"; ${fal_billed:.2f} actually billed by fal." if fal_billed is not None else "."
    lines += ["",
              f"Meta Model API: ${meta_usd:.2f} (token models at their billed cost, image and segment models at "
              f"list price). fal.ai: ${fal_logged:.2f} logged at list price{billed}",
              "Real-ESRGAN (realesr-animevideov3, BSD-3-Clause) ran locally at no cost. fal.ai lists every fal "
              "model above as licensed for commercial use (checked 2026-11-02).",
              "Every call, with its full prompt or input and reply, is in generation_records.jsonl. A paid video "
              "request that a run could not collect (the laptop slept) was collected by the next run, not paid "
              "for twice.",
              "", "## Sound design (Muse Spark)", "",
              "Score styles: " + "; ".join(sound["music"]["positive_global_styles"]) + ".",
              "Excluded: " + "; ".join(dict.fromkeys(sound["music"]["negative_global_styles"])) + ".", ""]
    for sec in sound["music"]["sections"]:
        if sec.get("starts_at_shot") in in_film:
            lines.append(f"- From {sec['starts_at_shot']}, {sec['section_name']}: "
                         + "; ".join(sec.get("positive_local_styles", [])))
    lines += ["", "The dodo's calls, modelled on its closest living relative, the Nicobar pigeon:", ""]
    lines += [f"- {c['shot_id']}: {c['description']}" for c in sound["calls"] if c["shot_id"] in in_film]
    lines += ["", "## Per-shot record", "",
              "In film order. Times are positions in the finished film. A take needs 7/10 or more from Muse "
              "Spark to be accepted.", ""]
    shot_sound = {s["shot_id"]: s["sound"] for s in sound["shots"]}
    for sid, t0, t1, *_ in timeline:
        shot, st, mo = shots[sid], film.state(shots[sid]), motion.get(sid, {})
        lines.append(f"### {sid} ({t0:.1f}–{t1:.1f} s)")
        if shot.get("kind") == "end_card":
            lines += [f'- End card: "{shot.get("end_card_text", "")}", typeset by the software.', ""]
            continue
        kf = st.get("keyframe_attempts", [])
        if kf:
            how = "; chosen by the director" if kf[-1].get("verdict", {}).get("chosen_by") == "director" else ""
            n = len(kf)
            lines.append(f"- Keyframe (Muse Image, {n} attempt{'s' * (n != 1)}, checked by Muse Spark{how}): "
                         f"{kf[-1]['prompt']}")
        if mo.get("motion_prompt"):
            lines.append(f"- Motion plan (Muse Spark): {mo['motion_prompt']}")
        if mo.get("revised_by"):
            lines.append(f"  - Revised by: {mo['revised_by']}")
        prev = sum(len(r["takes"]) for r in st.get("i2v_takes_prev", []))
        if prev:
            lines.append(f"- {prev} earlier take{'s' * (prev != 1)}, made before the keyframe or plan changed "
                         "(kept on record)")
        for tk in st.get("i2v_takes", []):
            rv = tk.get("review") or {}
            mark = " **(in the film)**" if tk["take"] == st.get("i2v_choice") else ""
            probs = "; ".join(rv.get("problems", [])) or tk.get("failed", "no problems noted")
            lines.append(f"- Take {tk['take']} ({tk.get('model', '?')}){mark}: Muse Spark "
                         f"{rv.get('score', '?')}/10, {probs}")
            if mark:
                lines.append(f"  - Prompt: {tk['prompt']}")
        if st.get("i2v_choice_why"):
            lines.append(f"- Choice: {st['i2v_choice_why']}")
        if mo.get("trim"):
            lines.append(f"- Edit: trimmed to {mo['trim'][0]:g}–{mo['trim'][1]:g} s of the take")
        if shot_sound.get(sid):
            lines.append(f"- Sound effects (MMAudio, from the shot's video): {shot_sound[sid]}")
        lines.append("")
    if left_out:
        lines += ["## Shots made but left out of the final cut", "",
                  "- " + ", ".join(left_out) + ". Their records are kept in the project files.", ""]
    lines += ["## Third-party material", "", (film.repo / "CREDITS.md").read_text(encoding="utf-8")]
    out = film.root / "AI_DISCLOSURE.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    raw = film.root / "generation_records.jsonl"
    raw.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in entries), encoding="utf-8")
    print(f"wrote {out} and {raw} ({len(entries)} AI calls)")


# ---------------------------------------------------------------- review helpers

def exploded(film, shot, res=(960, 540)):
    """Making-of shot: the film frame, then the camera swings out to show the layers floating in depth."""
    d = film.shot_dir(shot)
    sp = json.loads(spec(film, shot, res).read_text())
    sp.update(seconds=8.0, exploded={}, name=f"{shot['id']}_exploded")
    sp["camera"]["shake"] = {"deg": 0.0, "units": 0.0, "hz": 0.5}
    path = d / "spec_exploded.json"
    path.write_text(json.dumps(sp, indent=2))
    out = d / "frames_exploded"
    r = subprocess.run([BLENDER, "-b", "--factory-startup", "-P", str(film.repo / "cutaway" / "blender_shot.py"),
                        "--", str(path), str(out)], capture_output=True, text=True)
    if r.returncode or "Traceback" in r.stdout:
        raise RuntimeError(r.stdout[-2500:])
    mp4 = d / "exploded.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", str(out / "frame_%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(mp4)], check=True)
    return mp4


def show(film):
    p = film.plan
    print(f"{p['title']}: {p['logline']}\nSTYLE: {p['style']}\n")
    for s in p["shots"]:
        refs = [Path(r).stem.split("_")[1] for r in s["place_refs"]]
        print(f"{s['id']} beat {s['beat']} {s['duration_s']:>4}s {s['camera_move']}/{s['intensity']} "
              f"focus {s['focus_from']}->{s['focus_to']} {s['action']} {s['atmosphere']} {s['transition_in']} "
              f"subjects={s['subjects']} ground={s['ground']!r} fg={s['foreground']!r} refs={refs}")
        print(f"    {s['keyframe_prompt'] or s['end_card_text']}")
        print(f"    sound: {s['sound']}")


def storyboard(film):
    shots = [s for s in film.plan["shots"] if (film.root / "shots" / s["id"] / "keyframe.png").exists()]
    out = film.root / "storyboard.png"
    contact_sheet([film.root / "shots" / s["id"] / "keyframe.png" for s in shots], out, cols=4, cell=480)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("film")
    ap.add_argument("stage", choices=["plan", "show", "keyframes", "layers", "specs", "render", "review",
                                      "produce", "cut", "sound", "critique", "notes", "disclosure", "storyboard",
                                      "exploded", "motion", "i2v", "upscale", "score"])
    ap.add_argument("--source", choices=["render", "i2v"], default="render",
                    help="cut/sound/critique: Blender renders or the chosen video-model takes")
    ap.add_argument("--shots", default="")
    ap.add_argument("--audio", help="notes: a recording of the director's spoken notes")
    ap.add_argument("--force", action="store_true", help="review: review again even if already reviewed")
    ap.add_argument("--preview", action="store_true", help="render 3 stills per shot instead of the clip")
    ap.add_argument("--final", action="store_true", help="1920x1080 instead of 960x540")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):  # model text can hold any script; the Windows console is cp1252
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.platform == "win32" and a.stage in ("keyframes", "layers", "render", "produce", "exploded", "i2v",
                                               "upscale", "score"):
        # Keep the machine awake while this process works (long renders died when the laptop slept);
        # Windows drops the request when the process exits, and no power settings are changed.
        import ctypes
        ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    film = Film(a.film)
    meta.CONTEXT["film"] = film.root.name
    only = set(filter(None, a.shots.split(",")))
    if a.stage == "plan":
        return plan(film)
    if a.stage == "storyboard":
        return print(storyboard(film))
    if a.stage == "show":
        return show(film)
    if a.stage == "disclosure":
        return disclosure(film)
    if a.stage == "notes":
        voice_notes(film, a.audio)
        return print(f"spent ${meta.spent():.2f}")
    only = only or None
    if a.stage in ("motion", "i2v", "upscale"):
        from . import animate
        if a.stage == "motion":
            return animate.plan_motion(film, force=a.force)
        if a.stage == "i2v":
            return animate.produce(film, only)
        return animate.upscale(film, only)
    res = (1920, 1080) if a.final else ((1280, 720) if a.source == "i2v" else (960, 540))
    if a.stage == "cut":
        return cut(film, res, a.source)
    if a.stage == "sound":
        return soundtrack(film, res)
    if a.stage == "score":  # the i2v cut's sound: Muse Spark designs it, fal's audio models make it
        from . import i2v, score
        try:
            score.make(film, force=a.force)
        except i2v.BudgetError as e:
            print(f"STOP: {e}")
        return score.mix(film, res)
    if a.stage == "critique":
        out, timeline = cut(film, res, a.source)
        if a.source == "i2v":
            from . import score
            if (film.root / "sound_design.json").exists():  # critique the film as it will be seen and heard
                out = score.mix(film, res)
            r = critique_i2v(film, out, timeline)
            print(f"Muse Wonder: {r['score']}/10{' (UNRELIABLE)' if r.get('unreliable') else ''}. {r['overall']}")
            print(f" can hear audio: {r.get('can_hear_audio')}")
            for label in ("strengths", "weaknesses", "pacing", "sound"):
                for p in r.get(label, []):
                    print(f" {label}: {p}")
            for n in r["shots"]:
                print(f" {n['shot_id']}: {n['problem']} -> {n['fix']}")
            return print(f"spent ${meta.spent():.2f}")
        r = critique(film, out, timeline)
        print(f"Muse Wonder: {r['score']}/10{' (UNRELIABLE)' if r.get('unreliable') else ''}. {r['overall']}")
        for label in ("strengths", "weaknesses", "pacing"):
            for p in r.get(label, []):
                print(f" {label}: {p}")
        apply_critique(film, r)
        return print(f"spent ${meta.spent():.2f}")
    for shot in film.shots(only):
        meta.CONTEXT["shot"] = shot["id"]
        try:
            if a.stage == "keyframes":
                keyframe(film, shot)
            elif a.stage == "layers":
                layers(film, shot)
            elif a.stage == "specs":
                spec(film, shot, res)
            elif a.stage == "render":
                n = int(shot["duration_s"] * 24)
                print(shot["id"], render(film, shot, res, stills=[1, n // 2, n] if a.preview else None))
            elif a.stage == "review":
                review(film, shot, res, force=a.force)
            elif a.stage == "exploded":
                print(shot["id"], exploded(film, shot, res))
            elif a.stage == "produce":  # everything from the keyframe on; a no-op for finished shots
                if shot["kind"] == "end_card":
                    continue
                keyframe(film, shot)
                layers(film, shot)
                render(film, shot, res)
                review(film, shot, res)
                if not (film.shot_dir(shot) / f"shot_{res[0]}.mp4").exists():  # the review changed the shot
                    if not film.state(shot).get("keyframe_ok"):
                        keyframe(film, shot)
                        layers(film, shot)
                    render(film, shot, res)
                print(f"  {shot['id']} produced; spent ${meta.spent():.2f}", flush=True)
        except meta.BudgetError as e:
            sys.exit(str(e))
    print(f"spent ${meta.spent():.2f}")


if __name__ == "__main__":
    main()
