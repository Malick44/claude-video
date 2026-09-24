# Cue plan format

Use one JSON document as the reviewable editorial handoff. The `tension_beats` section records the model's reading of the story; the resolver uses `cues` for deterministic placement. Time values are seconds from the final narration or video timeline's zero point.

Each cue needs a unique `id`, an `anchor`, an existing `asset`, a nonempty `reason`, and `tension_before`/`tension_after` scores. Use 0–1 for tension scores. `gain_db` and fade values default to zero, but choose them deliberately after listening to the actual source effects. The optional `function` helps reviewers understand why the sound belongs there.

```json
{
  "version": 1,
  "tension_beats": [
    {"start": 0.0, "end": 3.2, "role": "setup", "tension": 0.25, "evidence": "The hallway was empty"},
    {"start": 3.2, "end": 6.4, "role": "reveal", "tension": 0.85, "evidence": "Then the door opened"}
  ],
  "cues": [
    {
      "id": "reveal-hit",
      "function": "accent the reveal",
      "anchor": {"kind": "word", "quote": "door opened", "edge": "start", "offset_ms": -80},
      "asset": "sfx/soft_impact.wav",
      "gain_db": -18,
      "fade_in_ms": 0,
      "fade_out_ms": 180,
      "reason": "The first concrete threat appears here",
      "tension_before": 0.45,
      "tension_after": 0.85
    }
  ]
}
```

## Anchors

- `{"kind":"word","quote":"door opened","edge":"start"}` matches contiguous words in actual word-level timing. Use `occurrence: 2` if the quote appears more than once. `offset_ms` may lead or trail the word, including a negative lead.
- `{"kind":"segment","index":3,"edge":"end"}` anchors at the boundary of the fourth timed SRT/VTT or JSON segment; indices start at zero. This has phrase-level precision.
- `{"kind":"absolute","seconds":6.32}` is for a time auditioned and verified against the final audio or picture. State that verification in `reason`.

A riser should generally start before the payoff and finish at it; choose an asset duration and lead time that make that happen. Store all asset paths relative to the plan file when practical. The resolver writes absolute paths into its resolved manifest so moving that manifest does not silently change which audio file is used.

The resolved manifest has `version: 1`, optional `duration_seconds`, and `cues` with numeric `at`, `asset`, `gain_db`, `fade_in_ms`, `fade_out_ms`, and the cue's `function`, `reason`, and tension values when supplied. Inspect it before running the renderer. The renderer places a cue at the specified time; it does not decide whether the cue belongs in the story.
