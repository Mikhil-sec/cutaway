# Progress

Last updated: 2026-11-02.

## Status

**Built and working (all pushed):**
- The full 2.5D pipeline:
  - Muse Spark plans the film; Muse Image paints keyframes; SAM 3.1 cuts layers; code fits the camera.
  - Blender Eevee renders with puppets, depth of field, fog and flashes.
  - Muse Spark reviews each shot; Muse Wonder critiques the cut.
  - Voice notes, sound mix, AI disclosure and a making-of.
- Finished outputs (not in git):
  - `films/dodo/film_1920.mp4` (139.5 s, 1080p), with the preview `film_1080_preview.mp4`.
  - `films/dodo/makingof/making_of.mp4` (2:38).
  - Neither has music yet.
- Muse Wonder critique score: 3/10 in round 1, 6/10 after round 2. Round 3 made things worse and was reverted.
- Meta API spend: about **$6.29 of the $150** credit. The code cap is `HARD_CAP` in `cutaway/meta.py`.

**User's verdict (2026-10-31):** the film is "far too static, does not look animated at all … just a sideshow". 2.5D camera moves over still paintings cannot win the film competition. The content and story are good.

## 2026-11-01: image-to-video bake-off done

- The user agreed to image-to-video and set up fal.ai. `FAL_KEY` is in `.env`; it uses the `API` preset, so it can't read the balance.
- **Budget: $45 of the user's own money; $50 only if really needed.**
  - `HARD_CAP_USD` in `cutaway/i2v.py` is set to 45.
  - The ledger is `ledger_fal.json` (gitignored).
  - Each stage script has its own cap on top of that.
- `cutaway/i2v.py`: fal queue client.
  - Submits the keyframe as a JPEG data URL, polls, downloads, and logs to `generation_log.jsonl`.
  - Reserves `margin` × list price upfront, then settles to list price.
- Bake-off: `experiments/i2v_bakeoff.py`.
  - Shots s03, s12 and s19, 5 s each, through MiniMax H3 (A), Kling 2.6 Pro (B) and Wan 3.0 (C). Cost **$2.55**.
  - Outputs and blind A/B/C comparisons are in `films/dodo/i2v/bakeoff/` (gitignored). Sent to the user; **waiting for their pick**.
  - My notes (not shared yet, to keep the test blind):
    - All three kept the style.
    - H3 adds its own sun flare. Its free audio looks like it includes music; the prompt can ask for "ambient only".
    - Kling outputs 1920×1080 and added a bus passing close in the foreground.
    - Wan 3.0 pulled out far and invented city that isn't Port Louis.
- Outputs: H3 is 1344×768 at the 768P setting (2K is an upscale); Wan 3.0 is 1280×720.
- Live prices come from the fal API `/v1/models/pricing`. Kling 4.0 is $0.157/s and Seedance is token-priced, about $0.15–0.25/s; both are too expensive for 2–3 takes per shot.
- **User direction: the film must flow like a movie,** with good transitions where needed, and redraw scenes with Muse Image if needed.
  - Plan: use start and end frames (all three models accept `end_image_url`) so shots connect.
  - Muse Image paints end frames and redraws scenes (billed to the Meta credit).
  - Muse Spark writes the motion prompts.
- **User picked C, Wan 3.0, for every shot.**
- **Real fal billing** (read with a BILLING-preset key, stored as `FAL_READONLY_KEY`):
  - Wan 3.0 costs $0.10/s at 720p and $0.20/s at 1080p. The list shows $0.05/s, which is presumably the 480p rate.
  - H3 billed 6 s for a 5 s clip. Kling costs exactly $0.07/s.
- **Spent $4.45 of the $10 loaded**, including one 1080p test clip of s12.
- `i2v.py` now reconciles the ledger with fal's usage records before and after every clip; the higher figure wins.
- MFDC sets no resolution rule (see `docs/MFDC_RULES.md`), but technical quality is judged.
- **Plan:**
  - Generate at 720p, about 2 takes per shot, roughly $28.
  - Upscale locally with Real-ESRGAN's anime video model (free); test it against the native 1080p s12 clip first.
  - Keep a buffer of about $12.55.
