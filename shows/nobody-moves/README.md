# NOBODY MOVES

A fictional true-crime parody for short-form video where every witness is a lawn ornament. The episodes are built from AI stills with slow camera moves, captions and scratch voices. Nobody moves while anyone is watching: in reality (every still and the doorbell cam) only the camera moves. An ornament moves only in a labelled 3D **reenactment**, the narrator's theory, which cuts hard back to the real ornament, unmoved, denying it. The series bible (cast, visual style, planted clues, episode roadmap) is in [`SERIES.md`](SERIES.md).

This folder is independent of the `watch` skill in the rest of the repo.

## Quick start

```bash
./setup.sh                                   # once: venv, Kokoro TTS model, fonts (PyPI + GitHub only)
./make_episode.sh episodes/ep01_three_feet   # ~10 min on a laptop CPU
./setup.sh --blender                         # optional: Blender (bpy, Python 3.11) for "Blender reenactments"
```

You need Python 3.10–3.13, which Kokoro requires. `setup.sh` finds one automatically. On a Mac the built-in `python3` is too old, so run `brew install python@3.12` first if setup says none was found.

Outputs, in `episodes/<episode>/build/` (not committed):

| File | What |
|---|---|
| `<episode>.mp4` | Master render, 1080×1920, 30 fps, about 9 Mbps |
| `<episode>_tiktok.mp4` | Upload copy under 29 MB |
| `soundtrack.wav`, `timeline.json` | The mixed audio and the shot, caption and word timings |

`make_episode.sh` also rewrites `episodes/<episode>/SCRIPT.md`, the timecoded script. Hand-written notes for an episode go in its own `NOTES.md`, which `SCRIPT.md` links to; anything typed into `SCRIPT.md` is lost on the next build.

## Making a new episode

With Claude Code (or any Agent Skills host), four skills in this repo do the whole loop:
- **`nobody-moves-write-episode`** writes the script, the image prompts and the continuity updates.
- **`nobody-moves-produce-episode`** builds and checks the episode.
- **`nobody-moves-render`** renders the final videos, verifies them and reviews them against another episode (the `nobody-moves-renderer` subagent runs it).
- **`nobody-moves-sound-design`** changes the score and sound effects and measures the mix.

To start a different show with this pipeline, use the **`ai-tiktok-series`** skill.

Just ask for "the next episode". By hand:

1. Copy an episode folder, or the template at `.agents/skills/nobody-moves-write-episode/references/episode-template.py`, to `episodes/epNN_<name>/episode.py`.
2. Reuse the **series library** in `stills/` (`garrison`, `porch`, `holes`, `yard_before`, `yard_after`, `aerial`, `lorraine`, `lorraine_bee`, `lorraine_easter`, `chime`, `basin_counsel`, `ray`, `cork`, and the derived doorbell frame `yard_gone`); every episode can use it by key. Episode-only stills go in `episodes/<ep>/stills/`, and a still there overrides a library still with the same key. To generate new ones, use the style prompt in `SERIES.md`.
3. Edit `episode.py`: the title, `NEXT_UP`, `ANSWER`, `STILLS` (prompts for any new images), `CLIPS` (prompts for any reenactment clips) and the `SHOTS` list.
4. Place coordinates with `.venv/bin/python pipeline/grid.py stills/<key>.webp -o episodes/<ep>/build/<key>_grid.png [--box x0,y0,x1,y1] [--bright 2.5]`. It overlays a grid labeled in the same fractions `episode.py` uses. Always pass `-o`: without it the grid image lands next to the still, in the library.
5. Check framing without a full render:
   ```bash
   .venv/bin/python pipeline/build_audio.py episodes/ep02_x --stems
   .venv/bin/python pipeline/mixcheck.py episodes/ep02_x                    # loudness, dialogue over music, music-out, hits
   .venv/bin/python pipeline/render.py episodes/ep02_x --contact            # one frame per shot -> build/contact.png
   .venv/bin/python pipeline/render.py episodes/ep02_x --preview 1,12.5,30  # frames at those seconds
   ```
6. Run `./make_episode.sh episodes/ep02_x`, then `.venv/bin/python pipeline/review.py episodes/ep02_x --ref episodes/ep01_three_feet` to verify the video and compare it with an earlier episode, beat by beat (`build/review/beats_vs_<ref>.png`).

The voice clips are cached by line text, so rebuilding after an edit only re-voices the lines you changed. Changing a character's `pitch` or `altered` re-processes their cached clips without voicing them again, which matters for an ElevenLabs voice, where voicing costs money.

## `episode.py` reference

Positions are **fractions of the source image**: `(0.5, 0.5)` is the center. Zoom `1.0` shows the whole image and `2.0` is a 2× push-in.

```python
V("still_key", (cx, cy, zoom_start), (cx, cy, zoom_end), look)   # one camera move on one still
L("WHO", "caption text", "optional spoken text")                 # a line; spoken text fixes pronunciation ("1994" -> "nineteen ninety-four")
P(0.5)                                                           # a pause, in seconds
```

