"""Round-five fix: s09's critique repaint was made without the critique's reason, so the dodo still faces away
from the mountains it is meant to long for. Repaint with the reason (now passed automatically)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import director, meta  # noqa: E402

film = director.Film(Path(__file__).resolve().parent.parent / "films" / "dodo")
meta.CONTEXT["film"] = "dodo"
shot = next(s for s in film.plan["shots"] if s["id"] == "s09_see_mountains")
director.apply_changes(film, shot, {}, redo_keyframe=True, why=[
    "The dodo must face toward Le Pouce and the Moka mountains, looking at them across the city with its back "
    "partly to the camera, so the shot reads as longing for the distant forested mountains."])
print("s09 queued")

# s13 was queued for a repaint by the same critique, also without its reason.
crate = next(s for s in film.plan["shots"] if s["id"] == "s13_crate_harbour")
st = film.state(crate)
if not st.get("keyframe_ok"):
    st["repaint_notes"] = ["The dodo must be visibly confined inside a closed wooden crate with slats in front of "
                           "it, being carried away, seen through the gaps between the slats; the harbour cranes "
                           "are glimpsed behind."]
    film.save_state(crate)
    print("s13 repaint notes set")
