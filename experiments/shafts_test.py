"""Render three stills of the proof scene with light shafts added, to check the effect."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "renders" / "proof"
spec = json.loads((P / "shot3.json").read_text())
spec["effects"] = [{"type": "shafts", "depth": 15, "opacity": 0.32},
                   {"type": "motes", "depth": 8, "opacity": 0.55, "scale": 20}]
spec["fog"] = []
(P / "shot_shafts.json").write_text(json.dumps(spec))
subprocess.run([r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe", "-b", "--factory-startup", "-P",
                str(ROOT / "cutaway" / "blender_shot.py"), "--", str(P / "shot_shafts.json"), str(P / "stills_shafts"),
                "--stills", "1,72,144"], capture_output=True, text=True, check=True)
print("ok")
