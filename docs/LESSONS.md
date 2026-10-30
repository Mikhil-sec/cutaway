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
