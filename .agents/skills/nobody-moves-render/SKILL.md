---
name: nobody-moves-render
description: Render a NOBODY MOVES episode or Confessional to its final 1080x1920 MP4s with the shows/nobody-moves pipeline, verify the files (format, stream lengths, size, black frames, loudness), and review the result side by side against a reference episode with pipeline/review.py, which compares pacing and grabs the same story beats from both videos at phone size. Use this whenever the user wants an episode rendered or re-rendered, asks to check, QA or review a finished video, wants to compare one episode with another ("compare episode 3 with episode 2"), or says "render episode 4", even without naming the pipeline. The nobody-moves-renderer subagent preloads this skill. Writing the script belongs to nobody-moves-write-episode; placing new images, voices and framing fixes belong to nobody-moves-produce-episode; sound changes belong to nobody-moves-sound-design.
---

# Render and review a NOBODY MOVES episode

This skill turns a written, framed episode into its final videos, proves the files are right, and reviews them against an episode the user has already seen. Whoever runs it reports problems and doesn't fix the script, the images or the sound: those belong to the skills named at the end, and a render is the wrong moment to change them silently.

**You can't watch video.** Judge from frame grabs and measurements, and say so in the report.

Run everything from the show folder:

```bash
cd shows/nobody-moves
PY=.venv/bin/python
```

Every output lands in `episodes/<ep>/build/`.

## 1. Preflight

