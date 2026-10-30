"""Sound: ambience beds and effects per shot, mixed to the cut's timeline, plus optional music.

Beds come from openly licensed recordings (assets/audio, see CREDITS.md) or are
synthesized here, so every sound in the film has a clear origin. Muse Spark
writes the cue sheet from each shot's sound notes; code does the mixing.
"""
import json
import random
import subprocess
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
AUDIO = ROOT / "assets" / "audio"
SR = 48000
BEDS = ["forest", "city", "crowd", "harbour", "room", "wind", "silence"]
LEVELS = {"low": -26, "mid": -18, "high": -12}  # dB


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], check=True)


def synth_assets():
    """Generate the synthesized beds and the shutter click once (60 s each)."""
    AUDIO.mkdir(parents=True, exist_ok=True)
    recipes = {
        "synth_traffic.wav": "anoisesrc=d=60:c=brown:a=0.6,lowpass=f=380,highpass=f=35,"
                             "tremolo=f=0.1:d=0.5",
        "synth_room.wav": "anoisesrc=d=60:c=pink:a=0.25,lowpass=f=900,highpass=f=60",
        "synth_wind.wav": "anoisesrc=d=60:c=pink:a=0.5,bandpass=f=500:width_type=o:w=2,tremolo=f=0.15:d=0.7",
        "synth_water.wav": "anoisesrc=d=60:c=pink:a=0.4,bandpass=f=900:width_type=o:w=1.5,tremolo=f=0.4:d=0.8",
    }
    for name, graph in recipes.items():
        if not (AUDIO / name).exists():
            ff("-f", "lavfi", "-i", graph, "-ar", SR, "-ac", 2, AUDIO / name)
    click = AUDIO / "synth_shutter.wav"
    if not click.exists():
        rnd = np.random.default_rng(3)
        t = np.arange(int(0.09 * SR)) / SR
        sig = np.zeros_like(t)
        for start, length, gain in ((0.0, 0.012, 1.0), (0.045, 0.02, 0.7)):  # mirror up, shutter close
            idx = (t >= start) & (t < start + length)
            env = np.exp(-(t[idx] - start) / (length / 4))
            sig[idx] += gain * env * rnd.standard_normal(idx.sum())
        sig = (sig / np.abs(sig).max() * 0.8 * 32767).astype(np.int16)
        with wave.open(str(click), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(sig.tobytes())


SOURCES = {  # bed -> (file, loopable length in s)
    "forest": [("birdsong_blackbird_ccby.ogg", 70), ("synth_wind.wav", 60)],
    "city": [("synth_traffic.wav", 60), ("cafe_crowd_cc0.ogg", 1200)],
    "crowd": [("cafe_crowd_cc0.ogg", 1200)],
    "harbour": [("synth_water.wav", 60), ("synth_wind.wav", 60)],
    "room": [("synth_room.wav", 60)],
    "wind": [("synth_wind.wav", 60)],
    "silence": [],
}


def cue_schema(shot_ids):
    return {"type": "object", "additionalProperties": False, "required": ["cues"], "properties": {
        "cues": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                            "required": ["shot_id", "bed", "level", "shutter_clicks"],
                                            "properties": {
                                                "shot_id": {"type": "string", "enum": shot_ids},
                                                "bed": {"type": "string", "enum": BEDS},
                                                "level": {"type": "string", "enum": list(LEVELS)},
                                                "shutter_clicks": {"type": "integer"}}}}}}


def mix(timeline, cues, out, total, music=None, seed=1):
    """timeline: [(shot_id, start, end, desc)]; cues: {shot_id: cue}. Writes a stereo wav of `total` seconds."""
    synth_assets()
    rnd = random.Random(seed)
    inputs, filters, labels = [], [], []
    n = 0
    for sid, t0, t1, _ in timeline:
        cue = cues.get(sid)
        if not cue:
            continue
        dur = (t1 - t0) + 0.7  # overlap into the next shot so beds crossfade
        gain = LEVELS[cue["level"]]
        for k, (name, length) in enumerate(SOURCES[cue["bed"]]):
            start = rnd.uniform(0, max(0.0, length - dur - 1))
            inputs += ["-ss", f"{start:.2f}", "-t", f"{dur:.2f}", "-i", AUDIO / name]
            g = gain - 6 * k  # secondary layers sit under the first
            filters.append(f"[{n}:a]aresample={SR},aformat=channel_layouts=stereo,volume={g}dB,"
                           f"afade=t=in:d=0.6,afade=t=out:st={dur - 0.7:.2f}:d=0.7,"
                           f"adelay={int(max(t0, 0) * 1000)}|{int(max(t0, 0) * 1000)}[s{n}]")
            labels.append(f"[s{n}]")
            n += 1
        for c in range(cue["shutter_clicks"]):
            at = t0 + rnd.uniform(0.3, max(0.4, t1 - t0 - 0.3))
            inputs += ["-i", AUDIO / "synth_shutter.wav"]
            filters.append(f"[{n}:a]aresample={SR},aformat=channel_layouts=stereo,volume={rnd.uniform(-20, -12):.1f}dB,"
                           f"adelay={int(at * 1000)}|{int(at * 1000)}[s{n}]")
            labels.append(f"[s{n}]")
            n += 1
    if music:
        inputs += ["-i", music]
        filters.append(f"[{n}:a]aresample={SR},aformat=channel_layouts=stereo,volume=-14dB,"
                       f"afade=t=in:d=3,afade=t=out:st={total - 6:.2f}:d=6[s{n}]")
        labels.append(f"[s{n}]")
        n += 1
    # Pad with silence to the cut's full length: the last shots may be silent by design, and a short soundtrack
    # would make the mux cut the film (and its end card) short.
    filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=longest,"
                   f"apad=whole_dur={total:.2f},atrim=0:{total:.2f},alimiter=limit=0.9[mix]")
    ff(*inputs, "-filter_complex", ";".join(filters), "-map", "[mix]", "-ar", SR, "-ac", 2, out)
    return out
