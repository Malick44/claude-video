# James Henrikson — North Dakota Oil Patch Murders (working title)

Workspace for a 22–28 minute YouTube documentary: faceless narration over archival footage, cinematic and dramatic in tone. For the folder layout and record shapes, see [`../README.md`](../README.md).

## Status

This is a scaffold only. Every record file is empty, and no case facts have been entered or verified.

## Decided

- YouTube, 16:9, 1920×1080, mastered to −14 LUFS integrated and −1 dBTP true peak (`manifest.json` → `project`).
- Faceless narration over archival footage, with no on-camera host.
- Voice: `auk_voiceover` or Kokoro, whichever wins a blind A/B on the same 60–90 s passage. `auk_voiceover` runs only on Apple Silicon.

## Handling rules for this case

This is a real case with victims and living families.

- Narrate only `verified` claims. Attribute court findings to the court, and allegations to whoever made them.
- Never imply guilt for anyone who was not charged or was acquitted.
- Crime-scene and victim imagery goes in `04_stills/restricted/`. It stays out of the edit unless a reviewed decision in `09_clearance/` says otherwise.
- AI-generated material goes in `05_graphics/synthetic/` and is disclosed as such.

## Next

1. Build the timeline and claims from primary sources (Department of Justice releases, court opinions). Confirm every claim the story depends on with two independent sources.
2. Draft the chapter spine in `manifest.json`.
3. Run a first footage-search test: take five beats through `source_requests.json` to approved clips with sidecars and clearance records.
