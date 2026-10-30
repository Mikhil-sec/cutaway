"""Can Muse Wonder watch a rendered shot? Send the 6 s proof clip at 2 fps and ask for director's notes."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import meta  # noqa: E402

clip = meta.ROOT / "renders" / "proof" / "proof2_shot.mp4"
schema = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "what_happens": {"type": "string"},
        "notes": {"type": "array", "items": {"type": "string"}},
        "looks_like_film": {"type": "integer", "description": "0-10"},
    },
    "required": ["what_happens", "notes", "looks_like_film"],
}
for model in sys.argv[1:] or ["muse-wonder-1.0"]:
    try:
        r = meta.chat(model, [
            {"role": "system", "content": "You are a film director reviewing a rendered shot from a 2.5D animated "
                                          "short made from a painted still cut into depth layers."},
            {"role": "user", "content": [
                {"type": "text", "text": "Watch this shot. Describe what happens, then give specific director's "
                                         "notes on camera, motion, timing and anything that breaks the illusion "
                                         "of a real film."},
                {"type": "video_url", "video_url": {"url": str(clip), "fps": 2}},
            ]},
        ], schema=schema, max_tokens=8000, reasoning_effort="low")
        print(model, json.dumps(r, indent=1))
    except Exception as e:
        print(model, "FAILED:", str(e)[:600])
print(f"spent ${meta.spent():.3f}")
