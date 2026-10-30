"""Round-two fix: the reveal (s15) must show many dodos unmistakably. The repaint asked for by its review
came back with one clear dodo and two distant heads."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import director, meta  # noqa: E402

film = director.Film(Path(__file__).resolve().parent.parent / "films" / "dodo")
meta.CONTEXT["film"] = "dodo"
shot = next(s for s in film.plan["shots"] if s["id"] == "s15_many_behind_glass")
prompt = (
    "Wide interior shot through a large glass wall into a bare enclosure with a sandy floor: five plump "
    "grey-brown dodos, each whole body clearly visible and roughly the same size, standing spaced apart in a "
    "row across the middle of the frame from left to right, none hidden or overlapping. In the dark foreground, "
    "silhouettes of visitors seen from behind hold up glowing phones toward the glass. Flash-lit night "
    "interior, cold light, a shocking reveal. No legible text or logos."
)
director.apply_changes(film, shot, {"keyframe_prompt": prompt}, redo_keyframe=True,
                       why=["Director's check: the repaint showed one clear dodo and two distant heads; the reveal "
                            "needs many dodos, unmistakably"])
print("queued s15")
