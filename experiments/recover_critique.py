"""Recover from the first Muse Wonder critique, which marked 11 shots for repainting (some whose own note
said to keep them), and act on it as the director would.

1. Restore each deleted keyframe from its clean plate plus the cut-out layers listed in its last spec.
2. Keep the critique's timing and intensity changes, but undo the 'startle' it gave the quiet search (s05).
3. Repaint only the three shots whose notes name a concrete content problem (s10, s12, s14).
"""
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import director, meta  # noqa: E402

film = director.Film(Path(__file__).resolve().parent.parent / "films" / "dodo")
meta.CONTEXT["film"] = "dodo"
by_id = {s["id"]: s for s in film.plan["shots"]}
REPAINT = {
    "s10_umbrellas_noticed": " The people under the umbrellas have all turned toward the dodo: faces, bodies and "
                             "raised phones point at it, some pointing with a hand.",
    "s12_crowd_wide": " The crowd forms a closed ring all the way around the dodo, leaving it alone in a small "
                      "empty circle of cobblestones in the middle; it is clearly trapped.",
    "s14_park_arrival": " The entrance reads as a tourist attraction, not a refuge: a ticket booth, a turnstile, "
                        "a queue rope and a large blank sign with a cartoon dodo logo over a gate in a chain-link "
                        "fence.",
}

restored = []
for shot in film.plan["shots"]:
    d = film.shot_dir(shot)
    spec_path = d / "spec_960.json"
    if shot["kind"] != "painted" or (d / "keyframe.png").exists() or not spec_path.exists():
        continue
    spec = json.loads(spec_path.read_text())
    frame = Image.open(spec["layers"][0]["image"]).convert("RGBA")  # the plate
    for layer in spec["layers"][1:]:
        if "puppet" in layer:  # characters back onto the plate they were removed from
            frame.alpha_composite(Image.open(layer["image"]).convert("RGBA"))
    frame.convert("RGB").save(d / "keyframe.png")
    st = film.state(shot)
    st["keyframe_ok"] = True
    st.setdefault("revisions", []).append({"changes": {}, "redo_keyframe": False, "why": [
        "Director: keyframe restored from its plate and cut-outs; the critique's repaint request was "
        "overruled (its note asked to keep the frame or concerned timing)"]})
    film.save_state(shot)
    restored.append(shot["id"])
print("restored:", restored)

director.apply_changes(film, by_id["s05_downtown_search"], {"action": "look_around"},
                       why=["Director: a startle does not fit the quiet search; keep looking around"])
for sid, addition in REPAINT.items():
    shot = by_id[sid]
    director.apply_changes(film, shot, {"keyframe_prompt": shot["keyframe_prompt"] + addition},
                           redo_keyframe=True,
                           why=["Director, acting on Muse Wonder's critique: " + addition.strip()])
print("repaint queued:", list(REPAINT))
total = sum(s["duration_s"] for s in film.plan["shots"])
print(f"planned length now {total:.1f} s")
