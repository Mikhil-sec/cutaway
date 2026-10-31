"""Build the making-of demo video from the dodo film's artifacts."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import director, makingof  # noqa: E402

film = director.Film(Path(__file__).resolve().parent.parent / "films" / "dodo")
source = film.root / "film_1920.mp4"
if not source.exists():
    source = film.root / "film_960.mp4"
out, length = makingof.build(film, film.root / "makingof", source)
print(f"{out} ({length:.1f} s)")
