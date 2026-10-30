"""Restore the approved reveal keyframe (s15) after an automatic repaint deleted it: the clean plate plus
the five cut-out dodos re-composite to the original. Lock it, re-cut layers, and clear the stale render."""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import director, meta  # noqa: E402

film = director.Film(Path(__file__).resolve().parent.parent / "films" / "dodo")
meta.CONTEXT["film"] = "dodo"
shot = next(s for s in film.plan["shots"] if s["id"] == "s15_many_behind_glass")
d = film.shot_dir(shot)
frame = Image.open(d / "plate.png").convert("RGBA")
for i in range(5):
    frame.alpha_composite(Image.open(d / f"bird_{i}.png").convert("RGBA"))
frame.convert("RGB").save(d / "keyframe.png")

st = film.state(shot)
st.update(keyframe_ok=True, keyframe_locked=True, reviewed=False)
st.pop("layers", None)
st.setdefault("revisions", []).append({"changes": {}, "redo_keyframe": False, "why": [
    "Director: approved keyframe restored from its plate and cut-outs and locked; the review's crop "
    "complaint was framing, fixed by group framing"]})
film.save_state(shot)
for p in d.glob("shot_*.mp4"):
    p.unlink()
print("restored and locked s15")
