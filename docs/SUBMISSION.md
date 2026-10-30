# Cutaway: hackathon submission

**Track:** Indie Developer · **Problem statement:** Build for Your World

## One-liner

An AI film crew that builds cinematic short films instead of generating them: Muse models plan, paint, cut, review and critique; Blender films it.

## What it is

I live in Mauritius and am entering a 90–180 second film in the national short film competition's AI category, with the theme "What If the Dodo Returns?". AI video models are expensive, last a few seconds per clip, and the main character changes from shot to shot. None of that works for a 150-second story on a student budget.

Cutaway takes a story and makes the film the way a 2.5D animation studio would. Muse Spark plans the shots. Muse Image paints each keyframe from a character sheet and real photographs of Port Louis. SAM 3.1 cuts every keyframe into depth layers and turns the characters into bendable puppets. Blender films the layers with real camera moves, rack focus, wind, fog and flashes. Then the agent watches its own work: Muse Spark reviews every rendered shot and Muse Wonder critiques the whole cut, and their fixes are applied and re-rendered. The director can also give spoken notes, which Muse Voice Transcribe turns into text and Muse Spark turns into shot changes.

The result is a 150-second film with a consistent character in real Mauritian places, made for a few dollars of API calls on a laptop with no dedicated GPU. It comes with the AI-disclosure report the competition requires: every prompt, check and revision is logged.

## How it uses Meta's models

- **Muse Spark 1.3:** shot planning inside a strict JSON schema of what the renderer can do; continuity supervision of every keyframe against the character sheet (image input); rewording prompts refused by the content filter; alternative phrasings when SAM finds nothing; **watching each rendered shot (video input)** and choosing fixes; interpreting the director's voice notes; the sound cue sheet.
- **Muse Image:** keyframes conditioned on a character sheet plus reference photos of real places; clean plates with the characters removed.
- **SAM 3.1:** characters, heads (for the puppet weight maps), ground and foreground as separate layers; verifying clean plates.
- **Muse Wonder:** **watching the full cut (video input)** against a shot timeline and giving shot-level editor's notes that the agent applies.
- **Muse Voice Transcribe:** the director's spoken notes, with keyword biasing for Mauritian place names.

## What was built during the hackathon

Everything in the repository, starting from an empty folder on Oct 30, 2026. The commit history shows the progression: a layered-parallax proof, film-style camera work, smooth puppet bends, the director agent, the review loops, sound and disclosure.

## Engineering highlights

- The model chooses, the code computes: camera paths are fitted so the character stays in frame and the camera never sees past any painted edge.
- Characters are single meshes with SAM-derived weight maps, so heads bend through the neck instead of hinging.
- Depth of field uses dithered transparency so each layer blurs by its own distance.
- A hard spend cap (reserve worst-case cost before each call), resumable stages and per-shot state.

## Links

- Code: https://github.com/Mikhil-sec/cutaway
- Demo video: (to add)