- The user topped up $25 and allowed running Real-ESRGAN (`tools/realesrgan/`, gitignored). Real-ESRGAN won the upscale comparison; it takes about 2.8 s per frame on the Intel Arc.
- **Production stage built:** `cutaway/animate.py`.
  - Director stages: `motion`, `i2v` and `upscale`, plus `cut --source i2v`.
  - `motion.json`: Muse Spark planned every shot's motion and transition in one call, seeing all the keyframes. It used a dream-match from sleep to waking, and mirrored the opening at the end.
  - Takes go to `shots/<id>/take_N.mp4`, and Muse Spark reviews each one against its keyframe.
  - The chosen take goes to `shot_i2v_1280.mp4`, trimmed to 24 fps.
  - Spending rules: `PRODUCTION_CEILING_USD = 30.50` on the absolute fal ledger; first takes for every shot before any retake; retakes worst-first, never touching funds owed for first takes; at most 3 takes per shot.
- **Pilot, s01–s04: $4.10 for 7 takes.** s01 9→8/10 and s02 9/10 passed first time. s03 failed at 4/10 (the street morphed into another avenue), then passed at 7/10. s04 scored 6, 6, then 8/10; the bus kept showing legible text.
  - Pilot cut: `films/dodo/i2v/pilot_s01-s04.mp4`, sent to the user.
  - fal ledger = real = $8.55; balance $26.45.
- **The user approved all three:**
  - The forest opening moves from dawn to evening.
  - s02 repainted as the same rock and light, from closer (`match_shots` in the keyframe); s01 ends mid-crouch, then a cut on action.
  - Text cards: see `films/dodo/story.md` "Text cards"; they're read from `films/dodo/captions.json` and burned in by `cut`. The third line, "It was not the only one.", is a proposal still to be confirmed.
- New s01 and s02 passed first time (8 and 9/10), and the cut connects.
- **The production limit was raised to $34.50** at the user's request: use all $35 loaded and stop cleanly. The user tops up tomorrow if needed.
- **The laptop hibernated mid-run** (battery). s08's clip had been paid for but not collected; it was recovered from fal by request id.
  - `i2v.generate` now writes `take_N.pending.json` before waiting, counts only answered polls toward the timeout, and resumes leftover requests on the next run.
- **Most city first takes failed** because Wan exaggerates camera moves (s05, s06, s07, s09). I stopped the run between clips, and Muse Spark rewrote s10–s21 for near-locked cameras (`animate.revise_motion`), then the run resumed (log in `films/dodo/i2v_full2.log`).
  - Real spend was $13.25 at the restart.
- **Production finished on 2026-11-02. fal real spend is $32.00 of the $35 loaded; $3.00 is left.**
  - 19 of 21 shots are accepted at 7–9/10. s11 keeps its 6/10 take. s05 keeps take 3 (4/10): the keyframe puts the dodo in the corner, so every model walks it into the road. On screen it reads as wandering, and it's flagged for the user.
  - The user suggested trying another model on failing shots, so a fallback was added: `WAN_TAKES = 2`, then `FALLBACK = kling26` for 2 takes. Kling rescued s06 (8/10). It stays faithful but under-acts.
  - An s10 request sent just before a process was killed was paid for and recovered (`orphan_take.mp4`). Never kill a run: create `films/dodo/i2v.stop` instead. For an old process, place a ledger hold so its budget check stops it.
