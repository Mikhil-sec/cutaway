# Cutaway: notes for Claude

Read `docs/PROGRESS.md` first. It holds the current status, the decisions made so far, open questions and next steps. Update it at the end of every work session, or when the context gets heavy, so a fresh session can pick up from it.

## What this is

Cutaway is an AI film-making agent. It is the user's entry for two competitions:
- **Meta Global AI Developer Hackathon**, Indie track, theme "Build for Your World". Due **2026-11-04 9:00 PM ET**. Needs a public repo, a 3-minute demo video and Meta models.
- **MFDC National Short Film Competition 2026, Category B (AI)**, theme "What If the Dodo Returns?". Due **2026-11-13 4:00 PM Mauritius time**. The film must run 90–180 s, AI use must be disclosed, and everything must be licensed. The rules are summarised in `docs/MFDC_RULES.md`.

The film is `films/dodo/`, and its story is in `films/dodo/story.md`. The story idea is the user's.

## Rules

- **Secrets:** API keys live only in `.env` (`MODEL_API_KEY`, and `FAL_KEY` if added). Never print, log or commit them. Never put the user's email in public material.
- **Privacy:** `refs/` (place photos, including a friend's private photos) stays out of git.
- **Spend:** every paid call goes through the reserve-then-settle hard cap in `cutaway/meta.py` (ledger in `ledger.json`). Any new paid API needs the same kind of cap.
- **Style:** muted cinematic anime with painterly backgrounds. Wordless; no Kreol dialogue. The user supplies the core ideas.
- **Motion:** rigid part rotation looks doll-like. Deform smoothly and keep it subtle.
- **Previews:** the user often reviews on a phone, so send preview images and clips with SendUserFile.
- **Processes:** close all background processes (Blender, ffmpeg, python) when work is done so the laptop can sleep. The director keeps the machine awake only while a stage runs.
- **Commits:** commit and push only when asked. The repo is public: https://github.com/Mikhil-sec/cutaway

## Running

- Python: `.venv/Scripts/python`. Blender 5.x and ffmpeg are on PATH.
- Run a stage: `.venv/Scripts/python -m cutaway.director films/dodo <stage> [--shots s03,s12] [--final] [--preview] [--force] [--audio file]`
- Stages: plan, show, keyframes, layers, specs, render, review, produce, cut, sound, critique, notes, disclosure, storyboard, exploded.
- Making-of video: `.venv/Scripts/python experiments/build_makingof.py`
- Long renders run in the background with logs in `films/dodo/*.log`. A 1920 render of the whole film takes hours.
