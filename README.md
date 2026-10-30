# Cutaway

**An AI film crew that builds cinematic short films instead of generating them.**

Video-generation models are expensive, cap out at a few seconds, and drift: the main character changes between shots. Cutaway works the way a 2.5D animation studio does. It paints each shot as a still, cuts the still into depth layers, and films the layers with a real virtual camera in Blender. Characters stay on-model for the whole film, every shot is as long as the story needs, and a 150-second film costs a few dollars of API calls.

It was built to make an entry for Mauritius's National Short Film Competition 2026 (AI category, theme "What If the Dodo Returns?"): a creator on a small island, with a laptop and no budget, telling a story about their own place.

Built for the Meta Global AI Developer Hackathon (Oct 27 – Nov 4, 2026), track **Build for Your World**. All code in this repository was written during the hackathon.

## How it works

```
story.md ──► plan ──► keyframes ──► layers ──► specs ──► render ──► review ──► cut ──► critique ──► sound
            Muse      Muse Image    SAM 3.1    camera     Blender    Muse      ffmpeg   Muse        Muse Spark
            Spark     + Muse Spark  + Muse     fitting    (Eevee)    Spark              Wonder      cue sheet
                      continuity    Image                            watches            watches
                      check         clean plate                      each shot          the cut
                                    ▲                                   │                 │
                                    └──────── fixes applied, shot re-made ◄───────────────┘
```

1. **Plan (Muse Spark).** The story becomes a shot list: 18–26 shots, each with a keyframe description, a named camera move and intensity, a rack focus, the character's action, an atmosphere, a transition and sound notes. The model can only choose from what the renderer can actually do: every field is constrained by a strict JSON schema.
2. **Keyframes (Muse Image + Muse Spark).** Each still is painted with the character's reference sheet and reference photographs of the real place (Port Louis, Mauritius). Muse Spark then acts as continuity supervisor: it compares the frame with the sheet and the shot's description, and failures are repainted with its notes. When the content filter refuses a prompt, Muse Spark rewords it and the agent retries.
3. **Layers (SAM 3.1 + Muse Image).** SAM cuts out every character, its head, the ground it stands on and the foreground. Muse Image paints a clean plate with the characters removed, and SAM checks that they are really gone. Each character becomes a bendable puppet: one mesh with a weight map, so the neck curves instead of hinging.
4. **Specs (code).** Muse Spark chose "push in, strong, rack focus from foreground to subject". Code turns that into an exact camera path, then shifts, pulls back or scales the move until the character stays in frame and the camera never sees past the painting's edge.
5. **Render (Blender).** Image layers at their depths, a moving camera with depth of field and handheld shake, puppet bends with overshoot and settle, contact shadows, wind in foreground plants, drifting fog, motes in the light and camera flashes.
6. **Review (Muse Spark, video input).** The agent watches each rendered shot next to its intent, scores it, and picks changes from the same menu (move, intensity, action, atmosphere, length, or repaint). It applies them once and re-renders.
7. **Critique (Muse Wonder, video input).** Muse Wonder watches the whole assembled cut against the shot timeline and gives editor's notes per shot, which are applied the same way.
8. **Director's voice notes (Muse Voice Transcribe).** The human director speaks a note ("the forest should linger, the reveal needs more flashes"). It is transcribed with the film's place names as keyword bias, and Muse Spark turns it into concrete shot changes.
9. **Sound and disclosure.** Muse Spark writes a sound cue sheet; code mixes licensed and synthesized ambience to the cut's exact timeline. Every model call, prompt, check and revision is logged, and `disclosure` writes the AI-use report the competition requires.

## Meta models used

| Model | Job in Cutaway |
|---|---|
| `muse-spark-1.3` | Shot planning, keyframe continuity checks, prompt rewording after filter refusals, SAM phrase alternatives, per-shot video review, voice-note interpretation, sound cue sheet |
| `muse-image-1.0` | Keyframes conditioned on character sheets and place photos; clean plates |
| `sam-3.1` | Characters, heads, ground and foreground as layers; checking clean plates |
| `muse-wonder-1.0` | Watching the full cut and giving shot-level editor's notes |
| `muse-voice-transcribe-1.0` | The director's spoken notes, with keyword biasing |

## Design choices

- **The model decides, the code does the geometry.** Muse Spark never writes coordinates. It chooses from a vocabulary, and code computes paths, checks frame edges and framing, and decides what gets re-made. Shot plans are always valid and renderable.
- **Check everything that can be checked.** Continuity against the character sheet, clean plates re-segmented, camera paths sampled against every edge, rendered shots watched by a second model.
- **Hard spend cap.** Meta's API has no hard cap, so `cutaway/meta.py` reserves each call's worst-case cost before sending it and refuses anything past the budget.
- **Resumable.** Every stage is idempotent and each shot keeps its own state file, so a crash, a budget stop or a change to one shot only redoes what depends on it.

## Usage

Requirements: Python 3.12+, Blender 5.x, ffmpeg, a Meta Model API key.

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
copy .env.example .env          # add MODEL_API_KEY
```

A film is a folder with `story.md` and `refs.json` (character sheets and place photos; see `films/dodo/`).

```
python -m cutaway.director films/dodo plan          # shot list
python -m cutaway.director films/dodo show          # read it
python -m cutaway.director films/dodo keyframes     # paint + continuity check
python -m cutaway.director films/dodo storyboard    # contact sheet of keyframes
python -m cutaway.director films/dodo produce       # layers, render, review, re-render
python -m cutaway.director films/dodo critique      # Muse Wonder watches the cut; fixes applied
python -m cutaway.director films/dodo notes --audio note.m4a   # director's voice notes
python -m cutaway.director films/dodo cut           # assemble with transitions and end card
python -m cutaway.director films/dodo sound         # cue sheet, mix, mux
python -m cutaway.director films/dodo disclosure    # AI-use report and generation records
python -m cutaway.director films/dodo exploded --shots s07_waterfront_pouce   # making-of layer view
```

Add `--shots id1,id2` to work on some shots, `--preview` to render three stills per shot, and `--final` for 1920×1080.

## Layout

- `cutaway/director.py`: the agent and its stages
- `cutaway/meta.py`: Meta Model API client (chat with video, images, SAM, transcription) with the spend cap and generation log
- `cutaway/keyframes.py`: keyframes that recover from content-filter refusals
- `cutaway/camera.py`: camera vocabulary, edge and framing checks, move fitting
- `cutaway/puppet.py`: bendable characters: weight maps, pivots, motion presets
- `cutaway/blender_shot.py`: headless Blender renderer for a JSON shot spec
- `cutaway/edit.py`, `cutaway/sound.py`: assembly, end cards, sound mixing
- `experiments/`: the proofs that led here

## Credits and licence

Code: MIT. Third-party photos, sounds and fonts are listed with their licences in [CREDITS.md](CREDITS.md).
