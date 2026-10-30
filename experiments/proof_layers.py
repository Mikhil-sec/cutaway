"""Day-1 proof, step 1: one Muse Image still -> SAM 3.1 cut-out + clean plate.

Run from the repo root: .venv/Scripts/python experiments/proof_layers.py
Outputs go to renders/proof/.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import meta  # noqa: E402

OUT = meta.ROOT / "renders" / "proof"
SCENE = OUT / "scene.png"
STYLE = "Muted cinematic anime film still, painterly backgrounds, soft natural light, 2D hand-painted look."

if not SCENE.exists():
    meta.image(
        f"{STYLE} Wide shot: a single dodo bird standing on a mossy basalt rock in a misty "
        "Mauritian native forest at dawn, tall ebony trees, ferns in the foreground, "
        "a distant volcanic peak in the haze. The dodo is in the right third of the frame, full body visible.",
        SCENE,
    )

matches = meta.segment(SCENE, "dodo")
print(f"dodo matches: {[round(c, 3) for c, _ in matches]}")
if not matches:
    sys.exit("SAM found no dodo")
conf, mask = matches[0]

rgb = Image.open(SCENE).convert("RGB")
alpha = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
cut = rgb.copy()
cut.putalpha(alpha)
cut.save(OUT / "dodo_cutout.png")
print(f"mask covers {mask.mean() * 100:.1f}% of the frame")

plate = OUT / "plate.png"
if not plate.exists():
    meta.image(
        "Remove the dodo bird completely from this image and fill in the rock and forest behind it. "
        "Keep everything else exactly the same: composition, colours, light and style.",
        plate,
        refs=[SCENE],
    )
print(f"spent so far: ${meta.spent():.2f}")
