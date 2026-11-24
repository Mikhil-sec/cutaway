# Lessons

Short, concrete lessons from building Cutaway and making its first film. Read before changing the agent.

## Critics and reviews

- **One model's notes must never discard work on their own.** The first Muse Wonder critique marked 11 keyframes for repainting, including shots whose own note said "keep it", and the agent obeyed. Now a second model (Muse Spark, looking at the frame) must agree a repaint would fix the problem; director-approved keyframes are locked; and a critique round may change at most 5 shots.
- **Good diagnosis is not good prescription.** The third critique's observations were accurate (the capture is never shown, the hero is blurred in the first seconds of some shots, the clones lack our protagonist), but its fixes gave nearly every shot "startle" plus a strong camera move. Take the notes, choose the fixes.
- **Validate the critic's answer.** One run returned "15/10" with every shot "keep". A review must stay on its scale and name strengths and weaknesses, or it is retried with deeper reasoning and otherwise ignored.
- **A repaint must carry the reason it was asked for.** Repainting with the same prompt produced the same problem (the dodo still facing away from the mountains). The note now goes into the new prompt.
- **Never append a correction that contradicts the original prompt.** "In the left third" plus "alone in the middle of the ring" failed three times; rewriting the prompt as one consistent description worked first time.
- **Below-threshold advice must not delete anything.** A review that suggested a repaint but scored above the threshold used to delete the render anyway.

## Rendering

- **Blended transparency writes no depth, so depth of field blurs every layer alike.** Use dithered transparency for image layers; keep blended only for pure glows (fog, motes, flashes).
- **Real-world apertures do nothing at scene scale.** Layers 5-40 m away at f/2.4 blur by under a pixel; f/0.35 reads as a long lens on a large sensor.
- **Two cut-out cards in the same plane fight over pixels** (a camouflage pattern under dithered transparency). Keep characters at least 0.08 apart in depth, and the ground behind all of them.
- **The overscan margin crops the composition.** 25% leaves room for moves but cuts characters near the painting's edge; step it down per shot until the characters fit, and ask for real breathing room (12%) around one character, not just "inside the frame".
- **A clip is current only if it was made from the current spec.** Stamp each frames folder with its spec and re-render when they differ; skip-if-exists silently kept stale renders.

## Video models (image-to-video)

- **Check the real bill, not the price list.** fal listed Wan 3.0 at $0.05/s but billed $0.10/s at 720p and $0.20/s at 1080p. A ledger built on list prices undercounted by 60%. Reconcile with fal's usage records (BILLING-preset key) before and after every clip.
- **Wan exaggerates camera moves and invents what the move reveals.** Trucks, cranes, orbits and pull-outs gave new buildings, the wrong mountains and a shrinking dodo; 4 of 5 city first takes were rejected for it. Nearly locked-off cameras passed. Put the life into the character's acting and the secondary motion inside the frame.
- **Shots that cut together need the same place and light, and the action must carry across the cut.** Two good shots in different light on different rocks read as unrelated. Repainting the second from the first's keyframe and ending the first mid-movement fixed it.
- **A paid request must never be abandoned.** The laptop hibernated mid-clip, the poll timed out on wall-clock time, and fal had already charged for the clip. Save the request id before waiting, count only answered polls toward the timeout, and collect leftover requests on the next run.
- **Muse Spark's review catches what the eye would:** morphing streets, teleporting characters, legible text on buses. Its rewritten prompt, as one consistent description, usually fixed the take.

## Process

- **Parallel runs must not share mutable state.** Two processes saving one plan.json lost each other's changes; each shot now keeps its own state file, and revisions are re-applied on load.
- **A process holds its state in memory.** Locking a keyframe while a run is working on that shot can be overwritten when the run saves; re-apply after it finishes.
- **Stop processes by exact command line.** Matching on a shot id also killed a run whose shot list merely contained it.
- **Keep the pieces.** Every deleted keyframe could be rebuilt exactly from its clean plate plus its cut-outs.
- **Don't delete on change; let staleness decide.** Changing a shot used to delete its frames, so reverting an
  overruled critique still cost seven re-renders. Renders are now stamped with their spec and redo themselves
  only when it really changed, and replaced keyframes are archived.
- **Muse Image's content filter is unpredictable,** and a critical story will trip it; rewording with Muse Spark gets through, but softens the mood, so put the harshness back with lighting.
- **Reference photos of real places are what make it local.** Without "Mauritius", Port Louis came out Indonesian.

## The bootcamp film (FLUX 3 Max, one day)

- **Hand-painted 2D anime holds in FLUX 3 Max image-to-video.** The first test clip kept the painted look from the first frame to the last. BFL's docs say nothing about non-photoreal styles, so test once before committing.
- **The real bill matched the list price** ($0.085/s at 720p on the discount). Reconcile anyway: fal's usage records lag by a minute.
- **Clips start static.** People hold still for 1–2 s before moving. A prompt line saying everyone is already moving at frame one, extras included, helps. Trimming the first 1–2 s in the edit fixes what's left.
- **Big camera moves over crowds morph faces** (a top-down crane over a wedding table). Over many small faces, keep the camera nearly locked off and put the life into the people.
- **An end frame far from the start frame makes FLUX cut** to a new shot mid-clip (stars → boy by the wall, airport hall → plane over a lagoon). Keep start and end frames related, or drop the end frame.
- **Someone who isn't in the start frame pops in** (Smriti appearing in the doorway). Put every character who matters in the first frame.
- **FLUX garbles names and short lines** ("So you're Wei" became "So your way") and drifts toward an American announcer voice. Lines where the speaker's back is to the camera are cleaner as TTS (ElevenLabs v3), with the clip's own speech turned down underneath.
- **A global style line applies to everything.** "Every crowd in Mauritius is diverse" made Muse Image add crowds of children to Meizhou and to the view through a doorway. Write conditional rules: "when a scene already has a crowd…", and "never add people who aren't described".
- **Spark marks down what it was told to avoid, even when the prompt asks for it.** It flagged the requested WELCOME HOME banner as "text", and a shop that wasn't "exactly centred" because the reference frame wasn't. Write precise constraints and look at the frames yourself before repainting.
- **Ageing chains work.** Painting each older sheet, or each photo in a sequence, from the previous one keeps faces consistent. But the user judged identity by eye: re-anchoring Wei at 14 and 26 on his 21-year-old sheet fixed "doesn't look like the same person".
- **Three candidates per keyframe, with Spark picking the best**, costs cents and lifts most frames to 8–9/10 in one round.
- **A dropped connection during submission** fails before fal accepts anything (nothing billed), but the code had already reserved the money. Requests already accepted resume from their `.pending.json`.
- **Feedback rounds take far longer than generation.** All 32 clips rendered in about 6 minutes in parallel, but the team's critique rounds took hours. Leave at least 40 minutes before the deadline for the final edit and export.
