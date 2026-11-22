# FLUX 3 Max playbook: bootcamp, 21 Nov 2026

For the China-Mauritius AI Storytelling and AI Video Clip Competition: a 3–4 minute film. All AI generation happens in one 80-minute session (10:40–12:00); editing afterwards is in non-AI software. Sources are listed at the end. "BFL" means Black Forest Labs' official docs; "fal" means fal's own guide.

## The endpoints (fal, commercial licence)

| Endpoint | Use | Key inputs |
|---|---|---|
| `blackforestlabs/flux-3-max/image-to-video` | **Default.** One Muse Image keyframe animated | `image_url`, `prompt`, optional `end_image_url` |
| `blackforestlabs/flux-3-max/keyframes-to-video` | Shots that must hit 2–10 set moments | `keyframes: [{image_url, frame_index}]`, `prompt` |
| `blackforestlabs/flux-3-max/text-to-video` | Not for story shots: nothing anchors the character | — |

**Settings for every call:**
- `duration` 5–20 s, always set explicitly.
- `resolution: 720p`. Higher resolutions are only upscaled from 720p.
- `aspect_ratio: auto`, which follows the keyframe. Paint every keyframe 16:9.
- `generate_audio`: on (the default) or off, decided per shot (see Sound).
- `reasoning_level`: `high` (the default) expands the prompt and runs slower; `low` follows it more literally. For exact timings, test both on one shot and keep one setting for the whole film.
- `seed`: when a take is nearly right, keep it and change one thing.

**Price:** $0.085/s at 720p until 23 Nov 00:00 UTC, then $0.17/s. One take of a whole 240 s film costs about $20.
**Speed:** BFL quotes about 12 s for a 10 s clip. We measure the real figure through fal on the first test.

## The workflow (the dodo lessons, applied)

1. **Muse Image first, and plenty of it.** The keyframe fixes the character, place, light and style; the video model only has to move them. A repaint costs $0.01, a 10 s take $0.85.
2. **Muse Spark checks every keyframe against the character sheet** before any video money is spent. It's free on the Meta credit, and it caught the wrong beak, the wrong colours and wrong positions on the dodo film.
3. **Shots that cut together share place and light.** Paint the next shot's keyframe with the previous shot's keyframe as a reference. Better still, use one shot's last frame as the next shot's `image_url`, or as the previous shot's `end_image_url`.
4. **Real reference photos make it local.** Without them, Port Louis came out looking Indonesian. Use them for Chinatown, the pagoda, the harbour.
5. **Action is allowed: anchor it, and cut it short.** Wan invented scenery on big camera moves; FLUX 3 Max handles fast motion far better. For action shots:
   - **Clips of 5–8 s.** Action films cut fast anyway, and short clips drift less.
   - **One dominant move per clip, with a clear direction:** whip pan, fast tracking shot, crash zoom, FPV drone dive, handheld chase.
   - **Pin the landing with an end frame** painted by Muse Image, so the move ends where the story needs it.
   - **Fast camera or fiddly detail, not both at once.** Fast camera with hand close-ups, or a running crowd plus kung-fu hands, breaks.
   - **Calm shots between the action** make the action hit harder.
6. **Retake by changing one thing:** the seed, the prompt's motion line, or the keyframe. Not everything at once.

## Writing the prompt (image-to-video)

BFL: "The source image sets the first frame; the prompt drives the motion." fal: spend "almost no words on appearance and almost all of them on motion".

