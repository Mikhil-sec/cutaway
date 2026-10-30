"""Find which wording trips Muse Image's content filter for the street scene."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import meta  # noqa: E402

OUT = meta.ROOT / "renders" / "consistency"
ref = OUT / "dodo_ref.png"
STYLE = "Muted cinematic anime film still, painterly backgrounds, soft natural light, 2D hand-painted look."
VARIANTS = {
    "street_a": "The dodo bird from the reference image stands on the pavement of a street in Port Louis, Mauritius, "
                "early morning, colourful shopfronts, green mountains behind the city. Wide shot.",
    "street_b": "The dodo bird from the reference image stands on the pavement of a busy street in a tropical island "
                "capital, early morning: colourful shopfronts, a bus passing, pedestrians, green mountains behind. "
                "Wide shot, the dodo in the left third.",
}
for name, prompt in VARIANTS.items():
    try:
        meta.image(f"{STYLE} {prompt}", OUT / f"{name}.png", refs=[ref])
        print(name, "ok")
    except RuntimeError as e:
        print(name, "refused:", str(e)[:120])
