# AI Creation Statement

China-Mauritius AI Storytelling and AI Video Clip Competition 2026, Generative AI Video Bootcamp

## 1. Participant information
- **Team name:** Proxima
- **Team leader:** Mikhil Naika
- **Institution:** Middlesex University
- **Participants:** 1. Mikhil Naika  2. Seeya Awotar  3. Yorvan Rengasamy

## 2. Project information
- **Title of video:** 55 Spring Festivals (五十五个春节)
- **Duration:** 3 min 59 s (3:58.8, including title and credits)
- **Date of creation:** 21/11/2026

## 4. AI tools and technologies used

| Tool / Software | Purpose | Online/Offline |
|---|---|---|
| Meta Muse Image (Meta Model API) | Character sheets and all keyframe images (about 565 images, made during the bootcamp) | Online |
| Meta Muse Spark (Meta Model API) | Checked every keyframe and video take, rewrote weak prompts, wrote the music composition plan | Online |
| FLUX 3 Max, Black Forest Labs (via fal.ai) | Image-to-video and keyframes-to-video: animated every shot and generated its sound effects | Online |
| ElevenLabs Music (via fal.ai) | The film's music score | Online |
| ElevenLabs Eleven v3 text-to-speech (via fal.ai) | All English dialogue and narration | Online |
| Claude (Anthropic) | Wrote the pipeline code and the image and video prompts with the team; adapted the team's comic into a shot list; translated the Chinese subtitles | Online |
| Cutaway (our own Python pipeline) | Runs and logs every AI call, its prompt and its cost | Offline |
| ffmpeg | Non-AI editing: cutting, ordering, flash transitions, captions and subtitles, audio mixing, MP4 export | Offline |

**Reference image (licensed, used only as an input reference, not shown in the film):** "Chinatown gate, Port Louis" by Ekaterina Antonova, Unsplash (https://unsplash.com/photos/G0D9rRvn-Uk), Unsplash License. It was used as a reference for the Chinatown lion-dance keyframe.

**Audio:** every sound was AI-generated during the bootcamp: FLUX 3 Max (sound effects), ElevenLabs (score and voice lines). No external music or sound effects were used.

## 5. Production breakdown

| Component | AI-generated (%) | Manual editing (%) |
|---|---|---|
| Visuals / Animation | 95 % | 5 % (team art direction and critique, trims, flash transitions, captions) |
| Sound / Music | 90 % | 10 % (team choice of lines and levels, mixing) |
| Script / Text | 40 % | 60 % (the story, characters and dialogue come from the team's own stage-1 comic; AI adapted it into shots and translated the Chinese subtitles) |
| Final editing | 20 % | 80 % (edited in ffmpeg, a non-AI tool, from the team's notes; the editing scripts were written with Claude) |

## 6. Originality declaration
- ☑ All content was created during the bootcamp. Every image, clip, sound and the music. The story, characters and dialogue are from the team's own stage-1 comic, and none of the comic's artwork was used.
- ☑ No copyrighted or pre-existing footage, music or images were used. Except one licensed Unsplash reference photo (see above). It was used only as an input reference and does not appear in the film.
- ☑ All AI tools used have been disclosed above.
- ☑ The work does not contain harmful, offensive or culturally insensitive content.
- ☑ The team is the sole author of this video and grants the organisers non-commercial rights.

## Spend
- fal.ai: $32.68 of the $60 pooled by the team (FLUX 3 Max $30.26, ElevenLabs Music $2.39, ElevenLabs TTS $0.02). A hard cap in the code ($58, with video limited to $50) was checked against fal's real bill after every clip.
- Meta Model API (Muse Image and Spark): about $11.50 of hackathon credit, about 1,150 calls.
- Every prompt, model, take and cost is logged in `generation_log.jsonl` and `films/bootcamp/shots/*/state.json`.