**Order** (fal's, best for image-to-video):
1. **Camera:** one framing term and one move, with its speed.
2. **Main action:** ordered beats joined by "then" and "as".
3. **Secondary motion** in the environment: lanterns swaying, steam, crowds, water.
4. **Light or time change**, if any.
5. **What stays still:** "The camera holds." "Nothing else moves."
6. **Sound line.**

**Rules:**
- **Refer to things already in the frame with "the"** ("the old man", "the red lantern"). Don't describe costumes, faces, palette or setting again; the image carries them, and re-describing them can fight the image.
- **One framing, one move.** BFL: "Start with one framing term, one movement term, and one clear subject action." Two moves only if each has its own verb. A stack like "low aerial handheld orbit push-in" doesn't work.
- **Camera moves that work:** slow push-in, locked-off, slow pan left/right, tilt up, dolly, pull back, low tracking shot, follow shot, crane, orbit, long lens, top-down. Avoid fast moves combined with complex limb action (running, dancing hands).
- **Concrete nouns and verbs a camera could see.** Vague adjectives ("beautiful", "emotional") leave the result to chance.
- **No negative-prompt field exists.** Write exclusions inline: "No on-screen text, no subtitles." "No other people enter." "One continuous shot" (stops a cut to a new angle inside the clip).
- **Length:** the fal examples run 60–100 words. Start short, then add only the details that matter.

**Long clips (15–20 s) as timed beats:** BFL suggests 2–3 beats per 5 s. For 15–20 s, aim for 3–5 timed beats and end on a 1–2 s hold, which gives the editor a clean cut point.

```
Core summary: one line for the whole clip.
Subject: [identity tag matching the keyframe]
0.0-5.0s: Slow push-in. The grandmother lifts the lid of the steamer; steam rolls up into the lamplight.
5.0-11.0s: She turns to the girl and holds out a dumpling on the chopsticks. The girl hesitates, then takes it.
11.0-15.0s: The camera holds as both laugh; red lanterns sway gently in the doorway behind them.
Sound: steam hiss, chopsticks on porcelain, distant Port Louis street traffic, soft laughter. No music. No on-screen text.
```

**Start and end frames:** keep the two frames related (same subject, scene and camera setup); the wider the gap, the more unpredictable the result. State the change in words: "the street turns from dusk blue to lantern-lit night".

**Keyframes mode:** frames are at 24 fps, so second 3 is frame 72. A 15 s clip has `frame_index` up to 360. Order matters: the frames are read as a timeline. Keep the composition consistent "so the shot reads as one take". Name keyframes by shot, beat and time, e.g. `s07_K2_t06.0` → frame 144.

## Sound (generated in the same pass)

- Four layers (BFL): speech, ambience, effects, music. **Name each sound's source** ("rain on tin awnings", "a wok clanging") rather than mood words. For quiet scenes, name something concrete ("a ceiling fan ticking"), or "quiet room tone" may turn into static.
- **Dialogue:** put the exact words in quotes and name a visible speaker, or write "voiceover". Otherwise the quoted line may appear as on-screen text. Keep lines short; BFL aims to finish speech by about 8 s. Add "no on-screen text or subtitles". Voice: give the age, accent, setting and delivery, e.g. "elderly woman, Mauritian Creole accent, soft, close to the microphone, no announcer delivery".
- **Language: all speech is in English** (the rules require English audio with Chinese subtitles). Keep the lines few and short. The Chinese subtitles are added in the edit, never by FLUX, so every prompt keeps "no on-screen text or subtitles".
- **Music: one score for the whole film, not one per clip.** FLUX makes the sound effects and ambience (gunfire, engines, rain, crowds, a wok clanging); that's its strength, so keep it. Music generated inside each clip changes at every cut and buries those effects, so each clip's Sound line ends "No music". The score is made once:
  1. **ElevenLabs Music** (via fal), from a composition plan Muse Spark writes to the cut's timing, as on the dodo film: quiet sections, a build, hits on the action. Billed per started minute, about $2.40 for a 4-minute film. Made in session 1, since it's AI.
  2. **Fallback, free:** a licensed royalty-free track (for example, YouTube Audio Library) added in the edit. The schedule lists "Audio" under the non-AI editing session.
  - In the edit, the score sits under the clips' own sound, dipping for big effects and dialogue, then everything is levelled to one loudness.
  - If a clip still comes back with music, set `generate_audio: false` for it and rely on the score.

## Failures and fixes

| Symptom | Fix |
|---|---|
| Spoken line appears as on-screen text | Name a visible speaker or "voiceover"; add "no on-screen text or subtitles" |
| Voice sounds like an advert | Describe a concrete person and recording setup; "no announcer delivery" |
| Last word cut off | Shorten the line, or give the clip more seconds |
| Extra motion or new people appear | "Nothing else moves." "The camera holds." |
| Cuts to a new angle mid-clip | "One continuous shot." |
| Camera wanders or invents scenery | One framing and one move, slower; or lock the end frame |
| Character drifts off-model | Shorter clip, or add an end frame / keyframes painted by Muse Image |
| Request Moderated / Content Moderated | Reword (Muse Spark rewrote refused prompts on the dodo film) |

## Sources

- BFL: [video overview](https://docs.bfl.ai/guides/prompting_video_overview), [image-to-video](https://docs.bfl.ai/guides/prompting_video_image_to_video), [text-to-video](https://docs.bfl.ai/guides/prompting_video_text_to_video), [camera terms](https://docs.bfl.ai/guides/prompting_video_camera_terms), [audio](https://docs.bfl.ai/guides/prompting_video_audio), [FLUX 3 video](https://docs.bfl.ai/flux_3/flux3_video)
- fal: [FLUX 3 Max prompting guide](https://fal.ai/learn/tools/flux-3-max-prompting-guide); the endpoint schemas, read through fal's API on 2026-11-20
- Our own lessons: [LESSONS.md](LESSONS.md)
