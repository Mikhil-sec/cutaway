"""Build the making-of demo video from the dodo film's artifacts.

Default: the image-to-video pipeline (films/dodo/makingof/making_of_i2v.mp4) from the final cut.
--blender: the earlier 2.5D Blender making-of.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import director, makingof  # noqa: E402

film = director.Film(Path(__file__).resolve().parent.parent / "films" / "dodo")
if "--blender" in sys.argv:
    source = film.root / "film_1920.mp4"
    if not source.exists():
        source = film.root / "film_960.mp4"
    out, length = makingof.build(film, film.root / "makingof", source)
else:
    out, length = makingof.build_i2v(film, film.root / "makingof", film.root / "cut_1920.mp4")
print(f"{out} ({length:.1f} s)")
