---
name: character_design
version: "0.2.0"
description: Dynamic AI Character Director & Stylist. Design, style, and generate photorealistic character looks with permanent identity preservation and animate approved looks into Seedance 2.5 video clips. Driven by creative briefs and scene context, with optional inspirational presets from https://daily-character-studio.higgsfield.app/.
argument-hint: "[creative-brief-or-scene-description] [--mode new|hair|outfit|animate] [--approved-image <path>]"
allowed-tools: Bash, Read, AskUserQuestion
homepage: https://github.com/bradautomates/claude-video
repository: https://github.com/bradautomates/claude-video
author: bradautomates
license: MIT
user-invocable: true
---

# /character_design

Act as an **AI Character Director & Stylist** to design, style, and generate photorealistic character looks with permanent identity preservation, and animate approved looks into cinematic **Seedance 2.5 / 2.0** video clips.

Inspired by [Daily Character Studio](https://daily-character-studio.higgsfield.app/), this skill replaces rigid, deterministic presets with an **intelligent, context-driven character styling engine**. You can provide any scene idea, script snippet, emotional beat, or aesthetic brief, and the skill will dynamically engineer the wardrobe, hairstyle, environment, lighting, optics, and video animation motion—while guaranteeing zero facial drift.

---

## Resolve `SKILL_DIR`

Every bundled script under `scripts/` can be executed locally. Set `SKILL_DIR` to the directory containing this `SKILL.md`:

```bash
SKILL_DIR="<absolute path of directory containing this SKILL.md>"
```

---

## When to Use

- **Script-to-Character Directing:** You have a video script, TikTok/Reels hook, or commercial storyboard and need to design a bespoke character look specifically matching that narrative context.
- **Narrative Wardrobe Continuity:** You need to transition one character across distinct story beats (e.g. morning routine → intense boardroom presentation → workout cooldown → evening dinner) while keeping their facial features 100% identical.
- **Still-to-Video Animation:** You have an approved look image and need to animate it into a Seedance 2.5 clip starting from that exact frame (`start_image`).
- **Dynamic Multi-Scene Wardrobe Packs:** You want a 5-scene wardrobe pack generated from a story synopsis for direct handoff to `/seedance_video_deconstructor` or CapCut.

---

## Core Architecture: Dynamic Look Synthesis + Identity Anchor

The skill operates on a strict two-stage contract:

### 1. The Permanent Identity Anchor (Anti-Drift)
The model anchors on a permanent facial reference sheet (`41caaf52-6a98-47f1-ac60-7e17f94a852a` by default, or the user's custom character). The prompt explicitly commands the generator that facial geometry, eye shape, nose bridge, smile line, skin undertones, apparent age, and physical proportions are immutable.

### 2. The 7-Point Cohesive Styling Blueprint
Rather than picking a generic preset, the agent dynamically synthesizes:
1. **Hairstyle:** Cut, texture, natural flyaways, and volume suited to the scene (e.g., *Tousled messy bun with loose tendrils* for late night vs *Sleek low ballet chignon* for corporate).
2. **Wardrobe & Textiles:** Specific garments, tailoring, texture, and color palette (e.g., *Tailored double-breasted charcoal wool blazer over ivory silk camisole*).
3. **Environment & Atmosphere:** Specific architectural textures, practical light sources, depth, and spatial layers.
4. **Kinetic Activity:** Believable, natural micro-actions (e.g., *Cradling warm ceramic mug, looking up from laptop* rather than stiff poses).
5. **Cinematic Lighting:** Color temperature, direction, key/fill ratios, and rim light (e.g., *Warm 2800K low-angle golden hour rim light* vs *Soft overcast daylight*).
6. **Camera Lens & Optics:** Focal length and depth of field (e.g., *85mm f/1.4 portrait prime with creamy bokeh* vs *35mm environmental wide*).
7. **Micro-Expressions:** Emotional subtlety (e.g., *Quietly confident smirk with tired eyes* vs generic smile).

---

## The 4 Generation Modes

| Mode | Purpose | Inputs Required | Output |
|---|---|---|---|
| `new` | Full lifestyle look synthesized from brief | Identity reference + creative brief | Photorealistic 2K image |
| `hair` | Change hairstyle only | Identity ref + approved look + new hair | 2K image with identical clothes & setting |
| `outfit` | Change wardrobe only | Identity ref + approved look + new outfit | 2K image with identical hair & setting |
| `animate` | Animate look into video | Approved look image + motion direction | 720p/1080p Seedance 2.5 video clip |

---

## Canonical Prompt Formulas

### 1. Dynamic Look Generation Formula (`new`)
```text
Create one photorealistic cinematic photograph.
IDENTITY: The first reference is the permanent identity source. Preserve the exact same recognizable facial geometry, eyes, nose, smile, skin tone, apparent adult age, and body proportions. Reference sheets depict ONE person: output only one person in one photograph, never a collage. Hair and wardrobe are changeable, not identity.
Hairstyle: [Synthesized Hairstyle]. Outfit: [Synthesized Wardrobe]. Location: [Synthesized Environment]. Activity: [Kinetic Micro-Action]. Framing: [Framing]. Expression: [Micro-Expression]. Lighting & Atmosphere: [Lighting Setup]. Camera Lens: [Lens & Optics]. Accessories & Details: [Props & Accents].
Creative Direction: [Scene Context / Brief]
Natural human skin texture, believable micro-shadows, photographic grain. No labels, no text overlays, no contact sheet, no watermark, no digital airbrushing.
```

### 2. Targeted Inpainting / Edit Formula (`hair` or `outfit`)
```text
Edit only the [hairstyle / clothing] of the final reference image. Preserve its [remaining elements], pose, background, lighting, and framing.
IDENTITY: The first reference is the permanent identity source. Preserve the exact same recognizable facial geometry, eyes, nose, smile, skin tone, apparent adult age, and body proportions. Reference sheets depict ONE person: output only one person in one photograph, never a collage. Hair and wardrobe are changeable, not identity.
[Hairstyle: ... / Outfit: ...] Keep all other details (outfit, pose, lighting, background) identical to the final reference.
Natural human skin texture, believable micro-shadows, photographic grain. No labels, no text overlays, no contact sheet, no watermark.
```

### 3. Seedance 2.5 Video Motion Formula (`animate`)
```text
Use the approved image as the exact first frame. [Natural breathing, gentle head movement, expressive speech or subtle movement matching scene activity]. Continuous camera, steady focal distance, believable micro-expressions, no morphing, no cuts.
```

---

## Bundled Automation Scripts (`scripts/character_studio.py`)

All operations support freeform creative briefs and custom overrides:

### 1. Compile & Preview Prompt from a Freeform Brief
```bash
# Preview dynamic look synthesis from a creative scenario
python3 "${SKILL_DIR}/scripts/character_studio.py" prompt \
  --brief "An exhausted tech founder in a server room at 3am fixing a critical bug under blue terminal glow"

# Preview video motion prompt for an approved look
python3 "${SKILL_DIR}/scripts/character_studio.py" prompt \
  --mode animate \
  --approved-image "./look_founder.png" \
  --brief "She rubs her temples, leans forward to review code, and lets out a relieved sigh" \
  --duration 5
```

### 2. Generate Look Image via Higgsfield CLI
```bash
# Dry-run preview
python3 "${SKILL_DIR}/scripts/character_studio.py" generate-look \
  --brief "Artisan ceramist in a sun-drenched pottery studio shaping clay on a potter's wheel" \
  --dry-run

# Real generation (GPT Image 2.5 / 2K)
python3 "${SKILL_DIR}/scripts/character_studio.py" generate-look \
  --brief "Artisan ceramist in a sun-drenched pottery studio shaping clay on a potter's wheel"
```

### 3. Edit Hairstyle or Outfit on an Approved Look
```bash
# Change hairstyle on an existing approved image while locking clothes and environment
python3 "${SKILL_DIR}/scripts/character_studio.py" edit-look \
  --edit-type hair \
  --approved-image "./approved_ceramist.png" \
  --hair "Tousled messy top-knot with loose wispy tendrils" \
  --dry-run
```

### 4. Animate Approved Look into Seedance 2.5 Video
```bash
# Animate approved image with context-aware motion
python3 "${SKILL_DIR}/scripts/character_studio.py" animate-look \
  --approved-image "./approved_ceramist.png" \
  --brief "Hands gently shape spinning clay, eyes focused and calm, subtle breathing, warm sunbeams" \
  --duration 5 \
  --aspect-ratio 9:16
```

### 5. Generate a Dynamic Multi-Scene Story Pack
```bash
# Synthesize a 5-scene narrative wardrobe pack matching a video story arc
python3 "${SKILL_DIR}/scripts/character_studio.py" pack \
  --brief "Day in the life of an investigative journalist uncovering a story in rainy Chicago" \
  --output "journalist_story_pack.json"
```

### 6. Inspirational Preset Archetypes (Optional)
If you want quick starting templates, browse the built-in archetypes:
```bash
python3 "${SKILL_DIR}/scripts/character_studio.py" list-presets
```

---

## Downstream Pipeline Handoff

Once character looks are synthesized or animated, hand off directly to:

1. **Multi-Shot Narrative Video (`/seedance_video_deconstructor`):**
   - Provide the generated wardrobe pack or approved look image URLs as `@Image_Ref1` in the deconstructor cut sheet.
   - Every scene in the short-form video will maintain 100% character identity.
2. **Viral Voiceovers (`/dylan_hook_voiceover` or `/auk_voiceover`):**
   - Generate high-retention audio for the character's dialogue or narrative voiceover.
3. **Timeline Assembly (`/capcut_video_assembler`):**
   - Import the Seedance 2.5 video clips + generated voiceovers directly into CapCut with kinetic captions.
