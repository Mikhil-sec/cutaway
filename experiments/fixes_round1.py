"""Round-one fixes from the shot reviews that asked for a repaint but scored above the automatic threshold.

Applied through director.apply_changes, so each is recorded in the shot's revision history.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import director, meta  # noqa: E402

film = director.Film(Path(__file__).resolve().parent.parent / "films" / "dodo")
meta.CONTEXT["film"] = "dodo"
by_id = {s["id"]: s for s in film.plan["shots"]}

fixes = {
    "s07_waterfront_pouce": (
        {"focus_to": "subject"},
        " The dodo stands fully inside the frame on the embankment in the left third, its whole body clearly "
        "visible with space around it, well away from the frame edge.",
        "Muse Spark review 5/10: dodo cropped at the left edge; focus pull left the dodo soft for its beat",
    ),
    "s10_umbrellas_noticed": (
        {},
        " Medium-wide: the dodo is small in the centre third with its whole body and feet visible and space "
        "around it; in the distance, tourists clearly hold phones up toward it.",
        "Muse Spark review 6/10: framing too close with feet cropped; distant tourists did not read as raising phones",
    ),
}
for sid, (changes, addition, why) in fixes.items():
    shot = by_id[sid]
    changes = {**changes, "keyframe_prompt": shot["keyframe_prompt"] + addition}
    director.apply_changes(film, shot, changes, redo_keyframe=True, why=[why])
    print("queued", sid)
