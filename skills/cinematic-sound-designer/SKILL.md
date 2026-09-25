---
name: cinematic-sound-designer
description: Analyze timed spoken narration for narrative tension, then plan and render precisely placed cinematic sound effects. Use for dialogue-led videos, trailers, explainers, or stories needing an SFX cue sheet or mix.
---

# Cinematic sound designer

Turn a **final spoken take** and its timed transcript into a sparse, story-led sound design. Deliver a reviewable tension map and cue plan, a timestamped SFX stem, and optionally a narration-plus-SFX mix. The model makes editorial decisions; the bundled scripts resolve timing and place audio deterministically.

## Inputs and timing

- Prefer the actual final narration audio and word-level timestamps from that same take. Accept JSON `words`, Whisper-style `segments[].words`, or a timed SRT/VTT for phrase-boundary work. If only plain text or planned beat timings exist, align them against the final take before promising precise placement. A generated script's planned timestamps are not evidence of where words were spoken.
- Treat SRT/VTT as phrase timing. Anchor to a cue's start/end only; do not estimate an individual word time by dividing a phrase evenly. If a requested impact must land on a particular spoken word, obtain word alignment or audition and mark an explicit time verified against the audio.
- Check the narration duration and any picture edit. Use the same timeline origin as the final video. Account for trimmed heads, speed changes, and video cuts before rendering.

## Design pass

1. Read the full transcript. Identify setup, uncertainty, escalation, turn, reveal, and release where they actually occur. Tension rises when stakes grow, an answer is withheld, a contradiction appears, or a speaker's options narrow; it falls when the uncertainty resolves. Excited wording alone is not a story turn. Record each beat's time range, tension from 0 to 1, and a short quote as evidence. A steady informational segment may have no dramatic cue.
2. Pick a few purposeful sounds: a low texture under uncertainty, a riser that **ends** at a reveal, an impact at a genuine turn, a transition whoosh at a visible cut, or a small release cue after resolution. Let silence and natural pauses carry some beats. Avoid literal Foley for events that exist only as metaphors in speech.
3. For each cue, record the narrative function, exact quoted anchor or verified timestamp, asset, gain, fades, and rationale. Use the [cue plan format](references/cue_plan.md). Resolve ambiguous repeated words by occurrence number or a longer quote. Review the resolved times before rendering.
4. Use supplied effects or effects the user is entitled to use. If the host has a sound-generation tool, it can create original assets; the skill does not depend on that tool. Audition assets, trim leading silence before an impact, and check where the audible transient actually begins. Set gain from the source asset's level and the narration, not from a fixed preset. Keep cues sparse enough that speech stays clear.

## Deterministic placement

Set `SKILL_DIR` to the absolute directory containing this `SKILL.md`. Then resolve and render:

```bash
python3 "${SKILL_DIR}/scripts/resolve_cues.py" \
  --plan /path/to/cue_plan.json \
  --transcript /path/to/aligned_words.json \
  --duration 30.0 \
  --output /path/to/resolved_cues.json

python3 "${SKILL_DIR}/scripts/render_cues.py" \
  --cues /path/to/resolved_cues.json \
  --stem /path/to/sfx_stem.wav \
  --narration /path/to/final_voice.wav \
  --mix /path/to/voice_sfx_preview.wav
```

The stem begins at timeline zero, so it can be imported into CapCut or another editor without moving individual effects by hand. Keep the resolved JSON and individual assets alongside the stem so the design remains editable. If a video editor is the requested final deliverable, place the stem in the actual project and export there; a rendered preview is not a native timeline edit.

The renderer uses the plan's media duration when present and rejects effect tails that run past it. Use `--trim-to-duration` only when cutting those tails is deliberate; its report lists trimmed samples. The standalone stem is 32-bit float WAV so overlapping effects are preserved. Check `stem_headroom_db` in the report: a negative value means lower cue gains before importing into an editor that may clip above 0 dBFS. The optional preview mix ducks effects under speech, while the stem remains unmodified for editing. Audition and adjust that stem against speech inside the final editor.

## Quality check

- Inspect every resolved cue against its transcript evidence and audition the 1–2 seconds around it in the **final** take. A technically exact placement can still sound late because of an asset's leading silence or fade, or land poorly because of a consonant, breath, or pause. Move/trim the cue so its **audible onset** lands at the intended moment.
- Keep speech intelligible. Lower, filter, shorten, or move an effect that masks a word. Check the full mix for clipping and excessive loudness; adjust and render again when needed.
- Confirm the stem/mix duration and first cue alignment with `ffprobe` or playback. Report when timing is only phrase-level. Never describe approximate placement as word-precise.

This skill plans and places sound effects. Use the CapCut assembler skill when the user also wants an editable CapCut project or video export.
