"""Show head (red tint) and body (blue tint) over magenta, cropped to the dodo, with the neck pivot marked."""
import json
from pathlib import Path

from PIL import Image, ImageDraw

P = Path(__file__).resolve().parent.parent / "renders" / "proof"
bg = Image.new("RGBA", (2048, 1152), (255, 0, 255, 255))
for name, tint in (("dodo_body.png", (0, 0, 255, 70)), ("dodo_head.png", (255, 0, 0, 70))):
    part = Image.open(P / name)
    bg.alpha_composite(part)
    overlay = Image.new("RGBA", part.size, tint)
    overlay.putalpha(part.getchannel("A").point(lambda a: 70 if a > 127 else 0))
    bg.alpha_composite(overlay)
piv = json.loads((P / "pivots.json").read_text())
d = ImageDraw.Draw(bg)
for x, y in piv.values():
    d.ellipse((x - 6, y - 6, x + 6, y + 6), outline=(255, 255, 0, 255), width=3)
bg.crop((1430, 360, 1820, 780)).convert("RGB").save(P / "parts_check.png")
