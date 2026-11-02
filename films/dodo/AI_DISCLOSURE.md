# AI disclosure: The Dodo Came Back

Category B (AI) · 124 seconds · 22 shots

## Extent of AI use

Approximately 100% of the picture and the sound is AI-generated. The author's contribution is the story, its direction and the choice of the final cut.

- **Images:** every frame starts from a keyframe painted by Muse Image (Meta). Real places in Port Louis were painted from reference photographs (see Third-party material); no photograph appears in the film as it was taken.
- **Motion:** each keyframe was animated by an image-to-video model (Wan 3.0, or Kling 2.6 where Wan failed twice), from a motion prompt written by Muse Spark (Meta). Muse Spark watched every take and accepted or rejected it. 720p takes were upscaled to 1080p locally with Real-ESRGAN (an AI upscaler, run on the author's laptop).
- **Sound:** the score (ElevenLabs Music), the effects (MMAudio) and the dodo's calls (ElevenLabs Sound Effects) are AI-generated, from a sound design written by Muse Spark. No recorded music or sound is used.
- **Text:** "Mauritius, 1681.", "Port Louis. Today.", "It was not the only one." and the end card "The dodo came back. Its home didn't.", drafted with an AI assistant, chosen by the author and set in EB Garamond.
- **Editing:** cutting, transitions, trims, the sound mix and loudness were done by the Cutaway software (ffmpeg), following Muse Spark's plan, Muse Wonder's critiques and the author's notes.

## Human and AI authorship

- The story idea is the author's own: a dodo wakes in modern Port Louis, becomes an attraction and ends in an enclosure with many dodos. The written brief (story.md) was drafted from that idea with an AI assistant (Claude, Anthropic) and approved by the author.
- The author directed through notes on each version. For example: an evening forest; the capture scene; the dodo waking on its own rock rather than in the road; a frightened escape instead of a calm walk after the startle; dodo calls as it wanders; an enclosure, not a real forest, at the end.
- The Cutaway software, which runs the Meta models and the video and audio models, was written with the same AI assistant. Choices that overruled the models (choosing between tied takes, overruling a critique, trims) are recorded per shot below as made by the director: the AI assistant acting on the author's behalf.
- The author reviewed every version and chose the final cut (version 7 of 7).

## AI tools used

| Model | Role | Calls | Cost (USD) |
|---|---|---|---|
| muse-image-1.0 | painting every keyframe from the character sheet and reference photos | 114 | 1.14 |
| muse-spark-1.3 | shot list, keyframe continuity checks, motion plan, review of every video take, prompt rewording, sound design | 266 | 2.05 |
| muse-wonder-1.0 | critique of the whole film with its soundtrack (editor's notes) | 11 | 1.71 |
| sam-3.1 | depth layers for the earlier Blender version (not in the final film) | 336 | 0.84 |
| h3 | model bake-off only, not in the film (MiniMax H3, via fal.ai) | 3 | 0.75 |
| kling26 | animating keyframes where Wan 3.0 failed twice (Kling 2.6 Pro, Kuaishou, via fal.ai) | 10 | 4.55 |
| mmaudio | each shot's sound effects, generated from the shot's video (MMAudio v2, via fal.ai) | 22 | 0.13 |
| music_el | the score, from a composition plan written by Muse Spark (ElevenLabs Music, via fal.ai) | 1 | 1.36 |
| sfx_el | the dodo's calls (ElevenLabs Sound Effects v2, via fal.ai) | 6 | 0.02 |
| wan30 | animating the keyframes (Wan 3.0 image-to-video, Alibaba, via fal.ai) | 57 | 35.30 |

Meta Model API: $5.74 (token models at their billed cost, image and segment models at list price). fal.ai: $42.12 logged at list price; $44.21 actually billed by fal.
Real-ESRGAN (realesr-animevideov3, BSD-3-Clause) ran locally at no cost. fal.ai lists every fal model above as licensed for commercial use (checked 2026-11-02).
Every call, with its full prompt or input and reply, is in generation_records.jsonl. A paid video request that a run could not collect (the laptop slept) was collected by the next run, not paid for twice.

## Sound design (Muse Spark)

Score styles: solo piano, soft strings, muted ravanne heartbeat and breathy bamboo flute; slow tender minimalist cinematic mood, melancholic and gentle; acoustic intimate dynamics evolving without genre change.
Excluded: no vocals, no choir, no spoken words; no electronic dance, no rock, no brass fanfare, no pop brightness; no abrupt tempo shifts, no genre breaks.

- From s01_forest_dawn, Ancient Forest Lullaby: warm solo piano lullaby with soft strings and evening air, very slow and calm
- From s03_wake_city, Concrete Awakening: same piano theme fractured with uneasy strings and faint ravanne pulse, anxious
- From s05_downtown_search, Lonely Search: wistful bamboo flute over soft piano and strings, wandering slow pace
- From s10_umbrellas_noticed, Gathering Eyes: plucked piano with quickening strings and light ravanne taps, curious then tense
- From s13_crate_harbour, Crate and Harbour Lament: mournful low strings with sparse piano and deep muted ravanne heartbeat, slow heavy
- From s17_mural_wall, Painted Forest Elegy: bare solo piano elegy with fading strings and breath silence, very soft and still

The dodo's calls, modelled on its closest living relative, the Nicobar pigeon:

- s03_wake_city: Low soft throaty waking grunt like a large drowsy pigeon, short chesty puff with beak barely open.
- s04_startle_close: Sharp startled throaty squawk-coo like a frightened large pigeon, brief rising chesty burst.
- s08_own_image: Soft questioning throaty coo like a curious large Nicobar pigeon, two low rolling notes tilting upward.
- s19_press_mural: Long sad low throaty coo like a mourning large pigeon, slow trembling breathy note held against paint.
- s21_sleep_again: A soft, low, sleepy two-note coo from a large drowsy pigeon settling down to sleep, fading out; clearly a bird's voice, not a breath or a human sigh.

## Per-shot record

In film order. Times are positions in the finished film. A take needs 7/10 or more from Muse Spark to be accepted.

### s01_forest_dawn (0.0–5.6 s)
- Keyframe (Muse Image, 1 attempt, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Muted cinematic anime with painterly 2D backgrounds and soft natural light. Wide shot of ancient Mauritian ebony forest at dawn, a plump grey-brown dodo with large hooked beak in centre third, full body visible standing on a mossy rock, standing still at home, tall ebony trees and mist between trunks, soft pink dawn light, tranquil mood, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. No legible text, logos or brand names.
- Motion plan (Muse Spark): Evening breeze moves the mist between the ebony trunks and leaves tremble in warm pink-gold light. The dodo stands on the mossy rock, looks around its forest calmly and gives a slow, contented shake of its feathers. Then it bends its legs and begins to crouch down onto the rock, head starting to lower, as the light begins to dim. The camera cranes down slowly.
  - Revised by: director (author's direction 2026-11-01): evening, cut on action
- 1 earlier take, made before the keyframe or plan changed (kept on record)
- Take 1 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: Evening breeze moves the mist between the ebony trunks and leaves tremble in warm pink-gold light. The dodo stands on the mossy rock, looks around its forest calmly and gives a slow, contented shake of its feathers. Then it bends its legs and begins to crouch down onto the rock, head starting to lower, as the light begins to dim. The camera cranes down slowly.
- Sound effects (MMAudio, from the shot's video): Soft evening breeze moves through ebony leaves with faint distant forest birds settling low under the canopy.

### s02_settle_sleep (5.6–10.4 s)
- Keyframe (Muse Image, 2 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Medium-close shot of the same mossy rock and ebony trees as the previous shot, the dodo in centre third, full body visible, crouching low on the mossy rock with its head lowering and eyes half-closed as it settles to sleep, warm pink-gold evening light starting to fade to soft blue dusk, mist gathering between the trunks, tranquil dreamlike mood, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. The last reference image is the previous shot of the film: show the same place, the same rock, trees, light and colours, from this shot's framing, so the cut reads as continuous. No legible text, logos or brand names. This repaint must fix: Author (2026-11-01): shots 1 and 2 did not connect; forest opening moved from dawn to evening so falling asleep makes sense, shot 2 repainted as the same rock and light from closer, motion linked by a cut on action
- Motion plan (Muse Spark): Continuing the same movement, the dodo settles fully onto the mossy rock, tucks its legs under its body, lowers its head and slowly closes its eyes, its breathing growing slow and calm. The warm pink-gold light fades gradually to soft blue dusk and the mist thickens between the trunks. The camera pushes in very slowly.
  - Revised by: director (author's direction 2026-11-01): evening, cut on action
- 1 earlier take, made before the keyframe or plan changed (kept on record)
- Take 1 (wan30) **(in the film)**: Muse Spark 9/10, no problems noted
  - Prompt: Continuing the same movement, the dodo settles fully onto the mossy rock, tucks its legs under its body, lowers its head and slowly closes its eyes, its breathing growing slow and calm. The warm pink-gold light fades gradually to soft blue dusk and the mist thickens between the trunks. The camera pushes in very slowly.
- Sound effects (MMAudio, from the shot's video): Fading birdsong thins into still blue-dusk air with gentle leaf rustle settling toward quiet.

### s03_wake_city (9.7–18.1 s)
- Keyframe (Muse Image, 7 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Wide shot of a modern downtown Port Louis street in early morning light. On the pavement, in a small roadside garden bed edged with low concrete, sits the same mossy rock as the reference, and on it the dodo, in centre third, full body visible, lying curled asleep with its head tucked down and eyes closed, exactly as it fell asleep in the forest. Around the garden bed: concrete pavement, office towers and shops, buses on the road beyond the kerb, blurred hurrying passers-by with no close-up faces, dust in the air. No legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. Use the reference photographs only for the real architecture and layout of this place in Port Louis, Mauritius; repaint everything in the film's style. The last reference image is an earlier shot of the film in the same place: show the same setting, surfaces, light and colours, from this shot's framing, so the cut reads as continuous. No legible text, logos or brand names. This repaint must fix: Author (2026-11-02): asleep at the kerb read as lying in the road, and nothing explained why it was there. It now wakes on its own forest rock, which survives in a roadside garden bed: the city grew around it while it slept. Avoid these problems from a previous attempt: Move dodo on mossy rock from left edge to centre third of frame; Blur right-side pedestrians to avoid sharp distinct figures and faces
- Motion plan (Muse Spark): The camera stays fixed on the mossy rock in the street median. The dodo blinks awake, lifts its head slowly, turns left and right in confusion and fluffs its neck feathers with beak parting slightly. Behind it blurred pedestrians drift along sidewalks, distant buses roll past softly out of focus, palm leaves stir and heat haze shimmers while it stares blinking at the city as a bus passes.
  - Revised by: Muse Spark, after reviews: These keyframes were just repainted. Wan 3.0 exaggerates camera moves and invents scenery, so keep the camera nearly loc
- 2 earlier takes, made before the keyframe or plan changed (kept on record)
- Take 1 (wan30): Muse Spark 4/10, Dodo stands fully upright on rock instead of staying curled seated; Foreground couple walks in close with distinct faces; Bus drives too close, sharp with legible text; Dodo neck stretches and proportions shift
- Take 2 (wan30) **(in the film)**: Muse Spark 6/10, camera pushes in to close-up then pulls back instead of steady medium pull-out; foreground pedestrians become sharp with distinct faces, violating blurred no close-up rule; new tall palm trunks pop in left and right foreground not in keyframe
  - Prompt: Slow medium pull-out from the mossy rock in the median garden bed, dodo stays curled seated. It blinks awake, slowly lifts its tucked head, looks left and right confused with soft blinking and slight beak part. Blurred distant pedestrians drift, distant buses stay soft out of focus, palm leaves stir in dusty morning light.
- Take 3 (kling26): Muse Spark 3/10, dodo stays curled asleep, never lifts head or looks around; camera pulls out too far, dodo becomes tiny; sharp close-up pedestrians with faces on left sidewalk; legible 'MON' text on passing bus
- Sound effects (MMAudio, from the shot's video): Early morning traffic rumbles with bus brakes hissing and hurried footsteps washing over the pavement garden.

### s04_startle_close (18.1–21.9 s)
- Keyframe (Muse Image, 2 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Close medium shot of the dodo, full body visible, standing on its mossy rock in the small roadside garden bed from the reference, ferns around it, neck stretched up and head jerked high, eyes wide in fright. Right behind it a city bus rushes past on the road, blurred with motion and with no lettering. Bright morning light, tense mood, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. The last reference image is an earlier shot of the film in the same place: show the same setting, surfaces, light and colours, from this shot's framing, so the cut reads as continuous. No legible text, logos or brand names. This repaint must fix: The startle placed the dodo in an empty street, breaking continuity with the rock in s03 (Muse Wonder critique of v3, 2026-11-02)
- Motion plan (Muse Spark): The camera stays locked on the mossy traffic island. A blurred city bus roars past behind without legible markings, stirring dust and fern leaves. The startled dodo jolts upright on its rock, feet gripping moss, neck stretching tall, eyes widening and beak parting. Its feathers puff and tremble, then it freezes, breathing fast, staring after the bus.
  - Revised by: Muse Spark, after reviews: These keyframes were just repainted. Keep the camera nearly locked off (Wan 3.0 invents scenery on camera moves) and put
- 3 earlier takes, made before the keyframe or plan changed (kept on record)
- Take 1 (wan30): Muse Spark 5/10, Bus sharpens mid-pass showing legible `910` and side logos; Dodo stays near-static, missing jolt upright and feather puff-tremble
- Take 2 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: Locked close shot on the startled dodo standing on its mossy rock in the roadside garden, ferns around its feet. A city bus streaks past behind as a featureless motion blur with no text or logos, stirring dust and a few fern leaves. The dodo jolts upright, neck stretching tall, eyes widening, beak parting, feathers puffing with a tremble, then freezes breathing fast, staring after the blur.
- Sound effects (MMAudio, from the shot's video): A loud bus horn blasts past with rushing air and blurred pedestrian footsteps pounding close behind.

### s05_downtown_search (21.9–26.9 s)
- Keyframe (Muse Image, 4 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Medium shot of a narrow back street in Port Louis Chinatown, old two-storey shopfronts with wooden shutters and red lanterns, the dodo in centre third, full body visible, hurrying along close to the wall with its feathers puffed and neck held low, glancing back over its shoulder in fear, a few blurred passers-by far behind with no faces, dappled late-morning light, anxious mood, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. Use the reference photographs only for the real architecture and layout of this place in Port Louis, Mauritius; repaint everything in the film's style. No legible text, logos or brand names. This repaint must fix: Author: after the scared close-up, the dodo strolling calmly down the same street looked wrong; it now flees through a different street, which leads to the Chinatown gate. Muse Wonder also noted it repeated s03. (2026-11-02) Avoid these problems from a previous attempt: Dodo looks forward instead of glancing back over its shoulder in fear; Neck is held high upright instead of held low while hurrying
- Motion plan (Muse Spark): The camera holds nearly locked on the sunlit alley and distant arch. The dodo hurries fearfully along the right wall with quick shuffling steps, body low, tail feathers twitching, glancing back over its shoulder with wide eyes. Overhead lanterns sway faintly, leaves flutter, dust drifts in light shafts and blurred distant figures amble while it presses on toward the bright end still glancing back.
  - Revised by: Muse Spark, after reviews: These keyframes were just repainted. Wan 3.0 exaggerates camera moves and invents scenery, so keep the camera nearly loc
- 5 earlier takes, made before the keyframe or plan changed (kept on record)
- Take 1 (wan30): Muse Spark 5/10, Dodo looks forward at wall instead of glancing back over shoulder; Feet shuffle in place with little forward progress toward bright arch; Large floating leaves pop in and distract from anxious beat
- Take 2 (wan30): Muse Spark 5/10, loses over-shoulder fearful glance, ends running facing forward; drifts off right wall to center of street; hurry reads as calm waddle, no low crouch or tail twitch
- Take 3 (kling26) **(in the film)**: Muse Spark 6/10, dodo pirouettes in place instead of travelling toward arch; forward progress stalls near right wall; beak briefly touches/merges with shutter; wing markings fade on rear view; feet shuffle with weak ground contact
  - Prompt: Near-locked medium shot of sunlit Chinatown alley with distant arch. The brown-grey dodo stays low hugging the right wall and hurries forward toward the bright arch with quick shuffling steps, neck low, body angled away while head turns back over shoulder with wide fearful eyes. Lanterns sway subtly, soft dust drifts, distant blurred figures amble.
- Sound effects (MMAudio, from the shot's video): Quick light shuffling on stone echoes in the alley with distant motorbike putters and faint market chatter.

### s06_chinatown_gate (26.9–32.0 s)
- Keyframe (Muse Image, 1 attempt, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Muted cinematic anime with painterly 2D backgrounds and soft natural light. Medium wide shot under the ornate Chinatown gateway arch in Port Louis, the dodo in centre third, full body visible standing on brick pavement looking up at the arch, red pillars and tiled roof details, blurred passers-by, soft daylight, curious mood, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. Use the reference photographs only for the real architecture and layout of this place in Port Louis, Mauritius; repaint everything in the film's style. No legible text, logos or brand names.
- Motion plan (Muse Spark): The camera glides slowly right beneath the gateway as passersby stroll past on either side and leaves stir overhead. The dodo steps forward, stops, lifts its beak high and gazes up at the arch, turning its head slowly from pillar to pillar. Its body sways slightly as it studies the structure.
- Take 1 (wan30): Muse Spark 4/10, dodo lowers head to stare at camera instead of holding beak up at arch; dodo walks toward camera growing larger instead of step then stop; overhanging tree branches grow in from top changing framing; pedestrians pop in and multiply on both sides
- Take 2 (wan30): Muse Spark 5/10, Dodo body spins/flips, tail swaps sides instead of staying steady; Upward gaze not held, head whips left-right; Oversized floating leaves look artificial; Passers-by pop in/out on right edge
- Take 3 (kling26) **(in the film)**: Muse Spark 8/10, left-side passers-by ghost and slide slightly; overhead leaves pop in late
  - Prompt: Muted cinematic anime medium-wide under Chinatown gateway, camera holds steady with very slow right drift. The dodo stays centered in profile, feet planted on brick, body steady as it lifts beak high to study the tiled roof, turning only its head slowly from pillar to pillar. Soft daylight, blurred passersby stroll naturally, faint leaves stir overhead, curious mood.
- Sound effects (MMAudio, from the shot's video): Murmuring street crowd hums beneath the gateway with soft wind in leaves and faint distant drumming.

### s07_waterfront_pouce (32.0–37.4 s)
- Keyframe (Muse Image, 3 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Wide shot of the Caudan Waterfront canal in Port Louis as in the reference photograph: still water between a long stone quay with a covered colonnade on the left and modern terraced buildings on the right, a low bridge in the distance, and the sharp peak of Le Pouce rising beyond the city. The dodo stands on the stone quay in the left third, full body visible, looking toward the distant mountain. Soft overcast daylight, longing mood, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. Use the reference photographs only for the real architecture and layout of this place in Port Louis, Mauritius; repaint everything in the film's style. No legible text, logos or brand names. This repaint must fix: The canal read as a generic European waterfront; repainted from a photograph of the real Caudan canal (Muse Wonder critique of v3, 2026-11-02)
- Motion plan (Muse Spark): The camera remains fixed on the canal overlook. Canal water ripples and shimmers with soft reflections while riverside flowers tremble faintly and thin mist drifts around Le Pouce. The dodo stands steady on the stone quay and slowly turns its head toward the peak, beak lifting slightly, settling into a lingering stare toward Le Pouce across the canal.
  - Revised by: Muse Spark, after reviews: These keyframes were just repainted. Keep the camera nearly locked off (Wan 3.0 invents scenery on camera moves) and put
- 2 earlier takes, made before the keyframe or plan changed (kept on record)
- Take 1 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: The camera remains fixed on the canal overlook. Canal water ripples and shimmers with soft reflections while riverside flowers tremble faintly and thin mist drifts around Le Pouce. The dodo stands steady on the stone quay and slowly turns its head toward the peak, beak lifting slightly, settling into a lingering stare toward Le Pouce across the canal.
- Sound effects (MMAudio, from the shot's video): Canal water laps softly against stone with drifting gull cries and palm fronds rustling in light breeze.

### s08_own_image (37.4–44.6 s)
- Motion plan (Muse Spark): The camera drifts subtly closer as the hanging lamp sways and glows, leaves tremble outside and warm light flickers. The dodo stares fixedly at the painted wall, tilts its head, leans forward, blinks slowly and shifts its weight. Its beak dips slightly as it studies the motionless figurines on the bench.
- Take 1 (wan30): Muse Spark 5/10, painted wall mural dodo animates, blinks and opens beak instead of staying static; bench figurines multiply from four to five and shift positions; live dodo glides left toward bench instead of standing in right third; feet slide without distinct steps, weight shift looks floaty
- Take 2 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: Slow gentle push-in on the dusk shopfront, warm lantern glow steady and soft. The live grey dodo remains planted in the right third, full body visible, staring at the wall. It tilts its head, blinks slowly, dips its beak slightly and leans forward in quiet recognition. The painted mural, small figurines, plants, bench and street stay perfectly still and unchanged.
- Sound effects (MMAudio, from the shot's video): Low market hum buzzes around the shop wall with a hanging lamp creaking faintly and leaves trembling outside.

### s09_see_mountains (43.9–48.6 s)
- Keyframe (Muse Image, 5 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Muted cinematic anime with painterly 2D backgrounds and soft natural light. Wide high shot from a hilltop overlook over Port Louis toward Champ de Mars racecourse and the jagged Moka range with Le Pouce, the dodo in centre third, full body visible standing on hilltop stone overlook looking toward far mountains, city haze below, golden late light, longing mood, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. Use the reference photographs only for the real architecture and layout of this place in Port Louis, Mauritius; repaint everything in the film's style. No legible text, logos or brand names. This repaint must fix: The dodo must face toward Le Pouce and the Moka mountains, looking at them across the city with its back partly to the camera, so the shot reads as longing for the distant forested mountains. Avoid these problems from a previous attempt: Dodo placed in right third instead of centre third
- Motion plan (Muse Spark): The camera orbits slowly left around the dodo as grasses and bushes sway, thin haze drifts over the city and clouds move across the peaks. The dodo stands steady on the rock, turns its head toward the distant mountains, lifts its beak slightly and holds its gaze. Its feathers stir gently in the wind.
- Take 1 (wan30): Muse Spark 4/10, Background morphs away: Le Pouce and racecourse vanish, replaced by triple peaks and new city grid; Camera orbit far too wide, not subtle locked overlook; Dodo stays frozen, no head turn toward mountains or beak lift; Foreground grasses and feather stir minimal, gaze beat feels static
- Take 2 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: Subtle slow push-in from locked hilltop overlook, dodo centered on stone ledge overlooking Port Louis, Champ de Mars racecourse below and Le Pouce peak right retained exactly. Dodo stands steady, slowly turns head right toward distant peaks and lifts beak to hold longing gaze. Gentle wind stirs feathers, grasses sway, thin haze drifts, clouds drift slowly. Golden light, painterly anime, no morphing, no new buildings or mountains.
- Edit: trimmed to 0–4.7 s of the take
- Sound effects (MMAudio, from the shot's video): High hilltop wind whistles through grasses with the city rumbling very far below in soft haze.

### s10_umbrellas_noticed (48.6–54.2 s)
- Keyframe (Muse Image, 4 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Muted cinematic anime with painterly 2D backgrounds and soft natural light. Medium wide shot at Caudan Waterfront under colourful hanging umbrellas over cobbled plaza, the dodo in centre third, full body visible standing on cobbled plaza looking around, small crowd of tourists at distance raising phones with no close-up faces, stone arch gate tower behind, bright dappled light, curious tension, no legible text or logos. Medium-wide: the dodo is small in the centre third with its whole body and feet visible and space around it; in the distance, tourists clearly hold phones up toward it. The people under the umbrellas have all turned toward the dodo: faces, bodies and raised phones point at it, some pointing with a hand. Every dodo must match the character reference sheet exactly: same design, colours and proportions. Use the reference photographs only for the real architecture and layout of this place in Port Louis, Mauritius; repaint everything in the film's style. No legible text, logos or brand names. Avoid these problems from a previous attempt: Background crowd in distance faces away through arch instead of toward dodo; Tourist phones not clearly raised and pointed at dodo; Edge figures cropped by frame on left side
- Motion plan (Muse Spark): The camera holds almost perfectly still, preserving the full plaza composition. Centered on the stones, the dodo stays the same size, shifting its feet and turning its head uncertainly left and right. Overhead the hanging umbrellas sway gently and dappled shadows tremble, palm fronds rustle, while the existing tourists on the right lean in slightly with raised phones toward it.
  - Revised by: Muse Spark, after reviews: This video model (Wan 3.0) exaggerates camera moves: any truck, crane, orbit or wide pull-out makes it invent new buildi
- Take 1 (wan30): Muse Spark 4/10, dodo rotates full body in a spin instead of head-only look-around; tourists' raised phones vanish and morph into clasped hands; crowd does not lean in, curious tension lost
- Take 2 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: Medium-wide locked view of cobbled plaza under hanging umbrellas preserves full composition. In centre, the grey-brown dodo stays in place shifting feet, turning only its head left and right uncertainly. Overhead umbrellas sway gently with trembling dappled light. On the right, the same distant tourists stay facing the dodo, holding phones raised toward it and leaning in slightly.
- Take 3 (wan30): Muse Spark 4/10, camera orbits far right instead of holding still; original tower replaced by new large stone arch gate; distant small tourists become close-up with detailed faces; dodo walks away rather than turning in place looking around
- Sound effects (MMAudio, from the shot's video): Excited crowd murmurs rise in the plaza with rapid phone camera clicks and soft shoe shuffles on stone.

### s11_surrounded (54.2–61.4 s)
- Keyframe (Muse Image, 3 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Close medium shot of the dodo in centre third, full body visible standing on cobbled plaza stones, head upright and looking around, in a circle of blurred visitor legs with blurred phones held above, faces out of frame, colourful umbrella shapes softly blurred above, bright midday light, open daytime atmosphere, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. Use the reference photographs only for the real architecture and layout of this place in Port Louis, Mauritius; repaint everything in the film's style. No legible text, logos or brand names. Ensure blurred phones held above legs are visible around the circle, and visitor figures are cropped at waist and top edge out of frame.
- Motion plan (Muse Spark): The camera stays nearly locked off with only a very faint drift, keeping the full frame and dodo scale unchanged. In the center the dodo freezes, eyes darting side to side, head jerking nervously, then crouching slightly and tilting its beak upward. Around it the existing arms tremble subtly and phones tilt, umbrellas swaying overhead while dappled light shimmers on the stones.
  - Revised by: Muse Spark, after reviews: This video model (Wan 3.0) exaggerates camera moves: any truck, crane, orbit or wide pull-out makes it invent new buildi
- Take 1 (wan30) **(in the film)**: Muse Spark 6/10, dodo freezes but head dart is stiff, no clear crouch and upward look at end; tourist arms and phones flicker, blur and multiply; crowd drifts inward, tightening more than planned
  - Prompt: The camera stays nearly locked off with only a very faint drift, keeping the full frame and dodo scale unchanged. In the center the dodo freezes, eyes darting side to side, head jerking nervously, then crouching slightly and tilting its beak upward. Around it the existing arms tremble subtly and phones tilt, umbrellas swaying overhead while dappled light shimmers on the stones.
- Take 2 (wan30): Muse Spark 5/10, tourist faces fade in from blur breaking no-faces framing; middle-ground phone hands ghost and flicker with motion blur; dodo stays upright and never crouches trapped looking up
- Take 3 (kling26): Muse Spark 5/10, tourist hands and phones smear with ghosted motion blur; dodo stays upright, no final crouch and upward beak tilt; head turn is stiff with no visible eye darting
- Take 4 (kling26): Muse Spark 4/10, tourist arms and phones smear with ghosting and double-images; hand and phone motion flickers fast instead of subtle tremble; dodo never crouches and ends looking down not up; eye-dart and startle not readable
- Sound effects (MMAudio, from the shot's video): Tight crowd shuffling closes in with rising anxious murmurs and many overlapping phone shutters clicking.

### s12_crowd_wide (61.4–66.2 s)
- Keyframe (Muse Image, 10 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. High wide shot looking down on the Caudan Waterfront walkway: rows of colourful umbrellas hang suspended on wires high overhead, exactly as in the reference photograph and the previous shot. A dense ring of tourists stands shoulder to shoulder in a closed circle on the paving, all facing inward, many holding up phones, faces too small to read. In the empty circle at the exact centre stands the dodo, alone, whole body visible, head lowered. Overwhelming, trapped mood. No legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. Use the reference photographs only for the real architecture and layout of this place in Port Louis, Mauritius; repaint everything in the film's style. The last reference image is an earlier shot of the film in the same place: show the same setting, surfaces, light and colours, from this shot's framing, so the cut reads as continuous. No legible text, logos or brand names. This repaint must fix: Muse Wonder: the umbrellas moved from overhead to the ground; they must hang overhead as in s10 and s11. (2026-11-02) Avoid these problems from a previous attempt: Dodo rendered as tiny top-down blob with no visible beak, head lowered pose, legs or wing markings; redraw whole body visible from high angle; Two centre tourists' heads hidden behind low blue umbrella; raise umbrellas so crowd is unobstructed; Tourist ring not tight shoulder-to-shoulder closed circle; close gaps
- Motion plan (Muse Spark): The camera stays locked high above the umbrella courtyard. At center the small dodo lowers its head and bows its neck, shifts one foot then grows still and bowed. Around it the closed crowd circle holds its position with only faint weight shifts and trembling phones, umbrella shadows drift softly across stones and palm fronds stir while it stands motionless alone.
  - Revised by: Muse Spark, after reviews: These keyframes were just repainted. Wan 3.0 exaggerates camera moves and invents scenery, so keep the camera nearly loc
- 1 earlier take, made before the keyframe or plan changed (kept on record)
- Take 1 (wan30): Muse Spark 4/10, camera pulls back and rises instead of staying locked high; dodo becomes too tiny to read head-bow action; crowd and umbrellas appear frozen with no shadow drift or phone tremble
- Take 2 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: Locked high wide overhead view of the umbrella courtyard with no camera move. In the paved center the grey dodo lowers its head and bows its neck, shifts one foot, then stands still and bowed alone. The closed tourist circle holds position facing inward with only faint weight shifts and trembling phones, while umbrella shadows drift softly and palm fronds stir.
- Sound effects (MMAudio, from the shot's video): Broad crowd swell holds in a tense hushed circle with faint whispers shifting under hanging umbrellas.

### s12b_crate_closed (66.2–71.0 s)
- Keyframe (Muse Image, 11 attempts, checked by Muse Spark; chosen by the director): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Close shot on a waterfront walkway under colourful umbrellas hanging overhead: a wooden slatted crate stands on the paving with the dodo standing inside it, whole body visible through the wide gaps between the planks, looking up at the open lid above. Blurred people's legs and raised phones around, no faces. Grey overcast light. The dodo must match the character reference sheet exactly. No legible text or logos.
- Motion plan (Muse Spark): The camera stays fixed on the wooden crate on wet stones. The slatted lid swings down slowly and shuts over the dodo, which flinches, ducks slightly and then lifts its eyes to peer out between the slats. Around it blurred onlookers hold trembling phones steady, overhead umbrellas sway faintly and reflections shimmer across the puddled pavement.
  - Revised by: Muse Spark, after reviews: These keyframes were just repainted. Wan 3.0 exaggerates camera moves and invents scenery, so keep the camera nearly loc
- 1 earlier take, made before the keyframe or plan changed (kept on record)
- Take 1 (wan30): Muse Spark 8/10, no problems noted
- Take 2 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: The camera stays fixed on the wooden crate. Two hands in khaki sleeves reach down from the top of the frame, take hold of the open lid and lower it slowly until it shuts over the dodo, which flinches and ducks, then lifts its eyes to peer out between the slats. Around it blurred onlookers hold their phones up, and the umbrellas overhead sway faintly.
- Choice: director: tied 8/10 with take 1; take 2 shows the keeper's hands closing the lid (Muse Wonder, v3)
- Sound effects (MMAudio, from the shot's video): Wooden slats knock and scrape as the heavy lid swings shut with muffled crowd movement outside.

### s13_crate_harbour (70.3–76.7 s)
- Keyframe (Muse Image, 3 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Muted cinematic anime with painterly 2D backgrounds and soft natural light. Medium shot of the dodo in centre third, full body visible standing on wooden crate floor inside a slatted wooden crate, looking around, Port Louis harbour with container cranes and ships at dusk across water behind, orange-grey sky, sad drifting mood, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. Use the reference photographs only for the real architecture and layout of this place in Port Louis, Mauritius; repaint everything in the film's style. No legible text, logos or brand names. This repaint must fix: The dodo must be visibly confined inside a closed wooden crate with slats in front of it, being carried away, seen through the gaps between the slats; the harbour cranes are glimpsed behind. Avoid these problems from a previous attempt: Dodo placed in right third instead of centre third; Dodo standing on top of crate, not clearly inside slatted crate
- Motion plan (Muse Spark): The camera holds nearly locked off inside the wooden crate, keeping the slats, dodo and harbour view fixed in scale. The dodo stays in place, shifting its feet in straw, turning its head slowly across the water, blinking, then lowering its gaze. Around it harbour water ripples softly, distant light shimmers, thin mist curls around the wood and dusk clouds dim very slightly.
  - Revised by: Muse Spark, after reviews: This video model (Wan 3.0) exaggerates camera moves: any truck, crane, orbit or wide pull-out makes it invent new buildi
- Take 1 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: The camera holds nearly locked off inside the wooden crate, keeping the slats, dodo and harbour view fixed in scale. The dodo stays in place, shifting its feet in straw, turning its head slowly across the water, blinking, then lowering its gaze. Around it harbour water ripples softly, distant light shimmers, thin mist curls around the wood and dusk clouds dim very slightly.
- Edit: trimmed to 0–6.4 s of the take
- Sound effects (MMAudio, from the shot's video): Truck engine drones low with metal harbour clanks and deep ship horns rolling across water through slats.

### s14_park_arrival (76.0–84.4 s)
- Keyframe (Muse Image, 3 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Muted cinematic anime with painterly 2D backgrounds and soft natural light. Medium wide shot of a modern park enclosure entrance with generic blank sign and palms, the dodo in centre third, full body visible standing on gravel path beside an open crate, standing still, keepers legs blurred, evening light, resigned mood, no legible text or logos. The entrance reads as a tourist attraction, not a refuge: a ticket booth, a turnstile, a queue rope and a large blank sign with a cartoon dodo logo over a gate in a chain-link fence. Every dodo must match the character reference sheet exactly: same design, colours and proportions. No legible text, logos or brand names.
- Motion plan (Muse Spark): The camera stays almost perfectly still, preserving the gates, booth, crate and dodo composition unchanged. Beside the open crate the dodo holds its size and position, turning its head slowly to survey the gates, chest rising and falling with heavy breaths. Straw flutters faintly, dust lifts in evening light, palm fronds sway gently while the blurred keeper on the left shifts softly in place.
  - Revised by: Muse Spark, after reviews: This video model (Wan 3.0) exaggerates camera moves: any truck, crane, orbit or wide pull-out makes it invent new buildi
- Take 1 (wan30) **(in the film)**: Muse Spark 8/10, dodo head turn and breathing motion very subtle; keeper snaps from motion blur to sharp standing figure
  - Prompt: The camera stays almost perfectly still, preserving the gates, booth, crate and dodo composition unchanged. Beside the open crate the dodo holds its size and position, turning its head slowly to survey the gates, chest rising and falling with heavy breaths. Straw flutters faintly, dust lifts in evening light, palm fronds sway gently while the blurred keeper on the left shifts softly in place.
- Sound effects (MMAudio, from the shot's video): Iron gates squeak open with gravel crunching under wheels and soft approaching footsteps in muted open air.

### s15_many_behind_glass (84.4–91.4 s)
- Keyframe (Muse Image, 8 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Wide interior shot through a large glass wall into a bare enclosure with a sandy floor, five plump grey-brown dodos inside, each whole body visible and each different: one sitting low near the front, one pecking at the sand, one standing facing away toward the back wall, and two huddled together at the side, at different distances from the glass. In the dark foreground, silhouettes of visitors seen from behind hold up glowing phones toward the glass. Cold artificial light, a shocking reveal. No legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. No legible text, logos or brand names. This repaint must fix: Muse Wonder: five identical dodos in an evenly spaced row looked stamped, not alive. (2026-11-02) Avoid these problems from a previous attempt: Foreground visitor silhouettes are cropped at bottom and sides; Enclosure has logs and grass tufts, should be bare sandy floor
- Motion plan (Muse Spark): The camera remains nearly locked on the glass enclosure holding all five dodos in frame. Each keeps its own pose without marching in step, one sitting blinking, one pecking faintly, one turned away, two touching beaks, with only small weight shifts, head tilts and feather ruffles. Phone screens glow in the foreground, flash flickers softly and reflections shimmer as they stir in place.
  - Revised by: Muse Spark, after reviews: These keyframes were just repainted. Wan 3.0 exaggerates camera moves and invents scenery, so keep the camera nearly loc
- 2 earlier takes, made before the keyframe or plan changed (kept on record)
- Take 1 (wan30) **(in the film)**: Muse Spark 7/10, motion almost frozen with only tiny head shifts; no visible flash flicker across glass; subtle push-in missing, framing feels static
  - Prompt: The camera remains nearly locked on the glass enclosure holding all five dodos in frame. Each keeps its own pose without marching in step, one sitting blinking, one pecking faintly, one turned away, two touching beaks, with only small weight shifts, head tilts and feather ruffles. Phone screens glow in the foreground, flash flickers softly and reflections shimmer as they stir in place.
- Sound effects (MMAudio, from the shot's video): Muffled visitor murmurs blend with awe-filled gasps and endless phone shutters clicking against glass.

### s16_phones_flashes (91.4–93.2 s)
- Keyframe (Muse Image, 1 attempt, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Medium shot of the dodo in centre third, full body visible standing on a sandy floor, large glass wall behind with blurred visitor hands holding phones and soft white light points, no close-up faces, gentle spotlights, calm quiet mood, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. No legible text, logos or brand names.
- Motion plan (Muse Spark): The camera remains almost entirely still, holding the enclosure, glass and dodo scale unchanged. The dodo stays centered in place, flinching slightly, jerking its head toward the glass, blinking rapidly, then hunching its shoulders back and puffing feathers faintly. Behind the glass the existing blurred hands waver holding phones, flashes pulse softly, dust floats through the light and leaves stir faintly on the sand.
  - Revised by: Muse Spark, after reviews: This video model (Wan 3.0) exaggerates camera moves: any truck, crane, orbit or wide pull-out makes it invent new buildi
- Take 1 (wan30): Muse Spark 6/10, visitor faces become sharp and readable, breaking blurred-background brief; leaves fly up airborne in large numbers instead of faint stir on sand; dodo flinch and hunch is very subtle
- Take 2 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: Hold a nearly locked medium shot of the dodo centered full-body on the sandy enclosure floor before the glass wall. The dodo flinches subtly, jerks its head toward the glass, blinks rapidly then hunches back with feathers slightly puffed. Behind glass keep all visitors as soft blurred silhouettes with wavering hands and phones, gentle pulsing white flashes, floating dust, faint leaf tremble on sand, no sharp faces, no camera move.
- Edit: trimmed to 0–1.8 s of the take
- Sound effects (MMAudio, from the shot's video): Rapid camera shutters burst in quick succession with harsh electronic pops amid restless murmurs.

### s17_mural_wall (92.5–96.0 s)
- Keyframe (Muse Image, 2 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Wide shot of the enclosure back wall with the same large faded, peeling painted forest mural as the reference: the same painted trees, flaking paint and stained concrete. The dodo in left third, full body visible, standing on the sandy enclosure floor looking up at the mural, dim cold light with dust in the air, melancholy mood, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. The last reference image is an earlier shot of the film in the same place: show the same setting, surfaces, light and colours, from this shot's framing, so the cut reads as continuous. No legible text, logos or brand names. This repaint must fix: Muse Wonder: the mural's design and condition changed between s17 and s18-s20; it must match s19. (2026-11-02)
- Motion plan (Muse Spark): The camera stays almost perfectly still on the peeling mural wall. The dodo holds scale at left, lifts its head with widening eyes, raises its beak and takes a small hesitant step toward the paint while its gaze rises across the painted trees and tail feathers tremble. Dust motes drift in dim light and a faint glow shifts gently as it stares upward.
  - Revised by: Muse Spark, after reviews: These keyframes were just repainted. Wan 3.0 exaggerates camera moves and invents scenery, so keep the camera nearly loc
- 2 earlier takes, made before the keyframe or plan changed (kept on record)
- Take 1 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: The camera stays almost perfectly still on the peeling mural wall. The dodo holds scale at left, lifts its head with widening eyes, raises its beak and takes a small hesitant step toward the paint while its gaze rises across the painted trees and tail feathers tremble. Dust motes drift in dim light and a faint glow shifts gently as it stares upward.
- Edit: trimmed to 0–3.5 s of the take
- Sound effects (MMAudio, from the shot's video): Hushed indoor room tone breathes softly with distant muffled crowd and faint air hum.

### s18_walk_to_mural (96.0–101.6 s)
- Keyframe (Muse Image, 2 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Wide shot of the enclosure: the dodo, full body visible, walking slowly across the sandy floor toward the same large faded, peeling painted forest mural as the reference, the same painted trees, flaking paint and stained concrete wall. Dim cold light, dust in the air, quiet longing mood, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. The last reference image is an earlier shot of the film in the same place: show the same setting, surfaces, light and colours, from this shot's framing, so the cut reads as continuous. No legible text, logos or brand names. This repaint must fix: The mural changed design between s17 and s18 (Muse Wonder critique of v3, 2026-11-02)
- Motion plan (Muse Spark): The camera stays nearly locked on the weathered mural wall. The dodo walks slowly and steadily left to right across the dusty ground with distinct heavy steps, body swaying and tail bobbing. Dust sparkles in the soft light shaft and dry grasses tremble faintly. It slows, stops close beneath the shaft, plants its feet, lifts its head and gazes intently upward.
  - Revised by: Muse Spark, after reviews: These keyframes were just repainted. Keep the camera nearly locked off (Wan 3.0 invents scenery on camera moves) and put
- 1 earlier take, made before the keyframe or plan changed (kept on record)
- Take 1 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: The camera stays nearly locked on the weathered mural wall. The dodo walks slowly and steadily left to right across the dusty ground with distinct heavy steps, body swaying and tail bobbing. Dust sparkles in the soft light shaft and dry grasses tremble faintly. It slows, stops close beneath the shaft, plants its feet, lifts its head and gazes intently upward.
- Sound effects (MMAudio, from the shot's video): Soft feet shuffle slowly in dry sand with faint rustle echoing lightly off the painted wall.

### s19_press_mural (101.6–108.6 s)
- Keyframe (Muse Image, 2 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Muted cinematic anime with painterly 2D backgrounds and soft natural light. Close medium shot of the dodo in right third, full body visible standing on sandy floor pressing its beak and wing gently against the faded painted forest mural, head tilted into the paint, peeling wall texture and painted mist, single warm light shaft, heartbreaking tender mood, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. No legible text, logos or brand names.
- Motion plan (Muse Spark): The camera holds almost perfectly still, keeping the peeling wall and dodo scale fixed. On the right the dodo stays in place, leaning forward to press its beak softly against the paint, tilting its head to rest there, wing shifting slightly as its body settles and eyes half close with slowing breath. Dust drifts down faintly in the light shaft, loose flakes tremble and the painted glow holds steady.
  - Revised by: Muse Spark, after reviews: This video model (Wan 3.0) exaggerates camera moves: any truck, crane, orbit or wide pull-out makes it invent new buildi
- Take 1 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: The camera holds almost perfectly still, keeping the peeling wall and dodo scale fixed. On the right the dodo stays in place, leaning forward to press its beak softly against the paint, tilting its head to rest there, wing shifting slightly as its body settles and eyes half close with slowing breath. Dust drifts down faintly in the light shaft, loose flakes tremble and the painted glow holds steady.
- Sound effects (MMAudio, from the shot's video): Deep near-silence holds with only a faint dusty scrape as feathers brush the peeling painted wall.

### s21_sleep_again (107.9–115.9 s)
- Keyframe (Muse Image, 2 attempts, checked by Muse Spark): Muted cinematic anime with painterly 2D backgrounds and soft natural light. Medium shot mirroring the opening, the dodo in centre third, full body visible, crouching low on the sandy enclosure floor to sleep, head lowered and eyes closed, in front of the same faded, peeling painted forest mural wall as the reference: the trees are flat paint on a cracked concrete wall, with flakes of paint on the floor and no real plants anywhere. One dim warm light shaft fading into dusk, dark corners, quiet heartbreaking mood, no legible text or logos. Every dodo must match the character reference sheet exactly: same design, colours and proportions. The last reference image is an earlier shot of the film in the same place: show the same setting, surfaces, light and colours, from this shot's framing, so the cut reads as continuous. No legible text, logos or brand names. This repaint must fix: Author (2026-11-02): the real forest behind the sleeping dodo was a mistake; it must be the enclosure, in front of the same faded, peeling painted mural wall as s19, so the ending matches the end card. (Muse Wonder flagged it too.)
- Motion plan (Muse Spark): The camera holds locked off. The dodo lies asleep on the sandy floor against the flat, peeling painted wall, its body rising and falling in slow, deep breaths; once it nestles its beak a little deeper and its tail feathers settle. Dust drifts in the single warm light shaft, which slowly fades as the corners darken. The wall and the painted trees stay perfectly still.
  - Revised by: director (author's direction 2026-11-02): enclosure, not a real forest; the dodo is already asleep
- 1 earlier take, made before the keyframe or plan changed (kept on record)
- Take 1 (wan30) **(in the film)**: Muse Spark 8/10, no problems noted
  - Prompt: The camera holds locked off. The dodo lies asleep on the sandy floor against the flat, peeling painted wall, its body rising and falling in slow, deep breaths; once it nestles its beak a little deeper and its tail feathers settle. Dust drifts in the single warm light shaft, which slowly fades as the corners darken. The wall and the painted trees stay perfectly still.
- Sound effects (MMAudio, from the shot's video): Warm still air hangs quietly with faint dust drifting and a very soft room settle fading toward silence.

### s22_end_card (115.9–124.0 s)
- End card: "The dodo came back. Its home didn't.", typeset by the software.

## Shots made but left out of the final cut

- s20_alone_vast. Their records are kept in the project files.

## Third-party material

# Credits and licences

Reference photographs used as visual references for keyframe generation. They
are repainted by Muse Image in the film's style and never appear as-is. The
photo files themselves are not in this repository.

| File (refs/port_louis/) | Shows | Author | Source | Licence |
|---|---|---|---|---|
| unsplash_street_2C7ATUy4XQ0.jpg | Downtown street | Talat Munshi | https://unsplash.com/photos/2C7ATUy4XQ0 | Unsplash License |
| unsplash_signalhill_IEheuRq4SyQ.jpg | City from Signal Hill | Fabien TWB | https://unsplash.com/photos/IEheuRq4SyQ | Unsplash License |
| unsplash_chinatown_G0D9rRvn-Uk.jpg | Chinatown gate | Ekaterina Antonova | https://unsplash.com/photos/G0D9rRvn-Uk | Unsplash License |
| unsplash_harbour_WX7iLclCnVI.jpg | Harbour cranes at dusk | Yannick Sookree | https://unsplash.com/photos/WX7iLclCnVI | Unsplash License |
| unsplash_champdemars_R1Dfnqiajqo.jpg | Champ de Mars, Le Pouce and the Moka range | Oosman Exptal. | https://unsplash.com/photos/R1Dfnqiajqo | Unsplash License |
| wikimedia_caudan_cc0.jpg | Caudan Waterfront entrance | Benoît Prieur | https://commons.wikimedia.org/wiki/File:Caudan_Waterfront,_February_2020.jpg | CC0 1.0 |
| Private photos (not in the repository) | Caudan Waterfront umbrella walkway and canal | A friend of the author | Private | Used with the photographer's permission (2026-11-02) |

Photos contributed by a friend of the author (Caudan Waterfront) are used with their permission.

## Sound

All sound in the film is AI-generated through fal.ai, which lists each model as licensed for commercial use
(checked 2026-11-02):

- Score: ElevenLabs Music (`fal-ai/elevenlabs/music`)
- Per-shot sound effects: MMAudio v2 (`fal-ai/mmaudio-v2`)
- The dodo's calls: ElevenLabs Sound Effects v2 (`fal-ai/elevenlabs/sound-effects/v2`)

The recordings below were used only by the earlier Blender version of the film. They are not in the final film.

| File (assets/audio/) | What | Author | Source | Licence |
|---|---|---|---|---|
| birdsong_blackbird_ccby.ogg | Common blackbird song | Diana Tudor (via xeno-canto 1059970) | https://commons.wikimedia.org/wiki/File:Common_Blackbird_song_(Turdus_merula).ogg | CC BY 4.0 |
| cafe_crowd_cc0.ogg | Café ambience, people chatting | Marble Toast | https://commons.wikimedia.org/wiki/File:Cafe_ambiance.ogg | CC0 1.0 |
| synth_*.wav | Traffic, room tone, wind, water, shutter clicks | Generated by Cutaway (cutaway/sound.py) | — | Original |

## Fonts

- EB Garamond (end cards), The EB Garamond Project Authors, SIL Open Font License 1.1 (assets/fonts/OFL.txt)

## Software and models

- Meta Muse Image, Muse Spark, Muse Wonder, SAM 3.1 (Meta Model API)
- Video: Wan 3.0 image-to-video (`alibaba/wan-3.0/image-to-video`) and Kling 2.6 Pro
  (`fal-ai/kling-video/v2.6/pro/image-to-video`), via fal.ai, both listed as licensed for commercial use
- Real-ESRGAN, model realesr-animevideov3 (BSD-3-Clause), for the 1080p upscale
- Blender (GPL; earlier version of the film only), ffmpeg (LGPL/GPL)
- meta-sam-parser (Meta), Pillow, NumPy, httpx, python-dotenv