- **Rough cut v2:** `films/dodo/i2v/roughcut_v2.mp4`, 139.2 s, 720p, with text cards; sent to the user.
- **Upscale done** (Real-ESRGAN, free): `shot_i2v_1920.mp4` for all 21 shots; s06 is native 1080p from Kling.
- **Final cut v1:** `films/dodo/cut_1920.mp4`, 1920×1080, 24 fps, 139.2 s, with text cards, no sound. A phone copy (`i2v/final_1080p_v1_share.mp4`, CRF 28, under SendUserFile's 30 MiB limit) was sent to the user.
- **Muse Wonder critique of the video cut: 6/10** (`critique_i2v.json`, new `critique --source i2v`: notes only, nothing applied; it sends a 960-wide proxy).
  - Strengths: the sleep bookend, the recognisable journey through Port Louis, s08's irony, the s15 reveal, the s19 peak.
  - Weaknesses: static holds (s07, s17, s18, s20); no capture between s12 and s13; the umbrellas change in s12 and the mural in s17; our dodo not distinguishable at s15/s16; flicker in crowds; s21 shows a real forest, which contradicts the end card.
  - Free fixes it names: trim s05, s07 and s20. The rest are retakes or repaints (fal money, user's call).
- **Hackathon demo draft v1:** `films/dodo/makingof/making_of_i2v.mp4` (2:42, no sound), built by `experiments/build_makingof.py` with `makingof.build_i2v` (`--blender` builds the old one). It shows: cold open, problem, motion plan, photo vs keyframe, keyframe check, take comparisons (s09, s03), Wan vs Kling (s06), the s01-s02 flow fix, spend, the Muse Wonder critique, and the film from s15 to the end card (about 52 s). Sent to the user.
- `docs/SUBMISSION.md` and `docs/X_POST.md` are rewritten for the video pipeline.
- **2026-11-02, after the user's answers:**
  - s21 repainted in the enclosure (the real forest was a mistake), with `match_shots: [s19_press_mural]`; Wan take 1 scored 8/10 ($0.80). fal real spend is now $32.80; the card holds $2.20.
  - Free trims in `motion.json` (`trim: [in_s, out_s]`, applied by `cut`): s05 0–2.75 s, s07 3.0–8.4 s, s20 0–3.0 s. The film is now 129.4 s.
  - The demo shows the last ~40 s of the film (`build_i2v(excerpt_s=40)`: from s17 to the end card). The user approved about 40 s.
  - Committed and pushed as 9e14094 (with the user's go-ahead). `films/*/makingof/` is gitignored, so no film footage is in the repo.
  - Film v2 and demo v2 were sent to the user.
  - Sound plan, proposed and not yet approved: Muse Spark writes the music brief and ElevenLabs Music composes it (about $1.40). MMAudio adds synced sound effects (about $0.15). A few sad dodo calls from ElevenLabs sound effects, modelled on the Nicobar pigeon (its closest living relative). The audio models must go through the fal ledger cap first. The user's own voice is suggested for the demo voice-over.
- **Next:**
  1. The user's verdict on s05, s11, the third text card, the demo draft, how much film the public demo may show (MFDC prior publication), and a voice-over or not.
  2. `sound --final`: ambience now; music waits for the user's licensed track in `films/dodo/music/`.
  3. Muse Wonder critique. Do NOT run the `critique` stage as is: `apply_critique` writes 2.5D-era changes (actions, intensity) into the plan. Write an i2v-aware critique first.
  4. Disclosure: add Wan/Kling and fal, and the text cards.
  5. Making-of and hackathon demo; the hackathon is due Nov 4, 9 PM ET.
- **Next:** upscale test; build `director` stage `i2v`, with Muse Spark writing motion prompts and reviewing takes, plus end-frame continuity; show the first few shots before the full run.

## 2026-11-02 (later): rounds 2-4, sound, versions

- **Budget:** the user topped up $12 (card total $47 loaded) but the cap stays **$45**. fal real spend is **$44.21**; nothing more is to be spent without the user's go-ahead. `PRODUCTION_CEILING_USD` is 44.00. One s12b retake was run with an explicit `limit=44.95`, inside the $45 cap.
- **Versions** live in `films/dodo/versions/` (gitignored): v1 (rough, 6/10), v2 (trims, s21 fixed), v3 (sound, 6/10, `critique_i2v.json` inside). Keep every version; a round can make things worse.
- **The user's friend approved use of their Caudan photos** (`refs/port_louis/WhatsApp ...`). They are used for s12, s12b (umbrella street) and s07 (canal). `refs/` stays out of git. Credit them in the disclosure, without a name unless the user gives one.
- **Picture changes:**
  - s03: the dodo wakes on its own forest rock, now in a roadside garden bed (the city grew around it).
  - s04: the startle happens on that rock.
  - s05: a frightened escape through a Chinatown back street, toward the gate.
  - s12: the umbrellas hang overhead.
  - **s12b_crate_closed (new):** a keeper's hands close the crate lid. The take was chosen by hand: take 2, tied 8/10.
  - s15: five varied dodos.
  - s17 and s18: the mural matches s19.
  - s07: the real Caudan canal with Le Pouce.
  - Trims are in `motion.json`: s09, s16 and s20, with a dissolve into s20.
- **Muse Image's filter** refused the capture six times, inconsistently. The same prompt passed with the s11 keyframe as a reference.
- **Sound (`cutaway/score.py`, stage `score`):**
  - Muse Spark designs it (`sound_design.json`).
  - ElevenLabs Music composes it from a composition plan whose section durations come from the timeline: `music/score_v1.mp3`, $1.80 (billed per whole minute).
  - MMAudio makes each shot's synced effects (`shots/*/sfx.wav`).
  - ElevenLabs sound effects make 5 dodo calls, modelled on the Nicobar pigeon (`sound/calls/`). call_05 was regenerated because the sigh read as human.
  - The mix is loudness-normalised to -16 LUFS.
  - `score.conform()` re-edits the score to a new timeline, so trims don't need a new score.
- **The critique now hears the sound:** it reports `can_hear_audio`, and it said true with accurate notes.

### Versions and critiques (all in `films/dodo/versions/`)

| Version | Length | Muse Wonder | What changed |
|---|---|---|---|
| v1 | 2:19 | 6/10 | First full video cut, silent |
| v2 | 2:09 | – | s21 in the enclosure; trims |
| v3 | 2:16 | 6/10 | Sound; capture shot; s03 on its rock; s05 Chinatown escape; s12, s15, s17 repainted |
| v4 | 2:11 | 7/10 | s04 on the rock; s07 real Caudan canal; s18 mural; keeper's hands; softer last call |
| v5 | 2:10 | 7/10 | s16 moved before s15; s20 cut |
| v6 | 2:07 | 7/10 ("competition-ready") | s15 back before s16; s17 shortened |
| **v7** | **2:04** | **7/10** | s13 and s16 trimmed. **Current film.** |

- The score levelled off at 7, and the critic flips on some notes (the s15/s16 order), so the loop was stopped at v7. `pacing` was removed from the critique schema because it kept coming back degenerate; a malformed reply is retried.
- **Remaining notes, all needing paid retakes after a top-up:**
  - s05 should scurry more.
  - s04's neck stretches too far.
  - s12's umbrellas are too saturated against s10/s11.
  - s14: the crate is too small, and the keeper smears.
  - s15: our dodo can't be told apart from the other five.
  - s19 should press clearly against the painted forest.
  - s02 should fall into blue dusk.
  - s09: the dodo looks giant.
- **Free notes not yet acted on:** trim s07 to about 3 s; cut s16 entirely (the critic contradicts itself on this).
- **Next:**
  1. Update `AI_DISCLOSURE.md`: Wan/Kling/fal, ElevenLabs Music and SFX, MMAudio, the friend's photos, the text cards.
  2. Rebuild the making-of with sound and the v7 film, and add the new story: the sound design and the critique loop with versions.
  3. Commit and push (ask the user).
  4. Submit the hackathon by Nov 4, 9 PM ET.

## Decision in progress: switch to image-to-video (background)

The plan is to keep everything up to and including the keyframes, then animate each keyframe with an image-to-video (I2V) model instead of the Blender 2.5D render. Cutaway gains a "video model" renderer beside the Blender one, and the harness:
- writes the motion prompts with Muse Spark;
- generates 2–3 takes per shot;
- has Muse Spark (video input) reject broken takes: morphing, extra legs, an off-model dodo;
- has Muse Wonder critique the cut.

Disclosure and records carry over.

Advice given to the user:
- **Skip the Grok Imagine subscription** ($18/month). Its limits are unpublished, clips max out at about 15 s at 720p, and there's no API on that plan, so it would mean uploading every take by hand. The Grok API costs about $0.14/s.
- **Use fal.ai pay-per-use instead.** Rough prices as of 2026-10:

  | Model | Price | Note |
  |---|---|---|
  | Kling 2.6 Pro | ~$0.07/s | Top candidate |
  | Hailuo 2.3 Standard | ~$0.28 per 6 s clip | Cheapest |
  | Veo 3.1 Lite / Fast | ~$0.05–0.10/s | |
  | Wan 2.5 at 720p | ~$0.10/s | |

  Check the current prices on fal.ai before building.
- **Budget: up to $40 of the user's own money.**
  - Bake-off: about $4. Shots s03 (waking in the city), s12 (ring of tourists) and s19 (mural), run through Kling, Hailuo and Veo Lite. The user picks the winner by eye.
  - Production: about $20–30. Roughly 140 s × 3 takes.
  - Buffer: about $5.
- **Waiting on the user:**
  1. Agree to the plan.
  2. Create a fal.ai account with a spend limit.
  3. Put `FAL_KEY=...` in `.env`. They shouldn't paste it in chat.

**Next steps once `FAL_KEY` exists:**
1. Look up fal's current API docs (Context7 or web) for the queue/subscribe API and the exact model endpoint ids. Then write `cutaway/i2v.py`:
   - upload the keyframe;
   - submit the prompt with duration and aspect;
   - poll and download;
   - add a cost cap and ledger like `meta.py`, and log to `generation_log.jsonl`.
2. Run the bake-off script in `experiments/` and send the clips to the user with SendUserFile.
3. Add an `i2v` render path to `director.py`. Have Muse Spark write the motion prompt from shot intent, action and camera. Add take selection, then cut, sound, critique and disclosure (add the model and provider to AI_DISCLOSURE).
4. Re-make the full film and rebuild the making-of. The hackathon story becomes "harness picks and checks video-model takes; Blender 2.5D as the cheap fallback".

## Open items waiting on the user

- Music tracks to drop into `films/dodo/music/` (licensed). Then run `sound --final` and rebuild the making-of.
- An optional voice-over for the hackathon demo.
- A review of the director decisions the assistant made on the user's behalf, listed in `films/dodo/AI_DISCLOSURE.md`.
- A check of the MFDC full Terms & Conditions on prior publication. Until then, keep the hackathon demo film separate from the competition film.
- The friend's permission for their Port Louis photos.
- Optional new shots: the capture, and our dodo among the five at the reveal.
- Hackathon submission (by Nov 4, 9 PM ET): use `docs/SUBMISSION.md` and `docs/X_POST.md`, record the demo video, and post on X.

## Key facts for a fresh session

- Meta API base `https://api.meta.ai/v1`. Muse Image (`/images/generations`, `/images/edits` with up to 10 refs, ~$0.01 each) and SAM 3.1 go through `/responses`. Chat models are `muse-spark-1.3` and `muse-wonder-1.0` (both take video input) and `muse-voice-transcribe-1.0`.
- Per-shot state: `films/dodo/shots/<id>/state.json`, plus keyframe, plate, layers, spec, and frames/clips. Keyframes can be locked. Repaints need a second-opinion gate, and nothing is deleted (old keyframes are archived as `keyframe_prev{n}.png`).
- Lessons learned are in `docs/LESSONS.md`. Licences and credits are in `CREDITS.md`.
- Untracked film artifacts (critiques, plan.json, disclosure, timeline) sit in `films/dodo/`. Decide whether to commit them before submission.
