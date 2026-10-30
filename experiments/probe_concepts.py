"""Try several SAM concept phrases on one image and report how many matches touch the bottom edge."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import meta  # noqa: E402

img = Path(sys.argv[1])
for concept in sys.argv[2:]:
    found = meta.segment(img, concept)
    H = found[0][1].shape[0] if found else 1
    bottom = sum(1 for _, m in found if np.where(m.any(axis=1))[0].max() > 0.92 * H)
    cover = np.any([m for _, m in found], axis=0).mean() * 100 if found else 0
    print(f"{concept!r}: {len(found)} matches, {bottom} touch bottom, cover {cover:.1f}%")
