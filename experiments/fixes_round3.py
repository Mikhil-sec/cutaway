"""Round-three fix: in the reveal (s15) the visitors' silhouettes are the foreground, but the planner's
foreground phrase ("glass reflection") found nothing, so they stayed on the background plate behind the
dodos. Re-cut the layers with a phrase SAM can find; the approved keyframe is kept."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import director, meta  # noqa: E402

film = director.Film(Path(__file__).resolve().parent.parent / "films" / "dodo")
meta.CONTEXT["film"] = "dodo"
shot = next(s for s in film.plan["shots"] if s["id"] == "s15_many_behind_glass")
director.apply_changes(film, shot, {"foreground": "person silhouette"},
                       why=["Director's check: visitor silhouettes were left on the background plate"])
film.state(shot).pop("layers", None)
film.save_state(shot)
print("s15: foreground phrase set, layers cleared")
