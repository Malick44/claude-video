---
name: nobody-moves-produce-episode
description: Build, check and deliver a NOBODY MOVES episode video with the shows/nobody-moves pipeline. Covers setup, placing user images as stills, voices (Kokoro, ElevenLabs, the user's own recordings), stock sounds, framing previews, the full 1080x1920 render and the under-30 MB TikTok copy. Use this whenever the user wants to render, build, export or preview a NOBODY MOVES episode, has sent new images or voice recordings for it, wants a shot reframed, a voice or sound swapped, or just says "make the video" or "render episode 2", even without naming the pipeline.
---

# Produce a NOBODY MOVES episode

Pipeline: `shows/nobody-moves/`. For writing the episode itself, use `nobody-moves-write-episode`. Run everything from the show folder:

```bash
cd shows/nobody-moves
```

## 1. Environment

- **Setup:** if `.venv/` or `assets/models/` is missing, run `./setup.sh`. It needs Python 3.10–3.13 and fetches the TTS model and fonts from PyPI and GitHub.
- **Self-test:** `.venv/bin/python pipeline/selftest.py` checks the stock-asset code offline, with no keys needed.
- **Cloud sessions:** many hosts are blocked, including Canva downloads, Higgsfield, Freesound, ElevenLabs and Pexels. Don't try to route around a block. Ask the user to send the images, or to allow the host, and carry on with everything that doesn't depend on it.

## 2. Stills from the user

- **Where they go:** recurring sets and cast go in `stills/` (the series library). Episode-only shots go in `episodes/<ep>/stills/`. Name each file after the key the episode uses (`lorraine.webp`, `basin_counsel.png`). A shot uses the first of its `views` whose still exists, so dropping in a file upgrades the shot with no code change.
- **Files that aren't on disk:** images the user sends *while you are mid-task* arrive as pictures only; they're not saved to disk. Only images in a normal message get a file path. If you can see an image but can't find its file, ask the user to send it again as a new message, rather than asking for a different image.
- **Placing coordinates:** use `.venv/bin/python pipeline/grid.py <still> [--box x0,y0,x1,y1] [--bright 2.5]`. Read the fractions for camera centers, `annot_arrow`, `annot_circles`, polaroid crops, `alter_box` and `alter_glow` straight off the grid.

## 3. Audio and timing

```bash
.venv/bin/python pipeline/build_audio.py episodes/<ep>
```

- **Timing table:** it prints one row per shot and the total. Aim for 60–90 seconds.
- **Voice order:** each line uses the first available source:
  1. a recording at `episodes/<ep>/recordings/<shot>_<n>.*`;
  2. the character's provider in `cast.py`, which is Kokoro unless set to ElevenLabs.
- **Caching:** voice clips are cached by line text and settings, so only changed lines are re-voiced.
- **Sounds:** they come from `soundtrack.py`, with the episode's `SOUNDS` overriding it. They're synthesized unless pointed at stock files or APIs; see the README section "Stock assets". Anything fetched is pinned in `stock/sources.lock.json`. Commit `stock/`.
- **The mix:** 48 kHz stereo, mastered to −14 LUFS (TikTok's target). The risers, whooshes and hits come from the shot kinds, and the score builds toward the last doorbell shot. Add `--stems` to write `build/stems/{dialogue,score,effects}.wav`.
- **Check the mix by measurement, not only by ear:**
  - Loudness: `$FF -i build/soundtrack.wav -af ebur128=peak=true -f null -` should give about −14 LUFS and a peak of −1.5 dBFS or lower. `$FF` is the `imageio_ffmpeg` binary.
  - Dialogue: in each line's window from `timeline.json`, the dialogue stem should be about 15 dB or more above score plus effects. Lines under deliberate ambience, like the chime, can sit around 10 dB.
  - A line that gets buried usually means an ambience or a hit is too close to it. Move the hit or trim `LEVELS`; don't turn the voices up.

## 4. Look before rendering

A full render takes about 10 minutes, and previews take seconds. Check framing first:

```bash
.venv/bin/python pipeline/render.py episodes/<ep> --contact             # one frame per shot -> build/contact.png
.venv/bin/python pipeline/render.py episodes/<ep> --preview 1,21.9,75.8 # exact moments -> build/preview_*.png
```

Open the images and actually look at them. Pick preview times from `build/timeline.json`: each line's start, the evidence flash plus about 0.5 s, the doorbell jump, and the pause after the flicker. Check:

- **Hook:** the first frame is a strong close-up, and the name card appears by about 0.4 s.
- **Clutter:** captions (y about 1050–1300) don't collide with name cards, arrows or circles. Move the camera center rather than the overlay if they do.
- **Annotations:** arrows and circles sit on the subject, at the moment the line mentions it.
- **Clue fairness:** the doorbell frame B clue is visible at phone size (look at the frame scaled to about 360 px wide) but not obvious. A mirrored `alter_box` shows no seams, and the box stays tight around the object. The clue must not sit under the call-to-action text (y about 1040–1330).
- **Text fit:** the title, the board card text and the call-to-action fit the width.
- **Script:** `SCRIPT.md` regenerates with `.venv/bin/python pipeline/script_md.py episodes/<ep>`. It lists every line's recording name and the credits for stock sounds.

## 5. Render and deliver

```bash
./make_episode.sh episodes/<ep>
```

It runs the audio, `SCRIPT.md`, the master render and the TikTok copy. It writes:
- `build/<ep>.mp4`, the master at about 9 Mbps, too big to send in chat;
- `build/<ep>_tiktok.mp4`, under 29 MB. **Send this one.**

Verify with `$FF -i <file>` (the `imageio_ffmpeg` binary; there's no ffprobe): 1080×1920, 30 fps, AAC stereo at 48 kHz, and the duration matching the timing table.

## 6. Hand-off

- **Commit:** `episode.py`, `SCRIPT.md`, any new stills, and `stock/` if it changed. Never commit `build/`, `.env` or `assets/`.
- **Tell the user:**
  - the runtime;
  - which shots still use fallback crops, and the prompts for their ideal stills (from the episode's `STILLS`);
  - that the voices are scratch TTS, and the recording names if they want to record lines.
- **Posting reminders:** turn on TikTok's AI-generated label; pin a hint comment about the clue without giving it away; paste any Attribution credits from `SCRIPT.md` into the description.

## Troubleshooting

- **`Error processing file ... phontab`:** the espeak-ng data path is longer than about 160 characters. Use a shorter checkout path.
- **`<NAME> is not in the cast`:** add the character to `cast.py`, or to the episode's `CAST`.
- **`unknown sound name`:** the valid names are listed in `soundtrack.py`.
- **A new episode crashes at a doorbell or board shot:** check the required fields in the write skill's `references/episode-template.py`.
