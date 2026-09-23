---
name: seedance_video_deconstructor
version: "0.1.0"
description: Deconstruct short-form narrative videos, transcripts, hook topics, or video URLs into a 1:1 scene-by-scene breakdown, viral retention cut sheet, and production-ready Seedance 2.5 prompt bundle with direct CLI video generation.
argument-hint: "<video-url-transcript-or-topic> [product-bridge]"
allowed-tools: Bash, Read, AskUserQuestion
homepage: https://github.com/bradautomates/claude-video
repository: https://github.com/bradautomates/claude-video
author: bradautomates
license: MIT
user-invocable: true
---

# /seedance_video_deconstructor

Transform any short-form video (TikTok, Instagram Reel, YouTube Short), video transcript, or narrative topic into a high-retention 1:1 breakdown, production-ready **Seedance 2.5** generation package, and execute direct CLI video generations.

This skill reverse-engineers viral short-form storytelling frameworks (e.g. Dylan Page's "absurd history pattern-interrupt" model), segments the video into modular 3–6 second shots, engineers exact Seedance 2.5 generative video prompts, and connects directly to the **Higgsfield CLI (`higgsfield-generate`)** to render AI video clips locally via CLI.

---

## Resolve `SKILL_DIR`

Every bundled script under `scripts/` can be executed locally. Set `SKILL_DIR` to the directory containing this `SKILL.md`:

```bash
SKILL_DIR="<absolute path of directory containing this SKILL.md>"
```

---

## When to Use

- User pastes a short-form video URL (TikTok, Instagram Reels, YouTube Shorts) and asks to recreate, deconstruct, or adapt it using Seedance 2.5.
- User provides a raw video transcript or narrative topic and wants a shot-by-shot production plan.
- User wants to convert an organic viral video into a UGC-style or hook-driven ad with an integrated product/brand bridge.
- User wants to **generate the actual AI video clips from the command line** using the `higgsfield` CLI and `seedance_2_5` model.
- User requests ready-to-run Seedance 2.5 prompt packs, CSV cut sheets, or an automated production zip package.

---

## Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `topic_or_transcript` | `string` | **Yes** | — | Raw transcript, narrative story, news hook, or video URL. |
| `target_duration` | `integer` | No | `45` | Total target video length in seconds (typically 30–60s). |
| `format_ratio` | `string` | No | `"9:16"` | Target aspect ratio (`"9:16"`, `"16:9"`, or `"1:1"`). |
| `ad_transition` / `product_bridge` | `string` | No | `None` | Optional product or brand hook bridge to inject at the narrative turning point. |

---

## Execution Rules & Framework

### 1. Pacing Enforcement
- **Modular Shot Length:** Segment into rapid modular shots of **3 to 6 seconds** each.
- Never generate a single monolithic 30–60 second video prompt. AI video generators maintain superior temporal coherence and motion physics in 4–6s bursts.
- Fast visual cuts every 2 to 4 seconds maintain maximum audience retention.

### 2. Viral Hook Framework (First 3 Seconds)
- Identify or construct the primary **Pattern Interrupt** in the first 3 seconds:
  - *Absurd Historical Fact:* An eyebrow-raising historical law or bizarre historical job.
  - *High-Contrast Juxtaposition:* Normal situation paired with an unexpected visual.
  - *Visual Shock / Curiosity Gap:* Macro close-up or striking action that forces the viewer to pause scrolling.

### 3. Seedance 2.5 Prompt Formula
Every video prompt generated **MUST** strictly adhere to this standardized formula:

```text
[Shot Type / Lens] + [Era & Film Stock / Aesthetic] + [Core Subject Action] + [Lighting & Environment] + [Camera Motion] + [--ar <ratio>] + [--motion <speed>]
```

- **Shot Type / Lens:** Macro extreme close-up, medium portrait shot, wide establishing tracking shot, 35mm lens, anamorphic.
- **Era & Film Stock:** 1920s archival documentary, silver-halide grain, 1946 Technicolor 3-strip, vintage newsreel monochrome.
- **Core Subject Action:** Clear kinetic verb describing characters and objects in motion (avoid static poses).
- **Lighting & Environment:** Harsh sunlight, dramatic chiaroscuro shadow play, flashing camera bulbs, sandy beach boardwalk.
- **Camera Motion:** Slow push-in, rapid lateral pan, handheld follow, comedic slow zoom.
- **CLI Parameter Flags:**
  - `--ar 9:16` (vertical mobile video)
  - `--motion 1-10` (motion intensity: 2-3 for portraits, 4-5 for walking/dialogue, 6-8 for montages/action)

### 4. Seedance 2.5 Generation Settings & Workflow
- **Mode:** Reference-to-Video (`omni_reference`) or Text-to-Video (`t2v`).
- **Reference Control Strength:** Set reference strength to **`0.75`** for historical/character accuracy without freezing motion.
- **Multi-Modal References (`@Image_Ref1`):** Pin primary character/uniform reference images to preserve consistent identity across shots.
- **Native Audio & Foley Sync:** Enable Seedance 2.5's Native Audio Sync to generate synchronized ambient audio (waves, crowds, camera clicks) directly on the prompt pass.
- **Region-Level Inpainting:** Note any areas likely to produce AI artifacts (modern sunglasses, distorted fingers, synthetic fabrics) for touchup with the Region-Level Editing brush.

### 5. Post-Production Retention Layer (CapCut / Premiere)
Always provide explicit post-production instructions:
1. **Talking-Head Picture-in-Picture (PiP):** Narration/reaction footage placed green-screened or masked in the lower third, pointing up at the generated Seedance visuals.
2. **Kinetic Captions:** High-contrast typography (`TheBoldFont` or `Montserrat Black`), 1 to 3 words at a time, center-screen, with active color flashes (`#FFE600` yellow and vibrant red).
3. **Sound Design Stacking:**
   - *Background Bed:* Low pulsating synth or ambient mystery music ducked by **-18 dB** under narration.
   - *Micro-SFX:* Subtle camera shutter snap on every visual cut; mechanical clicks or risers on key punchlines.

---

## Direct CLI Video Generation (via Higgsfield & Seedance 2.5)

To generate actual video clips directly via CLI, use the bundled `generate_video.py` runner or direct `higgsfield` commands:

### 1. Direct CLI Generation
```bash
# Text-to-Video generation (720p or 1080p, 9:16 vertical)
higgsfield generate create seedance_2_5 \
  --prompt "Cinematic 1920s archival documentary footage, authentic black-and-white 35mm film grain. Stern police officer kneeling on the beach with measuring tape. Slow push-in." \
  --aspect_ratio 9:16 \
  --duration 5 \
  --resolution 720p \
  --mode t2v \
  --wait

# Reference-to-Video (R2V) generation with reference image
higgsfield generate create seedance_2_5 \
  --prompt "Cinematic macro shot of hands pulling tape measure taut." \
  --image ./reference_images/ref1_beach_censor_1922.jpg \
  --mode omni_reference \
  --aspect_ratio 9:16 \
  --duration 5 \
  --resolution 720p \
  --wait
```

### 2. Automated Manifest Batch Runner (`scripts/generate_video.py`)
```bash
# Preview batch commands without consuming credits
python3 "${SKILL_DIR}/scripts/generate_video.py" --manifest configs/seedance_prompts.json --dry-run --all

# Generate a specific shot from manifest
python3 "${SKILL_DIR}/scripts/generate_video.py" --manifest configs/seedance_prompts.json --shot shot_01_hook

# Generate all shots in batch
python3 "${SKILL_DIR}/scripts/generate_video.py" --manifest configs/seedance_prompts.json --all
```

> [!NOTE]
> **Security & Permissions Notice:**
> The `higgsfield-generate` tools execute shell commands to interact with the Higgsfield CLI. Review security guidelines at `https://skills.sh/higgsfield-ai/skills` before executing extensive unattended generation pipelines.

---

## Output Structure

When executing this skill, always produce the following 4 sections:

### 1. 1:1 Scene-by-Scene Timeline Table
| Timestamp | Shot ID | Visual Content Description | Spoken Script / Voiceover | On-Screen Text & VFX | SFX / Foley Cues |
|---|---|---|---|---|---|
| `0:00 – 0:04` | `shot_01_hook` | ... | ... | ... | ... |

### 2. Seedance 2.5 Prompt Pack
For each shot, provide the copy-pasteable prompt block formatted with the formula, duration, and reference image flags.

### 3. Execution Payload JSON
A structured, valid JSON object containing global settings and the shot array for automated pipeline execution.

### 4. CapCut / Premiere Assembly Recipe & Packaging
Editing timeline instructions, font specifications, audio ducking levels, and script execution instructions to generate the complete `.zip` production bundle.

---

## Reference Case Study: Dylan Page "Bikini Police" (1:1 Breakdown)

Use this benchmark example from the Dylan Page viral short (*"Being a Bikini police officer is wild!"*):

### 1. Scene-by-Scene Narrative Breakdown

| Timestamp | Shot ID | Visual Content | Audio / Dylan Page Script | On-Screen Text & VFX | SFX & Foley |
|---|---|---|---|---|---|
| **0:00 – 0:04** (Hook) | `shot_01_hook` | Dylan Page close-up punch-in, cutting immediately to the iconic black-and-white scene: a stern 1920s police officer kneeling on the beach with a measuring tape against a woman's leg. | *"Being a bikini police officer was actually a real 9-to-5 job... and it was just as unhinged as you think."* | **"BIKINI POLICE WAS A REAL JOB?!"** (Bold yellow/white, kinetic drop-in) | Subtle camera shutter snap, tape measure click |
| **0:04 – 0:10** (The Rule) | `shot_02_rule` | Slow zoom on vintage beachgoers. Uniformed patrol officers walking through crowds of sunbathers carrying wooden rulers and fabric tape measures. | *"Back in the 1920s through the 1950s, modesty laws on public beaches were insanely strict. Your bathing suit could not be more than a few inches above the knee."* | Highlighted keywords: **"STRICT LAWS"**, **"MEASURING TAPES"** | Ocean waves, beach crowd murmur |
| **0:10 – 0:17** (The Absurdity) | `shot_03_macro` | Close-up macro shot of a measuring tape being pulled taut against a wool swimsuit hem. Officer shaking his head strictly. Surrounding beachgoers whispering. | *"Special beach censors and 'bathing police' literally patrolled the sand with tape measures to make sure women weren't showing 'too much thigh'."* | **"MEASURING THIGHS ON THE BEACH"** (Red warning box) | Tape measure click, quiet whispering |
| **0:17 – 0:24** (The Consequence) | `shot_04_arrest` | Black-and-white shot of two officers physically escorting a protesting woman off the beach boardwalk, with onlookers staring. | *"If you were even two inches too short? You didn't just get a warning. You got hit with massive fines or literally dragged straight to jail right off the sand."* | Red stamp effect: **"ARRESTED"** | Heavy footstep thud, crowd gasps, whoosh |
| **0:24 – 0:33** (1946 Turning Point) | `shot_05_bikini_reveal` | Black-and-white glamour shot of a 1946 Parisian runway/poolside. A woman reveals a two-piece bikini; photographers' flashbulbs explode. | *"Then in 1946, French engineer Louis Réard dropped the modern bikini—named after Bikini Atoll nuclear tests because he knew it would cause an explosion. Models literally refused to wear it."* | Vintage newsprint headline: **"TOO SCANDALOUS"** | Multiple flashbulb pops and sizzles |
| **0:33 – 0:42** (Global Backlash) | `shot_06_backlash` | Fast montage: The Vatican, Italian coastline beach bans, vintage Spanish police signs reading "Prohibido". | *"Spain, Italy, and France banned it instantly. The Vatican officially declared it sinful. But tourism exploded, society pushed back, and the beach police quietly vanished."* | Rapid map animations / X stamps across Italy & Spain | Rapid paper rustle, church bell chime |
| **0:42 – 0:48** (Comedic Outro) | `shot_07_punchline` | Cut back to the officer on his knees with the tape measure, slow comedic zoom on his deadpan face. | *"Imagine having to tell your grandkids that your government job was measuring swimsuits with a ruler. Follow for more crazy history."* | **"WORST JOB IN HISTORY?"** + Follow button pulse | Comedic violin pluck or record scratch |

---

### 2. Seedance 2.5 Prompts

- **Shot 1 (The Beach Police Hook, 0:00 – 0:04):**
  `Cinematic 1920s archival documentary footage, authentic black-and-white 35mm film grain, high contrast. A serious, stern male police officer kneeling on the sand, measuring the hemline of a woman's swimsuit with a wooden ruler. Beachgoers watching in the background. Wide establishing shot, slow push-in. --ar 9:16 --motion 4`

- **Shot 2 (Macro Measuring Detail, 0:04 – 0:10):**
  `Extreme close-up macro shot, vintage 1930s monochrome photography. A weathered pair of hands holding a yellowed fabric measuring tape against the edge of a wool bathing suit hem on a sandy beach. Shallow depth of field, subtle hand tremble. --ar 9:16 --motion 3`

- **Shot 3 (Beach Boardwalk Escort / Arrest, 0:10 – 0:17):**
  `Mid-shot tracking scene, vintage 1940s newsreel film aesthetic, authentic silver-halide grain. Two uniformed patrolmen firmly escorting an indignant woman in a vintage swimsuit across a crowded boardwalk. Bystanders turn and whisper. --ar 9:16 --motion 5`

- **Shot 4 (1946 Paris Fashion Reveal, 0:17 – 0:24):**
  `1946 Parisian fashion presentation at Piscine Molitor public swimming pool, vintage Technicolor 3-strip aesthetic. A glamorous French model poses courageously in a revolutionary newspaper-printed two-piece bikini as vintage press photographers with flashbulb cameras burst flashes. --ar 9:16 --motion 4`

- **Shot 5 (Global Backlash & Newspaper Montage, 0:24 – 0:33):**
  `Cinematic macro b-roll, high contrast black-and-white. Rapid cinematic pan across authentic vintage 1940s newspaper headlines reading 'SCANDALOUS' and 'BANNED', with dramatic shadow play and falling newspaper clippings. --ar 9:16 --motion 6`

- **Shot 6 (Comic Weary Officer Reaction, 0:33 – 0:42):**
  `Medium close-up portrait, 1920s archival documentary aesthetic. A vintage beach patrol officer looking directly into the lens with an exhausted, deadpan, bewildered expression, holding a measuring tape limply. Subtle comedic slow zoom-in. --ar 9:16 --motion 2`

---

## Bundled Automation Scripts

Located in: [`skills/seedance_video_deconstructor/scripts/`](file:///Users/malickdes/AIWORKSPACE/claude-video/skills/seedance_video_deconstructor/scripts/)

- `python3 scripts/deconstruct.py`: Run CLI deconstruction, schema generation, or JSON payloads.
- `python3 scripts/build_package.py`: Automatically creates production package directories, prompt manifests, CSV cut sheet, downloads archival reference images, and creates `.zip` bundles.
- `python3 scripts/generate_video.py`: Directly invokes Higgsfield CLI (`seedance_2_5`) for ad-hoc prompts or batch manifest generation.
