# Bootcamp: China-Mauritius AI Video Clip Competition 2026 (stage 2)

> **Done (21 Nov 2026).** *55 Spring Festivals* was submitted as `films/bootcamp/backup_v1/55_Spring_Festivals_RNA_team.mp4` (3:58.8) with the AI Creation Statement. fal spend: $32.72 of $60. The public copy is in `films/55_spring_festivals/`. What follows is the record from before and during the day; lessons are in [LESSONS.md](LESSONS.md).

Read this first in a new session about the bootcamp. It holds the rules, the decisions made so far, the budget and the plan. The dodo film (MFDC, submitted 16 Nov) is a separate project: see `PROGRESS.md`.

## The competition

- **Stage 2** of the China-Mauritius AI Comic Storytelling and AI Video Clip Competition. The team (3 university students) qualified with an AI comic in stage 1. Rules: `rules comic storytelling and templateNew.pdf` (user's copy).
- **Saturday 21 November 2026**, Huawei House, Ebene. 6 Chinese and 6 Mauritian university teams.
- **Deliverables:** a **3–4 minute AI-generated video**, plus an 8-minute slot: 4 min screening, 1.5 min concept and process, 1.5 min jury Q&A.
- **Themes** (the team's topic is confirmed on the day, probably from its stage-1 comic):
  1. Spring Festival stories shared by China and Mauritius.
  2. Touching stories of the ordinary people of China and Mauritius in the journey of 55 years.
- **Judging:** thematic relevance 30%, **innovation in AI application 40%**, artistic/narrative quality and editing cohesion 15%, compliance with format 15%.
- **Language:** English audio with Chinese subtitles (decided 21 Nov, from the official rules).

### Schedule

| Time | What happens | What it means for us |
|---|---|---|
| 10:15–10:40 | Theme brief handed out, topics confirmed | Turn the brief into a shot plan within minutes |
| **10:40–12:00** | **AI generation, 80 min** | All AI work happens here: keyframes, video, score |
| 12:45–14:15 | Editing in **non-AI software**: audio, sequencing, MP4 export | ffmpeg assembly is fine; no AI upscaler (Real-ESRGAN) |
| 14:15–14:30 | Organisers verify "creation and flow" and the **AI Creation Statements** | Have the statement ready |
| 14:30– | Pitches | |

### Rules that can disqualify

- **No pre-existing or previously created designs, illustrations, AI images or templates.** Generate nothing for the film before 10:40. Nothing from the dodo film may be reused, not even its character sheet or its dodo. Code, prompts, plans and style guides are fine to prepare.
- No copyrighted or unlicensed visuals. Reference photos must be licensed (Unsplash, CC0), as in `CREDITS.md`.
- **Content must be free of political, religious, offensive or discriminatory elements.** So no temple deities as characters, nothing about governments or territories, no flags used for statements.
- An honest AI Creation Statement. Falsifying it disqualifies.
- Organisers distribute "AI tool access" on the day. **Assumption: we may use our own tools and API keys.** Check at the 10:00 briefing.

## Budget (hard limits)

- **fal: $60 total, from a new fal account the three teammates fund (Rs1000 each). Never exceed it.** Code cap **$58**, checked against fal's real bill after every clip. On the dodo film the real bill was double the list price, so measure the real cost on the first clip.
- **Meta Model API:** the dashboard shows $144 of the $150 hackathon credit left. Whether it still pays for calls after the hackathon is being checked; see Status. If it works, all Meta calls (Muse Image, Spark, Wonder) are free to us and the whole $60 goes to video.
- **Keys** (user creates them; never paste them in chat), in `.env`:
  - `FAL_KEY`: scope **API**, runs the models;
  - `FAL_READONLY_KEY`: scope **Billing**, reads the balance and usage for the cap.
- **No paid fal call without the user's go-ahead.** First call: one short test clip to measure speed, real cost and action quality.

## Decisions

- **Video model: FLUX 3 Max on fal** (commercial licence).
  - `blackforestlabs/flux-3-max/image-to-video` by default, with an optional `end_image_url`.
  - `.../keyframes-to-video` for shots that must hit set moments.
  - Text-to-video is not used for story shots: nothing would anchor the characters.
  - 720p, $0.085/s until 23 Nov 00:00 UTC (the discount applies on bootcamp day), then $0.17/s. A 240 s film is about $20 per complete take. Clips are 5–20 s, and audio is generated in the same pass.
- **Keyframes first: lots of Muse Image, then video.** Muse Image paints start (and end) frames from a character sheet and licensed reference photos, so the video model can't drift. Muse Spark checks every keyframe before video money is spent. The user first wanted Muse Image only, without Spark checks; we agreed to keep the checks because they're nearly free.
- **Style: cinematic and action-capable** (the user's choice), not the dodo film's slow style.
  - Action clips of 5–8 s with one strong camera move each, landing pinned by an end frame.
  - Calmer shots in between.
  - Prompts cover camera, action, environment motion, light and sound.
  - Everything is in `FLUX3_PLAYBOOK.md`.
- **Sound:** FLUX makes the effects and ambience in each clip (engines, rain, crowds, firecrackers), and every clip prompt ends "No music". One score runs over the whole film: ElevenLabs Music from a composition plan Muse Spark writes (about $2.40 for 4 minutes, made in session 1). The fallback is a free licensed track added in the edit.
- **Story:** the user found the first hooks not "wow" enough. The bar is the dodo film: a simple premise, a character you feel for, an irony, and an ending that lands. Candidates must now fit the two themes and the no-politics, no-religion rule; see "Story candidates".
- **The pitch** (40% for innovation): Cutaway as an AI film crew. Muse Spark plans and directs, Muse Image paints, FLUX animates, Muse Spark reviews every take, and Muse Wonder critiques the cut. Every prompt and cost is logged, and the AI Creation Statement is generated from the log.

## Story candidates (decide once the topic is confirmed)

The team's own stage-1 comic is the natural base, if the topic is confirmed from it. Ask the user for it.
- **Spring Festival:** firecrackers, the dragon and lion dances, the family reunion dinner, red envelopes, Chinatown Port Louis decorated, fireworks over the harbour. Spring Festival is a public holiday in Mauritius.
- **55 years of ordinary people:**
  - a Hakka shopkeeper's "boutik sinwa" passed through three generations;
  - a fisherman and a Chinese engineer during a cyclone;
  - a grandmother's recipe crossing the ocean;
  - a letter or object travelling between two families over 55 years.
- **Action fits** a cyclone rescue, a chase through Chinatown on festival night, or a race to finish a lantern or dragon before midnight.

## Official rules received on the day (they replace the details above where they differ)

- **Judging:** thematic relevance 25%, **innovation in AI application using the official tool (Magnific) 35%**, artistic/narrative quality and editing cohesion 25%, presentation/pitching 15%.
- **Magnific** web access is given to each team; other AI tools are allowed. **Team decision (21 Nov): we don't use Magnific.** The pitch argues innovation from our own pipeline.
- **Language:** English with Chinese subtitles (or the reverse). **We use English audio with Chinese subtitles**, burned in during the edit (non-AI). If an AI translates the subtitles, the AI Creation Statement must say so.
- **Duration:** 3–4 min, **including the title and credits**.
- Event 09:00–15:35. "All AI-generated content must be created during bootcamp."
- Importing pre-made video, illustrations, AI images, **stock footage** or templates disqualifies. **Team decision (21 Nov): reference photos without copyright (CC0, public domain, or our own) may be used**, as inputs to Muse Image only and never shown in the film. List each one with its source and licence in `CREDITS.md` and the AI Creation Statement. (Rule 7 also says "no copyrighted or external material", so citing them openly is what protects us.)
- Audio: self-recorded audio, AI voice-over made on the day, and royalty-free sound or music **with a reference in the AI Creation Statement**.
- Pitch: 4 min screening, 1.5 min concept and process, 1.5 min Q&A.

## Confirmed on the day

- **Theme: "Touching Stories of the Ordinary People of China and Mauritius in the Journey of 55 Years".**
- **Team "Proxima", Middlesex University.** Members: Mikhil Naika (leader), Seeya Awotar, Yorvan Rengasamy.
- **The film is "55 Spring Festivals", adapted from the team's stage-1 comic.** The plan and shot list are in [BOOTCAMP_FILM.md](BOOTCAMP_FILM.md). The comic's artwork may not be reused.
- **fal keys: both work (checked 21 Nov). Balance $0.** Each teammate will add $20 during the day.
- **Meta credit is unconfirmed:** the dashboard still showed $144.02 after a $0.0007 call, and its request log showed zero. The dashboard may update late.

## AI Creation Statement form (handed in at 14:15)

Blank form: `Downloads/AI video creation statement form_….pdf`. The team details and signatures are already filled in.

| Section | What it asks for |
|---|---|
| 2 | Video title, duration, date of creation |
| 4 | A table of tools with purpose and online/offline |
| 5 | AI vs manual percentages for visuals, sound/music, script/text and final editing |
| 6 | Ticks, including "all content created during the bootcamp" and "no pre-existing footage, music or images" |

Fill it from the generation log at the end of session 1.
- **Tools, all online:** Muse Spark, Muse Image, Muse Wonder (Meta Model API), FLUX 3 Max (fal), ElevenLabs Music (fal), and Claude (pipeline code and story drafting).
- **Offline:** ffmpeg, for editing.

**Note:** signature 1 is dated "31/11/26", which doesn't exist; the others say 20/11/26. Correct it before handing the form in.

## The pipeline (built 21 Nov; tested offline with stubs, no money spent)

`cutaway/bootcamp.py`, all files in `films/bootcamp/`:

| Stage | Command | Cost |
|---|---|---|
| Plan | `python -m cutaway.bootcamp plan` (Muse Spark writes `film.json` from BOOTCAMP_FILM.md and the playbook; review and edit it) | Meta |
| Sheets | `python -m cutaway.bootcamp sheets` (one per character and age, in parallel, Spark-checked) | Meta |
| Keyframes | `python -m cutaway.bootcamp keyframes [--shots ...]` (dependency waves; one automatic repaint below 7/10) | Meta |
| Quote | `python -m cutaway.bootcamp quote` | free |
| Video | `python -m cutaway.bootcamp video --yes [--shots ...] [--revised]` (all clips at once, 8 threads) | **fal** |
| Review | `python -m cutaway.bootcamp review` (Spark watches every new take) | Meta |
| Rough cut | `python -m cutaway.bootcamp cut` (the clips' own sound; white flash on `flash_out` shots) | free |
| Score | `python -m cutaway.bootcamp score --yes` (Spark writes the plan; ElevenLabs Music) | **fal**, about $2.40 |
| Mix | `python -m cutaway.bootcamp mix` (score at -9 dB under the cut, -16 LUFS) | free |
| Other | `status`, `statement` (draft of the AI Creation Statement) | free |

Details:
- **`film.json` format:** see the docstring in `bootcamp.py`. `@name` refers to a character sheet and `@sid.frame` to another shot's keyframe. Per-shot options: `trim`, `seed`, `audio`, `reasoning`, and a `choice` in the shot's `state.json` to pick a take by hand.
- **`i2v.py` profiles:** `CUTAWAY_FAL_PROFILE`, default `bootcamp`, uses `ledger_fal_bootcamp.json` with a $58 cap and usage since 2026-11-20. The `dodo` profile is the old one.
- **FLUX 3 Max** (`flux3`, `flux3_kf`): $0.085/s at 720p until 23 Nov, reserved at a 2× margin until the bill is confirmed.
- **`meta.py`:** the log context is now per thread (`thread_context`), and `chat` takes a time limit. All bootcamp Spark calls use low reasoning with a time limit; the plan uses medium with up to 15 minutes.
- **Safety:** with a $0 fal balance, `_run` refuses before sending anything.
- **If Spark's `plan` is slow or weak:** write `film.json` by hand (Claude can) from BOOTCAMP_FILM.md.

## Status (2026-11-21, morning)

- **The pipeline is built** (see above). Not yet tested against the real services:
  - the first real FLUX call, which will show the real speed, the real bill and the response format (the code expects `result["video"]["url"]`);
  - Muse Image keyframes in parallel threads.
- **First paid step, after the team's go-ahead:** one short action test clip, then compare `i2v.reconcile()` with the price, to confirm the bill and lower the 2× margin.
- Meta credit check: see `PROGRESS.md`, and the latest note below.
