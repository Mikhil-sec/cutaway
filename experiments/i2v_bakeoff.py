"""Bake-off: the same three keyframes through each video model, for the user to judge by eye.

Stage cap: this script may add at most STAGE_USD to the fal ledger.
Outputs go to films/dodo/i2v/bakeoff/<shot>__<model>.mp4, plus one comparison
clip per shot (models stacked, labelled A/B/C) for viewing on a phone.
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from cutaway import i2v, meta  # noqa: E402

STAGE_USD = 5.00
FILM = ROOT / "films" / "dodo"
OUT = FILM / "i2v" / "bakeoff"
MODELS = ["h3", "kling26", "wan30"]  # shown as A, B, C
SHOTS = {
    "s03_wake_city": "The dodo wakes on the pavement: it blinks, shakes its head, then turns its head left and "
                     "right in confusion and takes one hesitant step back. Buses crawl in the distance, people "
                     "walk past on the sidewalks, dust drifts in the harsh morning light. Slow camera pull-out.",
    "s12_crowd_wide": "The ring of tourists slowly tightens around the dodo, raising phones and pointing. The dodo "
                      "lowers its head and turns nervously in place. The umbrellas overhead sway gently in the "
                      "breeze. The camera slowly cranes down.",
    "s19_press_mural": "The dodo gently presses its beak and cheek against the painted forest on the mural and "
                       "slowly closes its eyes; its chest rises and falls with one slow breath and its feathers "
                       "ruffle softly. Dust motes drift in the warm shaft of light. Very slow push-in.",
}


def run(shot, model):
    out = OUT / f"{shot}__{model}.mp4"
    if out.exists():
        return out
    meta.CONTEXT.update(film="dodo", stage="i2v_bakeoff")
    try:
        i2v.generate(model, FILM / "shots" / shot / "keyframe.png", SHOTS[shot], out, seconds=5, limit=LIMIT)
        print(f"done {out.name}  (fal ledger ${i2v.spent():.2f})", flush=True)
        return out
    except Exception as e:  # one model failing must not stop the others
        print(f"FAILED {shot} {model}: {e}", flush=True)


def compare(shot, clips):
    """Stack the takes vertically at 960 wide with A/B/C labels: easy to judge on a phone."""
    font = "C\\:/Windows/Fonts/arialbd.ttf"
    inputs, chains = [], []
    for i, (label, clip) in enumerate(clips):
        inputs += ["-i", str(clip)]
        chains.append(f"[{i}:v]fps=24,scale=960:540:force_original_aspect_ratio=decrease,"
                      f"pad=960:540:(ow-iw)/2:(oh-ih)/2,setsar=1,"
                      f"drawtext=fontfile='{font}':text='{label}':x=16:y=12:fontsize=40:"
                      f"fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=8[v{i}]")
    graph = ";".join(chains) + ";" + "".join(f"[v{i}]" for i in range(len(clips))) + \
        f"vstack=inputs={len(clips)}[out]"
    dest = OUT / f"compare_{shot}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph, "-map", "[out]",
                    "-an", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-shortest", str(dest)],
                   check=True)
    return dest


if __name__ == "__main__":
    LIMIT = i2v.spent() + STAGE_USD
    worst = sum(i2v.quote(m, 5)[1] for m in MODELS) * len(SHOTS)
    listed = sum(i2v.quote(m, 5)[0] for m in MODELS) * len(SHOTS)
    print(f"fal ledger ${i2v.spent():.2f}; this stage: list ${listed:.2f}, worst case ${worst:.2f}, "
          f"stage cap ${STAGE_USD:.2f}, total cap ${i2v.BUDGET:.2f}", flush=True)
    jobs = [(s, m) for s in SHOTS for m in MODELS]
    with ThreadPoolExecutor(2) as pool:  # fal's starting concurrency limit is 2
        results = dict(zip(jobs, pool.map(lambda j: run(*j), jobs)))
    for shot in SHOTS:
        clips = [(chr(65 + i), results[(shot, m)]) for i, m in enumerate(MODELS) if results[(shot, m)]]
        if clips:
            print("compare", compare(shot, clips), flush=True)
    print(f"fal ledger now ${i2v.spent():.2f}", flush=True)