The spoken text can carry ElevenLabs audio tags in square brackets, which steer the delivery: `L("GARRISON", "I didn't see nothing.", "[too quickly] I didn't see nothing.")`. Tags go to an ElevenLabs voice as written, so give that character `"model": "eleven_v4"` in `cast.py`. `build_audio.py` warns when tags go to an older ElevenLabs model (it may read them out loud) or to a Kokoro voice (it leaves them out). In the word highlight a sound tag (`[sighs]`, `[exhales]`) keeps its own stretch of the line, so no word lights up during it, while a direction (`[too quickly]`, `[quietly]`) takes no time. `SCRIPT.md` prints a line's tags after it as a direction, *(too quickly)*, for anyone recording their own take.

Before anything is voiced, `build_audio.py` stops and names the shot and line when a tag would be both shown in a caption and sent to the voice (a caption with brackets and no third argument), or when the spoken text has a bracket that isn't a whole tag. Brackets that are only on screen are fine once the spoken text is given separately: `L("NARRATOR", "His statement: [REDACTED].", "His statement: redacted.")`. Lines with a recording skip these checks.

`views` is a list of camera moves. The shot uses the first one whose still exists, so list the ideal image first and a crop of one you already have as the fallback. The optional `look` is `"anon"` (blurred and cold, for anonymous sources) or `"longlens"` (a soft stakeout crop).

`DERIVED_STILLS` brightens a still without a new image: `{"garrison_lift": {"from": "garrison", "gamma": 1.5}}` gives a key that views can use like any still. The renderer computes it in memory: an optional `"blur"` (a Gaussian radius), then `out = in ** (1 / gamma)`, then `"tint"` (per channel) and `"gain"` multiply. The pixels and framing are the source's, so its coordinates still apply (place them with `grid.py` on the source) and later episodes and doorbell frames still match. A key can lift a library still under its own name (`"cork": {"from": "cork", "gamma": 1.5}`); a file of that name in the episode's own `stills/` wins over the entry.

| `kind` | What it draws | Fields |
|---|---|---|
| `still` | A camera move on a still, captions, and an optional name card | `views`, `items`, `post`, `lower_third=(name, line2, line3)`, `lower_third_at`: `"last"` (in on the last line) or `"cut"` (fully on from the first frame to the cut, with no fade, for a short or silent cutaway whose card is the joke) |
| `evidence` | A still plus a camera flash, an EXHIBIT tag and timestamp, and drawn annotations | as `still`, plus `label`, `stamp`, `annot_arrow={"from","to","label"}`, `annot_circles=[(x, y, r)]` |
| `title` | Series title and episode name | `views`, `min` |
| `qcard` | A black card where the interviewer's question types out | `text`, `min` |
| `board` | Cork board with polaroids, red string and an index card that lands on the last line | `kb`, `card` (default "WHO MOVED DEB?"), `polaroids=[(still, (x0, y0, x1), label, fx, fy, size, rotation, look)]` (the first is the hub). Uses the `cork` still if present, otherwise a drawn board |
| `doorbell` | Night-vision cam: jump-cuts from A to B, flickers after the last line, pauses on B and shows a call to action | `frame_a`, `frame_b`, `kb`, `clock_start` (seconds past 03:11:00, or `"HH:MM:SS"` with `jump_after`, a whole number of seconds), `frames=(a, b)`, `cta=(line1, line2)`, `cta_sub`, `camera` (the top-right label). For the hidden clue in frame B: `alter_box=(x0, y0, x1, y1)` mirrors a region (it turned around); `alter_glow=(x, y, r)` lights a point (it switched on). `lit=[(x, y, r)]` lights points in both frames, for a light that is already on (continuity, not a clue). `"flicker": False` shows only the jump (a cold open): no flicker, frame label, call to action, glitches, riser, reveal hit or hush |
| `reenactment` | A generated 3D clip of the narrator's theory under a red `REENACTMENT · AI` tag, with a hit and a swell, then a hard cut (see **Reenactments**) | `clip`, `dur`, `in`, `out`, `speed`, `label`, `stamp`, `fallback`, `kb`, `look`, `cue`, `cut_silence`, `interp`, `items`, `pre`, `post`, `min` |
| `end` | End card with `NEXT_UP` and the AI disclosure | `min` |

Every shot also takes `note` (the stage direction for `SCRIPT.md`), `sfx`, `"music": "out"` to cut the score for that shot, and `"climax": True` to make the score build to that shot instead of the last doorbell shot (for an episode without a doorbell ending, like a Confessional). The `sfx` options are `sting`, `sting_end`, `sting_soft`, `shutter`, `wind`, `chimes` and `crickets`. The score, the typewriter clicks, and the risers, whooshes and hits are added automatically.

Episode-level fields besides the title, `NEXT_UP`, `ANSWER`, `STILLS` and `SHOTS`: `CORNER_LABEL` (a yellow badge on every reality shot; not on reenactments, nor on the end card when it equals `TITLE`), `CAST` and `SOUNDS` (merged over the series ones), `DERIVED_STILLS` (above), `CLIPS` and `CLIP_SOURCES` (**Reenactments**), and `HUMAN_TAKES`: the lines a human records only when a TTS voice can't land them after 3 tries, as `{"rec": "one line of direction"}` or a list of recording names. `SCRIPT.md` stars those lines and lists them under "Lines to record by a human".

`build_audio.py` checks the shots before anything is voiced and stops on a mistake, naming the shot and the fix: a shot id used twice (recordings, clips and captions are keyed by it), an unknown `kind` (with the closest match), a `lower_third_at` it doesn't know or `"last"` on a shot with no lines, a doorbell `flicker` that isn't True or False or a `jump_after` that isn't a whole number, and every reenactment error below. It also warns, on any shot, about a name card fully legible for under 1.2 s, and on a shot with no lines about a name-card note over 20 characters a second of legible time: a silent cutaway's card is its joke.

