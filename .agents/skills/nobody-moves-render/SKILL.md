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
- **Derived stills:** if the episode has a `make_stills.py`, the stills it writes must exist (Episode 3's writes the library still `stills/yard_gone.webp`). Run it only if one is missing. It's deterministic, so rerunning it rewrites a tracked file with the same bytes.
- **The reference episode:** by default the previous main episode (for Episode 3, Episode 2). For a Confessional, the latest main episode. Its `build/<ref>_tiktok.mp4` must exist. If it doesn't, render the reference first or review without `--ref`.
- **Nothing else is building this episode.** `make_episode.sh` rewrites `build/soundtrack.wav` and the render reads it; two builds of one episode at once corrupt each other. Check with `pgrep -af '[m]ake_episode\.sh .*episodes/<ep>|[p]ipeline/(build_audio|render|deliver|script_md)\.py .*episodes/<ep>'`, which prints nothing when nothing is building. The bracketed first letters stop the pattern from matching the shell that runs it; a plain `pgrep -af "episodes/<ep>"` always matches itself, and any log monitor left running. Rendering two different episodes at once is safe, just slower.

## 2. Audio and the mix gate

```bash
$PY pipeline/build_audio.py episodes/<ep> --stems
$PY pipeline/mixcheck.py episodes/<ep>
```

- **The timing table** gives the runtime: 60–90 s for a main episode, 15–25 s for a Confessional.
- **mixcheck exit 1 stops the render.** Hand the failure to `nobody-moves-sound-design`. Run mixcheck here, right after the `--stems` build: `make_episode.sh` rebuilds the soundtrack without stems, so a later mixcheck can measure old stems.
- **After the render, mixcheck prints `NOTE: stems are N min older than soundtrack.wav`.** That's expected: `make_episode.sh` rebuilds the soundtrack without stems. The numbers you checked before the render still stand if no audio input changed since, which is when this prints nothing: `find episodes/<ep>/episode.py cast.py soundtrack.py pipeline/build_audio.py pipeline/sounds.py -newer episodes/<ep>/build/stems/dialogue.wav`.
- **Fallbacks:** `render.py` (the next step) prints `fallback views (shot: missing stills -> used): ...` for every shot not on its first-choice still, naming each missing choice (`hook: lorraine_bee, lorraine -> yard_before`), and `PLACEHOLDERS` for any still that's missing entirely. Fallbacks are allowed; placeholders mean a missing file. List the fallbacks in the report with their prompts. A key in this episode's `STILLS` has its prompt there. For a key requested by an earlier episode, find it with `grep -n '"<key>"' episodes/*/episode.py`. A key with no real prompt anywhere (`aerial`, `cork`) is reported as "no prompt yet".

## 3. A quick look before the long render

```bash
$PY pipeline/render.py episodes/<ep> --contact          # one frame per shot, seconds -> build/contact.png
```

Open `build/contact.png`. A missing still shows as a labeled placeholder card, and an unknown shot kind renders as the end card; both are cheaper to catch here than after 10 minutes. Each cell is labeled with its shot id and time, and doorbell shots are grabbed paused on the clue frame, with their call to action. Framing problems go back to `nobody-moves-produce-episode`, section 4.

## 4. Render

```bash
./make_episode.sh episodes/<ep> > episodes/<ep>/build/render.log 2>&1
```

- **Run it in the background** and wait for it to finish; don't poll with `sleep`. It takes about 10 minutes for a 90 s episode on this container (3 minutes for a Confessional), and longer while other heavy jobs run. Episode 3 took 9.5 minutes:
  - the audio, about 45 s;
  - the frames, about 6.5 minutes at about 7 fps (`frame N/M` lines);
  - the TikTok copy, about 2.3 minutes. It prints nothing for its first 2 minutes after `wrote <ep>.mp4`; that's the first pass of its two-pass encode, not a hang.
- **Watch the log for the end:** `wrote .../<ep>_tiktok.mp4 (NN MB ...)` means it finished. `Traceback` or `Error` means it failed; read the last 30 lines of `render.log`.
- **What it writes:** `SCRIPT.md` (in the episode folder), the master `<ep>.mp4` (about 9 Mbps) and the upload copy `<ep>_tiktok.mp4` (under 29 MB). The audio rebuild inside it is bit-identical to the one you checked, if nothing changed in between.
- **Audio-only change?** Don't re-render: remux, per `nobody-moves-sound-design`, "Re-render or remux".

## 5. Verify and compare

```bash
$PY pipeline/review.py episodes/<ep> --ref episodes/<ref>        # exit 1 on a FAIL
```

It checks the TikTok copy (`--file master` checks the master), then compares the two episodes. It takes about 30 s. Each run writes its own report, `build/review/report_<file>[_vs_<ref>].json`, so checking the master doesn't overwrite the comparison.

| Row | Pass | If it fails |
|---|---|---|
| video | H.264, 1080×1920, 30 fps | re-render; something overrode the encoder settings |
| audio | AAC, 48 kHz, stereo | re-render |
| video length, audio length | each within 0.15 s of the timeline total | a stale `timeline.json`: rebuild the audio, then re-render |
| size | under 29 MB, in the decimal MB that `deliver.py` prints | `$PY pipeline/deliver.py episodes/<ep> --max-mb 28` |
| black frames | no black stretch of 0.4 s or more, except question cards and the end card's fade from black | a missing still or a broken shot; find the stretch with `--grab` |
| WARN call to action | each doorbell's call to action stays on screen 1.5 s or more | raise that shot's `"post"` (write skill). Episodes 2 and 3 hold the replay's for only 0.95 s |
| loudness (info) | about −14 LUFS, true peak −1.0 to −1.2 dBFS after AAC | off by more than 1 LU means the soundtrack wasn't mastered: rebuild the audio |
| ref (info) | "all file checks pass" for the reference | the reference's video doesn't match its timeline, so its beat grabs are misplaced: re-render it before comparing |

**The pacing table** compares the two timelines. Read the deltas against the format rules, not against zero:
- **runtime:** 60–90 s (Confessional 15–25).
- **title at:** about 5–6 s, right after the hook.
- **payoff at:** the replay's call to action, within about 25 s. It's empty for Episode 1 and for Confessionals.
- **words per minute:** within about 15% of the reference. Much faster reads as rushed, and the captions stop being readable.
- **speech share, mean shot length and longest shot:** a shot of 10 s or more is a long hold on a still; check the reference had the same.
- **music-out shots:** one or two, before a punchline or reveal.
- **CTA on screen:** each doorbell's call-to-action hold, in seconds (the WARN row).
- **score builds to:** the shot the build's rule picks (the last `"climax": True`, else the last doorbell), read from the timeline, not measured. It should be the cliffhanger, near the end.

**The beats sheets,** `build/review/beats_vs_<ref>_1.png` and `_2.png`, are the review. Open both and look. The reference is on top, the new episode below, and each column is the same story beat, grabbed from the finished MP4s at phone size:
- hook, title, payoff (the replay's call to action);
- the first question card, the first exhibit, the first interview's name card (the first one after a question card);
- silence (the first `"music": "out"` shot's last line), board;
- cliff A (the cliffhanger's frame A, before the jump and the flicker), cliff B + CTA (paused on frame B);
- end card.

A beat the episode doesn't have is a gray "none" cell; a beat that lands on the same moment as an earlier one (Episode 3's music-out shot is its exhibit) reads "same as exhibit". Each run replaces the earlier sheets, so a sheet on disk is always from the latest run. Put cliff A and cliff B side by side to see the clue as a viewer comparing frames would. For each column, check:
- **Same show:** the grade, fonts, caption style, lower thirds and doorbell HUD match the reference. A difference means a pipeline change leaked into the look. Captions are white at 68 px, at most two lines, with the spoken word in yellow. A reference rendered before the word highlight has smaller, all-white captions; re-render it before comparing.
- **Text:** nothing clipped at the edges, and no caption colliding with a name card, arrow, circle or call to action.
- **Hook:** the hook cell (0.6 s, once the name card has animated in) is a strong, readable close-up. A soft long-lens crop here means the hero still is missing: flag its prompt as the top priority.
- **Payoff and cliffhanger:** the answer to last week's clue is visible in the payoff cell. The new clue is findable in the cliffhanger cells at this size but not obvious, and not under the call-to-action text.
- **End card:** `NEXT_UP` names the right next episode.

**Moments the sheets don't cover:** `$PY pipeline/review.py episodes/<ep> --grab 36.2,40.4,80.6` tiles labeled frames from the video, with each one's shot id, into `build/review/grabs_N.png`, six per sheet, in a few seconds (it skips the checks). Take the times from `build/timeline.json`: a gag's name card, the flicker, a line you doubt. The pacing table and every check are also in the report JSON.

**A line that mixcheck ranks worst:** the worst-line list names the line, not the cause. `nobody-moves-sound-design` shows whether the score or an effect sits over it (`soundprobe.py --lines`); hand it over if the line is under about 12 dB. First look in `.agents/skills/nobody-moves-sound-design/references/baselines.md`: a line listed there with its cause (Episode 3's Ray line, under the replay hit's tail) is known, so report it as known rather than new.

## 6. Report

Send the user `episodes/<ep>/build/<ep>_tiktok.mp4`. For a main episode, the master is too big for chat. When they asked for a comparison, send the two beats sheets too. Report:
- **The verification:** PASS or FAIL per row, the mixcheck result (PASS n/5, the dialogue median, the worst line), and the encoded loudness.
- **Pacing against the reference,** only the deltas that matter, each in plain words ("the payoff lands 13 s in, against 26 s last week").
- **Findings,** most serious first. Give each one the beat or time and the shot id, what you saw, the fix, and the skill that owns it:
  - `nobody-moves-write-episode`: lines, runtime, pacing, clue design;
  - `nobody-moves-produce-episode`: framing, stills, voices;
  - `nobody-moves-sound-design`: the mix.
- **Fallbacks:** the shots still on fallback crops, with the prompts for their stills.
- **The limit:** you judged from frame grabs and measurements, not by watching; ask the user to watch it on a phone.

Don't commit `build/`: the videos, the sheet and the report stay local. Commit only what the render changed in the tree, which is normally just a regenerated `SCRIPT.md`.
