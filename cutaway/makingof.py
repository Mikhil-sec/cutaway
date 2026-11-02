"""The making-of: a demo video assembled from what the agent recorded while making a film.

Every panel is built from the film's own artifacts (plan, per-shot state, keyframes, layers,
reviews, critique, generation log), so the demo shows what actually happened.
"""
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from . import edit

W, H = 1920, 1080
BG = (14, 15, 18)
INK = (236, 232, 224)
DIM = (150, 150, 158)
ACCENT = (232, 176, 92)
FONT = edit.FONT
MONO = Path("C:/Windows/Fonts/consola.ttf")


def font(size, mono=False):
    return ImageFont.truetype(str(MONO if mono and MONO.exists() else FONT), size)


def canvas():
    return Image.new("RGB", (W, H), BG)


def fit(img, box):
    """Paste-ready copy of img scaled to fit box (w, h)."""
    return ImageOps.contain(img.convert("RGB"), box, Image.LANCZOS)


def text_block(draw, xy, text, size=40, width=60, fill=INK, mono=False, gap=1.25):
    x, y = xy
    f = font(size, mono)
    for para in text.split("\n"):
        for line in textwrap.wrap(para, width) or [""]:
            draw.text((x, y), line, font=f, fill=fill)
            y += int(size * gap)
    return y


def card(title, body="", kicker=""):
    img = canvas()
    d = ImageDraw.Draw(img)
    y = 380
    if kicker:
        d.text((160, y - 70), kicker.upper(), font=font(30), fill=ACCENT)
    y = text_block(d, (160, y), title, 76, 34)
    if body:
        text_block(d, (160, y + 30), body, 40, 70, DIM)
    return img


def side_by_side(left, right, left_label, right_label, caption):
    img = canvas()
    d = ImageDraw.Draw(img)
    for i, (src, label) in enumerate(((left, left_label), (right, right_label))):
        pic = fit(Image.open(src), (900, 560))
        x = 40 + i * 940 + (900 - pic.width) // 2
        img.paste(pic, (x, 140))
        d.text((40 + i * 940, 720), label, font=font(34), fill=ACCENT)
    text_block(d, (40, 800), caption, 40, 90)
    return img


def picture_with_notes(src, title, notes, overlay=None):
    img = canvas()
    d = ImageDraw.Draw(img)
    pic = fit(Image.open(src), (1150, 650))
    if overlay is not None:
        pic = Image.blend(pic, fit(overlay, pic.size).resize(pic.size), 0.45)
    img.paste(pic, (40, 200))
    d.text((40, 90), title, font=font(52), fill=INK)
    y = 210
    for n in notes:
        y = text_block(d, (1240, y), n, 32, 34, DIM) + 24
    return img


def mask_overlay(shot_dir, layers):
    """Characters in amber, ground in teal, foreground in violet: what SAM 3.1 cut."""
    base = Image.open(shot_dir / "keyframe.png").convert("RGB")
    over = Image.new("RGB", base.size, (0, 0, 0))
    paint = [(s["image"], (232, 150, 40)) for s in layers["subjects"]]
    if layers["ground"]:
        paint.append((layers["ground"]["image"], (40, 190, 180)))
    if layers["foreground"]:
        paint.append((layers["foreground"]["image"], (150, 90, 230)))
    for path, colour in paint:
        a = Image.open(path).getchannel("A")
        over.paste(Image.new("RGB", base.size, colour), (0, 0), a)
    return over


def still_clip(img, seconds, out, fade=0.4):
    png = Path(out).with_suffix(".png")
    img.save(png)
    edit.ff("-loop", 1, "-t", seconds, "-i", png,
            "-vf", f"fade=in:d={fade},fade=out:st={seconds - fade}:d={fade},format=yuv420p",
            "-r", 24, "-c:v", "libx264", "-crf", 18, out)
    return out