## Reenactments

A reenactment is the narrator's dramatized theory of what happened: a generated 3D clip (any aspect ratio, cover-cropped to 9:16, 3–6 s) in which an ornament moves as a rigid object on a locked camera. It is labelled `REENACTMENT · AI` on every frame, lands on a hit and a swell, and ends in a hard cut, in picture and sound, back to the real ornament, unmoved, for the denial. Reenactments are theories, never evidence: no human, no clue, nothing the bible contradicts. The rules are in `SERIES.md`; the Episode 1 remake (`episodes/ep01r_three_feet_reenacted`) is the worked example. Its `REENACTMENT_PROMPTS.md` walks through generating the reference sheets, keyframes and clips; its `tools/fit_takes.py` prints, from a build's `timeline.json`, the pace against the 50 s ceiling and, for each reenactment, the hold time to write into the motion prompt and the `in` to set once the clip exists; `tools/make_prompts_md.py` regenerates `REENACTMENT_PROMPTS.md` from `episode.py` and the timeline. The decisions behind it are in [`docs/DECISIONS_EP01R.md`](docs/DECISIONS_EP01R.md), and `docs/` also holds the design of the final voices ([`docs/AUDIO_ELEVENLABS_V4.md`](docs/AUDIO_ELEVENLABS_V4.md)).

```python
{"id": "heist", "kind": "reenactment",
 "clip": "rx_heist_gnome", "in": 0.25, "dur": 4.05,              # play the take from 0.25 s, cut at 4.05 s
 "label": "REENACTMENT · AI", "stamp": "THEORY #1: THE GNOME",
 "fallback": [V("rx_heist_gnome_key", (0.5, 0.55, 1.0), (0.5, 0.52, 1.35)), V("garrison", (0.47, 0.52, 1.6), (0.47, 0.50, 2.3))],
 "pre": 0.35, "items": [L("NARRATOR", "That night, he was facing her. Then he made his move.")]},
{"id": "g_deny", "kind": "still", "music": "out", "pre": 0.45, ...},  # the cut back: the real gnome, in silence
```

| Field | Default | What it does |
|---|---|---|
| `clip` | required | The clip key, prefixed `rx_`: `episodes/<ep>/clips/<key>.mp4`, else the series library's `clips/<key>.mp4` (an episode clip overrides a library one, as with stills) |
| `dur` | none | The shot's exact length; the clip is cut there, mid-action if need be. Recommended: the timing then stays the same before and after the clip exists. `pre` + the lines + at least 0.5 s, at most 6.0 |
| `in`, `out` | 0, the clip's end | The part of the clip to play. `in` is the timing knob: move it so the move lands on its word |
| `speed` | 1.0 | 0.25–2.0, or `"fit"` (stretch the trimmed clip to the shot). Keep 1.0: slow motion belongs in the generated take, or in a one-time retime at intake. Without `dur`, the shot runs the longer of its lines and its clip; a clip shorter than the lines freezes on its last frame |
| `label` | `"REENACTMENT · AI"` | Must be exactly that: every reenactment is marked AI on screen. The theory and any escalation go in the stamp |
| `stamp` | none | The mono line under the tag, such as `"THEORY #2: THE GOOSE (DIRECTOR'S CUT)"`. No clock times. Tag and stamp must end before x 930 |
| `fallback` | `[]` | Views to render, under the same tag, while the clip is missing: the first whose still exists (the 3D keyframe, then a crop of the real still), else a "clip pending" card. The episode builds either way |
| `kb` | locked at the centre | The camera on the clip, `(cx, cy, zoom)` pairs as in `V()`; keep it locked |
| `look` | `"reenact"` | The bright, saturated, bloomed grade that sets a theory apart from reality's film grade; `None` for the plain grade |
| `cue`, `cut_silence` | `True`, 0.6 | The hit (a reversed suck-in 0.35 s before the first frame, the downbeat on it) and a swell under the lines that peaks into the cut; then `cut_silence` seconds of total silence (score and the shot's own sounds) after it. The clip's own audio is never used |
| `interp` | `"nearest"` | How frames are picked at a speed other than 1: `"nearest"` repeats frames, `"blend"` cross-fades them (it ghosts) |

A reenactment takes no `lower_third`, `"music": "out"` or `climax`, can't be the last shot, and an episode with one needs an end card of at least 2.45 s: the end card's disclosure then fades in with the title, fully visible from 0.65 s, and reads "Footage, reenactments and voices made with AI." (An episode without a reenactment reads "Reenactments and voices made with AI." when its soundtrack holds an ElevenLabs voice, a line voiced by one or a locked v4 take, and "Reenactments dramatized with AI." otherwise. `timeline.json` records which lines those are, so the card follows the build, whatever `NM_VOICES` says when `render.py` runs.) `build_audio.py` also stops on a label other than `REENACTMENT · AI`, a tag past x 930, lines longer than `dur`, `in`/`out` outside the clip, `"speed": "fit"` on a shot with nothing to give it a length (no lines, pauses, `pre`, `post`, `min` or `dur`), and a clip that isn't 30 fps or carries a display rotation or non-square pixels (file it with `clips.py`). It warns about a length outside 3–6 s, a freeze over 1 s, a speed other than 1.0, a moving `kb`, a stamp with a clock time, a next shot that isn't a still or evidence shot, a last line ending under 0.5 s before the cut, the previous shot's last line ending under 0.35 s before it (the hit's suck-in would play over it), a `sting_soft` on the shot before, more than 2 reenactments or over 20% of the runtime (in a Confessional, whose share is always over 20%, more than one or one over 5 s instead), a missing clip, a clip with no `clips.json` entry, and the prompt lint below.

