---
name: nobody-moves-render
description: Render a NOBODY MOVES episode or Confessional to its final 1080x1920 MP4s with the shows/nobody-moves pipeline, adjust renderer-owned on-screen graphics, verify the files (format, stream lengths, size, black frames, loudness), review the result side by side against a reference episode with pipeline/review.py, and review the 3D reenactment shots (the REENACTMENT · AI label, the hard cut back, the reenact.png sheet), generated or rendered in Blender (blender_reenact.py's sheet.png, proxy and draft clips). Use this whenever the user wants an episode rendered or re-rendered, requests a video label or graphic adjustment, asks to check, QA or review a finished video, or wants to compare episodes. The nobody-moves-renderer subagent preloads this skill. Writing the script belongs to nobody-moves-write-episode; placing new images, voices and framing fixes belong to nobody-moves-produce-episode; sound changes belong to nobody-moves-sound-design.
---

# Render and review a NOBODY MOVES episode

This skill turns a written, framed episode into its final videos, proves the files are right, and reviews them against an episode the user has already seen. Renderer-owned graphics can be changed here when requested. Script, image and sound problems belong to the skills named at the end; report those rather than changing them silently during a render.

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
- **The reference episode:** by default the previous main episode (for Episode 3, Episode 2). For a Confessional, the latest main episode. For a remake, the published episode it remakes (`ep01r_three_feet_reenacted` against `ep01_three_feet`). Its `build/<ref>_tiktok.mp4` must exist. If it doesn't, render the reference first or review without `--ref`.
- **Nothing else is building this episode.** `make_episode.sh` rewrites `build/soundtrack.wav` and the render reads it; two builds of one episode at once corrupt each other. Check with `pgrep -af '[m]ake_episode\.sh .*episodes/<ep>|[p]ipeline/(build_audio|render|deliver|script_md)\.py .*episodes/<ep>'`, which prints nothing when nothing is building. The bracketed first letters stop the pattern from matching the shell that runs it; a plain `pgrep -af "episodes/<ep>"` always matches itself, and any log monitor left running. Rendering two different episodes at once is safe, just slower, but build their audio one at a time: three `build_audio.py` runs at once on this 4-core container ran for over 17 minutes without finishing, when each takes under 40 s alone (voices cached; about 1.5 minutes with new lines). To render several episodes, run `build_audio.py` for each in turn, then `script_md.py`, `render.py` and `deliver.py` (the rest of `make_episode.sh`) for all of them in parallel.

## 2. Audio and the mix gate

```bash
$PY pipeline/build_audio.py episodes/<ep> --stems
$PY pipeline/mixcheck.py episodes/<ep>
```

- **The timing table** gives the runtime: under 50 s for a main episode, 15–25 s for a Confessional.
- **mixcheck exit 1 stops the render.** Hand the failure to `nobody-moves-sound-design`. Run mixcheck here, right after the `--stems` build: `make_episode.sh` rebuilds the soundtrack without stems, so a later mixcheck can measure old stems.
- **After the render, mixcheck prints `NOTE: stems are N min older than soundtrack.wav`.** That's expected: `make_episode.sh` rebuilds the soundtrack without stems. The numbers you checked before the render still stand if no audio input changed since, which is when this prints nothing: `find episodes/<ep>/episode.py cast.py soundtrack.py pipeline/build_audio.py pipeline/sounds.py -newer episodes/<ep>/build/stems/dialogue.wav`.
- **Fallbacks:** `render.py` (the next step) prints `fallback views (shot: missing stills -> used): ...` for every shot not on its first-choice still, naming each missing choice (`hook: lorraine_bee, lorraine -> yard_before`), and `PLACEHOLDERS` for any still that's missing entirely. Fallbacks are allowed; placeholders mean a missing file. A reenactment whose clip isn't filed prints `REENACTMENT FALLBACK (clip missing): <shot> (<clip>) -> <still>` and renders its fallback still under the label; `clips not provided (rendering fallbacks): ...` lists them. That's fine for a review render, never for posting: say so in the report. List the fallbacks in the report with their prompts. A key in this episode's `STILLS` has its prompt there. For a key requested by an earlier episode, find it with `grep -n '"<key>"' episodes/*/episode.py`. A key with no real prompt anywhere (`aerial`, `cork`) is reported as "no prompt yet".

## 3. A quick look before the long render

```bash
$PY pipeline/render.py episodes/<ep> --contact          # one frame per shot, seconds -> build/contact.png
```

Open `build/contact.png`. A missing still shows as a labeled placeholder card, which is cheaper to catch here than after 10 minutes (an unknown shot kind now stops the audio build instead). Each cell is labeled with its shot id and time, and doorbell shots are grabbed paused on the clue frame, with their call to action. A reenactment gets two cells, 40% in and its last frame before the cut, each with a footer row, `RX <clip> 1x`, or `FALLBACK <still>` in red while its clip is missing; the row sits at the bottom of the cell so the red `REENACTMENT · AI` tag stays visible at the top. Check the tag is there in both cells. Framing problems go back to `nobody-moves-produce-episode`, section 6.

**Episode corner labels:** An episode can set `CORNER_LABEL = "EPISODE 1"` in its `episode.py`. `draw_corner_label()` in `pipeline/render.py` draws it on every reality frame; episodes without that setting get no badge. It is never drawn on a reenactment (the red AI tag is the only badge there), nor on the end card when `CORNER_LABEL` equals `TITLE`. For a requested size, color or placement change, edit that renderer function, then preview the hook, both evidence shots, board and doorbell before the full render. Keep the badge below the apps' top bars and clear of exhibit stamps, the doorbell readout and the board's polaroids; a shot-specific vertical position is appropriate where those elements compete. Run `pipeline/safezones.py episodes/<ep>` after the edit, since it detects badge text along with other text. Do not make a badge universal unless the user asks for the series-wide change.

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

It checks the TikTok copy (`--file master` checks the master), then compares the two episodes, then checks the text against the TikTok, Reels and Shorts UI. It takes about 70 s, or 30 s with `--no-zones`. Each run writes its own report, `build/review/report_<file>[_vs_<ref>].json`, so checking the master doesn't overwrite the comparison.

| Row | Pass | If it fails |
|---|---|---|
| video | H.264, 1080×1920, 30 fps | re-render; something overrode the encoder settings |
| audio | AAC, 48 kHz, stereo | re-render |
| video length, audio length | each within 0.15 s of the timeline total | a stale `timeline.json`: rebuild the audio, then re-render |
| size | under 29 MB, in the decimal MB that `deliver.py` prints | `$PY pipeline/deliver.py episodes/<ep> --max-mb 28` |
| black frames | no black stretch of 0.4 s or more, except question cards and the end card's fade from black | a missing still or a broken shot; find the stretch with `--grab`. Inside a reenactment it's usually the generator's fade from black: raise the shot's `in` past it, or regenerate (`nobody-moves-produce-episode`) |
| WARN reenactment | each reenactment plays its real clip, runs 3–6 s, freezes its last frame for 1 s or less, and cuts to a `still` or `evidence` shot | a missing clip renders the fallback (not postable); a long freeze or a short clip means the locked take outgrew the clip: regenerate it against the take (produce skill, section 5) |
| WARN call to action | each doorbell's call to action stays on screen 1.5 s or more | raise that shot's `"post"` (write skill). Episodes 2 and 3 hold the replay's for only 0.95 s |
| PASS/WARN TikTok, Reels, Shorts | no text under that app's buttons, top bar or description (`pipeline/safezones.py`) | open `build/review/zones.png`: text under an app's UI is magenta. Move the camera (`kb`) or the element, per `nobody-moves-produce-episode` section 6. Episodes 1–3 pass on all three |
| info Reels ads | shots with text below y 1248, Meta's limit for sponsored Reels | nothing, for ordinary posts. Only matters if the user boosts a Reel |
| loudness (info) | about −14 LUFS, true peak −1.0 to −1.2 dBFS after AAC | off by more than 1 LU means the soundtrack wasn't mastered: rebuild the audio |
| ref (info) | "all file checks pass" for the reference | the reference's video doesn't match its timeline, so its beat grabs are misplaced: re-render it before comparing |

**The pacing table** compares the two timelines. Read the deltas against the format rules, not against zero:
- **runtime:** under 50 s for a main episode (Confessional 15–25).
- **title at:** empty for a new main episode, which has no title card (the corner label is the title); about 5–6 s in the published Season 1.
- **first question at / reenactments / first reenactment at:** the easy comment question by about 10 s (it's on the board, so read it from the beats sheet when there's no question card); at most 2 reenactments, about 20% of the runtime or less, the first one soon after the question.
- **payoff at:** the replay's call to action, within about 25 s. It's empty for Episode 1 and for Confessionals.
- **words per minute:** 110–120 overall, and about 165 while someone is speaking (words per minute ÷ speech share; 150 is the floor). Against a Season 1 reference expect a faster pace; much faster than 165 while speaking reads as rushed, and the captions stop being readable.
- **speech share, mean shot length and longest shot:** a shot of 10 s or more is a long hold on a still; check the reference had the same.
- **music-out shots:** each reenactment's cut-back, plus one or two before a punchline or reveal.
- **CTA on screen:** each doorbell's call-to-action hold, in seconds (the WARN row).
- **score builds to:** the shot the build's rule picks (the last `"climax": True`, else the last doorbell that flickers), read from the timeline, not measured. It should be the cliffhanger, near the end.

**The beats sheets,** `build/review/beats_vs_<ref>_1.png` and `_2.png`, are the review. Open both and look. The reference is on top, the new episode below, and each column is the same story beat, grabbed from the finished MP4s at phone size:
- hook, title, payoff (the replay's call to action; none for a cold-open doorbell without a flicker);
- reenact (the first reenactment, 60% in), cut back (0.5 s into the shot after it);
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

**The reenactment sheet,** `build/review/reenact.png`, has one row per reenactment, grabbed from the MP4: its first frame, 25%, 50% and 75% in, its last frame before the cut, and the first frame after it. Open it and check every cell:
- **No human anywhere:** no person, hand, glove, foot, face, silhouette, shadow or reflection.
- **The label:** `REENACTMENT · AI` and its stamp are legible in every reenactment cell and gone in the cell after the cut; no cap, beam or key action plays behind them; no yellow series badge under them; no generated text, chyron, title card or letterbox bars in the picture.
- **The move:** one ornament, one rigid move, nothing bending, stepping or turning, on a locked camera; the ornament on-model (Garrison's hands and cap unchanged, Lorraine bare and beak-left, Deb on two legs); bright and obviously CG at this size.
- **Canon:** nothing contradicts SERIES.md (the doorbell tables, every window dark before 03:15, no hidden change before its payoff, nothing touching Deb).
- **The cut:** the cell after the cut is the real, unmoved ornament, back in its spot, at about the same size.

A failure goes to `nobody-moves-produce-episode` (a new clip or keyframe), or to `nobody-moves-write-episode` when the theory itself breaks canon.

**Blender renders run only on the user's machine,** never in a cloud session; if you are in one, say so and stop rather than rendering. **A Blender clip** (a shot with a `"blender"` dict, a `<key>_bl` clip rendered by `pipeline/blender_reenact.py`; `docs/BLENDER_REENACTMENTS.md`) gets the same checks, plus:
- **Its own sheet first:** `build/blender/<clip>/sheet.png` from `--preview` (frame 0, each beat, the move + 0.5 s, the last frame before the cut; the red box is the AI tag's zone, the blue line the button column) and `preview.mp4` (true timing, with the soundtrack). Nothing may enter the red box; the move starts on its word and the landing comes after it.
- **The run's WARN lines are review findings:** the tag zone, the cut-back match (the real ornament on the hard cut sits where, and as big as, the clip's first frame shows it; the warning names the `kb` the next still needs), effect coverage, feet hidden at the cut, and the timing. Report each one. The sidecar `clips/<key>.blender.json` keeps them under `checks`.
- **Proxy and draft:** a clip rendered with a stand-in model (striped, named `_PROXY`, `proxy: true`) or at draft quality (540×960) is a placeholder. `review.py` warns ("rendered with a PROXY model", "a draft render, not final") and `deliver.py` refuses it unless `--allow-draft` (which `make_episode.sh` passes outside `NM_FINAL=1`). Say in the report that the episode isn't postable until a final with filed models replaces it (`--quality final --require-models`, on a GPU machine).
- **Rigid by construction** (only the root moves, the yaw never changes, checked every frame), so look for staging, not deformation: the subject reads as the library character, the set is dark with the subject the brightest thing, and the label is `REENACTMENT · AI` like every reenactment.

**The end card,** on an episode with a reenactment, reads "Footage, reenactments and voices made with AI." over "The flamingo is real.", fully visible from about 0.65 s into the card; the build already refuses a card that shows it for under 1.8 s. Grab the card's start plus 0.7 s with `--grab` if in doubt. Without a reenactment it reads "Reenactments and voices made with AI." when the soundtrack holds an ElevenLabs voice or a locked v4 take (`recordings/<rec>.v4.*`), else "Reenactments dramatized with AI."; the renderer reads that from `timeline.json`, not from `NM_VOICES`, so it follows the build. A v4 take copied to `recordings/` without the `.v4` counts as human and drops "voices": on a re-voiced episode, grab the card's start plus 1.9 s and check the line.

**The zones sheet,** `build/review/zones.png`, has one row per app (TikTok, Reels, Shorts). It shows the first name card, the lowest text, the first reenactment's tag, the last call to action, the end card and every moment that warned, with the app's covered areas shaded red and text inside them in magenta. It's rendered from the timeline, not grabbed from the MP4, so it needs no render and can run before one.

**Moments the sheets don't cover:** `$PY pipeline/review.py episodes/<ep> --grab 36.2,40.4,80.6` tiles labeled frames from the video, with each one's shot id, into `build/review/grabs_N.png`, six per sheet, in a few seconds (it skips the checks). Take the times from `build/timeline.json`: a gag's name card, the flicker, a line you doubt. The pacing table and every check are also in the report JSON.

**A line that mixcheck ranks worst:** the worst-line list names the line, not the cause. `nobody-moves-sound-design` shows whether the score or an effect sits over it (`soundprobe.py --lines`); hand it over if the line is under about 12 dB. First look in `.agents/skills/nobody-moves-sound-design/references/baselines.md`: a line listed there with its cause (Episode 3's Ray line, under the replay hit's tail) is known, so report it as known rather than new.

## 6. Report

Send the user `episodes/<ep>/build/<ep>_tiktok.mp4`. For a main episode, the master is too big for chat. When they asked for a comparison, send the two beats sheets too. Report:
- **The verification:** PASS or FAIL per row, the mixcheck result (PASS n/m: 6 hard checks with a reenactment, 5 without; the dialogue median, the worst line), and the encoded loudness.
- **Pacing against the reference,** only the deltas that matter, each in plain words ("the payoff lands 13 s in, against 26 s last week").
- **Findings,** most serious first. Give each one the beat or time and the shot id, what you saw, the fix, and the skill that owns it:
  - `nobody-moves-write-episode`: lines, runtime, pacing, clue design;
  - `nobody-moves-produce-episode`: framing, stills, voices, reenactment clips and keyframes;
  - `nobody-moves-sound-design`: the mix.
- **Fallbacks:** the shots still on fallback crops, with the prompts for their stills, and any reenactment still rendering its fallback (the episode isn't postable until its clips are filed).
- **The limit:** you judged from frame grabs and measurements, not by watching; ask the user to watch it on a phone.

Don't commit `build/`: the videos, the sheet and the report stay local. Commit only what the render changed in the tree, which is normally just a regenerated `SCRIPT.md`.