def video_clip(src, out, start=0.0, seconds=None, caption=None):
    """A piece of a rendered video, scaled to 1920x1080, with an optional caption bar."""
    vf = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0e0f12"
    if caption:
        png = Path(out).with_suffix(".caption.png")
        bar = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(bar)
        d.rectangle((0, H - 120, W, H), fill=(0, 0, 0, 170))
        d.text((60, H - 95), caption, font=font(44), fill=INK)
        bar.save(png)
        args = ["-ss", start, "-i", src, "-i", png]
        if seconds:
            args = ["-ss", start, "-t", seconds, "-i", src, "-i", png]
        edit.ff(*args, "-filter_complex", f"[0:v]{vf}[v];[v][1:v]overlay=0:0,format=yuv420p",
                "-an", "-r", 24, "-c:v", "libx264", "-crf", 18, out)
    else:
        args = ["-ss", start] + (["-t", seconds] if seconds else []) + ["-i", src]
        edit.ff(*args, "-vf", vf + ",format=yuv420p", "-an", "-r", 24, "-c:v", "libx264", "-crf", 18, out)
    return out


def compare_clip(left, right, left_label, right_label, caption, out, seconds=None, start=0.0):
    """Two clips side by side (a rejected take and the one that replaced it), labelled, with a caption.
    The shorter clip holds its last frame."""
    seconds = seconds or max(edit.duration(left), edit.duration(right)) - start
    png = Path(out).with_suffix(".frame.png")
    img = canvas()
    d = ImageDraw.Draw(img)
    for i, label in enumerate((left_label, right_label)):
        text_block(d, (40 + i * 940, 680), label, 30, 52, ACCENT if i else DIM)
    text_block(d, (40, 860), caption, 36, 95)
    img.save(png)
    box = "scale=900:506:force_original_aspect_ratio=decrease,pad=900:506:(ow-iw)/2:(oh-ih)/2:color=0x0e0f12"
    hold = f"tpad=stop_mode=clone:stop_duration={seconds}"
    edit.ff("-loop", 1, "-t", seconds, "-i", png, "-ss", start, "-i", left, "-ss", start, "-i", right,
            "-filter_complex", f"[1:v]fps=24,{box},{hold}[l];[2:v]fps=24,{box},{hold}[r];"
                               f"[0:v][l]overlay=40:150[a];[a][r]overlay=980:150,format=yuv420p",
            "-t", seconds, "-an", "-r", 24, "-c:v", "libx264", "-crf", 18, out)
    return out