**Prompts.** `CLIPS = {"rx_key": "<motion prompt>"}` holds each clip's image-to-video prompt, as `STILLS` holds image prompts, and `CLIP_SOURCES = {"rx_key": {"keyframe", "keyframe_refs", "seconds", "aspect", "camera_fixed", "negative", "seedance_suffix"}}` records what the generators were given. A motion prompt may name no person once its negated clauses ("no people") are stripped, and should end with the bible's motion suffix. The lint treats hand(s), arm(s), finger(s), figure(s), kid(s), man/men and the like as human words even when they describe an ornament, and a negation strips only the words after it ("his hands never move" fails), so describe the pose instead ("as one rigid piece, his pose unchanged"), as the remake's `CLIPS` do; an `rx_` keyframe in `STILLS` should end with the still suffix and carry no date, clock time or "slow motion". The suffixes are read from `SERIES.md`. `build_audio.py` runs this lint on every build.

**Clips.** Generate the clip from its keyframe at 9:16, then file it:

```bash
.venv/bin/python pipeline/clips.py add episodes/<ep> rx_heist_gnome take3.mp4 --generator "Kling 2.5" [--retime 0.5] [--credit "..."]
.venv/bin/python pipeline/clips.py add series rx_key take.mp4 --generator "..." --episode episodes/<ep>   # a recurring library clip
.venv/bin/python pipeline/clips.py sheet episodes/<ep>    # first, middle and last frame of each clip -> build/review/clips.png
.venv/bin/python pipeline/clips.py lint episodes/<ep>     # the prompt lint on CLIPS and the rx_ keyframes
```

