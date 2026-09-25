# Baselines

These are the measurements of the current sound, taken after the cinematic redesign. Compare any change against them. Nobody has judged these mixes by ear yet, so they are a reference point, not a verdict. When the user approves a new sound, re-measure and replace these tables.

## mixcheck.py, per episode (all PASS 5/5)

| | ep01_three_feet | ep02_i_was_right_here | ep03_the_goose |
|---|---|---|---|
| Loudness / true peak | -14.0 LUFS / -1.5 dBTP | -14.0 / -1.5 | -14.0 / -1.5 |
| Loudness range | 3.6 LU | 4.2 LU | 3.7 LU |
| Dialogue median | 19.8 dB | 20.2 dB | 20.1 dB |
| Worst line | chime 48.18 s, 10.3 dB | chime 66.58 s, 9.6 dB | ray 16.47 s, 11.1 dB |
| Music-out shots | none | `calm`, -120 dBFS (silent) | `exhibit`, -120 dBFS (silent) |
| Phone presence (effects / mix) | 30% / 34% | 31% / 33% | 30% / 32% |
| Mono: correlation, mono sum vs stereo | 0.951, -0.1 LU | 0.949, -0.1 LU | 0.955, +0.0 LU |
| Lowest 1 s correlation | 0.68 at 79.0 s (end card) | 0.63 at 89.0 s (end card) | 0.63 at 87.5 s (end card) |
| Length vs timeline, tail | 80.59 vs 80.09 s, -46.0 dBFS | 90.68 vs 90.18 s, -45.8 dBFS | 89.20 vs 88.70 s, -46.0 dBFS |
| Stem match | 0.93 to 0.94, soundtrack +5.0 ms | same | same |

**Five worst lines:**
- **ep01:** chime 48.18 s 10.3, chime 53.66 11.3, board 64.42 12.7, chime 57.52 13.5, doorbell 66.25 13.8.
- **ep02:** chime 66.58 s 9.6, board 75.52 12.4, hook4 4.49 12.9, chime 63.70 13.5, basin 39.38 15.3.
- **ep03:** ray 16.47 s 11.1 (right after the replay reveal hit at 15.82 s; the braam tail is under the line), board 73.37 12.8, basin 63.78 13.8, exhibit 33.30 14.1, doorbell 79.56 14.8.

The chime lines sit near 10 dB because wind and chimes play under them on purpose.

The board lines (12.4–12.8 dB) have a silent effects stem: their whole bed is score. `soundprobe.py --lines` names it, and splitting `under` out in a scratch build showed `sting_soft` 5–7 dB above the bed under that line (ep01 -31.6 vs -36.3 dBFS, ep02 -30.4 vs -37.0, ep03 -30.7 vs -35.8). Without it, the lines would read 19.3, 20.2 and 19.0 dB. The ep02 and ep03 basin lines are also score-only, with just the bed under them.

**Hit lists (the 6 loudest 0.5 s windows of the effects stem):**
- **ep01:** reveal hit 74.84 s -14.1; title sting 5.11 -14.3; end sting 76.79 -14.6; shutter 16.16 -19.8; shutter 22.39 -19.8; doorbell jump 70.25 -28.0.
- **ep02:** replay reveal 26.45 -13.7; doorbell reveal 85.13 -13.9; title sting 6.11 -14.1; end sting 86.88 -14.3; doorbell jump 83.26 -27.5; replay jump 23.08 -27.7.
- **ep03:** doorbell reveal 83.54 -13.8; replay reveal 15.82 -13.9; end sting 85.40 -14.2; title sting 4.98 -14.2; exhibit shutter 33.06 -19.5; doorbell jump 80.80 -27.8.

The reveal hits and stings cluster within 1 dB of each other at about -14 dBFS; they are the peaks of the episode. A change that reorders them, or pushes a jump or shutter up to that level, changes the shape of the episode.

## soundprobe.py --stems (low end and phone presence)

| | ep01 | ep02 | ep03 |
|---|---|---|---|
| score stem: <60 Hz / >250 Hz | 25% / 39% | 20% / 40% | 22% / 40% |
| effects stem: <60 Hz / >250 Hz | 19% / 30% | 16% / 31% | 17% / 30% |
| dialogue stem: <60 Hz / >250 Hz | 0% / 33% | 0% / 31% | 0% / 32% |
| soundtrack: <60 Hz | 3% | 3% | 3% |

Before the redesign's mud fix, ep02's score had 36% of its energy below 60 Hz. The fix reduced the drone and cello, highpassed the bed at 45 Hz and the master at 30 Hz, and added a violin layer, which brought it down to 20%.

## Timings

| Step | Time |
|---|---|
| `build_audio.py <ep> --stems` with cached voices | 40 to 60 s per episode |
| `mixcheck.py` | 6 to 9 s |
| `soundprobe.py --determinism`, all 16 sounds | about 20 s |
| `selftest.py` | about 15 s, 15 checks |
| Full render | about 10 min |
| Audio remux into an existing MP4 | about 9 s |
| `deliver.py` TikTok copy (two-pass encode) | about 4 min |
