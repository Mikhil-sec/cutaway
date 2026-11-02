"""Sound for the image-to-video cut: Muse Spark designs it, fal's audio models make it, code mixes it.

- Muse Spark reads the story and the cut's timeline and writes the sound design: a composition plan for the
  score (sections that start on chosen shots), what each shot should sound like, and a few moments where the
  dodo itself calls. Code turns the sections into exact durations from the timeline, so the music turns where
  the picture turns.
- ElevenLabs Music composes the score from that plan; MMAudio watches each shot and makes its synced sound
  effects; ElevenLabs sound effects make the dodo's calls. Nobody knows what a dodo sounded like: the calls
  are modelled on its closest living relative, the Nicobar pigeon (low, soft, throaty coos and grunts).
- Every call goes through the fal ledger cap in i2v.py. Each version of the sound is kept (score_v1, v2...).
"""
import base64
import json
import subprocess
from pathlib import Path

from . import edit, i2v, meta

SPARK = "muse-spark-1.3"
SR = 48000
LEVEL_DB = {"silent": None, "low": -24, "mid": -17, "high": -11}
CALL_DB = -8
MUSIC_DB = {"low": -20, "mid": -14, "high": -9}
AUDIO_CEILING_USD = 44.00
TARGET_LUFS = -16  # absolute fal ledger total, as for the video takes

S = {"type": "string"}


def _obj(props):
    return {"type": "object", "additionalProperties": False, "required": list(props), "properties": props}


def _design_schema(ids):
    sid = {"type": "string", "enum": ids}
    lvl = {"type": "string", "enum": list(LEVEL_DB)}
    styles = {"type": "array", "items": S}
    return _obj({
        "music": _obj({
            "positive_global_styles": styles,
            "negative_global_styles": styles,
            "sections": {"type": "array", "items": _obj({
                "section_name": S, "starts_at_shot": sid, "level": {"type": "string", "enum": list(MUSIC_DB)},
                "positive_local_styles": styles, "negative_local_styles": styles})},
        }),
        "shots": {"type": "array", "items": _obj({"shot_id": sid, "sound": S, "level": lvl})},
        "calls": {"type": "array", "items": _obj({
            "shot_id": sid, "at_s": {"type": "number"}, "seconds": {"type": "number"}, "description": S})},
    })


def _timeline(film):
    return json.loads((film.root / "timeline.json").read_text(encoding="utf-8"))


def design(film, force=False):
    """One Muse Spark call: the score's sections, each shot's sound, and the dodo's calls."""
    path = film.root / "sound_design.json"
    if path.exists() and not force:
        return json.loads(path.read_text(encoding="utf-8"))
    tl = _timeline(film)
    shots = {s["id"]: s for s in film.plan["shots"]}
    motion = json.loads((film.root / "motion.json").read_text(encoding="utf-8"))
    acting = {m["shot_id"]: m["motion_prompt"] for m in motion["shots"]}
    lines = "\n".join(f"{sid}  {t0:6.1f}-{t1:6.1f} s  {desc[:160]}\n    on screen: {acting.get(sid, '')[:260]}\n"
                      f"    sound note: {shots[sid].get('sound', '')}" for sid, t0, t1, desc in tl)
    meta.CONTEXT.pop("shot", None)
    r = meta.chat(SPARK, [
        {"role": "system", "content":
            "You are the composer and sound designer of a wordless animated short film. Design its sound:\n"
            "music: an instrumental score in sections. Each section starts at a shot (the first at the first "
            "shot) and lasts until the next section starts; use 5 to 8 sections that follow the story's "
            "emotional turns. Styles are short phrases for a music model (instruments, tempo, mood, dynamics); "
            "keep one consistent palette for the whole film (for example solo piano, soft strings, a muted "
            "Mauritian ravanne heartbeat used sparingly) and develop it, rather than changing genre. No vocals. "
            "level: how loud the music sits under the scene.\n"
            "shots: for every shot, one sentence describing only the sounds of the place and the action that a "
            "video-to-audio model should make (no music, no speech, no dodo voice), and how loud they sit.\n"
            "calls: 4 to 7 moments where the dodo itself makes a sound, only where its acting shows it (a waking "
            "grunt, a startled squawk, a questioning coo, a long sad coo against the mural, a sleepy sigh). No "
            "one knows a dodo's voice; describe each call as a large pigeon's (its closest relative is the "
            "Nicobar pigeon): low, soft, throaty coos and grunts. at_s is seconds from the start of that shot; "
            "seconds is the call's length (0.8 to 3)."},
        {"role": "user", "content": f"Story:\n{(film.root / 'story.md').read_text(encoding='utf-8')}\n\n"
                                    f"The cut, shot by shot:\n{lines}"},
    ], schema=_design_schema([t[0] for t in tl]), max_tokens=16000, reasoning_effort="medium")
    path.write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
    return r


