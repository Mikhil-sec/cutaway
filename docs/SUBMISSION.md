# Cutaway: hackathon submission

**Track:** Indie Developer · **Problem statement:** Build for Your World

## One-liner

An AI film crew for a 2-minute animated short: Meta's Muse models plan, paint, direct and critique, and video models do the camera work under their supervision.

## What it is

I live in Mauritius and I'm entering a 90–180 second film in the national short film competition's AI category, on the theme "What If the Dodo Returns?". On their own, AI video models give you a few seconds per prompt, a different character every shot, and streets that melt halfway through. A 2-minute story needs a director: someone who plans every shot, checks every take and asks for it again.

Cutaway is that director. Muse Spark turns the story into a shot list. Muse Image paints each keyframe from the dodo's character sheet and real photographs of Port Louis, and Muse Spark checks every painting against the character sheet. Muse Spark then writes a motion plan for the whole film, thinking across cuts: what each shot ends on, how it leads into the next, and which transition joins them. A video model (Wan 3.0, with Kling 2.6 as the fallback) animates each keyframe. Muse Spark watches every take as video and scores it against the shot's intent and the painted frame. When a take invents scenery or loses the bird, Muse Spark rewrites the prompt and asks for another. After two failures on one model it switches to the other. Finally Muse Wonder watches the whole film and gives editor's notes.

The result is a 139-second film at 1080p, with a consistent dodo in real Mauritian places. 19 of its 21 shots were rated 7/10 or better by the reviewer. It comes with the AI-disclosure report the competition requires, because every prompt, take, review and cost is logged.

## How it uses Meta's models

- **Muse Spark 1.3:**
  - the shot list, inside a strict JSON schema;
  - continuity checks on every keyframe against the character sheet (image input);
  - the motion plan, written for flow across cuts;
  - **watching every video take (video input)**, scoring it, listing its problems and rewriting the prompt for the retake;
  - rewording prompts the content filter refuses.
- **Muse Image:**
  - keyframes conditioned on a character sheet and reference photos of real places;
  - repainting a shot from the previous shot's keyframe, so that consecutive shots share one place and one light.
- **Muse Wonder:** **watching the whole film (video input)** against its shot timeline and story brief, with a score, strengths, weaknesses and the cheapest fix for each problem shot.
- **Muse Voice Transcribe:** the director's spoken notes, with keyword biasing for Mauritian place names.
- **SAM 3.1:** depth layers for the earlier 2.5D Blender renderer, which is still in the repo as a zero-cost fallback.

## What was built during the hackathon

Everything in the repository, starting from an empty folder on Oct 30, 2026. The commit history shows the progression:
1. A 2.5D Blender pipeline: layered parallax, puppet bends and review loops.
2. The director agent, sound and the disclosure report.
3. The switch to supervised image-to-video when that pipeline proved too static to tell the story.

## Engineering highlights

- **The models supervise each other's work.** A take is accepted only when Muse Spark, watching it, scores it 7/10 or better. Rejected takes are kept, so every decision can be audited.
- **A hard spend cap on the user's own money.** Each clip's worst-case cost is reserved before it is sent, and the ledger is reconciled with fal's real billing after every clip. That mattered, because the list price was half the billed price.
  - Result: $32 of video against a $45 cap.
  - First takes for every shot are funded before any retake.
- **A paid request is never abandoned.** The request ID is saved before waiting. When the laptop hibernated mid-clip, the next run collected the clip instead of paying for it again.
- **Free 1080p.** The 720p takes are upscaled on the laptop with Real-ESRGAN's anime video model. Native 1080p would have doubled the video bill.

## Links

- Code: https://github.com/Mikhil-sec/cutaway
- Demo video: (to add)
