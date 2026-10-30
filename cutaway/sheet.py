"""Contact sheets: many images on one page, for quick review.

    python -m cutaway.sheet out.png img1 img2 ... [--cols 3] [--cell 640]
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


def contact_sheet(paths, out, cols=3, cell=640, labels=True):
    paths = [Path(p) for p in paths]
    rows = (len(paths) + cols - 1) // cols
    ch = cell * 9 // 16
    sheet = Image.new("RGB", (cols * cell, rows * (ch + (22 if labels else 0))), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    for i, p in enumerate(paths):
        with Image.open(p) as im:
            thumb = ImageOps.contain(ImageOps.exif_transpose(im).convert("RGB"), (cell, ch))
        x, y = (i % cols) * cell, (i // cols) * (ch + (22 if labels else 0))
        sheet.paste(thumb, (x + (cell - thumb.width) // 2, y + (ch - thumb.height) // 2))
        if labels:
            draw.text((x + 6, y + ch + 4), p.name[:80], fill=(230, 230, 230))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--cell", type=int, default=640)
    a = ap.parse_args()
    contact_sheet(a.images, a.out, a.cols, a.cell)
