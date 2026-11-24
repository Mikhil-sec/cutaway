# Cutaway: notes for Claude

Read `docs/PROGRESS.md` first. It holds the current status, the decisions made so far, open questions and next steps. Update it at the end of every work session, or when the context gets heavy, so a fresh session can pick up from it.

## What this is

Cutaway is an AI film crew: Muse Spark plans, directs and reviews, Muse Image paints keyframes, an image-to-video model animates them, and ElevenLabs does the music and voices. The repo is public, and its README presents the films.

Finished films (don't change them without being asked):
- **The Dodo Came Back** (`films/dodo/`): MFDC National Short Film Competition 2026, submitted 16 Nov. Made with `cutaway/director.py` (Wan 3.0 and Kling 2.6). Show only its last 40 s in public until the MFDC rules on prior publication are checked.
- **55 Spring Festivals** (public folder `films/55_spring_festivals/`, working folder `films/bootcamp/`, which is gitignored and 3.6 GB): China-Mauritius AI video bootcamp, 21 Nov, made with teammates Seeya Awotar and Yorvan Rengasamy. Made with `cutaway/bootcamp.py` and FLUX 3 Max.

**A new film starts with the bootcamp pipeline.** See "Starting a new film" in `docs/PROGRESS.md`.

## Rules

- **Secrets:** API keys live only in `.env` (`MODEL_API_KEY`, `FAL_KEY`, `FAL_READONLY_KEY`). Never print, log or commit them. Never put the user's email in public material.
- **Privacy:** `refs/` (place photos, including a friend's private photos) stays out of git. Teammates' names and GitHub usernames may appear in public credits.
- **Spend:** every paid call goes through a reserve-then-settle hard cap: `cutaway/meta.py` for Meta, and `cutaway/i2v.py` for fal (one ledger and cap per fal account, in `PROFILES`). Any new paid API needs the same kind of cap. **Ask before every paid fal call, and agree the budget and whose money it is before a new film spends anything.**
- **Story and style:** the user supplies the core ideas and critiques every keyframe set and cut. Style is chosen per film (both films so far are hand-painted 2D anime). Everything in a clip must be alive and moving from the first frame, with varied camera angles.
- **Approval gates:** show the final keyframes (after Spark's review loop) before any video money is spent, and give rough cuts with shot IDs burned in so notes can name a shot.
- **Previews:** the user often reviews on a phone, so send preview images and clips with SendUserFile.
- **Processes:** close all background processes (Blender, ffmpeg, python) when work is done so the laptop can sleep.
- **Commits:** commit and push only when asked. Work on a branch, open a PR, and merge it when the user says so. The repo is public: https://github.com/Mikhil-sec/cutaway

## Running

- Python: `.venv/Scripts/python`. ffmpeg is on PATH; Blender 5.x is only needed for the old 2.5D pipeline.
- **Bootcamp pipeline** (new films): `.venv/Scripts/python -m cutaway.bootcamp <stage> [--shots s01,s05] [--force] [--yes]`. Stages: plan, sheets, keyframes, quote, video, review, cut, score, voice, mix, status, statement. The final edit is `python -m cutaway.bootcamp_final timeline|render`. The plan format is in the docstring of `bootcamp.py`; `docs/FLUX3_PLAYBOOK.md` covers prompting.
- **Director pipeline** (the dodo film): `.venv/Scripts/python -m cutaway.director films/dodo <stage>`. Stages: plan, show, keyframes, motion, i2v, upscale, cut --source i2v, score, critique, notes, disclosure, storyboard, plus the 2.5D ones (layers, specs, render, review, produce, exploded).
- Long runs go in the background with logs in the film folder.
- Read `docs/LESSONS.md` before changing the agent or writing prompts.
