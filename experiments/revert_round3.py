"""Overrule the third Muse Wonder critique: its notes were sharp, but its changes made nearly every shot a
strong-camera 'startle', which would make the quiet film jittery.

1. Rebuild the plan from Muse Spark's original plan plus every revision except this critique's.
2. Apply only the clear wins: the hero in focus from the first frame (s01, s09, s10) and a shorter s16.
3. Restore the keyframes it deleted (plate + cut-outs from the last spec) so their layers can be re-cut.
"""
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import director, meta  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
film = director.Film(ROOT / "films" / "dodo")
meta.CONTEXT["film"] = "dodo"
round3 = {n["shot_id"] for n in json.loads((film.root / "critique.json").read_text(encoding="utf-8"))["shots"]}

# 1. The original plan, from the planning call in the generation log.
plan_call = next(json.loads(line) for line in meta.LOG.read_text(encoding="utf-8").splitlines()
                 if '"kind": "chat"' in line and "You are the director of a short animated film" in line)
original = director.validate_plan(json.loads(plan_call["reply"]), film)
base = {s["id"]: s for s in original["shots"]}

for shot in film.plan["shots"]:
    st = film.state(shot)
    revs = st.get("revisions", [])
    if shot["id"] in round3:  # drop this critique's revision: the last one it made for the shot
        for i in range(len(revs) - 1, -1, -1):
            if any(str(w).startswith("Muse Wonder:") for w in revs[i]["why"]):
                dropped = revs.pop(i)
                st.setdefault("overruled", []).append(dropped)
                break
    rebuilt = dict(base[shot["id"]])
    for rev in revs:
        rebuilt.update(rev["changes"])
    for k in list(shot):
        if not k.startswith("_"):
            shot.pop(k)
    shot.update(rebuilt)
    film.save_state(shot)
film.save()

# 3. Restore keyframes deleted by this round's repaints.
for shot in film.plan["shots"]:
    d = film.shot_dir(shot)
    st = film.state(shot)
    if shot["kind"] != "painted" or (d / "keyframe.png").exists():
        continue
    spec = json.loads((d / "spec_960.json").read_text())
    frame = Image.open(spec["layers"][0]["image"]).convert("RGBA")
    for layer in spec["layers"][1:]:
        if "puppet" in layer:
            frame.alpha_composite(Image.open(layer["image"]).convert("RGBA"))
    frame.convert("RGB").save(d / "keyframe.png")
    st["keyframe_ok"] = True
    st.pop("repaint_notes", None)
    film.save_state(shot)
    print("restored keyframe", shot["id"])

# 2. The clear wins.
by_id = {s["id"]: s for s in film.plan["shots"]}
for sid in ("s01_forest_dawn", "s09_see_mountains", "s10_umbrellas_noticed"):
    director.apply_changes(film, by_id[sid], {"focus_from": "subject"},
                           why=["Director, from Muse Wonder's critique: keep the hero in focus from the first frame"])
director.apply_changes(film, by_id["s16_phones_flashes"], {"duration_s": 3.8},
                       why=["Director, from Muse Wonder's critique: shorten a repeated beat so the middle sags less"])
total = sum(s["duration_s"] for s in film.plan["shots"])
print(f"overruled round 3 on {sorted(round3)}; planned length {total:.1f} s")
