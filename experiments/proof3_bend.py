"""Proof 3: the proof dodo as a bendable puppet (no separate head layer), same camera as proof 2.

Renders --stills for a quick look; pass --full for the whole clip.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway import puppet  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "renders" / "proof"
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"

dodo = np.asarray(Image.open(P / "dodo_cutout.png").getchannel("A")) > 127
head = np.asarray(Image.open(P / "dodo_head.png").getchannel("A")) > 127
piv = puppet.build(dodo, head, P / "dodo_weights.npy")
facing = puppet.facing_from_mask(dodo, head)
anim = puppet.motion("look_around", 6.0, seed=3, facing=facing)
print("pivots", piv, "facing", facing)

shot = json.loads((P / "shot2.json").read_text())
shot["name"] = "proof3_dodo_bend"
shot["layers"] = [
    {"name": "plate", "image": str(P / "plate.png"), "depth": 40},
    {"name": "rock", "image": str(P / "rock_mid.png"), "depth": 12.2},
    {"name": "dodo", "image": str(P / "dodo_cutout.png"), "depth": 12.0,
     "puppet": {"weights": str(P / "dodo_weights.npy"), "pivot": piv["neck"], "feet": piv["feet"]}, "anim": anim},
    {"name": "ferns", "image": str(P / "ferns_fg.png"), "depth": 5},
]
for k in shot["camera"]["keys"]:
    if k.get("focus") == "dodo_body":
        k["focus"] = "dodo"
(P / "shot3.json").write_text(json.dumps(shot, indent=2))

args = [BLENDER, "-b", "--factory-startup", "-P", str(ROOT / "cutaway" / "blender_shot.py"), "--",
        str(P / "shot3.json")]
if "--full" in sys.argv:
    args.append(str(P / "frames3"))
else:
    args += [str(P / "stills3"), "--stills", "1,30,50,90"]
log = subprocess.run(args, capture_output=True, text=True)
print("\n".join(l for l in log.stdout.splitlines() if "edge" in l or "Error" in l or "Traceback" in l))
if log.returncode:
    print(log.stdout[-3000:], log.stderr[-3000:])
