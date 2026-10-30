"""Proof 2, step 1: split the dodo into puppet parts (head, body) with SAM 3.1.

The head is dilated a little so it overlaps the neck: when it tilts, the seam
stays covered instead of showing the background through a gap. The head's
pivot is the middle of that seam, where head meets body.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import meta  # noqa: E402

P = meta.ROOT / "renders" / "proof"
scene = Image.open(P / "scene.png").convert("RGB")
dodo = np.asarray(Image.open(P / "dodo_cutout.png").getchannel("A")) > 127


def as_img(mask):
    return Image.fromarray((mask * 255).astype(np.uint8))


def save(mask, name):
    im = scene.copy()
    im.putalpha(as_img(mask).filter(ImageFilter.GaussianBlur(1.2)))
    im.save(P / name)


if not (P / "dodo_head.png").exists():
    heads = meta.segment(P / "scene.png", "dodo head")
    print(f"head matches: {[round(c, 3) for c, _ in heads]}")
    raw_head = heads[0][1] & dodo
    head = (np.asarray(as_img(raw_head).filter(ImageFilter.MaxFilter(9))) > 127) & dodo
    save(head, "dodo_head.png")
    save(dodo & ~raw_head, "dodo_body.png")

head = np.asarray(Image.open(P / "dodo_head.png").getchannel("A")) > 127
body = np.asarray(Image.open(P / "dodo_body.png").getchannel("A")) > 127
seam = head & body  # the dilated overlap at the neck
ys, xs = np.nonzero(seam)
feet_y = int(np.where(dodo.any(axis=1))[0].max())
feet_x = int(np.where(dodo[feet_y])[0].mean())
pivots = {"neck": [int(xs.mean()), int(ys.mean())], "feet": [feet_x, feet_y]}
(P / "pivots.json").write_text(json.dumps(pivots))
print(pivots, f"spent ${meta.spent():.2f}")