def sequence(clips, out):
    """[(path, seconds)] trimmed and butted together, for before/after comparisons of a cut."""
    inputs, graph = [], []
    for i, (path, secs) in enumerate(clips):
        inputs += ["-i", path]
        graph.append(f"[{i}:v]fps=24,scale=1280:720,setsar=1,trim=0:{secs},setpts=PTS-STARTPTS[v{i}]")
    graph.append("".join(f"[v{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=1:a=0[o]")
    edit.ff(*inputs, "-filter_complex", ";".join(graph), "-map", "[o]", "-c:v", "libx264", "-crf", 18,
            "-pix_fmt", "yuv420p", out)
    return out


LIST_PRICES = {"muse-image-1.0": 0.01, "sam-3.1": 0.0025, "muse-voice-transcribe-1.0": 0.003}


def costs(film_root, log_path):
    """Calls and spend for one film, from the generation log (token models carry their billed cost)."""
    entries = [json.loads(line) for line in Path(log_path).read_text(encoding="utf-8").splitlines()
               if f'"film": "{Path(film_root).name}"' in line]
    by_model, total = {}, 0.0
    for e in entries:
        m = e.get("model", "?")
        by_model[m] = by_model.get(m, 0) + 1
        total += e.get("cost_usd", LIST_PRICES.get(m, 0.0))
    return {"calls": len(entries), "by_model": by_model, "usd": total}


def build(film, out_dir, film_cut, res_tag="960"):
    """Assemble the making-of from the film's artifacts. film: a director.Film."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    shots = {s["id"]: s for s in film.plan["shots"]}
    clips, n = [], 0

    def add(clip_fn, *args, **kw):
        nonlocal n
        n += 1
        clips.append((clip_fn(*args, out=out_dir / f"{n:02d}.mp4", **kw), "cut"))

    def pick(pred):
        return next((s for s in film.plan["shots"] if s["kind"] == "painted" and pred(s)), None)

    # 1. Cold open on the film itself.
    add(video_clip, film_cut, start=0.0, seconds=9.0)
    add(still_clip, card("Cutaway", "An AI film crew that builds cinematic short films instead of generating them. "
                                    "Made with Meta's Muse models, SAM 3.1 and Blender.", "Meta Global AI Hackathon"), 5)
    add(still_clip, card("AI video is expensive, a few seconds long, and the character changes every shot.",
                         "I needed 150 seconds, on a laptop, for Mauritius's national short film competition. "
                         "So Cutaway doesn't generate video. It builds it.", "The problem"), 7)

    # 2. Plan.
    lines = "\n".join(f"{s['id']}  {s['camera_move']}/{s['intensity']}  {s['action']}  {s['atmosphere']}"
                      for s in film.plan["shots"][:14])
    img = canvas()
    d = ImageDraw.Draw(img)
    d.text((80, 70), "Muse Spark turns the story into a shot list", font=font(52), fill=INK)
    text_block(d, (80, 170), "Every field comes from a JSON schema of what the renderer can actually do.", 34, 90, DIM)
    text_block(d, (80, 260), lines, 30, 120, ACCENT, mono=True, gap=1.35)
    add(still_clip, img, 7)

    # 3. Real places: reference photo -> keyframe.
    for s in [pick(lambda s: "chinatown" in "".join(s["place_refs"])), pick(lambda s: "caudan" in "".join(s["place_refs"]))]:
        if s:
            ref = film.ref_path(s["place_refs"][0])
            add(still_clip, side_by_side(ref, film.shot_dir(s) / "keyframe.png", "Reference photo (free licence)",
                                         "Keyframe by Muse Image",
                                         "Real Port Louis, repainted in the film's style, with the dodo's character "
                                         "sheet as a second reference so it stays the same bird."), 6)

    # 4. Continuity supervisor catching a problem.
    s = pick(lambda s: len(film.state(s).get("keyframe_attempts", [])) > 1)
    if s:
        att = film.state(s)["keyframe_attempts"]
        notes = [f"Attempt {i + 1}: " + ("; ".join(a["verdict"]["problems"][:2]) or "approved")
                 for i, a in enumerate(att)]
        add(still_clip, picture_with_notes(film.shot_dir(s) / "keyframe.png",
                                           "Muse Spark checks every keyframe and sends back fixes", notes), 8)

    # 5. Layers: SAM masks, then the exploded view.
    s = shots.get("s07_waterfront_pouce") or pick(lambda s: film.state(s).get("layers"))
    L = film.state(s)["layers"]
    add(still_clip, picture_with_notes(film.shot_dir(s) / "keyframe.png", "SAM 3.1 cuts the still into layers",
                                       ["Amber: the dodo, as a bendable puppet", "Teal: the ground it stands on",
                                        "Violet: foreground", "Muse Image paints a clean plate behind them, and SAM "
                                        "checks the dodo is really gone."], overlay=mask_overlay(film.shot_dir(s), L)), 7)
    exploded = film.shot_dir(s) / "exploded.mp4"
    if exploded.exists():
        add(video_clip, exploded, caption="Blender films the layers with a real camera: parallax, focus, shake")

    # 6. Reviews.
    s = pick(lambda s: film.state(s).get("reviews"))
    if s:
        r = film.state(s)["reviews"][-1]
        mp4 = film.shot_dir(s) / f"shot_{res_tag}.mp4"
        add(video_clip, mp4, caption=f"Muse Spark watches every shot: {r['score']}/10. {r['notes'][0][:70]}")
    first, latest = film.root / "critique_round1.json", film.root / "critique.json"
    if first.exists() and latest.exists():
        c1 = json.loads(first.read_text(encoding="utf-8"))
        c2 = json.loads(latest.read_text(encoding="utf-8"))
        img = canvas()
        d = ImageDraw.Draw(img)
        d.text((80, 70), f"Muse Wonder watches every cut:  {c1['score']}/10  →  {c2['score']}/10",
               font=font(56), fill=INK)
        y = text_block(d, (80, 170), "First cut: " + c1["overall"], 32, 100, DIM)
        for note in c1["shots"][:3]:
            y = text_block(d, (110, y + 10), f"{note['shot_id']}: {note['problem']}", 28, 110, ACCENT)
        y = text_block(d, (80, y + 40), "Now, strengths it names:", 32, 100, DIM)
        for s in c2.get("strengths", [])[:3]:
            y = text_block(d, (110, y + 10), s, 28, 110, INK)
        add(still_clip, img, 12)
        img = canvas()
        d = ImageDraw.Draw(img)
        d.text((80, 80), "Two models must agree before work is thrown away", font=font(52), fill=INK)
        text_block(d, (80, 190),
                   "When Muse Wonder asks for a repaint, Muse Spark looks at the frame and the note and must agree "
                   "that a new painting would fix it. A critique round may change at most five shots, and the "
                   "director can lock a keyframe. When a critique diagnoses well but prescribes badly, the "
                   "director keeps the notes and overrules the fixes.", 36, 80, DIM)
        add(still_clip, img, 8)

    # 6b. Director's voice notes.
    img = canvas()
    d = ImageDraw.Draw(img)
    d.text((80, 80), "Direct it by voice: Muse Voice Transcribe", font=font(52), fill=INK)
    y = text_block(d, (80, 190), "“The forest shots at the start should linger a little longer. In the Caudan "
                                 "umbrella scenes, make the camera move stronger. And the Dodo Park reveal needs "
                                 "more camera flashes.”", 38, 75, ACCENT)
    text_block(d, (80, y + 40), "Transcribed with the film's place names as keyword bias, then turned by Muse Spark "
                                "into concrete changes to specific shots.", 34, 85, DIM)
    add(still_clip, img, 7)

    # 7. The film.
    add(still_clip, card("The Dodo Came Back", "What if the dodo returned to Mauritius?", "The film"), 3)
    total = edit.duration(film_cut)
    add(video_clip, film_cut, start=max(0.0, total - 52.0), seconds=50.0)  # the reveal to the end card

    # 8. Numbers.
    c = costs(film.root, film.repo / "generation_log.jsonl")
    painted = sum(1 for s in film.plan["shots"] if s["kind"] == "painted")
    add(still_clip, card(f"{total:.0f} seconds. {painted} shots. ${c['usd']:.2f} of API calls.",
                         f"{c['calls']} model calls, every prompt and check logged, and an AI-disclosure report "
                         "generated for the competition. Open source: github.com/Mikhil-sec/cutaway", "Result"), 8)
    out, length = edit.assemble(clips, out_dir / "making_of.mp4")
    return out, length


def _take(film, sid, n):
    shot = next(s for s in film.plan["shots"] if s["id"] == sid)
    t = next(t for t in film.state(shot)["i2v_takes"] if t["take"] == n)
    return film.shot_dir(shot) / Path(t["file"]).name, t


def _note(take, n=1):
    return "; ".join(p.rstrip(".") for p in (take["review"].get("problems") or [])[:n])


def soundtrack(video, clips, sounds, film_cut, score, out, bed_from=0.0, bed_db=-7.0, fade=0.4):
    """Lay sound under the assembled making-of. sounds[i] is clip i's: ("film", start) plays the film's own
    sound for that stretch; ("bed",) or ("bed", call, at_s) plays the score, picking up where it left off, so
    the panels between film excerpts hear the music continue (with a dodo call at at_s into the panel)."""
    inputs, graph, parts, t, cursor = ["-i", video, "-i", film_cut, "-i", score], [], [], 0.0, bed_from
    bed_end = edit.duration(score)
    for i, ((path, _), s) in enumerate(zip(clips, sounds)):
        d = edit.duration(path)
        if s[0] == "film":
            src, a = 1, s[1]
        else:
            if cursor + d > bed_end:  # the score ran out: start it again after the cold open
                cursor = bed_from
            src, a, cursor = 2, cursor, cursor + d
        gain = 0.0 if s[0] == "film" else bed_db
        graph.append(f"[{src}:a]atrim={a:.3f}:{a + d:.3f},asetpts=PTS-STARTPTS,volume={gain}dB,"
                     f"afade=in:d={fade},afade=out:st={max(d - fade, 0):.3f}:d={fade},adelay={t * 1000:.0f}:all=1[p{i}]")
        parts.append(f"[p{i}]")
        if len(s) == 3:  # a dodo call over the bed
            inputs += ["-i", s[1]]
            k = len(inputs) // 2 - 1
            graph.append(f"[{k}:a]volume=-2dB,adelay={(t + s[2]) * 1000:.0f}:all=1[c{i}]")
            parts.append(f"[c{i}]")
        t += d
    graph.append("".join(parts) + f"amix=inputs={len(parts)}:normalize=0:duration=longest,"
                 f"atrim=0:{t:.3f},loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]")
    edit.ff(*inputs, "-filter_complex", ";".join(graph), "-map", "0:v", "-map", "[a]", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-shortest", out)
    return out


def build_i2v(film, out_dir, film_cut, excerpt_s=40):
    """The making-of for the image-to-video pipeline: Muse models direct, video models animate. It shows
    only the last ~excerpt_s seconds of the film, from a shot boundary: the demo is public before the
    competition film is. film_cut: the film with its sound (film_<w>.mp4)."""
    from . import i2v
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timeline_rows = json.loads((film.root / "timeline.json").read_text(encoding="utf-8"))
    timeline = {sid: (t0, t1) for sid, t0, t1, _ in timeline_rows}
    painted = [s for s in film.plan["shots"] if s["kind"] == "painted"]
    by_id = {s["id"]: s for s in painted}
    in_film = [s for s in painted if s["id"] in timeline]
    clips, sounds, n = [], [], 0

    def add(clip_fn, *args, sound=("bed",), **kw):
        nonlocal n
        n += 1
        clips.append((clip_fn(*args, out=out_dir / f"i2v_{n:02d}.mp4", **kw), "cut"))
        sounds.append(sound)

    # 1. Cold open: the forest, the first text card, the cut into the dodo settling.
    cold_open = timeline["s02_settle_sleep"][1]
    add(video_clip, film_cut, start=0.0, seconds=cold_open, sound=("film", 0.0))
    add(still_clip, card("Cutaway", "An AI film crew for a 2-minute animated short. Meta's Muse models plan, "
                                    "paint, direct and critique; video models do the camera work.",
                         "Meta Global AI Hackathon"), 5)
    add(still_clip, card("One prompt gives you five seconds, a different bird every shot, and streets that melt.",
                         "I'm making a film for Mauritius's national short film competition. A story needs a "
                         "director: someone who plans every shot, checks every take and asks for it again.",
                         "The problem"), 7)

    # 2. The motion plan, written for flow across cuts.
    motion = json.loads((film.root / "motion.json").read_text(encoding="utf-8"))
    img = canvas()
    d = ImageDraw.Draw(img)
    d.text((80, 60), "Muse Spark directs the motion, thinking across cuts", font=font(52), fill=INK)
    y = text_block(d, (80, 150), motion["flow_notes"], 30, 115, DIM)
    for m in motion["shots"][2:5]:
        y = text_block(d, (80, y + 28), f"{m['shot_id']}   in: {m['transition_in']}", 28, 120, ACCENT, mono=True)
        y = text_block(d, (110, y + 4), m["motion_prompt"], 26, 125, INK)
        y = text_block(d, (110, y + 4), "ends on: " + m["ends_on"], 26, 125, DIM)
    add(still_clip, img, 10)

    # 3. Real places, repainted, and the keyframe check.
    s = by_id["s06_chinatown_gate"]
    add(still_clip, side_by_side(film.ref_path(s["place_refs"][0]), film.shot_dir(s) / "keyframe.png",
                                 "Reference photo (Unsplash licence)", "Keyframe by Muse Image",
                                 "Real Port Louis, repainted in the film's style, with the dodo's character sheet "
                                 "as a second reference so it stays the same bird."), 6)
    s = next((s for s in painted if len(film.state(s).get("keyframe_attempts", [])) > 1), None)
    if s:
        notes = [f"Attempt {i + 1}: " + ("; ".join(a["verdict"]["problems"][:2]) or "approved")
                 for i, a in enumerate(film.state(s)["keyframe_attempts"])]
        add(still_clip, picture_with_notes(film.shot_dir(s) / "keyframe.png",
                                           "Muse Spark checks every keyframe and sends back fixes", notes), 7)

    # 4. Muse Spark watches every take; a bad one gets a rewritten prompt and goes again.
    for sid, bad, good in (("s09_see_mountains", 1, 2), ("s03_wake_city", 1, 2)):
        (lp, lt), (rp, rt) = _take(film, sid, bad), _take(film, sid, good)
        add(compare_clip, lp, rp, f"Take {bad}: {lt['review']['score']}/10. {_note(lt)}",
            f"Take {good}: {rt['review']['score']}/10, accepted",
            "Muse Spark watches every take as video, scores it against the shot's intent and the painted "
            "frame, and rewrites the prompt when the model invents scenery or loses the bird.", seconds=8)

    # 5. When one model keeps failing, try another.
    (lp, lt), (rp, rt) = _take(film, "s06_chinatown_gate", 2), _take(film, "s06_chinatown_gate", 3)
    add(compare_clip, lp, rp, f"Wan 3.0, take 2: {lt['review']['score']}/10. {_note(lt)}",
        f"Kling 2.6, take 3: {rt['review']['score']}/10, accepted",
        "After two failed takes on one model, the agent switches to another. Each model fails differently.",
        seconds=7)

    # 6. Flow: the first cut, before and after Muse Image repainted shot 2 into the same place and light.
    s1, s2 = by_id["s01_forest_dawn"], by_id["s02_settle_sleep"]
    d1, d2 = s1["duration_s"], s2["duration_s"]
    before = sequence([(film.shot_dir(s1) / "prev0_take_1.mp4", d1), (film.shot_dir(s2) / "prev0_take_1.mp4", d2)],
                      out_dir / "i2v_flow_before.mp4")
    after = sequence([(film.shot_dir(s1) / "take_1.mp4", d1), (film.shot_dir(s2) / "take_1.mp4", d2)],
                     out_dir / "i2v_flow_after.mp4")
    add(compare_clip, before, after, "Before: two good shots that don't connect",
        "After: one place, one light, the movement carries across the cut",
        "Shots must flow like a movie. Muse Image repainted the second shot from the first one's keyframe, and "
        "the first shot now ends mid-movement so the cut lands on action.")

    # 7. Sound: Muse Spark designs it, audio models perform it, and a dodo call is heard over the panel.
    design = json.loads((film.root / "sound_design.json").read_text(encoding="utf-8"))
    img = canvas()
    d = ImageDraw.Draw(img)
    d.text((80, 60), "Muse Spark designs the sound; audio models perform it", font=font(52), fill=INK)
    y = text_block(d, (80, 150), "The score: one composition plan, its sections timed to the cut "
                                 "(ElevenLabs Music)", 32, 110, INK)
    for sec in [s for s in design["music"]["sections"] if s.get("starts_at_shot") in timeline][:4]:
        y = text_block(d, (110, y + 8), f"{sec['section_name']}: " + "; ".join(sec["positive_local_styles"]),
                       26, 125, DIM)
    y = text_block(d, (80, y + 26), "Every shot's effects, generated from its own video (MMAudio)", 32, 110, INK)
    y = text_block(d, (80, y + 26), "The dodo's voice, modelled on its closest living relative, the Nicobar "
                                    "pigeon (ElevenLabs SFX)", 32, 110, INK)
    i, call = next((i, c) for i, c in enumerate(design["calls"], start=1) if c["shot_id"] == "s19_press_mural")
    y = text_block(d, (110, y + 8), "Listen: " + call["description"], 26, 125, ACCENT)
    call_file = film.root / "sound" / "calls" / f"call_{i:02d}.mp3"  # score.make's numbering
    add(still_clip, img, 12, sound=("bed", call_file, 7.0))

    # 8. Muse Wonder watches and hears the whole film; seven cuts, every one kept.
    crit = film.root / "critique_i2v.json"
    if crit.exists():
        c = json.loads(crit.read_text(encoding="utf-8"))
        img = canvas()
        d = ImageDraw.Draw(img)
        d.text((80, 70), f"Muse Wonder watches and hears the whole film:  {c['score']}/10", font=font(52),
               fill=INK)
        y = text_block(d, (80, 170), c["overall"], 32, 100, DIM)
        y = text_block(d, (80, y + 30), "What it heard:", 32, 100, INK)
        for x in c.get("sound", [])[-1:]:
            y = text_block(d, (110, y + 8), x, 28, 110, ACCENT)
        y = text_block(d, (80, y + 30), "Notes for the next cut:", 32, 100, INK)
        for x in c["weaknesses"][:2]:
            y = text_block(d, (110, y + 8), x, 28, 110, DIM)
        add(still_clip, img, 13)
    versions = sorted((film.root / "versions").glob("v*"), key=lambda p: int(p.name[1:]))
    if versions:  # a version cut without a new critique shows a dash
        scores = [(p.name, json.loads((p / "critique_i2v.json").read_text(encoding="utf-8")).get("score")
                   if (p / "critique_i2v.json").exists() else None) for p in versions]
        img = canvas()
        d = ImageDraw.Draw(img)
        d.text((80, 70), "Critique, fix, critique again: seven cuts, every one kept", font=font(52), fill=INK)
        x0 = 120
        for v, s in scores:
            d.text((x0, 220), v, font=font(40), fill=DIM)
            d.text((x0, 280), f"{s}/10" if s else "–", font=font(56), fill=ACCENT if s and s >= 7 else INK)
            x0 += 240
        text_block(d, (80, 420),
                   "Muse Wonder's notes became retakes, repaints and trims: a capture scene, a keeper's hands on "
                   "the crate, the real Caudan canal, sound. The author's notes went in alongside them. The loop "
                   "stopped when the score held at 7 and the critic began to contradict itself, and the author "
                   "chose the cut. Each version and its critique is kept, in case a fix makes things worse.",
                   34, 95, DIM)
        add(still_clip, img, 10)

    # 9. Spend: the user's own money, under a hard cap.
    fal = i2v.real_spent() or json.loads((film.repo / "ledger_fal.json").read_text(encoding="utf-8"))["spent_usd"]
    takes = sum(len(film.state(s).get("i2v_takes", [])) + sum(len(p["takes"]) for p in film.state(s).get(
        "i2v_takes_prev", [])) for s in painted)
    add(still_clip, card(f"${fal:.2f} of video and sound, under a hard $45 cap.",
                         f"{takes} takes for {len(in_film)} shots. Every clip's worst-case cost is reserved before "
                         "it is sent, and the ledger is checked against fal's own bill after each one. When the "
                         "laptop hibernated mid-clip, the paid request was saved and collected on the next run.",
                         "Spend"), 8)

    # 10. The end of the film, from the shot boundary nearest excerpt_s before the end, with its sound.
    add(still_clip, card("The Dodo Came Back", "What if the dodo returned to Mauritius?", "The film"), 3)
    total = edit.duration(film_cut)
    start = min((t0 for t0, _ in timeline.values()), key=lambda t0: abs(total - t0 - excerpt_s))
    add(video_clip, film_cut, start=start, seconds=total - start, sound=("film", start))

    # 11. Numbers.
    log = film.repo / "generation_log.jsonl"
    c = costs(film.root, log)
    entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()
               if f'"film": "{film.root.name}"' in line]
    muse = sum(e.get("cost_usd", LIST_PRICES.get(e.get("model"), 0.0)) for e in entries if e.get("kind") not in ("video", "audio"))
    accepted = sum(1 for s in in_film for t in film.state(s).get("i2v_takes", [])
                   if t["take"] == film.state(s).get("i2v_choice") and (t.get("review") or {}).get("score", 0) >= 7)
    add(still_clip, card(f"{total:.0f} seconds. {len(in_film)} shots. {accepted} rated 7/10 or better.",
                         f"${fal:.2f} of video and sound, ${muse:.2f} of Meta model calls. {c['calls']} calls in "
                         "all, every prompt, take and review logged, and an AI-disclosure report generated for the "
                         "competition. Open source: github.com/Mikhil-sec/cutaway", "Result"), 8, sound=("bed",))
    silent, _ = edit.assemble(clips, out_dir / "making_of_i2v_silent.mp4")
    score = sorted((film.root / "music").glob("score_v*.mp3"), key=lambda p: p.stat().st_mtime)[-1]
    out = soundtrack(silent, clips, sounds, film_cut, score, out_dir / "making_of_i2v.mp4", bed_from=cold_open)
    return out, edit.duration(out)
