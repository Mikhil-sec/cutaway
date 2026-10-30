"""Day-1 proof, step 2: cut a foreground fern layer from the clean plate and write the shot spec."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import meta  # noqa: E402

P = meta.ROOT / "renders" / "proof"
plate = P / "plate.png"
H = Image.open(plate).height

fg = np.zeros((H, Image.open(plate).width), dtype=bool)
matches = meta.segment(plate, "fern leaves")  # plain "fern" returned no matches
for conf, m in matches:
    rows = np.where(m.any(axis=1))[0]
    if len(rows) and rows.max() > 0.92 * H:  # touches the bottom edge: nearest to camera
        fg |= m
print(f"fern matches {len(matches)}, foreground covers {fg.mean() * 100:.1f}%")

rgb = Image.open(plate).convert("RGB")
rgb.putalpha(Image.fromarray((fg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)))
rgb.save(P / "ferns_fg.png")

# The rock under the dodo's feet must sit at the dodo's depth, or the bird slides when the camera moves.
dodo_alpha = np.asarray(Image.open(P / "dodo_cutout.png").getchannel("A")) > 127
feet_y = np.where(dodo_alpha.any(axis=1))[0].max()
feet_x = int(np.where(dodo_alpha[feet_y])[0].mean())
ground = np.zeros_like(fg)
for conf, m in meta.segment(plate, "rock"):
    if m[min(feet_y + 15, H - 1), feet_x]:
        ground |= m
print(f"ground rock covers {ground.mean() * 100:.1f}%")
rgb = Image.open(plate).convert("RGB")
rgb.putalpha(Image.fromarray((ground * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)))
rgb.save(P / "rock_mid.png")

shot = {
    "name": "proof_dodo_forest",
    "fps": 24,
    "seconds": 5,
    "resolution": [1280, 720],
    "layers": [
        {"image": str(plate), "depth": 40},
        {"image": str(P / "rock_mid.png"), "depth": 12.2},
        {"image": str(P / "dodo_cutout.png"), "depth": 12, "focus": True},
        {"image": str(P / "ferns_fg.png"), "depth": 5},
    ],
    "camera": {"from": [-0.35, 0.0, 0.0], "to": [0.35, 1.6, 0.05], "fstop": 4.0},
}
(P / "shot.json").write_text(json.dumps(shot, indent=2))
print(f"spent so far: ${meta.spent():.2f}")
