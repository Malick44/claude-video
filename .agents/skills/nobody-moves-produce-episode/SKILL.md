---
name: nobody-moves-produce-episode
description: Build, check and deliver a NOBODY MOVES episode or Confessional video with the shows/nobody-moves pipeline. Covers setup, placing user images as stills, voices (Kokoro, ElevenLabs, the user's own recordings), framing previews, the mixcheck gate, handing the render to nobody-moves-render, and the draft PR. Use this whenever the user wants to build, export or preview a NOBODY MOVES episode, has sent new images or voice recordings for it, wants a shot reframed or a voice swapped, asks to "install Kokoro on my computer", or just says "make the video", even without naming the pipeline. Rendering, verifying and reviewing the finished video belong to nobody-moves-render. Sound and music changes, and measuring or fixing the mix, belong to nobody-moves-sound-design. Writing or rewriting the script belongs to nobody-moves-write-episode.
---

# Produce a NOBODY MOVES episode

Pipeline: `shows/nobody-moves/`. Other skills own the rest:
- **`nobody-moves-write-episode`** writes the episode. If `episodes/<ep>/` doesn't exist yet (e.g. "render episode 4" before it's written), write it with that skill first.
- **`nobody-moves-render`** (or the `nobody-moves-renderer` subagent, which preloads it) renders the final videos, verifies them and reviews them against a reference episode.
- **`nobody-moves-sound-design`** owns sound and music changes and diagnosing the mix. Hand off to it for any mixcheck FAIL, a line under 8 dB, or a request to change a sound.

Run everything from the show folder:

```bash
cd shows/nobody-moves
FF=$(.venv/bin/python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")   # after setup; there's no ffprobe
```

Every build output lands in `episodes/<ep>/build/`, not in the show folder.

## 1. Environment

