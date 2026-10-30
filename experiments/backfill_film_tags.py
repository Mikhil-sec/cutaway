"""One-off: stamp film="dodo" on generation-log entries made for the dodo film before log entries carried
a film tag. Starts at the planning call; leaves out the side experiments run in the same period."""
import json
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "generation_log.jsonl"
lines = LOG.read_text(encoding="utf-8").splitlines()
entries = [json.loads(line) for line in lines]
start = next(i for i, e in enumerate(entries)
             if e.get("kind") == "chat" and "You are the director of a short animated film" in json.dumps(e["prompt"]))


def experiment(e):
    blob = json.dumps(e, ensure_ascii=False)
    return ("scratchpad" in blob                                # test voice notes
            or "reviewing a rendered shot from a 2.5D animated short made from a painted still" in blob
            or "renders\\\\proof" in blob or "renders\\\\consistency" in blob)


tagged = 0
for e in entries[start:]:
    if "film" not in e and not experiment(e):
        e["film"] = "dodo"
        tagged += 1
LOG.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n", encoding="utf-8")
print(f"tagged {tagged} entries from #{start} of {len(entries)}")
