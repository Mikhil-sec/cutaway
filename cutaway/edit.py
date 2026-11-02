"""Editing: end cards and assembling shot clips into the cut with the planned transitions."""
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "assets" / "fonts" / "EBGaramond.ttf"  # SIL Open Font License, assets/fonts/OFL.txt
XFADE_S = 0.7
FADE_IN_S = 0.9


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def end_card(text, seconds, out, resolution):
    """White serif text on black, fading in after a beat of black and out at the end."""
    w, h = resolution
    img = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(str(FONT), int(h * 0.05))
    lines = [s.strip() + "." for s in text.split(".") if s.strip()]  # one sentence per line
    gap = int(h * 0.025)
    heights = [draw.textbbox((0, 0), ln, font=font)[3] for ln in lines]
    y = (h - sum(heights) - gap * (len(lines) - 1)) // 2
    for ln, lh in zip(lines, heights):
        tw = draw.textlength(ln, font=font)
        draw.text(((w - tw) / 2, y), ln, font=font, fill=(232, 228, 220))
        y += lh + gap
    png = Path(out).with_suffix(".png")
    img.save(png)
    ff("-loop", 1, "-t", seconds, "-i", png,
       "-vf", f"fade=in:st=1.0:d=1.5,fade=out:st={seconds - 1.5}:d=1.5,format=yuv420p",
       "-r", 24, "-c:v", "libx264", "-crf", 18, out)
    return out


def caption_png(text, out, resolution):
    """A text card: warm white serif near the bottom edge (below the characters' feet), over a soft dark
    gradient and shadow so it reads on bright city streets as well as dark forest."""
    from PIL import ImageFilter
    w, h = resolution
    font = ImageFont.truetype(str(FONT), int(h * 0.052))
    grad = Image.new("L", (1, h))
    for y in range(h):  # transparent above 72% of the height, up to ~45% black at the bottom edge
        grad.putpixel((0, y), int(115 * max(0.0, (y / h - 0.72) / 0.28) ** 1.4))
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    base.putalpha(grad.resize((w, h)))
    draw = ImageDraw.Draw(base)
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    xy = ((w - (r - l)) / 2 - l, h * 0.945 - b)
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text(xy, text, font=font, fill=(0, 0, 0, 235))
    shadow = shadow.filter(ImageFilter.GaussianBlur(h * 0.008))
    card = Image.alpha_composite(base, shadow)
    ImageDraw.Draw(card).text(xy, text, font=font, fill=(244, 240, 230, 255))
    card.save(out)
    return out


def add_captions(cut, captions, out, resolution):
    """captions: [(text, start_s, seconds)] on the cut's timeline; each fades in and out over the picture."""
    if not captions:
        return cut
    inputs, graph, acc = ["-i", cut], [], "0:v"
    for i, (text, start, dur) in enumerate(captions, start=1):
        png = caption_png(text, Path(out).with_name(f"caption_{i}.png"), resolution)
        inputs += ["-loop", 1, "-t", dur, "-i", png]
        graph.append(f"[{i}:v]format=rgba,fade=in:st=0:d=0.8:alpha=1,fade=out:st={dur - 0.8}:d=0.8:alpha=1,"
                     f"setpts=PTS+{start}/TB[c{i}]")
        graph.append(f"[{acc}][c{i}]overlay=0:0:eof_action=pass[o{i}]")
        acc = f"o{i}"
    ff(*inputs, "-filter_complex", ";".join(graph), "-map", f"[{acc}]", "-c:v", "libx264", "-crf", 18,
       "-pix_fmt", "yuv420p", out)
    return out


def assemble(clips, out):
    """clips: [(path, transition_in)] in order. Crossfades overlap clips; cuts butt them together."""
    inputs, graph = [], []
    for i, (path, trans) in enumerate(clips):
        inputs += ["-i", path]
        chain = f"[{i}:v]fps=24,format=yuv420p,settb=1/24"
        if trans == "fade_from_black":
            chain += f",fade=in:st=0:d={FADE_IN_S}"
        graph.append(f"{chain}[v{i}]")
    acc, length = "v0", duration(clips[0][0])
    for i, (path, trans) in enumerate(clips[1:], start=1):
        d = duration(path)
        nxt = f"a{i}"
        if trans == "crossfade":
            graph.append(f"[{acc}][v{i}]xfade=transition=fade:duration={XFADE_S}:offset={length - XFADE_S:.3f}[{nxt}]")
            length += d - XFADE_S
        else:
            # concat outputs a microsecond timebase; xfade needs both inputs on the same one
            graph.append(f"[{acc}][v{i}]concat=n=2:v=1:a=0,settb=1/24[{nxt}]")
            length += d
        acc = nxt
    ff(*inputs, "-filter_complex", ";".join(graph), "-map", f"[{acc}]", "-c:v", "libx264", "-crf", 18,
       "-pix_fmt", "yuv420p", out)
    return out, length
