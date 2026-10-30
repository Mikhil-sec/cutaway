"""Find which layer corrupts bird_1 in s15: render one still with growing subsets of the layers."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "films" / "dodo" / "shots" / "s15_many_behind_glass"
OUT = ROOT / "renders" / "isolate"
spec = json.loads((D / "spec_960.json").read_text())
layers = {l["name"]: l for l in spec["layers"]}
cases = {  # bird_0 is the focus target, so every case keeps it
    "e_plate_bird0_bird1": ["plate", "bird_0", "bird_1"],
    "f_plus_ground": ["plate", "ground", "bird_0", "bird_1"],
}
for name, keep in cases.items():
    s = dict(spec, layers=[layers[k] for k in keep])
    if name != "d_all_layers_no_fx":
        s.update(fog=[], effects=[], shadows=[])
    else:
        s.update(fog=[], effects=[])
    path = OUT / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(s))
    subprocess.run([r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe", "-b", "--factory-startup",
                    "-P", str(ROOT / "cutaway" / "blender_shot.py"), "--", str(path), str(OUT / name),
                    "--stills", "84"], capture_output=True, text=True, check=True)
    print("rendered", name)
