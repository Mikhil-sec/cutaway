# Cutaway: hackathon submission

**Track:** Indie Developer · **Problem statement:** Build for Your World

## One-liner

An AI film crew for a 2-minute animated short. Meta's Muse models plan, paint, direct, design the sound and critique; video and audio models do the camera and sound work under their supervision.

## What it is

I live in Mauritius, and I'm entering a 90–180 second film in the national short film competition's AI category, on the theme "What If the Dodo Returns?". AI video models alone give you a few seconds per prompt, a different character every shot, and streets that melt halfway through. A 2-minute story needs a director: someone who plans every shot, checks every take, asks for it again, and decides what the film should sound like.

Cutaway is that director. The pipeline runs in five stages:

1. **Shot list.** Muse Spark turns the story into a shot list.
2. **Keyframes.** Muse Image paints each keyframe from the dodo's character sheet and from real photographs of Port Louis. Muse Spark checks every painting against the character sheet.
3. **Motion.** Muse Spark writes a motion plan for the whole film, thinking across cuts: what each shot ends on and how it leads into the next. A video model animates each keyframe (Wan 3.0, with Kling 2.6 as the fallback). Muse Spark watches every take as video and scores it. When a take invents scenery or loses the bird, it rewrites the prompt and asks again. After two failures on one model, it switches to the other.
4. **Sound.** Muse Spark designs the soundtrack:
   - a score in sections, timed to the cut;
   - effects for each shot;
   - the dodo's voice, modelled on its closest living relative, the Nicobar pigeon.

   ElevenLabs Music, MMAudio and ElevenLabs SFX perform it, and Cutaway mixes it to broadcast loudness.
5. **Critique.** Muse Wonder watches and listens to the whole film and gives editor's notes. The notes became retakes, repaints and trims over seven versions, and every version is kept.

**The result:**
- A 124-second film at 1080p with a full soundtrack, a consistent dodo, and real Mauritian places.
- Muse Wonder rates it 7/10 ("a clear, moving wordless fable"), and friends who watched it found the ending moving.
- An AI-disclosure report, which the competition requires, generated from the logs, because every prompt, take, review and cost is recorded.

## Who it's for

Students and independent filmmakers in small countries, with local stories and no studio budget. Mauritius has a national film competition with an AI category, but turning a story idea into a coherent two-minute film with video models normally takes a great deal of manual prompting and checking, and it is easy to spend too much. Cutaway does that work under a hard spending cap: this film cost $44 in video and sound and about $6 in Meta model calls. Its record of every model call is exactly what a competition needs to judge responsible AI use.

## How it uses Meta's models

- **Muse Spark 1.3:**
  - the shot list, inside a strict JSON schema;
  - continuity checks on every keyframe against the character sheet (image input);
  - the motion plan, written for flow across cuts;
  - **watching every video take (video input)**, scoring it, listing its problems and rewriting the prompt for the retake;
  - **the sound design**: a composition plan for the score, an effects brief for each shot, and the dodo's calls with their timing;
  - rewording prompts the content filter refuses.
- **Muse Image:**
  - keyframes conditioned on a character sheet and reference photos of real places;
  - repainting a shot from the previous shot's keyframe, so that consecutive shots share one place and one light.
- **Muse Wonder:** **watching and hearing the whole film (video with audio)** against its shot timeline and story brief. It returns a score, strengths, weaknesses, notes on the sound, and the cheapest fix for each problem shot. It is run again after every revision.
- **Muse Voice Transcribe:** the director's spoken notes, with keyword biasing for Mauritian place names.
- **SAM 3.1:** depth layers for the earlier 2.5D Blender renderer, still in the repo as a zero-cost fallback.

## What was built during the hackathon

Everything in the repository, starting from an empty folder on Oct 30, 2026. The commit history shows the progression:
1. A 2.5D Blender pipeline with layered parallax, puppet bends and review loops.
2. The director agent and the disclosure report.
3. The switch to supervised image-to-video, when the Blender pipeline proved too static to tell the story.
4. Sound design and the critique loop with sound.

## Engineering highlights

- **The models supervise each other's work.**
  - A take is accepted only when Muse Spark, watching it, scores it 7/10 or better; 18 of the film's 21 shots are.
  - Rejected takes are kept, so every decision can be audited.
  - When the critic began contradicting itself, the loop stopped and the author chose the cut.
- **A hard spend cap on my own money.**
  - Every video or audio call reserves its worst-case cost before it is sent, and the ledger is reconciled with fal's real billing after each one. That mattered: the billed price turned out to be twice the list price.
  - First takes for every shot are funded before any retake.
  - Result: $44.21 against a $45 cap.
- **A paid request is never abandoned.** The request ID is saved before waiting. When the laptop hibernated mid-clip, the next run collected the clip instead of paying for it again.
- **Edits without re-rendering.** Trims and omitted shots live in the motion plan, and the score is re-conformed to the new timeline, so a critique note often costs nothing to act on.
- **Free 1080p.** The 720p takes are upscaled on the laptop with Real-ESRGAN's anime video model. Native 1080p would have doubled the video bill.

## Links

- Code: https://github.com/Mikhil-sec/cutaway
- Demo video: (to add)
