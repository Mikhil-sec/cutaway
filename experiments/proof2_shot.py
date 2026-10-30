"""Proof 2, step 2: write a dramatic shot spec for the dodo scene.

The camera starts low with the ferns in focus, racks focus to the dodo while
craning in toward it; the dodo breathes and tilts its head; fog drifts between layers.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "renders" / "proof"
piv = json.loads((P / "pivots.json").read_text())

shot = {
    "name": "proof2_dodo_dramatic",
    "fps": 24,
    "seconds": 6,
    "resolution": [1280, 720],
    "image_size": [2048, 1152],
    "layers": [
        {"name": "plate", "image": str(P / "plate.png"), "depth": 40},
        {"name": "rock", "image": str(P / "rock_mid.png"), "depth": 12.2},
        {"name": "dodo_body", "image": str(P / "dodo_body.png"), "depth": 12.0, "pivot": piv["feet"],
         "anim": {"breathe": {"amp": 0.012, "period": 2.6}}},
        {"name": "dodo_head", "image": str(P / "dodo_head.png"), "depth": 11.98, "pivot": piv["neck"],
         "follow": "dodo_body",
         "anim": {"rot": [[0, 0], [1.8, 0], [2.3, 9], [3.5, 9], [4.1, -5], [6, -5]]}},
        {"name": "ferns", "image": str(P / "ferns_fg.png"), "depth": 5},
    ],
    "fog": [
        {"depth": 25, "opacity": 0.28, "speed": 0.06},
        {"depth": 8, "opacity": 0.07, "speed": 0.1},  # 0.18 veiled the whole close-up
    ],
    "camera": {
        "fstop": 2.0,
        "shake": {"deg": 0.15, "units": 0.01, "hz": 0.5},
        "keys": [
            {"t": 0.0, "pos": [0.3, 0.0, -0.35], "lens": 35, "focus": "ferns", "pitch": 2.5},
            {"t": 2.2, "pos": [1.0, 1.2, -0.1], "lens": 38, "focus": "dodo_body", "pitch": 1.0},
            {"t": 6.0, "pos": [2.0, 3.0, 0.2], "lens": 44, "focus": "dodo_body", "pitch": -0.5, "yaw": -2, "roll": -1.2},
        ],
    },
}
(P / "shot2.json").write_text(json.dumps(shot, indent=2))
print("wrote", P / "shot2.json")
