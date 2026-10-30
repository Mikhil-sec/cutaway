"""Composite the dodo cut-out over magenta and crop to its alpha box, to inspect the mask edge."""
from pathlib import Path

from PIL import Image

P = Path(__file__).resolve().parent.parent / "renders" / "proof"
cut = Image.open(P / "dodo_cutout.png")
box = cut.getchannel("A").getbbox()
print("size", cut.size, "alpha bbox", box)
bg = Image.new("RGBA", cut.size, (255, 0, 255, 255))
bg.alpha_composite(cut)
x0, y0, x1, y1 = box
pad = 30
bg.crop((x0 - pad, y0 - pad, x1 + pad, y1 + pad)).convert("RGB").save(P / "dodo_check.png")
