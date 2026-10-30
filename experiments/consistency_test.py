"""Can Muse Image keep the same dodo across new scenes, and can Muse Spark tell?

1. Reference sheet: the proof dodo on a plain background.
2. Two story scenes generated with that reference (Port Louis street; Dodo Park).
3. Muse Spark compares each scene's dodo with the reference (schema-constrained).
"""
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import keyframes, meta  # noqa: E402

P = meta.ROOT / "renders" / "proof"
OUT = meta.ROOT / "renders" / "consistency"
OUT.mkdir(parents=True, exist_ok=True)
STYLE = "Muted cinematic anime film still, painterly backgrounds, soft natural light, 2D hand-painted look."

ref = OUT / "dodo_ref.png"
if not ref.exists():
    cut = Image.open(P / "dodo_cutout.png")
    box = cut.getchannel("A").getbbox()
    sheet = Image.new("RGBA", (1024, 1024), (225, 222, 215, 255))
    dodo = cut.crop(box)
    dodo.thumbnail((820, 820))
    sheet.alpha_composite(dodo, ((1024 - dodo.width) // 2, (1024 - dodo.height) // 2))
    sheet.convert("RGB").save(ref)

SCENES = {
    "street": "The dodo bird from the reference image, same design, colours and proportions, stands confused on the "
              "pavement of a busy street in modern Port Louis, Mauritius, early morning: colourful shopfronts, a bus "
              "passing, people walking, the green Moka mountains behind the city. Wide shot, the dodo in the left third.",
    "park": "Many dodo birds of exactly the same design as the reference image stand behind a thick glass wall in a "
            "tourist attraction called Dodo Park; tourists hold up phones and take flash photos; harsh fluorescent "
            "light, a faded painted mural of a forest on the enclosure's back wall. Wide shot.",
}
for name, prompt in SCENES.items():
    out = OUT / f"{name}.png"
    if not out.exists():
        _, used = keyframes.generate(f"{STYLE} {prompt}", out, refs=[ref])
        print(f"{name} prompt used: {used}")

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "same_character": {"type": "boolean"},
        "score": {"type": "integer", "description": "0-10, how closely the dodo matches the reference"},
        "differences": {"type": "array", "items": {"type": "string"}},
        "style_match": {"type": "boolean", "description": "same painting style as the reference"},
    },
    "required": ["same_character", "score", "differences", "style_match"],
}
for name in SCENES:
    verdict = meta.chat("muse-spark-1.3", [
        {"role": "system", "content": "You are a continuity supervisor for an animated film. Compare the dodo "
                                      "character in the scene with the reference sheet. Judge design only: body "
                                      "shape, beak, colours, markings, eyes, tail, proportions. Ignore pose, "
                                      "lighting and size in frame."},
        {"role": "user", "content": [
            {"type": "text", "text": "Reference sheet:"},
            {"type": "image_url", "image_url": {"url": str(ref)}},
            {"type": "text", "text": f"Scene '{name}':"},
            {"type": "image_url", "image_url": {"url": str(OUT / f'{name}.png')}},
        ]},
    ], schema=SCHEMA, max_tokens=6000)
    print(name, json.dumps(verdict, indent=1))
print(f"spent ${meta.spent():.3f}")
