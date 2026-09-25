# Mix knobs

Every number that shapes the show's sound, where it lives, and which way is "more dramatic". Find each one by searching for the quoted code. Every knob in the tables is show-wide: changing it changes every episode on its next build. The one per-episode lever for a synthesized sound is in "Per-episode trim" below.

## `pipeline/sounds.py`

| Knob | Code | Now | What it does |
|---|---|---|---|
| Levels | `LEVELS = {...}` | see the sound catalog | Gain in dB per sound, relative to each other and to the dialogue, which is fixed at -17 dBFS RMS (`voice_line()`). The master only sets overall loudness, so raising every entry by x dB lowers dialogue over bed by x dB |
| Theme notes | `THEME_NOTES` | `[69, 72, 76, 72, 69, 72, 75, 72]` | A C E C A C D# C, played an octave lower. The D# (flat five) is the unease; keep one dissonant note or the theme turns cheerful |
| Turn note | `THEME_TURN` | `74` (D) | Replaces the note at index 6 (the D#) on every other bar. The index is hard-coded as `i % len(THEME_NOTES) == 6` in `theme_layers`; update it if you move the dissonant note |
| Tempo | `THEME_STEP` | `0.62` s per note | Also sets the heartbeat period (`2 * THEME_STEP`, 1.24 s) and each pad chord's length (`THEME_STEP * len(THEME_NOTES) * 2`, 9.92 s). Shorter is more urgent |
| Chords | `PAD_CHORDS` | A minor, F, D minor, E major (i, VI, iv, V) | Voicings in MIDI numbers; two ostinato bars per chord |
| Piano accents | `0.55 if i % 4 else 0.8` in `theme_layers` | every 4th note accented | Velocity pattern of the ostinato |
| Reverb sizes | `reverb(..., 3.2, 0.42)` piano, `0.45` pad, `0.55` shimmer; `3.5, 0.3` hits | seconds, wet | Bigger and wetter reads as more "cinematic" but muddier under dialogue |
| Pad tone | `highpass(lowpass(y, 2600, 2), 70, 1)` in `string_pad` | 70 Hz to 2.6 kHz | Opening the lowpass brightens the strings |

## `pipeline/build_audio.py` (in `main()`)

| Knob | Code | Now | More dramatic |
|---|---|---|---|
| Intensity floor | `intensity = 0.3 + 0.7 * ...` | 0.3 at the title, 1.0 at the climax | Raise the floor and lower the span with it, keeping floor + span = 1 (`0.45 + 0.55 * ...`). Raising only the floor lifts the climax too: `0.45 + 0.7` peaks at 1.15, and the pad weight goes from 0.90 to 0.98 |
| Intensity curve | `... ** 1.3` | builds late | Lower it (0.9) to build sooner |
| Climax | `climax = next((s["start"] for s in reversed(shots) if s["kind"] == "doorbell"), bed_end)` | last doorbell's start | Intensity reaches 1.0 here |
| Piano | `L["piano"] * 0.85` | constant | The signature; keep it steady |
| Drone | `L["drone"] * 0.25` | constant | 55 + 82.4 Hz. Raising it mostly adds mud |
| Pad | `L["pad"] * (0.35 + 0.55 * intensity)` | swells with intensity | Raise the 0.55 |
| Heartbeat | `L["pulse"] * (0.7 * smooth((intensity - 0.5) / 0.3))` | enters at 0.5, full at 0.8 | Lower 0.5 (0.35) to bring it in earlier; raise 0.7 |
| Shimmer | `L["shimmer"] * (0.3 * smooth((intensity - 0.8) / 0.2))` | enters at 0.8 | Lower 0.8, or raise 0.3 |
| Stock theme | `bank.get("theme", length) * (0.7 + 0.3 * intensity)` | only when `theme` is stock | A stock theme has no layers, so it can only swell in level |
| Bed highpass | `snd.highpass(bed[:, ch], 45, 2)` | 45 Hz | Mud control; don't lower it |
| Bed fade | `k = int(1.5 * SR)` | 1.5 s at the end | |
| Music out | `dip(s["start"], s["end"], 0.0)` | fades out 0.2 s before the shot, back in over 0.4 s after | Per shot, from `episode.py` |
| Reveal hush | `dip(s["flicker_at"], s["flicker_at"] + CTA_DELAY, 0.3, 0.3, 0.6)` | score to 0.3 (-10.5 dB) under each flicker | 0.0 for a full drop before the hit |
| Flicker time | `s["flicker_at"] = round(s["lines"][-1]["end"] + 0.15, 3)` | 0.15 s after the doorbell's last line | Written to `timeline.json` and used by `render.py`: changing it means a full re-render |
| Duck depth | `duck = (1 - 0.6 * np.clip(env / db(-26), 0, 1))` | up to -8 dB, full at a -26 dBFS voice envelope | 0.7 clears lines more but pumps more |
| Duck speed | `w = int(0.25 * SR)` | 0.25 s smoothing | Shorter reacts faster and pumps more audibly |
| Title riser | `rs = min(2.0, s["start"])` | 2 s | |
| Whoosh lead | `s["start"] - 0.45` | 0.45 s before a question card | Keeps its peak on the cut |
| Typing | `span = (s["end"] - s["start"]) * 0.6`, from `+ 0.15` | first 60% of the card | |
| Glitches | `for j in range(6): put(... flick + j * 0.3 ...)` | 6, 0.3 s apart | |
| Shutter impact | `put(fxbus, s["start"], bank.get("impact"), LEVELS["impact"] - 4)` | 4 dB under a reveal impact | Couples the shutter to `LEVELS["impact"]`: raising the impact raises every shutter hit (ep01 has 2, ep03 has 1) |
| Reveal hit | `put(fxbus, flick + CTA_DELAY, bank.get("impact"), LEVELS["impact"])` and the same line for `braam` | impact placed -16.0 and braam -17.3; together -13.6 (power sum), -13.7 to -13.9 in the hit lists | For the reveal alone, raise `LEVELS["braam"]`, which only this line uses (`sting()` calls `snd.braam()` directly): +3 dB took ep02's reveals to -12.3/-12.4 (the power sum predicts -12.1). For the full +3, add the same offset to both lines (`LEVELS["impact"] + 3`), which leaves the shutter hits alone |
| Board swell | `put(under, s["lines"][-1]["start"] - 0.1, bank.get(name), LEVELS[name])` (sfx `sting_soft`) | starts 0.1 s before the board shot's last line | Sits on `under`, so it counts as score. It is the usual cause of the board line being the second-worst line in every episode; see recipe (d) |
| Voice level | `y = y * (db(-17) / rms)` in `voice_line()`, peak cap -1.5 | every line at -17 dBFS RMS | Leave it. Fix balance with the bed and effects instead |
| Pre-master peak | `norm = db(-1.0) / (np.max(np.abs(mix)) + 1e-9)` | mix peak at -1 dBFS; the stems are scaled by the same `norm` | |

## Per-episode trim of a synthesized sound

`gain_db` only works on a stock source, so a synthesized sound has no per-episode level. To trim one in a single episode, freeze it to a file:

1. Run `$PY pipeline/sound_kit.py`, then copy the sound's kit WAV to `episodes/<ep>/audio/`. `KIT` in `sound_kit.py` maps names to files, e.g. `sting_soft` to `sting_soft.wav` and `shutter` to `camera_shutter.wav`.
2. In that episode's `episode.py`, add `SOUNDS = {"sting_soft": {"file": "audio/sting_soft.wav", "gain_db": -3}}`. `Bank` looks in the episode folder first.
3. Probe it with `$PY $PROBE --episode episodes/<ep> sting_soft`. `src` should read `stock`, and `placed` should drop by the `gain_db`.

- **Why it's exact:** the generators and the kit are both peak-normalized, and `Bank` peak-normalizes the file again. At `gain_db` 0 the file matches the synthesized sound to 16-bit precision (a residual of -79 dB). Tested on ep02 with -3: the board line went from 12.4 to 14.6 dB, and nothing else in mixcheck moved.
- **Fixed-length sounds only:** `sting`, `sting_end`, `sting_soft`, `impact`, `braam`, `whoosh`, `shutter`, `ding`, `glitch`, `jump`. Not `riser`, whose length varies per use; not `typewriter`, which has 16 variants; not `theme`, which loses its layers as a file; and not the ambiences, which a file would loop and fade, so they no longer stop dead at the cut.
- **Freezing `impact`** trims that episode's shutter hits too.
- **Commit the WAV,** and tell the user it won't follow later changes to the generator. Re-freeze it after any change to that sound.

## `master()` in `build_audio.py`

```
highpass=f=30,
acompressor=threshold=0.125:ratio=2.5:attack=15:release=250:makeup=1.5,
alimiter=limit=0.9:attack=5:release=60
then two-pass loudnorm I=-14 (LOUDNESS):TP=-1.5:LRA=11, linear=true, written as 16-bit 48 kHz
```

- **Limiter delay:** the limiter's 5 ms look-ahead makes `soundtrack.wav` run exactly 240 samples (5.0 ms) behind the stems and the timeline. That's inaudible. mixcheck allows for it; anything else you write that compares the soundtrack with the stems must allow for it too.
- **Louder hits don't make a louder master.** Loudness is normalized to -14 LUFS, so pushing the hits up makes the limiter work harder and pulls everything else down. After raising hits, check the true peak, the loudness range and the dialogue median.

## `pipeline/common.py`

- **`CTA_DELAY = 1.9`:** seconds from the doorbell flicker to the call to action. The renderer shows the text then, and the mix lands the riser's end, the impact and the braam there. Changing it changes the picture, so re-render every episode.
