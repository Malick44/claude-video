---
name: capcut_video_assembler
version: "1.2.0"
description: "Edit videos in CapCut Desktop, including timeline assembly, captions, audio, and export. Optionally stage a top/down split-screen asset package when requested."
argument-hint: "<media or CapCut project> <requested edit>"
homepage: https://github.com/bradautomates/claude-video
repository: https://github.com/bradautomates/claude-video
author: bradautomates
license: MIT
user-invocable: true
---

# /capcut_video_assembler

Use **CapCut Desktop** to complete the video edit the user requested. This skill covers ordinary timeline work: selecting takes, trimming and splitting, clip order and pacing, aspect ratio and crop, split screens and overlays, speed changes, text and captions, music and voiceover, audio levels, color, transitions, effects, and export. Choose only the operations the request calls for; the top/down presenter format is one optional recipe.

## Edit in CapCut

1. Identify the source media, the intended output (editable project, exported video, or both), and any given format, duration, caption, or style requirements. Probe media duration, dimensions, frame rate, and audio streams; inspect the final narration transcript when it determines the edit. If the user names an existing project, open that exact project. Do not silently substitute the most recent draft when a name or link does not resolve.
2. Use a supported CapCut integration if one is available; otherwise, when desktop control is available, operate CapCut through the visible UI. Import the requested files, build or modify the timeline with CapCut's native controls, and inspect the timeline/player after consequential changes. Use the controls visible in the installed version rather than assuming a fixed menu path or screen coordinate. If someone else is changing the open project, coordinate a brief handoff instead of racing their input. Preserve linked source files until the project and any requested export are verified.
3. Choose one intended narration track. If it replaces speech embedded in a clip, mute that clip's audio to prevent doubled voices. Mix music below speech and verify the exported audio, adjusting levels in CapCut when needed.
4. For supplied subtitles, use a UTF-8 SRT file and import it as editable caption blocks. Check text, timing, line breaks, and placement in the video. If generating captions from speech, review recognition errors before delivery. For narration-led short videos or a request to highlight each spoken word, read [references/speech_led_short_form.md](references/speech_led_short_form.md).
5. Save the project. If an exported video was requested, export from CapCut at the requested ratio, resolution, frame rate, and format. Open or probe the resulting file and check its duration, picture, captions, and audio against the request. If the user requested only an editable project, verify that the timeline changes appear in CapCut.

CapCut does not provide a documented stable draft-file schema for this workflow. Do not write into its private draft folders or claim that copying media into a draft folder imports it onto the timeline. A launcher, asset package, or FFmpeg render is not a completed CapCut edit.

If desktop control is unavailable, prepare the source files, captions, and a precise edit plan in a normal output folder. Explain the remaining CapCut import/edit steps and state plainly that the native timeline has not been edited. An FFmpeg preview may help communicate a layout, but label it as a preview and keep the CapCut deliverable status accurate.

## Optional top/down split recipe

Use `scripts/assemble_capcut_package.py` only when the user wants a story clip above a presenter clip. It stages two 1080×960 video tracks, the supplied audio, optional timed captions, and an optional FFmpeg preview. The package is for import into CapCut; it does not create a native CapCut project.

The helper needs one intended audio track and removes embedded audio from both video tracks. If only the videos were supplied, inspect their audio and extract the track the user wants to hear, or clarify the choice if it is ambiguous. Check that the story footage covers the intended audio duration and review both center crops for cut-off subjects before import.

Set `SKILL_DIR` to the absolute directory containing this `SKILL.md`, then run:

```bash
python3 "${SKILL_DIR}/scripts/assemble_capcut_package.py" \
  --top-video /path/to/story.mp4 \
  --bottom-video /path/to/presenter.mp4 \
  --audio /path/to/voiceover.wav \
  --transcript-json /path/to/timed-captions.json \
  --output-dir /path/to/output
```

The transcript JSON contains `{"beats": [{"start": 0.0, "end": 2.0, "text": "Caption"}]}`. Omit `--transcript-json` if captions were not supplied; do not invent transcript text. Use the generated asset guide to place tracks in CapCut and import any SRT. Use `--render-master` only when an FFmpeg preview is wanted. Never target or copy assets into an existing CapCut draft through this helper.

CapCut's current help documents [desktop subtitle import](https://www.capcut.com/help/how-to-import-subtitles) and [rebuilding a timeline from source media](https://www.capcut.com/help/how-to-export-pro-project). Check the current UI for feature locations before acting.
