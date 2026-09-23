---
name: hyperframe
version: "1.1.0"
description: "Turn mobile & web app screenshots into animated 9:16 vertical full-screen phone demo videos (or 3D device mockups) with kinetic UI motion, audio sync, and MP4 rendering. Focuses purely on rendering the clean phone demo part."
argument-hint: "--screenshots <path1,path2...> [--audio <path>] [--demo-only] [--output-dir <path>] [--render]"
allowed-tools: Bash, Read, Write, AskUserQuestion
homepage: https://github.com/bradautomates/claude-video
repository: https://github.com/bradautomates/claude-video
author: bradautomates
license: MIT
user-invocable: true
---

# /hyperframe — App Screenshot to HyperFrames Phone Demo Engine

Turn raw mobile app or web screenshots into high-retention **full-screen phone demo videos** (HTML5 + CSS + GSAP) designed for TikTok, Instagram Reels, YouTube Shorts, and UGC video pipelines.

---

## Architecture: Modular UGC Pipeline

In modern UGC / Short-form video production, video assets are generated across decoupled stages:

1. **Stage 1 (Higgsfield Video Director)**: Generates the creator/character video clips (e.g. Scroll-stop Hook talking head, Outro dilemma reaction) using models like `minimax_h3_max` or `seedance_2_5`.
2. **Stage 2 (HyperFrames Phone Demo Engine)**: Takes raw app screenshots and voiceover audio to render the **clean, full-screen phone demo clip** (1080x1920 edge-to-edge UI, zero titles, zero subtitles, subtle cinematic pan/zoom).
3. **Stage 3 (Timeline Assembly)**: Assembles character clips and the phone demo clip into the final master cut via CapCut Desktop or FFmpeg.

---

## Capabilities

1. **Clean Full-Screen Phone Demo Mode (`--demo-only` / `--fullscreen`)**:
   - Renders edge-to-edge 1080x1920 phone UI screens with zero title overlays and zero subtitles.
   - Smooth cinematic camera zooms, scroll passes, and cross-fades between app screens.
   - Synced to the middle demo portion of the voiceover audio.
2. **3D Device Mockup Showcase Mode**:
   - Wraps screenshots in realistic iPhone chassis with Dynamic Island, glass reflections, and 3D tilts.
3. **Deterministic Rendering Engine**:
   - Strict `data-start`, `data-duration` timeline attributes.
   - Single paused `gsap.timeline({ paused: true })` registered at `window.__timelines["main"]`.
   - Renderable via `npx hyperframes render` to crystal-clear 1080x1920 MP4 at 30/60 FPS in seconds.

---

## CLI Usage

```bash
# Render standalone full-screen phone demo (no titles, no subtitles, no character)
python3 "${SKILL_DIR}/scripts/showcase_builder.py" \
  --title "VoiceReader Phone Demo" \
  --screenshots "./assets/screen1.png,./assets/screen2.png,./assets/screen3.png" \
  --audio "./assets/demo_narration.mp3" \
  --output-dir "./output_phone_demo" \
  --demo-only \
  --render
```

---

## Output Files Produced

- `index.html` — Full HyperFrames standalone composition with responsive full-screen phone UI and GSAP timeline.
- `hyperframes.json` — HyperFrames CLI rendering configuration (`1080x1920`, `30fps`).
- `assets/` — Staged screenshots and synced voiceover audio.
- `renders/` — Rendered 1080x1920 MP4 phone demo video (`voicereader_phone_demo.mp4`).
