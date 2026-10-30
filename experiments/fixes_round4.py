"""Round-four fix: s12's prompt said 'the dodo in left third' and the critique's addition said 'alone in the
middle', so three attempts put the dodo outside the ring. Replace the prompt with one consistent description."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import director, meta  # noqa: E402

film = director.Film(Path(__file__).resolve().parent.parent / "films" / "dodo")
meta.CONTEXT["film"] = "dodo"
shot = next(s for s in film.plan["shots"] if s["id"] == "s12_crowd_wide")
prompt = ("High wide shot looking down on the Caudan Waterfront plaza under colourful hanging umbrellas: a dense "
          "ring of tourists stands shoulder to shoulder in a closed circle, all facing inward, many holding up "
          "phones. In the empty circle of cobblestones at the exact centre of the ring stands the dodo, alone, "
          "whole body visible, head lowered. The stone arch gate tower and palms are behind. Overwhelming, "
          "trapped mood. No legible text or logos.")
director.apply_changes(film, shot, {"keyframe_prompt": prompt, "focus_from": "subject"}, redo_keyframe=True,
                       why=["Director: the appended note contradicted the original placement; prompt rewritten"])
print("s12 prompt rewritten")