- **The episode exists:** `episodes/<ep>/episode.py`. If not (e.g. "render episode 4" before it's written), stop and write it with `nobody-moves-write-episode`.
- **Setup:** `.venv/`, `assets/models/` and `assets/fonts/` exist. If not, run `./setup.sh` (PyPI and GitHub only).
- **Derived stills:** if the episode has a `make_stills.py`, the stills it writes must exist (Episode 3's writes the library still `stills/yard_gone.webp`). Run it if one is missing; it's deterministic.
- **The reference episode:** by default the previous main episode (for Episode 3, Episode 2). For a Confessional, the latest main episode. Its `build/<ref>_tiktok.mp4` must exist. If it doesn't, render the reference first or review without `--ref`.
- **Nothing else is building this episode.** `make_episode.sh` rewrites `build/soundtrack.wav` and the render reads it; two builds of one episode at once corrupt each other. Rendering two different episodes at once is safe, just slower.

## 2. Audio and the mix gate

```bash
$PY pipeline/build_audio.py episodes/<ep> --stems
$PY pipeline/mixcheck.py episodes/<ep>
```

- **The timing table** gives the runtime: 60–90 s for a main episode, 15–25 s for a Confessional.
- **mixcheck exit 1 stops the render.** Hand the failure to `nobody-moves-sound-design`. Run mixcheck here, right after the `--stems` build: `make_episode.sh` rebuilds the soundtrack without stems, so a later mixcheck can measure old stems.
- **Fallbacks:** the next command prints `not provided (using fallbacks): ...`. Those shots use crops of library stills; list them in the report with the prompts from the episode's `STILLS`.

## 3. A quick look before the long render

```bash
$PY pipeline/render.py episodes/<ep> --contact          # one frame per shot, seconds -> build/contact.png
```

Open `build/contact.png`. A missing still shows as a labeled placeholder card, and an unknown shot kind renders as the end card; both are cheaper to catch here than after 10 minutes. Framing problems go back to `nobody-moves-produce-episode`, section 4.

## 4. Render

```bash
./make_episode.sh episodes/<ep> > episodes/<ep>/build/render.log 2>&1
```

- **Run it in the background** and wait for it to finish; don't poll with `sleep`. It takes about 10 minutes for a 90 s episode on this container (3 minutes for a Confessional), and longer while other heavy jobs run.
- **Watch the log for the end:** `wrote .../<ep>_tiktok.mp4 (NN MB ...)` means it finished. `Traceback` or `Error` means it failed; read the last 30 lines of `render.log`.
- **What it writes:** `SCRIPT.md` (in the episode folder), the master `<ep>.mp4` (about 9 Mbps) and the upload copy `<ep>_tiktok.mp4` (under 29 MB). The audio rebuild inside it is bit-identical to the one you checked, if nothing changed in between.
- **Audio-only change?** Don't re-render: remux, per `nobody-moves-sound-design`, "Re-render or remux".

## 5. Verify and compare

```bash
$PY pipeline/review.py episodes/<ep> --ref episodes/<ref>        # exit 1 on a FAIL
```

It checks the TikTok copy (`--file master` checks the master), then compares the two episodes. It takes about 30 s.

| Check | Pass | If it fails |
|---|---|---|
| video | H.264, 1080×1920, 30 fps | re-render; something overrode the encoder settings |
| audio | AAC, 48 kHz, stereo | re-render |
| video length, audio length | each within 0.15 s of the timeline total | a stale `timeline.json`: rebuild the audio, then re-render |
| size | under 29 MB | `$PY pipeline/deliver.py episodes/<ep> --max-mb 28` |
| black frames | no black stretch of 0.4 s or more outside question cards | a missing still or a broken shot; look at the stretch's time in the beats sheet or with `render.py --preview` |
| loudness (info) | about −14 LUFS and a true peak near −1.2 dBFS after AAC | if it's off by more than 1 LU, the soundtrack wasn't mastered: rebuild the audio |

**The pacing table** compares the two timelines. Read the deltas against the format rules, not against zero:
- **runtime:** 60–90 s (Confessional 15–25).
- **title at:** about 5–6 s, right after the hook.
- **payoff at:** the replay's call to action, within about 25 s. It's empty for Episode 1 and for Confessionals.
- **words per minute:** within about 15% of the reference. Much faster reads as rushed, and the captions stop being readable.
- **speech share, mean shot length and longest shot:** a shot of 10 s or more is a long hold on a still; check the reference had the same.
- **music-out shots:** one or two, before a punchline or reveal.
- **score peak at:** the cliffhanger (or a shot marked `"climax": True`), near the end.

**The beats sheet,** `build/review/beats_vs_<ref>.png`, is the review. Open it and look. The reference is on top, the new episode below, and each column is the same story beat, grabbed from the finished MP4s at phone size: hook, title, payoff, first question card, first exhibit, first name card, board, cliffhanger jump, cliffhanger call to action, end card. A beat the episode doesn't have is a gray cell. For each column, check:
- **Same show:** the grade, fonts, caption style, lower thirds and doorbell HUD match the reference. A difference means a pipeline change leaked into the look.
- **Text:** nothing clipped at the edges, and no caption colliding with a name card, arrow, circle or call to action.
- **Hook:** the first frame is a strong, readable close-up with its name card. A soft long-lens crop here means the hero still is missing: flag its prompt as the top priority.
- **Payoff and cliffhanger:** the answer to last week's clue is visible in the payoff cell. The new clue is findable in the cliffhanger cells at this size but not obvious, and not under the call-to-action text.
- **End card:** `NEXT_UP` names the right next episode.

To check a moment the sheet doesn't cover, grab it from the video: `$FF -ss <t> -i episodes/<ep>/build/<ep>_tiktok.mp4 -frames:v 1 -y /tmp/f.png`, where `FF=$($PY -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")`. Everything is also in `build/review/report.json`.

## 6. Report

Send the user `episodes/<ep>/build/<ep>_tiktok.mp4`. For a main episode, the master is too big for chat. Report:
- **The verification:** PASS or FAIL per row, the mixcheck result (PASS n/5, the dialogue median, the worst line), and the encoded loudness.
- **Pacing against the reference,** only the deltas that matter, each in plain words ("the payoff lands 13 s in, against 26 s last week").
- **Findings,** most serious first. Give each one the beat or time and the shot id, what you saw, the fix, and the skill that owns it:
  - `nobody-moves-write-episode`: lines, runtime, pacing, clue design;
  - `nobody-moves-produce-episode`: framing, stills, voices;
  - `nobody-moves-sound-design`: the mix.
- **Fallbacks:** the shots still on fallback crops, with the prompts for their stills.
- **The limit:** you judged from frame grabs and measurements, not by watching; ask the user to watch it on a phone.

Don't commit `build/`: the videos, the sheet and the report stay local. Commit only what the render changed in the tree, which is normally just a regenerated `SCRIPT.md`.
