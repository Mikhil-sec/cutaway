"""Recompute shot specs with the current director code and report which shots would change.

    python experiments/spec_audit.py [--skip id1,id2] [--apply]

With --apply, deletes the rendered clip of each changed shot so 'produce' re-renders it
(its stale frames are discarded by the spec stamp).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import director  # noqa: E402

skip = set(sys.argv[sys.argv.index("--skip") + 1].split(",")) if "--skip" in sys.argv else set()
film = director.Film(Path(__file__).resolve().parent.parent / "films" / "dodo")
changed = []
for s in film.plan["shots"]:
    if s["kind"] != "painted" or s["id"] in skip or not film.state(s).get("layers"):
        continue
    path = film.shot_dir(s) / "spec_960.json"
    stamp = film.shot_dir(s) / "frames_960" / ".spec"
    rendered_with = stamp.read_text() if stamp.exists() else ""
    new = director.spec(film, s).read_text()
    sp = json.loads(new)
    diff = new != rendered_with
    print(f"{s['id']:<24} overscan {sp.get('overscan', 1.25)} scale {film.state(s)['camera_scale']:.2f} "
          f"{'CHANGED' if diff else 'same'}")
    if diff:
        changed.append(s)
if "--apply" in sys.argv:
    for s in changed:
        (film.shot_dir(s) / "shot_960.mp4").unlink(missing_ok=True)
    print("cleared renders:", [s["id"] for s in changed])
