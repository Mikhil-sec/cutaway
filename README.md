# Cutaway

**An AI film crew that builds cinematic short films instead of generating them.**

Video-generation models are expensive and drift between shots. Cutaway works like a 2.5D animation studio:

1. **Muse Spark** breaks a story into a shot list.
2. **Muse Image** paints each shot's keyframe (about $0.01 a still).
3. **SAM 3.1** cuts every keyframe into depth layers: background, ground, characters and foreground.
4. **Blender** stages the layers in 3D and films them with real camera moves, parallax and depth of field.
5. **Muse Wonder** watches the rendered cut and gives director's notes, and the agent re-renders the shots that fail.

Every prompt, model call and cost is logged, so each film comes with its own AI-disclosure record.

Built for the Meta Global AI Developer Hackathon (Oct 27 – Nov 4, 2026). All code in this repository was written during the hackathon.

## Status

Day-1 proof works: one Muse Image still → SAM 3.1 layers (dodo, rock, foreground ferns, clean background plate) → a 5-second parallax camera move rendered in Blender, for $0.10 of API calls.

## Setup

- Python 3.12+, Blender 5.x, ffmpeg
- `python -m venv .venv` then `.venv/Scripts/python -m pip install -r requirements.txt`
- Copy `.env.example` to `.env` and add your Meta Model API key. `cutaway/meta.py` stops all calls at a hard budget cap (default $120).

## Layout

- `cutaway/meta.py`: Meta Model API client (Muse Image, SAM 3.1) with a spend cap and a generation log
- `cutaway/blender_shot.py`: renders one 2.5D shot from a JSON shot spec, headless
- `experiments/`: the day-1 proof scripts

## License

MIT
