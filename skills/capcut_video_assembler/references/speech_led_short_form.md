# Speech-led short videos in CapCut

Use this when narration drives a short edit or the user wants words highlighted as they are spoken. Match visuals to the claims in the final audio, and ensure the video track covers the full narration. When a presenter clip and a separate voiceover say similar lines, compare their timing before choosing which audio to keep; a different take can look out of sync.

## Word-synced captions

1. Start from the final narration audio. A phrase-level SRT is useful for ordinary editable captions, but it does not carry individual word times. For an active-word color effect, generate CapCut Auto Captions from the intended narration source. Review the recognized words and their timing in the caption editor; correct errors against the verified transcript.
2. Decide whether existing captions can be replaced before generating new ones. Use a delete-current-captions option only when all existing captions can be discarded. If auto captions create another timeline track, hide the older phrase-caption track before styling or exporting. Keep separate titles and calls to action visible. Check the player near the start, middle, and end for doubled text.
3. Select an auto-caption clip and inspect **Animation → Captions**. In one macOS build, **Verbatim Color II** displayed the active word in yellow while surrounding words stayed white. Preset names and controls can change, so choose by preview rather than name alone. Set a legible position, size, and outline for the actual footage.
4. Verify the effect on several separate caption clips. **Apply to all main captions** in the Text panel may not apply a caption animation to every clip. If the chosen effect only changes one clip, apply it to the other caption clips through the visible UI. Selecting a different clip may reset the sidebar to Text, requiring **Animation → Captions** again. Reinspect the UI after each panel change; do not reuse stale accessibility indices or screen coordinates.
5. Scrub nearby frames within a phrase to confirm that yellow advances with speech, and check different backgrounds for contrast. Confirm that the captions do not obscure essential visual details or the closing call to action.

If the installed CapCut version cannot produce the requested word behavior, align words to the final audio and spot-check pauses. A transparent caption MOV can show the phrase in white with only the current word yellow. Import it into CapCut on an upper track starting at 0:00, hide the other caption tracks, and verify transparency and timing in the CapCut player. Keep the timing data and overlay as source assets; the overlay's text appearance is baked into the MOV even though its placement remains editable on the timeline.

## Audio and export check

- Listen to the narration over the music and inspect the exported audio's integrated loudness and true peak. If it is too quiet or clips, change track gain in CapCut and export again. A waveform alone is not a reliable level check.
- Use a clear new filename for a revised export when the previous version should remain available. Verify the saved file's duration, dimensions, frame rate, video/audio codecs, and a few frames across the opening, middle, and ending. Specifically inspect caption color changes, duplicate text, crop, and the closing card.
- The export/share screen confirms a local save; publishing to a social account is a separate action and should follow the user's request.

For a quick read-only export check, use `ffprobe` for streams and duration, then `ffmpeg -i <export> -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null -` and read its `input_i` and `input_tp` fields. This measures the file; it does not alter it.