`add` files a mezzanine (H.264 at a constant 30 fps, no audio, longest side 1920 or less, never cropped, turned upright with square pixels: a phone clip's display rotation and a non-square pixel aspect are applied, since the renderer reads neither) in the episode's `clips/` (or the show's `clips/` for `series`), and records it in that folder's `clips.json`: the source and mezzanine sha1, generator, prompt and negative (read from `CLIPS` and `CLIP_SOURCES`; `--prompt` only for a clip with no `CLIPS` entry), keyframe, references, retime, date, size, length, credit and `"ai_generated": true`. It refuses a file with no video, under 1 s or over 10 s, a prompt that fails the lint, and an existing clip without `--force`, and warns when a 9:16 crop leaves under 720 px of width, when the clip starts or ends black, or when its middle frame is too dark. `--retime F` retimes once, with optical flow (0.5 = half speed). Commit clips like stills (about 6 MB per 5 s).

**After a clip lands, rebuild the audio:** the shot's length can depend on the clip, so `render.py` stops when a clip changed since `build_audio.py` ran. A reenactment's timeline entry records the clip it used (`clip_file`, `clip_sha1`, `clip_in`, `clip_out`, `clip_speed`, `clip_freeze_at`, `clip_missing`, `clip_fallback` and the resolved `label`, `look`, `cue` and `cut_silence`). The renderer decodes each clip from frame 0 through a pipe, never seeking, so a preview, the contact sheet (two cells per reenactment: 40% in and the last frame before the cut) and the full render give the same pixels. `review.py` adds a "reenact" and a "cut back" beat, the reenactments' share of the runtime, warnings for a missing clip, a length outside 3–6 s, a long freeze or a next shot that isn't the real ornament, and `build/review/reenact.png`: each reenactment's first frame, 25%, 50% and 75% in, the last frame before the cut and the first after it, to check for humans, the tag and the cut back. `mixcheck.py` fails a reenactment whose cut isn't followed by silence.

## Blender reenactments

A reenactment can also be **rendered in Blender** instead of generated. **Blender renders run on your own machine only.** Never in a cloud or remote session: `pipeline/blender_reenact.py` refuses to start Blender when `CLAUDE_CODE_REMOTE` is set, and its selftest reports the rendering half as skipped there. Render finals and previews on your computer, then file the clip with `blender_reenact.py`.

The `pipeline/blender_reenact.py` tool builds the scene from the cast's 3D models (or a procedural stand-in), times the move to this build's own words in `build/timeline.json`, renders it, and files it like any other clip, through `clips.py add`: `clips/<key>.mp4`, its `clips.json` entry, and a `<key>.blender.json` sidecar with the full provenance. `render.py` plays it like any clip. The ornament is rigid by construction (only its root moves; it never turns), the camera is locked, and no human can appear. The label is still `REENACTMENT · AI` (decision D4). The full guide is [`docs/BLENDER_REENACTMENTS.md`](docs/BLENDER_REENACTMENTS.md); making and filing the 3D models is in [`models/README.md`](models/README.md).

A shot opts in with a `"blender"` dict and a clip key of its own, ending in `_bl` (an AI clip's key, one in `CLIPS`, is an error):

```python
{"id": "heist", "kind": "reenactment",
 "clip": "rx_heist_gnome_bl", "in": 0.0, "speed": 1.0, "dur": 4.05,     # dur required, in 0, speed 1.0
 "blender": {"template": "heist", "subject": "garrison", "props": [],
             "move_on": "move", "move_at": 3.23, "flare_on": "move",   # the word, then seconds as a fallback
             "camera": "beside_deb", "options": {"path": "left", "travel": 0.25, "accel_s": 0.12}},
 "kb": ((0.5, 0.5, 1.0), (0.5, 0.5, 1.0)), "label": "REENACTMENT · AI", "stamp": "THEORY #1: THE GNOME",
 "fallback": [V("rx_heist_gnome_bl_key", (0.5, 0.5, 1.0), (0.5, 0.5, 1.0)), V("garrison", ...)], ...}
```

The templates are `heist` (a subject dead still in a laser grid until its word, then a rigid glide, cut mid-glide) and `action` (Lorraine rocks on one to three words, tips on `tip_on` and drops a step in front of a fireball, landing on `land_on`). The beats name words in the shot's own lines (`"goose#2"` for the second one, or `{"word", "nth", "edge", "offset"}`), with `move_at`/`tip_at`/`land_at`/`flare_at` seconds as the fallback. `build_audio.py` checks the dict on every build, so a typo stops the build before anything is voiced. The Episode 1 remake's two reenactments carry one each.

**Install** (once; either works):
- `./setup.sh --blender`: `.venv-bpy/`, Blender as a Python module (`pip install bpy==5.0.1`, which exists for **Python 3.11 only**). It is found automatically.
- The **Blender 5.0 app** from blender.org, then `export NM_BLENDER=/path/to/blender` (macOS: `/Applications/Blender.app/Contents/MacOS/Blender`). Recommended on a GPU machine.

Then check the machine: `.venv/bin/python pipeline/blender_reenact.py --selftest` (pure-Python checks, then a tiny render, about a minute on a CPU). `pipeline/selftest.py` runs it with `--allow-skip`, and prints SKIP for the rendering half where no Blender is found.

```bash
B=pipeline/blender_reenact.py
.venv/bin/python $B episodes/<ep> --dry-run                  # the plan: each beat (word -> seconds -> frame), engine, cost
.venv/bin/python $B episodes/<ep> --preview [--shot heist]   # look and timing, never filed: build/blender/<clip>/sheet.png
.venv/bin/python $B episodes/<ep> --build                    # files a draft, or "up to date" (make_episode.sh runs this)
.venv/bin/python $B episodes/<ep> --quality final --require-models   # the deliverable, on a GPU machine
.venv/bin/python $B episodes/<ep> --keyframe                 # frame 0 -> stills/<clip>_key.png, a fallback view
.venv/bin/python $B model add garrison garrison.glb --source "..." --ai    # models/README.md; also: model list
.venv/bin/python $B --showcase garrison --mode sheet --preview          # a model's (or proxy's) four views
```

**Preview, draft, final.** `--preview` renders every 6th frame plus the beat frames at 270×480 (Cycles 12 spp) into `build/blender/<clip>/`: `sheet.png` (frame 0, each beat, the move + 0.5 s, the cut, with the AI tag's zone and the button column drawn), `contact.png` and `preview.mp4` (the held frames, with the shot's slice of the soundtrack). It never touches `clips/`. A **draft** (540×960, 24 spp) is filed so the whole episode can be built and watched, but it is flagged: `review.py` warns and `deliver.py` refuses it. A **final** (1080×1920, 128 spp, volumetric haze) is the deliverable. Until `models/<name>.glb` is filed, the subject renders as a striped `_PROXY` stand-in, recorded as `proxy: true`, which `deliver.py` refuses too (`--allow-draft` for a test upload).

**GPU.** `--engine auto` picks Eevee on a real GPU, else Cycles; `--device auto` uses OptiX, CUDA, HIP, Metal or oneAPI when Cycles finds one, else the CPU. A final on 4 CPU cores takes many hours a clip: the driver estimates about 113 hours for the heist's 123 frames at 1080×1920 (about 45 hours if the guide's measured frame time is scaled up, §12.2 of `docs/BLENDER_REENACTMENTS.md`). The driver prints its estimate before rendering and asks for `--yes` above 30 minutes; a heist draft on the CPU is estimated at about 133 minutes, so the CPU route is for previews: render drafts and finals on a GPU machine (the guide's "Rendering finals on a GPU machine"). The plan line (`--dry-run --reprobe`) must say `eevee gpu` or `cycles gpu OPTIX` (or CUDA, HIP, METAL).

**In `make_episode.sh`.** An episode with a `"blender"` dict builds in this order: `build_audio.py` (word times) → `blender_reenact.py --build` (at `NM_RX_QUALITY`, default draft) → `build_audio.py` again (records the filed clip) → `script_md.py` → `render.py` → `deliver.py --allow-draft`. Without Blender, or over the time budget, the pass prints a WARN and the reenactment plays its fallback still. `NM_FINAL=1` is the release build: final quality, a missing model is an error, no Blender is an error, and `deliver.py` refuses a draft or proxy. Episodes without a `"blender"` dict build exactly as before.

**Reviewing a Blender clip.** Look at `build/blender/<clip>/sheet.png` first, and read the run's WARN lines: the tag zone (no subject, beam or fireball under the AI tag), the cut-back match (the real ornament on the hard cut sits where, and as big as, the reenactment's first frame showed it; the warning prints the `kb` that would match), the effect's size, the feet at the cut, and the timing (the drop on its word, the landing 0.25 s or more after it). After filing, the clip goes through the usual `clips.py sheet`, `render.py --contact` and `review.py` checks. The `.blender.json` sidecar records the Blender version, device, quality, models, beats, checks and both cache keys.

## Captions

Each line's caption is its `L(...)` text: white, 68 px, left of TikTok's buttons, with the word being spoken in the show's yellow.

- **Timing comes from the voice itself.** `pipeline/words.py` measures each finished voice clip. The pauses at commas and full stops split the line into phrases, and each word gets its share of the phrase's voiced time by its length in phonemes. `build_audio.py` stores the result as `words` in each caption of `timeline.json`. It follows any voice (Kokoro, ElevenLabs or your own recording), and spoken text that differs from the caption ("three twelve" for "3:12") is mapped back onto the caption's words.
- **At most two lines,** because a third would run into the name card. A line holds about 20 characters, so a longer caption is split into chunks that each appear when the voice reaches their first word. The splits prefer sentence ends, then commas, and avoid a lone word, a split name ("Birchwood / Court") or a chunk on screen under 0.7 s.
- **Self-check:** `.venv/bin/python pipeline/words.py` checks the timing on synthetic speech, offline.

## Voices

By default every line is spoken by [Kokoro](https://github.com/thewh1teagle/kokoro-onnx), an open-weight text-to-speech model that runs locally on the CPU with no API key. Each character is a Kokoro preset voice plus a little post-processing: a speaking rate, a pitch shift, and for the anonymous source a "voice altered" filter.

The voices are defined once, in [`cast.py`](cast.py), and every episode uses them. Kokoro is deterministic, so the same line with the same settings and model files always produces the same audio. `setup.sh` checks the model files against pinned checksums, and `requirements.txt` pins the TTS packages. That keeps Garrison sounding like Garrison in Episode 12.

- **A new character:** add an entry to `CAST_KOKORO` in `cast.py` (and to `CAST_V4` once its voice is designed). Use an English preset (`af_`, `am_`, `bf_`, `bm_`): `build_audio.py` pronounces voices starting with "a" as US English and all others as British English, so other languages come out wrong. Pick one that's clearly different from the rest of the cast. `cast.py` has a commented-out suggestion for Ray.
- **A one-off speaker in a single episode:** define `CAST = {...}` in that episode's `episode.py`. It's merged over the series cast.
- **Changing an existing voice:** edit its `CAST_KOKORO` entry in `cast.py`. That character changes in every episode the next time each one is built.

The voices are scratch tracks. Recording your own takes is the biggest quality upgrade.

### Final voices: Eleven v4

`cast.py` holds two casts. `CAST_KOKORO` is the scratch cast above. `CAST_V4` holds the final voices, designed with ElevenLabs Voice Design from text prompts (never cloned, never a soundalike) on the `eleven_v4` model, with `"lang"` set to the accent the word timing assumes. Their `voice_id`s are placeholders until each voice is designed; record each one's design prompt, preview text and date beside it. `seed` and `voice_settings` stay out until a test shows v4 honors them. The CHIME keeps its pitch and "voice altered" chain, because the disguise is the joke.

- **Which cast builds.** `CAST` is Kokoro, with the characters listed in `FINAL_V4` switched to v4 once the public voice test promotes them; today it is empty, so the default is all Kokoro. `NM_VOICES=kokoro` forces every character onto Kokoro, and `NM_VOICES=v4` every character onto v4, for an A/B arm: `NM_VOICES=v4 ./make_episode.sh episodes/<ep>`. A v4 build stops before voicing anything when a line's character still has a placeholder `voice_id`, so a v4 arm is never Kokoro in disguise. Any other `NM_VOICES` value stops with a message. An episode's own `CAST` merges over whichever cast is chosen.
- **Audio tags.** `TAGS` in `cast.py` lists each character's approved tags. Untagged is the default; a tag goes only on a punchline or button line, in the spoken text (`L()`'s third argument), at most one tagged line per shot and one NARRATOR tag per episode, and it stays only if the tagged take beats the untagged one in a blind pick. Never laughter, sound-effect, accent, shouting or SSML tags. Kokoro leaves tags out, so a scratch build keeps its timing.
- **Cost and takes.** A v4 line is a paid request, and a take isn't guaranteed to repeat. The voice cache keys the API call on the generation fields only (provider, voice, model, seed, settings and the spoken text with its tags), so a pitch, `altered` or `"lang"` change re-processes the cached clip without paying again. Until takes are locked in the pipeline, keep a chosen take by copying its `build/voice/<WHO>_<key>_raw.wav` to the episode's `recordings/<rec>.v4.wav`. The `.v4` marks a generated take: the build uses it in place of the API, `timeline.json` marks the line `"generated"`, so the end card and `SCRIPT.md` still count it as an AI voice, and `NM_VOICES=kokoro` skips it, so a Kokoro build stays Kokoro. A take copied without `.v4` counts as a human take: it wins over every cast, and on an episode without a reenactment the end card drops "voices". Before posting such an episode, check that `render.py --preview <end start + 1.9>` reads "Reenactments and voices made with AI."

Casting, the settings to verify on the first paid run, locking takes, consent and the rollout are in [`docs/AUDIO_ELEVENLABS_V4.md`](docs/AUDIO_ELEVENLABS_V4.md).

### Kokoro outside this project

`tools/install-kokoro.sh` installs Kokoro for your whole user account: its own environment and model files go in `~/.kokoro`, and a `kokoro` command goes in `~/.local/bin`. It uses the same pinned versions and model files as the show, so you can audition voices or lines anywhere:

```bash
shows/nobody-moves/tools/install-kokoro.sh
kokoro --voices                                              # all 54 preset voices
kokoro "I didn't see nothing." garrison.wav am_fenrir && afplay garrison.wav
```

The `kokoro` command plays the plain preset voice. It doesn't apply `cast.py`'s pitch shift or "voice altered" filter; the episode pipeline adds those.

If voicing fails with `Error processing file ... phontab`, the folder's path is too long for espeak-ng (the pronunciation engine), which has a limit of about 160 characters. Move the project to a shorter path. Both scripts warn when a path is near the limit.

## Score and sound effects

There are no samples or stock audio by default: every sound is synthesized in code in [`pipeline/sounds.py`](pipeline/sounds.py), the show's sound library. The palette is the movie-trailer toolkit, at 48 kHz stereo.

| Sound | How it's made |
|---|---|
| Theme | The show's signature: a sparse A-minor piano ostinato (A C E C A C D# C, 0.62 s per note, with a D on every other bar). It sits on a detuned string pad that moves i–VI–iv–V, with cellos an octave down and violins an octave up. A heartbeat pulse and a high string shimmer come in as the tension builds (see **Dynamics**). |
| Braam | A low brass-like blast: a detuned sawtooth power chord whose filter opens on the attack, saturated so phones can hear it |
| Impact | A sub drop, a punchy mid body, a noise boom and a transient crack. The saturated harmonics carry it on phone speakers. |
| Riser, whoosh | A riser is a noise sweep, rising tones and an accelerating tremolo that peak exactly on the next hit. A whoosh is a noise swell that passes from left to right. |
| Stings | Title and end: braam, impact and a low A-minor piano cluster. Soft: the string chord swelling out of nothing, with a sub underneath. |
| Piano | Additive synthesis: 12 slightly stretched harmonics, each decaying at its own rate, plus a hammer thump |
| Room | One shared stereo hall (decorrelated left and right tails), so everything sounds like it's in the same space |
| Camera shutter | Two filtered noise clicks and a flash-charge whine, landing on an impact |
| Typewriter | Filtered noise keys with a body thump, and a three-tone carriage bell |
| Wind chimes, wind | Random strikes of five pitches with inharmonic overtones, spread across the stereo field; low band-passed noise with slow gusts |
| Reenactment hit, swell | Into each reenactment: a reversed noise suck-in, then an impact and a braam slowed to 0.6x, the downbeat on the clip's first frame. Under it: an overblown string-and-brass crescendo on the theme's chords with timpani-like rolls, quiet under the lines and full at the cut, where it stops dead |
| Night crickets | Three crickets at 4.4, 4.75 and 5.1 kHz in different positions, plus a faint 60 Hz porch-light hum |
| Doorbell glitch, jump | A square-wave buzz in noise; the jump cut adds a short sub hit |

**Automatic hits.** The mix places most effects from the shot kinds, so an episode gets the cinematic treatment without any extra fields:

- a riser sweeps into the title card and lands on the title sting;
- every question card is preceded by a whoosh, then its question types out;
- every `shutter` lands on an impact;
- the doorbell jump cut gets a sub hit;
- a riser runs across the flicker, and a braam and impact land on the call to action.

**Dynamics.** The score starts quietly on the title card and builds toward the last shot marked `"climax": True`, else the last doorbell shot that flickers (a `"flicker": False` cold open never counts), else the end card: the pad swells, the heartbeat fades in around the middle, and the shimmer enters in the last stretch. It hushes under the doorbell flicker so the reveal hit lands. Give a shot `"music": "out"` to cut the score for that shot: silence before a punchline or a reveal is the most dramatic sound there is. The score and risers duck automatically under dialogue.

**Mastering.** The mix is highpassed at 30 Hz, lightly compressed and limited, then normalized in two passes to −14 LUFS with true peaks at −1.5 dBTP, which is TikTok's loudness target. Build with `pipeline/build_audio.py <episode> --stems` to also write `build/stems/{dialogue,score,effects}.wav` for remixing in an editor.

**Reuse.** Every episode uses this same library, so the next episode gets the same theme, hits and effects automatically; choose the extra ones per shot with `sfx`. Each sound seeds its own random stream, so it's identical in every episode no matter what else the episode contains. The mix levels are shared too (`LEVELS` in `sounds.py`). To change the show's sound, edit `sounds.py`: the theme notes are `THEME_NOTES` and the chords are `PAD_CHORDS`.

**Sound kit.** `.venv/bin/python pipeline/sound_kit.py` exports every sound to `sound_kit/*.wav` at 48 kHz (mono or stereo, as each sound is made). That covers:

- the theme (60 s);
- three stings, and the braam, impact, a 2 s riser and the whoosh;
- the shutter, a typewriter key, the bell and a full typed question;
- 20 s beds of wind, chimes and crickets;
- the glitch and the jump.

Use them for Confessionals or trailers in CapCut; they match the episodes exactly.

## Stock assets: local files and third-party APIs

Anything the show uses can come from your own files or from an API instead of being generated.

**Sounds and music.** Point a name in [`soundtrack.py`](soundtrack.py) at a source, and every episode uses it. An episode can override a name with its own `SOUNDS = {...}`. The names are `theme`, `sting`, `sting_end`, `sting_soft`, `riser`, `impact`, `braam`, `whoosh`, `shutter`, `typewriter`, `ding`, `wind`, `chimes`, `crickets`, `glitch`, `jump`, `reenact_hit` (its downbeat 0.35 s in) and `reenact_swell`. Stereo files stay stereo.

```python
SOUNDS = {
    "sting":    {"file": "stock/audio/my_sting.wav"},                          # your own file, any format
    "ding":     {"url": "https://example.com/bell.mp3", "credit": "Bell by X, CC-BY"},
    "shutter":  {"freesound": 123456},                                        # a Freesound sound id
    "crickets": {"freesound_search": "crickets night ambience", "max_seconds": 60},
    "theme":    {"elevenlabs_sfx": "ominous solo piano ostinato, true crime", "seconds": 22},
}
```

The looped names (`theme`, `wind`, `chimes`, `crickets`) are looped with a crossfade, or trimmed, to fit the shot. Every source also takes `gain_db` to adjust its level.

**Voices.** Any character in [`cast.py`](cast.py) can use an ElevenLabs voice instead of Kokoro; with `"model": "eleven_v4"` its lines can also carry audio tags (see the `episode.py` reference and **Voices**). Your own takes beat both: save a line as `recordings/<name>.m4a` in the episode folder. `SCRIPT.md` shows the name for every line, for example `hook_1` or `chime_3`. A recording replaces that line's text-to-speech; the other lines keep their generated voice.

**Images.** Stills are already local files: put any image in `stills/` (the series library) or `episodes/<ep>/stills/`. To pull one from a stock library into an episode:

```bash
.venv/bin/python pipeline/stock.py image episodes/ep02_x aerial --pexels "suburban cul-de-sac at night"
.venv/bin/python pipeline/stock.py image episodes/ep02_x aerial --url https://.../photo.jpg --credit "Name, license"
```

**Keys.** Copy `.env.example` to `.env` (it's gitignored) and fill in only the services you use: `FREESOUND_API_KEY`, `ELEVENLABS_API_KEY`, `PEXELS_API_KEY`. The keys are never written anywhere else.

**Pinned and credited.** Anything fetched over the network is saved once in `stock/` and recorded in `stock/sources.lock.json` with its license and author. Every later build and every episode reuses that exact file with no API call; a Freesound search, for example, keeps the sound it found the first time. Commit `stock/` so the pins travel with the show. To fetch something again, delete its lock entry. `stock/CREDITS.md` lists everything, and each episode's `SCRIPT.md` ends with the credits for the sounds it used.

**Licensing.** Freesound searches only return CC0 and Attribution sounds, never NonCommercial ones, because a monetized TikTok counts as commercial use. Paste Attribution credits into the video description. For files you add yourself, record the license with `"credit"`.

**Self-test.** `.venv/bin/python pipeline/selftest.py` checks every source type against a local mock of Freesound, ElevenLabs and Pexels, the audio-tag handling, `cast.py`'s `NM_VOICES` switch and the reenactment kind (filing clips, the timeline, every build error, frames, the tag, the hard cut in picture and sound, the end card, review and `SCRIPT.md`) on generated test clips. It needs no keys or network and doesn't touch `stock/` or your episodes. Add `--full` to also render the reenactment test episode and review it.

## Posting

Turn on TikTok's **AI-generated** label, and pin a comment that points at the hidden clue without giving it away. The description's disclosure line follows the end card (`channel/CHANNEL.md`, "Every post"). Season 1's main episodes run over 60 seconds, the minimum for TikTok's Creator Rewards program; new main episodes stay under 50 seconds for retention while the channel is small, and the 60-second minimum is revisited near eligibility.

The same `_tiktok.mp4` works as an Instagram Reel and a YouTube Short. Turn on Instagram's "AI info" label and YouTube's "altered or synthetic content" setting, and keep the Reels description to one line so it doesn't cover the name cards. `pipeline/review.py` checks the on-screen text against all three apps' buttons, top bars and descriptions. It runs `pipeline/safezones.py`, which also works before the full render (`.venv/bin/python pipeline/safezones.py episodes/<ep>`), and writes `build/review/zones.png`. The full cross-posting notes are in `.agents/skills/ai-tiktok-series/references/posting-playbook.md`, under "Reels and Shorts".

**Channel.** [`channel/CHANNEL.md`](channel/CHANNEL.md) has the live channel status, the name, handle, bios and YouTube description for each app, and leads to the TikTok and Facebook Page launch kits (profile copy, first-post metadata, alternate art, setup steps and the account-agent handoff) for the platforms not yet live. `.venv/bin/python channel/make_channel_art.py` builds the profile picture every app shares and the YouTube banner into `channel/art/`; `.venv/bin/python channel/make_covers.py` builds every episode's grid cover into `channel/covers/`; `.venv/bin/python channel/make_launch_art.py` rebuilds the platform launch variants. Add `--preview` to any of them to write a `build/` preview, which shows each file at the sizes the apps display it.