def composition_plan(film, d):
    """Section durations from the timeline: each section runs from its first shot to the next section's."""
    tl = _timeline(film)
    start = {sid: t0 for sid, t0, _, _ in tl}
    total = tl[-1][2]
    secs = sorted([s for s in d["music"]["sections"] if s["starts_at_shot"] in start],
                  key=lambda s: start[s["starts_at_shot"]])
    secs[0] = {**secs[0], "starts_at_shot": tl[0][0]}
    times = [max(0.0, start[s["starts_at_shot"]]) for s in secs] + [total]
    plan, merged = [], []
    for s, t0, t1 in zip(secs, times, times[1:]):  # a section under 3 s joins the one before it
        if merged and (t1 - t0) < 3:
            merged[-1][2] = t1
        else:
            merged.append([s, t0, t1])
    for s, t0, t1 in merged:
        ms = int(round((t1 - t0) * 1000))
        while ms > 120000:  # the model's longest section
            plan.append({"section_name": s["section_name"][:100], "duration_ms": 60000, "lines": [],
                         "positive_local_styles": s["positive_local_styles"],
                         "negative_local_styles": s["negative_local_styles"]})
            ms -= 60000
        plan.append({"section_name": s["section_name"][:100], "duration_ms": max(3000, ms), "lines": [],
                     "positive_local_styles": s["positive_local_styles"],
                     "negative_local_styles": s["negative_local_styles"]})
    return {"positive_global_styles": d["music"]["positive_global_styles"],
            "negative_global_styles": d["music"]["negative_global_styles"] + ["vocals", "singing", "lyrics"],
            "sections": plan}, merged


def _data_url(path, mime):
    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"


def _clip_for(film, sid, w=1280):
    """The shot as it appears in the cut (with the editor's trim), small enough to upload."""
    from . import animate
    shot = next(s for s in film.plan["shots"] if s["id"] == sid)
    d = film.shot_dir(shot)
    trim = animate.load_motion(film).get(sid, {}).get("trim")
    out = d / "sfx_source.mp4"
    args = ["-ss", trim[0], "-to", trim[1]] if trim else []
    edit.ff(*args, "-i", d / f"shot_i2v_{w}.mp4", "-vf", "scale=640:-2", "-an", "-c:v", "libx264", "-crf", 28, out)
    return out


def _versioned(folder, stem, ext):
    folder.mkdir(parents=True, exist_ok=True)
    n = 1
    while (folder / f"{stem}_v{n}{ext}").exists():
        n += 1
    return folder / f"{stem}_v{n}{ext}"


