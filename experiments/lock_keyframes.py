"""Lock keyframes the human director has approved, so no automatic review can repaint them.

    python experiments/lock_keyframes.py s19_press_mural [s15_many_behind_glass ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import director  # noqa: E402

film = director.Film(Path(__file__).resolve().parent.parent / "films" / "dodo")
for shot in film.plan["shots"]:
    if shot["id"] in sys.argv[1:]:
        film.state(shot)["keyframe_locked"] = True
        film.save_state(shot)
        print("locked", shot["id"])