- **Setup:** if `.venv/` or `assets/models/` is missing, run `./setup.sh`. It needs Python 3.10–3.13 and fetches the TTS model and fonts from PyPI and GitHub.
- **Self-test:** `.venv/bin/python pipeline/selftest.py` checks the stock-asset code offline, with no keys needed.
- **Cloud sessions:** many hosts are blocked, including Canva downloads, Higgsfield, Freesound, ElevenLabs and Pexels. Don't try to route around a block. Ask the user to send the images, or to allow the host, and carry on with everything that doesn't depend on it.
- **Kokoro on the user's own computer:** a cloud session can't install anything on their machine, so give them the command to run there, from the root of their checkout: `shows/nobody-moves/tools/install-kokoro.sh`. It puts a `kokoro` command in `~/.local/bin` (and prints the PATH line if that folder isn't on it), with the show's pinned versions and model files. Then `kokoro --voices` lists the presets and `kokoro "I didn't see nothing." garrison.wav am_fenrir && afplay garrison.wav` plays one on a Mac. It speaks the plain preset, without `cast.py`'s pitch shift or "voice altered" filter.

## 2. Stills from the user

- **Where they go:** recurring sets and cast go in `stills/` (the series library). Episode-only shots go in `episodes/<ep>/stills/`. Name each file after the key the episode uses (`lorraine.webp`, `basin_counsel.png`). A shot uses the first of its `views` whose still exists, so dropping in a file upgrades the shot with no code change.
- **Files that aren't on disk:** images the user sends *while you are mid-task* arrive as pictures only; they're not saved to disk. Only images in a normal message get a file path. If you can see an image but can't find its file, ask the user to send it again as a new message, rather than asking for a different image.
- **Placing coordinates:** `mkdir -p episodes/<ep>/build && .venv/bin/python pipeline/grid.py <still> -o episodes/<ep>/build/<key>_grid.png [--box x0,y0,x1,y1] [--bright 2.5]`. The `mkdir` is for an episode that hasn't been built yet, since grid.py doesn't create folders. Always pass `-o`: without it the grid image is written next to the still, into the library. Read the fractions for camera centers, `annot_arrow`, `annot_circles`, polaroid crops, `alter_box` and `alter_glow` straight off the grid.

## 3. Audio, timing and the mix check

```bash
.venv/bin/python pipeline/build_audio.py episodes/<ep> --stems
.venv/bin/python pipeline/mixcheck.py episodes/<ep>
```

- **Timing table:** `build_audio.py` prints one row per shot and the total. Aim for 60–90 seconds (a Confessional: 15–25).
- **Voice order:** each line uses the first available source:
  1. a recording at `episodes/<ep>/recordings/<shot>_<n>.*`;
  2. the character's provider in `cast.py`, which is Kokoro unless set to ElevenLabs.
- **Caching:** voice clips are cached by line text and settings, so only changed lines are re-voiced.
- **Swapping a voice:**
  - **The user's own take wins.** Save it as `episodes/<ep>/recordings/<shot>_<n>.m4a` (or .wav/.mp3), using the names in `SCRIPT.md`. Add `"fx_on_recordings": True` to the character in `cast.py` to run its pitch and "voice altered" chain on the take, for example to disguise the user as the anonymous source.
  - **One episode only:** override the character in that episode's `CAST`.
  - **`cast.py`** only for a character in no published episode. A changed entry re-voices that character in every episode on its next build, so posted episodes stop matching.
  - **English presets only** (`af_`, `am_`, `bf_`, `bm_`), also when auditioning with `kokoro --voices`, because the pipeline phonemizes other presets as English.
- **Sounds:** they come from `soundtrack.py`, with the episode's `SOUNDS` overriding it, and are synthesized unless pointed at a file or an API. To swap or add a sound, use `nobody-moves-sound-design` (recipes b and c): it matches the new sound's level and handles licensing and credits. Anything fetched is pinned in `stock/sources.lock.json`; commit `stock/`.
- **The mix:** 48 kHz stereo, mastered to −14 LUFS (TikTok's target). The risers, whooshes and hits come from the shot kinds. The score builds toward the last shot marked `"climax": True`, else the last doorbell shot, else the end card. `--stems` writes `episodes/<ep>/build/stems/{dialogue,score,effects}.wav`, which mixcheck reads.
- **Gate on mixcheck, not on your ears** (you can't hear the mix):
  - **Exit 1 is a HARD failure** (loudness, true peak, dialogue over the bed, a music-out beat that isn't silent, or length). Don't deliver.
  - **Run it right after a `--stems` build.** `make_episode.sh` rebuilds the soundtrack without stems, and mixcheck can't tell old stems from fresh ones, so checking after it can measure an older mix. With nothing changed in between, that rebuild is bit-identical to the soundtrack you checked.
  - **Hand off** to `nobody-moves-sound-design` on any FAIL, any line under 8 dB, or a request to change the sound: recipe (d) for a buried line, recipe (e) for a music-out beat. Don't turn the voices up: lines are loudness-matched and the master re-normalizes, so louder voices only flatten the hits.

## 4. Look before rendering

A full render takes about 10 minutes for a main episode, and previews take seconds. Check framing first:

```bash
.venv/bin/python pipeline/render.py episodes/<ep> --contact             # one frame per shot -> episodes/<ep>/build/contact.png
.venv/bin/python pipeline/render.py episodes/<ep> --preview 1,21.9,75.8 # exact moments -> episodes/<ep>/build/preview_*.png
```

Open the images and actually look at them. Pick preview times from `episodes/<ep>/build/timeline.json`: each line's start, the evidence flash plus about 0.5 s, the doorbell jump, and the pause after the flicker. Check:

- **Hook:** the first frame is a strong close-up, and the name card appears by about 0.4 s.
- **Clutter:** captions (y about 1050–1240, at most two lines) don't collide with name cards, arrows or circles. Move the camera center rather than the overlay if they do.
- **Caption highlight:** the word being spoken is yellow. Its timing is measured from the voice clip on each build, so a new recording or voice needs no other change. A line whose yellow word runs ahead of or behind the voice on the phone is a word-timing bug in `pipeline/words.py`, not a script fix.
- **Annotations:** arrows and circles sit on the subject, at the moment the line mentions it.
- **Clue fairness:** the doorbell frame B clue is visible at phone size (look at the frame scaled to about 360 px wide) but not obvious. A mirrored `alter_box` shows no seams, and the box stays tight around the object. A derived frame B (from a `make_stills.py`) shows no smudge at phone size. Lights listed in SERIES.md's doorbell table are lit in both frames. The clue must not sit under the call-to-action text (y about 1040–1330).
- **Text fit:** the title, the board card text and the call-to-action fit the width.
- **Script:** `SCRIPT.md` regenerates with `.venv/bin/python pipeline/script_md.py episodes/<ep>`. It lists every line's recording name and the credits for stock sounds.

## 5. Render and deliver

Follow `nobody-moves-render`, or delegate the whole step to the `nobody-moves-renderer` subagent. It runs `./make_episode.sh episodes/<ep>` in the background (about 10 minutes), then `pipeline/review.py` to verify the files and compare the episode with the previous one, beat by beat. Its outputs, in `episodes/<ep>/build/`:
- `<ep>.mp4`, the master at about 9 Mbps, too big to send in chat for a main episode;
- `<ep>_tiktok.mp4`, under 29 MB. **Send this one.**

**Audio-only change:** if only the audio changed and `timeline.json` keeps the same `total`, `shots` and `captions`, remux the new soundtrack into the existing MP4 in seconds instead of re-rendering. Follow `nobody-moves-sound-design`, "Re-render or remux".

## 6. Hand-off

- **Commit:** `episode.py`, `SCRIPT.md`, any new stills, any `make_stills.py`, and `stock/` if it changed. Never commit `build/`, `.env` or `assets/`.
- **PR:** open it as a draft. Merge only when the user says so ("merge it"), because they review the video first, and use a merge commit, like the repo's earlier PRs. A `git fetch` right after the merge may be denied; confirm the merge on GitHub instead.
- **Tell the user:**
  - the runtime;
  - the mixcheck result: PASS n/5, the dialogue median and the worst line;
  - which shots still use fallback crops, and the prompts for their ideal stills (from the episode's `STILLS`);
  - that the voices are scratch TTS, and the recording names if they want to record lines.
- **Posting reminders:** turn on TikTok's AI-generated label; pin a hint comment about the clue without giving it away; paste any Attribution credits from `SCRIPT.md` into the description.

## Changing the pipeline

A later episode may need a new shot kind or renderer feature (the roadmap has The Mower as a shadow in Ep. 5 and an inflatable's timer in Ep. 6). Every published episode must still rebuild byte-identically.
- **Regression check:** with your change stashed (`git stash`), build the audio and render `--preview` at a dozen fixed times for each published episode, and copy the PNGs and `soundtrack.wav` aside. Then `git stash pop`, do the same, `cmp` each pair, and confirm the voice cache made no new clips. Details: `.agents/skills/ai-tiktok-series/references/lessons.md`, "Determinism and regressions".
- **New kinds:** add each one to `render()`'s dispatch in `pipeline/render.py`, and to the lower-third and caption rules under it. An unknown kind silently renders as the end card.
- **Sound code** (`sounds.py`, `LEVELS`, the mix in `build_audio.py`) goes through `nobody-moves-sound-design`.

## Troubleshooting

- **`Error processing file ... phontab`:** the espeak-ng data path is longer than about 160 characters. Use a shorter checkout path.
- **`<NAME> is not in the cast`:** add the character to `cast.py` (English presets only; see the write skill), or to the episode's `CAST`.
- **`unknown sound name`:** the valid names are listed in `soundtrack.py`.
- **A new episode crashes at a doorbell or board shot:** check the required fields in the write skill's `references/episode-template.py`.