def make(film, parts=("music", "sfx", "calls"), force=False):
    """Generate the audio the design asks for. Existing pieces are kept unless force; a forced new score is a
    new version (score_v2...), never an overwrite."""
    d = design(film)
    tl = _timeline(film)
    total = tl[-1][2]
    made = {}
    if "music" in parts:
        latest = sorted((film.root / "music").glob("score_v*.mp3")) if (film.root / "music").exists() else []
        if latest and not force:
            made["music"] = latest[-1]
        else:
            plan, _ = composition_plan(film, d)
            out = _versioned(film.root / "music", "score", ".mp3")
            seconds = sum(s["duration_ms"] for s in plan["sections"]) / 1000
            meta.CONTEXT["shot"] = "score"
            i2v.audio("music_el", {"composition_plan": plan, "respect_sections_durations": True,
                                   "output_format": "mp3_44100_192"}, out, seconds, limit=AUDIO_CEILING_USD)
            out.with_suffix(".plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
            made["music"] = out
            print(f"  score: {out.name} ({seconds:.0f} s), fal ledger ${i2v.spent():.2f}", flush=True)
    if "sfx" in parts:
        for x in d["shots"]:
            shot = next((s for s in film.plan["shots"] if s["id"] == x["shot_id"]), None)
            if not shot or shot["kind"] != "painted" or LEVEL_DB[x["level"]] is None:
                continue
            out = film.shot_dir(shot) / "sfx.wav"
            if out.exists() and not force:
                continue
            src = _clip_for(film, shot["id"])
            dur = edit.duration(src)
            meta.CONTEXT["shot"] = shot["id"]
            vid = out.with_name("sfx_mmaudio.mp4")
            i2v.audio("mmaudio", {"video_url": _data_url(src, "video/mp4"), "prompt": x["sound"],
                                  "negative_prompt": "music, speech, voices, singing, bird calls, squawks",
                                  "duration": round(dur, 2), "num_steps": 25}, vid, dur, limit=AUDIO_CEILING_USD)
            edit.ff("-i", vid, "-vn", "-ar", SR, "-ac", 2, out)
            print(f"  sfx: {shot['id']} ({dur:.1f} s)", flush=True)
    if "calls" in parts:
        folder = film.root / "sound" / "calls"
        folder.mkdir(parents=True, exist_ok=True)
        for i, c in enumerate(d["calls"], start=1):
            out = folder / f"call_{i:02d}.mp3"
            if out.exists() and not force:
                continue
            secs = min(3.0, max(0.8, c["seconds"]))
            text = (f"{c['description']} A single call from one large, flightless, pigeon-like bird, close and "
                    "dry, nothing else audible: no music, no other animals, no people.")
            meta.CONTEXT["shot"] = c["shot_id"]
            i2v.audio("sfx_el", {"text": text, "duration_seconds": secs, "prompt_influence": 0.6,
                                 "output_format": "mp3_44100_192"}, out, secs, limit=AUDIO_CEILING_USD)
            print(f"  call {i}: {c['shot_id']} +{c['at_s']} s", flush=True)
    return made


def mix(film, res=(1920, 1080), music=None):
    """Mix the score, each shot's effects and the dodo's calls under the cut; mux onto film_<w>.mp4."""
    d = design(film)
    tl = _timeline(film)
    start = {sid: (t0, t1) for sid, t0, t1, _ in tl}
    total = tl[-1][2]
    music = music or next(iter(sorted((film.root / "music").glob("score_v*.mp3"))[-1:]), None)
    _, sections = composition_plan(film, d)
    inputs, filters, labels = [], [], []

    def add(path, chain):
        n = len(inputs) // 2
        inputs.extend(["-i", str(path)])
        filters.append(f"[{n}:a]aresample={SR},aformat=channel_layouts=stereo,{chain}[a{n}]")
        labels.append(f"[a{n}]")

    for x in d["shots"]:
        shot = next((s for s in film.plan["shots"] if s["id"] == x["shot_id"]), None)
        db = LEVEL_DB[x["level"]]
        if not shot or shot["id"] not in start or db is None or not (film.shot_dir(shot) / "sfx.wav").exists():
            continue
        t0, t1 = start[shot["id"]]
        dur = t1 - t0
        ms = int(max(t0, 0) * 1000)
        add(film.shot_dir(shot) / "sfx.wav", f"atrim=0:{dur:.3f},volume={db}dB,afade=t=in:d=0.25,"
                                             f"afade=t=out:st={max(0.0, dur - 0.35):.3f}:d=0.35,adelay={ms}|{ms}")
    for i, c in enumerate(d["calls"], start=1):
        f = film.root / "sound" / "calls" / f"call_{i:02d}.mp3"
        if f.exists() and c["shot_id"] in start:
            t0, t1 = start[c["shot_id"]]
            ms = int(min(t1 - 0.5, t0 + c["at_s"]) * 1000)
            add(f, f"volume={CALL_DB}dB,afade=t=out:st={max(0.1, c['seconds'] - 0.3):.2f}:d=0.3,adelay={ms}|{ms}")
    if music:
        # The score's loudness follows the design, section by section.
        expr = "+".join(f"between(t,{t0:.3f},{t1:.3f})*{10 ** (MUSIC_DB[s['level']] / 20):.4f}"
                        for s, t0, t1 in sections)
        add(music, f"volume='{expr}':eval=frame,afade=t=out:st={total - 4:.2f}:d=4")
    filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=longest,"
                   f"apad=whole_dur={total:.2f},atrim=0:{total:.2f},"
                   f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11,aresample={SR}[mix]")  # web/festival loudness
    wav = film.root / f"soundtrack_i2v_{res[0]}.wav"
    edit.ff(*inputs, "-filter_complex", ";".join(filters), "-map", "[mix]", "-ar", SR, "-ac", 2, wav)
    out = film.root / f"film_{res[0]}.mp4"
    edit.ff("-i", film.root / f"cut_{res[0]}.mp4", "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-shortest", out)
    print(f"film with sound: {out} (score: {music.name if music else 'none'})")
    return out


def conform(film, old_timeline, music, out, xfade=0.5):
    """Re-edit a score made for an earlier cut to fit the current one, the way a music editor would: each
    shot keeps the music that played under its start, cut where the shot now ends, with short crossfades
    wherever a cut in the picture became a cut in the music. Free, where composing again is not."""
    old = {sid: t0 for sid, t0, _, _ in old_timeline}
    new = _timeline(film)
    total = new[-1][2]
    starts = [t0 for _, t0, _, _ in new] + [total]
    spans = []  # (source start, source end) in the old score
    for (sid, t0, _, _), nxt in zip(new, starts[1:]):
        src0 = old.get(sid, t0)
        src1 = src0 + (nxt - t0)
        if spans and abs(spans[-1][1] - src0) < 0.05:
            spans[-1] = (spans[-1][0], src1)
        else:
            spans.append((src0, src1))
    if len(spans) == 1:
        edit.ff("-i", music, "-t", f"{total:.3f}", out)
        return out
    inputs, graph = [], []
    for i, (a, b) in enumerate(spans):  # each span runs on by the crossfade it will lose to the next
        tail = xfade if i < len(spans) - 1 else 0.0
        inputs += ["-i", music]
        graph.append(f"[{i}:a]atrim={max(0.0, a):.3f}:{b + tail:.3f},asetpts=PTS-STARTPTS[s{i}]")
    acc = "s0"
    for i in range(1, len(spans)):
        graph.append(f"[{acc}][s{i}]acrossfade=d={xfade}:c1=tri:c2=tri[x{i}]")
        acc = f"x{i}"
    edit.ff(*inputs, "-filter_complex", ";".join(graph), "-map", f"[{acc}]", "-ar", SR, out)
    return out
