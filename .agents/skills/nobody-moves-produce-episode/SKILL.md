---
name: nobody-moves-produce-episode
description: Build, check and deliver a NOBODY MOVES episode or Confessional with the shows/nobody-moves pipeline. Covers setup, user images as stills, generating and filing the 3D reenactment clips (REENACTMENT_PROMPTS.md, pipeline/clips.py) or rendering them in Blender (pipeline/blender_reenact.py), voices (Kokoro scratch, Eleven v4 designed voices, NM_VOICES, locked takes, the user's recordings), framing previews, the mixcheck gate, handing the render to nobody-moves-render, and the draft PR. Use this whenever the user wants to build, export or preview a NOBODY MOVES episode, has sent new images, clips or voice recordings for it, wants a reenactment generated or rendered in Blender, a shot reframed or a voice swapped, asks to "install Kokoro on my computer", or just says "make the video", even without naming the pipeline. Rendering, verifying and reviewing the finished video belong to nobody-moves-render; sound, music and the mix to nobody-moves-sound-design; writing the script to nobody-moves-write-episode.
---

# Produce a NOBODY MOVES episode

Pipeline: `shows/nobody-moves/`. Other skills own the rest:
- **`nobody-moves-write-episode`** writes the episode. If `episodes/<ep>/` doesn't exist yet (e.g. "render episode 4" before it's written), write it with that skill first.
- **`nobody-moves-render`** (or the `nobody-moves-renderer` subagent, which preloads it) renders the final videos, verifies them and reviews them against a reference episode.
- **`nobody-moves-sound-design`** owns sound and music changes and diagnosing the mix. Hand off to it for any mixcheck FAIL, a line under 8 dB, or a request to change a sound.
- **`higgsfield-generate`** makes the reenactments' keyframes and clips, and the cast's 3D models (GLB), when Higgsfield is reachable (sections 5 and 5b).

Run everything from the show folder:

```bash
cd shows/nobody-moves
FF=$(.venv/bin/python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")   # after setup; there's no ffprobe
```

Every build output lands in `episodes/<ep>/build/`, not in the show folder.

**Order for an episode with reenactments** (the Episode 1 remake's `TEST_PLAN.md` and `NOTES.md` are the worked example):
1. Build the audio on the Kokoro scratch voices (with `NM_VOICES=kokoro` once the voice IDs are in `cast.py`, or every plain build of an episode that ships v4 voices, and bills, its changed lines), with no clips: the reenactments render their fallback stills under the label. Check the timing, captions, safe zones, mixcheck and the `validate()` warnings.
2. Voice the lines on the final voices and lock the takes, the reenactment lines first (section 4).
3. Generate the reference sheets and keyframes, then the clips against the locked takes, and file them (section 5); or, for a shot with a `"blender"` dict, render it in Blender (section 5b).
4. Rebuild, look (section 6), then render and review (section 7).

## 1. Environment

- **Setup:** if `.venv/` or `assets/models/` is missing, run `./setup.sh`. It needs Python 3.10–3.13 and fetches the TTS model and fonts from PyPI and GitHub.
- **Self-test:** `.venv/bin/python pipeline/selftest.py` checks the stock-asset code, the audio-tag handling, the reenactment kind and the Blender path offline, with no keys needed. It runs `pipeline/blender_reenact.py --selftest --allow-skip`, whose rendering half prints SKIP where no Blender is found.
- **Blender (optional, for Blender reenactments):** `./setup.sh --blender` (`.venv-bpy`, `bpy==5.0.1`, Python 3.11 only), or the Blender 5.0 app with `export NM_BLENDER=/path/to/blender`. Check with `.venv/bin/python pipeline/blender_reenact.py --selftest`.
- **Cloud sessions:** many hosts are blocked, including Canva downloads, Higgsfield, Freesound, ElevenLabs and Pexels. Don't try to route around a block. Ask the user to send the images, clips or takes, or to allow the host, and carry on with everything that doesn't depend on it. The paid steps (Eleven v4 takes, Higgsfield clips) run wherever those hosts are reachable, usually the user's own machine.
- **Kokoro on the user's own computer:** a cloud session can't install anything on their machine, so give them the command to run there, from the root of their checkout: `shows/nobody-moves/tools/install-kokoro.sh`. It puts a `kokoro` command in `~/.local/bin` (and prints the PATH line if that folder isn't on it), with the show's pinned versions and model files. Then `kokoro --voices` lists the presets and `kokoro "I didn't see nothing." garrison.wav am_fenrir && afplay garrison.wav` plays one on a Mac. It speaks the plain preset, without `cast.py`'s pitch shift or "voice altered" filter.

## 2. Stills from the user

- **Where they go:** recurring sets and cast go in `stills/` (the series library), the 3D reference sheets `ref3d_*` included. Episode-only shots go in `episodes/<ep>/stills/`, reenactment keyframes `rx_<name>_key` included. Name each file after the key the episode uses (`lorraine.webp`, `basin_counsel.png`). A shot uses the first of its `views` whose still exists, so dropping in a file upgrades the shot with no code change.
- **Files that aren't on disk:** images the user sends *while you are mid-task* arrive as pictures only; they're not saved to disk. Only images in a normal message get a file path. If you can see an image but can't find its file, ask the user to send it again as a new message, rather than asking for a different image.
- **Placing coordinates:** `mkdir -p episodes/<ep>/build && .venv/bin/python pipeline/grid.py <still> -o episodes/<ep>/build/<key>_grid.png [--box x0,y0,x1,y1] [--bright 2.5]`. The `mkdir` is for an episode that hasn't been built yet, since grid.py doesn't create folders. Always pass `-o`: without it the grid image is written next to the still, into the library. Read the fractions for camera centers, `annot_arrow`, `annot_circles`, polaroid crops, `alter_box` and `alter_glow` straight off the grid.
- **Dark stills:** don't regenerate a library still to brighten it. The episode's `DERIVED_STILLS` lifts it with a gamma curve at render time (same pixels, so the doorbell frames keep matching); aim for a mean of about 80/255 per shot.

## 3. Audio, timing and the mix check

```bash
.venv/bin/python pipeline/build_audio.py episodes/<ep> --stems
.venv/bin/python pipeline/mixcheck.py episodes/<ep>
```

- **Before anything is voiced,** `build_audio.py` checks the lines (a tag that would show in a caption, a stray bracket, a speaker missing from the cast, a v4 voice whose `voice_id` is still the placeholder) and validates the shots (an unknown kind, a repeated shot id, a reenactment's label, a clip that isn't a filed mezzanine, the end card's disclosure time, `lower_third_at`, `jump_after`). An error stops the build and names the shot and the fix. After voicing, it stops on a reenactment line longer than `dur`, and warns about name-card legibility (under 1.2 s) and the hit's pre-roll (the shot before a reenactment ending its last line under 0.35 s before the cut). Its other warnings are worth reading too: a reenactment outside 3–6 s, a moving `kb`, a `sting_soft` before a reenactment, a prompt-lint finding on `CLIPS` or a keyframe, and the reenactments' share of the runtime (in a Confessional, more than one or one over 5 s instead).
- **Timing table:** `build_audio.py` prints one row per shot and the total. A main episode runs under 50 s (a Confessional: 15–25), with about 1.5 s of headroom on the Kokoro scratch build for the longer final takes.
- **Voice order:** each line uses the first available source:
  1. the user's own take, `episodes/<ep>/recordings/<shot>_<n>.*`;
  2. a locked v4 take, `episodes/<ep>/recordings/<shot>_<n>.v4.*` (section 4; skipped under `NM_VOICES=kokoro`);
  3. the character's provider in the cast: `cast.py`, with the episode's own `CAST` merged over it.
- **Caching:** voice clips are cached by line text and settings, so only changed lines are re-voiced. A `pitch`, `altered` or `fx_on_recordings` change re-processes the cached clip without voicing it again, and `"lang"` changes no key; a change to the voice, model, seed, `voice_settings`, the text or its tags re-voices (and, on ElevenLabs, re-bills) every line it touches.
- **Swapping a voice:**
  - **The user's own take wins.** Save it as `episodes/<ep>/recordings/<shot>_<n>.m4a` (or .wav/.mp3), using the names in `SCRIPT.md`. Add `"fx_on_recordings": True` to the character in `cast.py` to run its pitch and "voice altered" chain on the take, for example to disguise the user as the anonymous source.
  - **One episode only:** override the character in that episode's `CAST`.
  - **`cast.py`** only for a character in no published episode. A changed entry re-voices that character in every episode on its next build, so posted episodes stop matching.
  - **English presets only** (`af_`, `am_`, `bf_`, `bm_`), also when auditioning with `kokoro --voices`, because the pipeline phonemizes other presets as English.
- **Sounds:** they come from `soundtrack.py`, with the episode's `SOUNDS` overriding it, and are synthesized unless pointed at a file or an API. To swap or add a sound, use `nobody-moves-sound-design` (recipes b and c): it matches the new sound's level and handles licensing and credits. Anything fetched is pinned in `stock/sources.lock.json`; commit `stock/`.
- **The mix:** 48 kHz stereo, mastered to −14 LUFS (TikTok's target). The risers, whooshes and hits come from the shot kinds, the reenactment cue included (a hit into each reenactment, a swell that stops dead on its cut). The score builds toward the last shot marked `"climax": True`, else the last doorbell shot that flickers (never a `"flicker": False` cold open), else the end card. `--stems` writes `episodes/<ep>/build/stems/{dialogue,score,effects}.wav`, which mixcheck reads.
- **Gate on mixcheck, not on your ears** (you can't hear the mix):
  - **Exit 1 is a HARD failure** (loudness, true peak, dialogue over the bed, a music-out beat that isn't silent, a reenactment cut that isn't silent, or length). Don't deliver.
  - **Run it right after a `--stems` build.** `make_episode.sh` rebuilds the soundtrack without stems, and mixcheck can't tell old stems from fresh ones, so checking after it can measure an older mix. With nothing changed in between, that rebuild is bit-identical to the soundtrack you checked.
  - **Hand off** to `nobody-moves-sound-design` on any FAIL, any line under 8 dB, or a request to change the sound: recipe (d) for a buried line, recipe (e) for a music-out beat. Don't turn the voices up: lines are loudness-matched and the master re-normalizes, so louder voices only flatten the hits.

## 4. Voices: Eleven v4 and locked takes

The final voices are Eleven v4 voices designed from text prompts; Kokoro is the scratch voice every episode builds on first. The plan, the casting prompts, the settings to verify, the tag rules and the cost note are in `docs/AUDIO_ELEVENLABS_V4.md`; read it before spending anything.

- **Which cast a build uses.** `cast.py` has `CAST_KOKORO` (scratch) and `CAST_V4` (designed voices); `CAST` is Kokoro plus the characters in `FINAL_V4`, the ones the public voice test has promoted. `NM_VOICES=kokoro` forces every character onto Kokoro, `NM_VOICES=v4` every character onto v4 (an A/B arm only; the build stops on a character whose `voice_id` is still a placeholder, so a v4 arm is never Kokoro in disguise). An episode's own `CAST` merges over whichever is chosen. The Episode 1 remake ships v4 (D9), so its `CAST` switches its four speakers to `CAST_V4` once all four have a `voice_id`, whatever `FINAL_V4` says (`NM_VOICES=kokoro` still forces Kokoro); its NARRATOR (TRAILER) is the NARRATOR's v4 voice, or a pitched-down Kokoro preset on the scratch cast.
- **Designing a voice** (the user runs it where ElevenLabs is reachable, or gives you the IDs): check 0 first (a designed voice renders on `eleven_v4`), then the casting prompt from the doc. Never a cloned voice, never a prompt that names or evokes a real person, never a Voice Library narrator; reject any Library voice that names or evokes one, and record that check. Write the prompt, preview text, design date and `voice_id` into `cast.py` as a comment beside the entry. Designed voices drop the Kokoro-era `pitch` and `speed`, except the CHIME, whose disguise is the joke.
- **Settings:** `seed` and each `voice_settings` field go in only once the doc's settings checks show v4 honours them, decided before any take is locked (adding one later re-bills every line).
- **Cost check before a v4 build:** count the characters to be voiced (each line's `say`, tags included) and the takes per line, and tell the user the total before building. FX and `"lang"` edits are free; a generation-field edit re-bills.
- **Takes, per line:** up to 3 v4 takes. A tagged line's takes are picked blind against one untagged v4 take of the same line, and the tag is dropped if the untagged take wins. Among takes that land the line, prefer the one closest to its Kokoro length (each at most +5%; the runtime headroom is one budget shared by every take). A line no take lands in 3 tries goes to a human: the ★ lines in `SCRIPT.md` ("Lines to record by a human", from `HUMAN_TAKES`) are the likeliest, with their direction and same-session companions.
- **Lock every chosen take before the final render.** A v4 take isn't guaranteed to repeat and `build/` isn't committed, so a fresh clone would re-bill and get a different take. Until the takes lock is built into `build_audio.py`, copy the chosen take's raw clip, `build/voice/<WHO>_<key>_raw.wav` (the newest one right after building that line: `ls -t episodes/<ep>/build/voice/<WHO>_*_raw.wav | head -1`), to `episodes/<ep>/recordings/<rec>.v4.wav`. The `.v4` marks it as a generated take: the build uses it in place of the API, `timeline.json` marks the line `"generated"`, so the end card and `SCRIPT.md` still count it as an AI voice, and `NM_VOICES=kokoro` skips it. A take copied without `.v4` (`recordings/<rec>.wav`) counts as a human take: it wins over every cast, Kokoro included, and on an episode without a reenactment the end card drops "voices". Either way, check `render.py --preview <end start + 1.9>` reads "Reenactments and voices made with AI." on such an episode before posting. The CHIME's cast entries keep its disguise on any take (`"fx_on_recordings": True`). Commit `recordings/`.
- **Lock a reenactment's line before its clip is generated** (section 5): the clip's motion is timed to the take.
- **After locking,** rebuild and re-check the pace: under 50 s, about 165 words/min while speaking (150 the floor) and 110–120 overall (`review.py`'s pacing table; for the remake, `episodes/ep01r_three_feet_reenacted/tools/fit_takes.py --ref <the Kokoro build's timeline.json>`). Copy the Kokoro build's `build/timeline.json` aside before locking any take, or rebuild it with `NM_VOICES=kokoro`, which skips `.v4` takes; a human take in `recordings/` wins over every cast, so move such takes aside first if the reference must be all Kokoro. Over 49.5 s, apply the episode's trim list in `NOTES.md`, in its order, before touching a joke silence.
- **Re-measure the mix** of every re-voiced episode with mixcheck: quiet tags come back at normal loudness, and the CHIME's hushed, pitched voice under wind and chimes is the likeliest line under 8 dB.

## 5. Reenactment clips

Each reenactment is a generated 3D clip, one ornament making one rigid move on a locked camera, filed into the episode and played at 1.0x under a burned-in `REENACTMENT · AI` label. The episode's `REENACTMENT_PROMPTS.md` holds every prompt, reference, negative, per-tool setting and review checklist (the remake's is written from `episode.py` by its `tools/make_prompts_md.py`); `episode.py` is the source when the two differ.

1. **Until a clip exists,** its shot renders its `fallback` views (the 3D keyframe still, else a crop of the real still) under the same label, and `render.py` prints `REENACTMENT FALLBACK (clip missing)`. That's fine for review, never for posting: the reenactment's joke is motion.
2. **Reference sheets, once per character, into the library.** Generate `ref3d_<name>` from its `STILLS` prompt with the library photo attached as image 1, the canvas at 16:9 in the tool; then `ref3d_lineup` from the sheets, so they share a scale. File them in `stills/`. Every later reenactment of that character reuses them.
3. **Keyframes, into the episode.** Generate `rx_<name>_key` from its `STILLS` prompt, with the canvas set to 9:16 in the tool (prompt text doesn't set it) and exported at 1080x1920. Attach the references in the prompt's image-map order, each cropped to one view (a whole turnaround sheet makes the model draw copies; never Lorraine's back view), the library photos cropped to the character. Check it against the clip's checklist (no human, no text, exactly the ornaments named, windows dark, the top left clear of cap, beam or key action, bright and obviously CG), then file it in `episodes/<ep>/stills/`.
4. **Fit the motion prompt to the locked take** before generating: a move on a key word holds still "For the first X seconds", X = `pre` + the key word's time in the locked take + `in`; a landing after the line comes "At about Y seconds", Y = `pre` + the take's length + `in` (the key word's time in the take is its start in the caption's `words` in `build/timeline.json` minus the caption's `start`, since both are timeline seconds: heist, 12.993 − 11.083 = 1.91 s). Set `dur` to `pre` + the take + pauses + at least 0.5 (at most 6.0), and generate a take that covers `in` + `dur`: 10 s when that passes 5 s, with `CLIP_SOURCES` `seconds` to match. Edit `CLIPS` in `episode.py`, then regenerate the prompts file.
5. **Clips, image to video,** from the keyframe alone, never from text alone, with the higgsfield-generate skill (or by the user, from `REENACTMENT_PROMPTS.md`, when Higgsfield is blocked): the 9:16 aspect, the motion prompt from `CLIPS`, and the clip's settings from `CLIP_SOURCES`. On Seedance there is no negative field: fix the camera (`camera_fixed`) and append the `seedance_suffix`. On Kling the negative goes in `negative_prompt`, and a motion brush can paint the ornament's path. Never first-and-last-frame mode: it spreads the move over the whole take. Make several takes and keep the one where nothing bends, steps or turns and the move comes on time.
6. **If no take works,** build the clip outside the generator: cut the ornament out of the keyframe and slide it along its path over a clean plate of the same keyframe (ffmpeg `overlay`, or any editor), and use image-to-video only for the haze, flares and fire.
7. **File it:** `.venv/bin/python pipeline/clips.py add episodes/<ep> rx_<name> <file> --generator "<tool and model>"` (`series` instead of `episodes/<ep>` for a recurring library clip). It transcodes a 30 fps mezzanine with no audio, records the prompt and negative from `CLIPS` and `CLIP_SOURCES` in `clips/clips.json`, and warns about a soft crop, black ends or a dark middle. `--retime F` retimes once, at intake, with optical flow; never slow a clip with the shot's `speed`.
8. **Set `in`** so the move lands on its word: if the move comes at S seconds into the take, `in` = S − (`pre` + the key word's time); it can only fall to 0, so a clip absorbs a fraction of a second of a longer line at most. A longer locked take means a new clip, not a longer `dur` (that freezes the last frame).
9. **Check it:** `.venv/bin/python pipeline/clips.py sheet episodes/<ep>` writes the first, middle and last frame of every clip to `build/review/clips.png`; go through the clip's checklist in `REENACTMENT_PROMPTS.md`. `.venv/bin/python pipeline/clips.py lint episodes/<ep>` re-runs the prompt lint.
10. **Rebuild the audio** after filing or replacing a clip: the shot length can depend on the clip, and `render.py` refuses a clip that changed since the timeline was built ("rebuild the audio").

## 5b. Blender reenactments

**Blender renders run on your own machine only.** Never in a cloud or remote session: `pipeline/blender_reenact.py` refuses to start Blender when `CLAUDE_CODE_REMOTE` is set, and its selftest reports the rendering half as skipped there. Render finals and previews on your computer, then file the clip with `blender_reenact.py`.


A reenactment shot with a `"blender"` dict is rendered by `pipeline/blender_reenact.py` instead of generated: the cast's 3D models (or striped `_PROXY` stand-ins until a model is filed), a rigid move landed on a word of the build's own take, a locked camera, no human possible. It is filed like any generated clip, through `clips.py add` (`clips/<key>.mp4`, its `clips.json` entry with `quality`, `proxy` and `sidecar`, and `clips/<key>.blender.json`). The label stays `REENACTMENT · AI`. Guide: `docs/BLENDER_REENACTMENTS.md`; models: `models/README.md`.

- **Blender path or AI clip.** Use Blender when the move must land exactly on a word, must be repeatable after a re-voice, or no generator take keeps the ornament rigid; the AI route (section 5) when the look needs something the templates (`heist`, `action`) can't stage. One shot plays one source: the Blender clip has its own key ending in `_bl` (`rx_heist_gnome_bl`), never the AI clip's key, and the AI route's values stay in a comment on the shot. Switching back means pointing `"clip"` (and `in`, `kb`) at the AI key.
- **The order.** `./make_episode.sh episodes/<ep>` does it: `build_audio.py` → `blender_reenact.py --build` (a draft; `NM_RX_QUALITY=final` for finals) → `build_audio.py` → render. Without Blender, or with a CPU estimate over 30 min, it warns and the fallback still plays. By hand: `--dry-run` (beats and cost), `--preview` (look and timing: `build/blender/<clip>/sheet.png`, never filed), `--build`. Re-voicing a line moves its beats; the next `--build` re-renders only when a beat lands on a different frame.
- **Read the run's WARN lines** before anything else: the tag zone, the cut-back match (with the `kb` the next still needs; on the remake, `l_deny` goes to `(0.50, 0.50, 1.0)` once the Blender action ships), effect coverage, feet at the cut, and the timing (the drop within 0.1 s of its word, the landing 0.25 s or more after it). Hand the sheet review to `nobody-moves-render`.
- **Models.** Each subject wants `models/<name>.glb`: a Higgsfield 3D GLB (`higgsfield-generate`, `multi_image_to_3d`, textured) from one clean view of the series still (the front view cropped from `ref3d_<name>`; Lorraine's beak-left three-quarter view, never her back), or any modelling tool with the same conventions (+Y up, front on +Z, one figurine; scale and origin are ignored). File it with `.venv/bin/python pipeline/blender_reenact.py model add <name> <file.glb> --source "..." --ai` (or `--no-ai`), which checks it in Blender before filing, then compare its sheet with the library still: the library wins on identity. Never edit `models.json` by hand.
- **Proxies and drafts are placeholders.** A clip rendered with a proxy, or at draft quality, is flagged in `clips.json` and the timeline: `review.py` warns, `deliver.py` refuses it without `--allow-draft`, and `NM_FINAL=1 ./make_episode.sh` makes a missing model or no Blender an error. Finals (`--quality final --require-models`) belong on a GPU machine (the plan line must say `eevee gpu` or `cycles gpu OPTIX`/CUDA/HIP/METAL); a CPU final takes many hours a clip (about 113 hours for the heist's 123 frames by the driver's estimate, about 45 hours by the guide's measured frame time scaled up; the driver prints its estimate before rendering and asks for `--yes` above 30 minutes).
- **Commit:** `models/models.json` after a `model add` (the GLB itself only on purpose: `git add -f models/<name>.glb`), the episode's `clips/clips.json`, and a final Blender clip with its sidecar on purpose (`git add -f episodes/<ep>/clips/<key>_bl.mp4 episodes/<ep>/clips/<key>_bl.blender.json`; drafts are git-ignored). Never commit `build/blender/` or the show's `build/`.

## 6. Look before rendering

A full render takes about 10 minutes for a main episode, and previews take seconds. Check framing first:

```bash
.venv/bin/python pipeline/render.py episodes/<ep> --contact             # one frame per shot (two per reenactment) -> episodes/<ep>/build/contact.png
.venv/bin/python pipeline/render.py episodes/<ep> --preview 1,21.9,75.8 # exact moments -> episodes/<ep>/build/preview_*.png
```

Open the images and actually look at them. Pick preview times from `episodes/<ep>/build/timeline.json`: each line's start, the evidence flash plus about 0.5 s, the doorbell jump, the pause after the flicker, the middle of each reenactment and the first frame after its cut. Check:

- **Hook:** the first frame is the event or a strong close-up, readable at once; a name card appears by about 0.4 s. No title card in a main episode.
- **The comment question** is on screen and spoken by about 10 s.
- **Reenactments:** the red `REENACTMENT · AI` tag and its stamp are legible, nothing important sits behind them (x 64 to about 750, y 190–320), no series corner badge is drawn under them, and the frame right after the cut is the real ornament, unmoved, at about the same size.
- **Clutter:** captions (y about 1050–1240, at most two lines) don't collide with name cards, arrows or circles. Move the camera center rather than the overlay if they do.
- **Every app's UI:** `.venv/bin/python pipeline/safezones.py episodes/<ep>` (about 45 s, no render needed) flags text under the buttons, top bar or description of TikTok, Reels or Shorts and draws `build/review/zones.png`. A push-in (`kb` zoom above 1) carries text near the edges outward as the shot goes on: frame it so the text ends inside, or move the element. The lineup board's push-in ends at `(0.5, 0.5, 1.1)` with the two suspects at `fy` 0.56, which keeps the index card and the labels clear of every app's UI; re-run `safezones.py` after any board change.
- **Caption highlight:** the word being spoken is yellow. Its timing is measured from the voice clip on each build, so a new recording or voice needs no other change; an audio tag never lights a word. A line whose yellow word runs ahead of or behind the voice on the phone is a word-timing bug in `pipeline/words.py`, not a script fix.
- **Annotations:** arrows and circles sit on the subject, at the moment the line mentions it.
- **Brightness:** reality shots read on a phone (about 80/255 or more), reenactments brighter still; a near-black hold only where the darkness is the joke.
- **Clue fairness:** the doorbell frame B clue is visible at phone size (look at the frame scaled to about 360 px wide) but not obvious. A mirrored `alter_box` shows no seams, and the box stays tight around the object. A derived frame B (from a `make_stills.py`) shows no smudge at phone size. Lights listed in SERIES.md's doorbell table are lit in both frames. The clue must not sit under the call-to-action text (y about 1040–1330).
- **Text fit:** the board card text and the call-to-action fit the width.
- **Script:** `SCRIPT.md` regenerates with `.venv/bin/python pipeline/script_md.py episodes/<ep>`. It lists every line's recording name (★ for the human fallback lines), each tagged line's *(direction)*, the reenactment clips and the credits for stock sounds. Hand-written notes live in the episode's `NOTES.md`.

## 7. Render and deliver

Follow `nobody-moves-render`, or delegate the whole step to the `nobody-moves-renderer` subagent. It runs `./make_episode.sh episodes/<ep>` in the background (about 10 minutes), then `pipeline/review.py` to verify the files and compare the episode with the previous one, beat by beat. Its outputs, in `episodes/<ep>/build/`:
- `<ep>.mp4`, the master at about 9 Mbps, too big to send in chat for a main episode;
- `<ep>_tiktok.mp4`, under 29 MB. **Send this one.**

**Grid cover:** add the episode to `COVERS` in `channel/make_covers.py` if it isn't there: its own subject, not the hook's Garrison close-up, and nothing that gives the answer away. A reenactment frame used as a cover keeps its label. Then run `.venv/bin/python channel/make_covers.py <ep>`, and check the new cover's own file, `channel/covers/<ep>.jpg`. Commit it with the episode.

**Audio-only change:** if only the audio changed and `timeline.json` keeps the same `total`, `shots` and `captions`, remux the new soundtrack into the existing MP4 in seconds instead of re-rendering. Follow `nobody-moves-sound-design`, "Re-render or remux".

## 8. Hand-off

- **Commit:** `episode.py`, `SCRIPT.md`, `NOTES.md` and `REENACTMENT_PROMPTS.md` if the episode has them, any new stills (keyframes in the episode, `ref3d_*` sheets in the library), `clips/` with its `clips.json` (a final Blender clip with `git add -f`, section 5b), `models/models.json` if a model was filed, `recordings/` (the user's takes and locked v4 takes), any `make_stills.py`, the grid cover and its `COVERS` entry, and `stock/` if it changed. Never commit `build/`, `.env` or `assets/`.
- **PR:** open it as a draft. Merge only when the user says so ("merge it"), because they review the video first, and use a merge commit, like the repo's earlier PRs. A `git fetch` right after the merge may be denied; confirm the merge on GitHub instead.
- **Tell the user:**
  - the runtime and the pace (words/min overall and while speaking);
  - the mixcheck result: PASS n/m (6 hard checks with a reenactment, 5 without), the dialogue median and the worst line;
  - which shots still use fallback crops, and which reenactments still render a fallback (not postable), with the prompts for their stills and clips;
  - which voices are scratch Kokoro and which are v4, how many takes are locked, and the recording names of the ★ lines if they want to record any.
- **Posting reminders:** upload `channel/covers/<ep>.jpg` as the cover; turn on TikTok's AI-generated label, Instagram's "AI info" and YouTube's "altered or synthetic content"; the description's disclosure line follows the end card ("Written by [NAME]. Footage, reenactments and voices made with AI. The flamingo is real." on an episode with a reenactment) and, with a reenactment, adds "Reenactments are theories. Nothing in this yard moves while anyone is watching."; pin a comment that points at the bonus without naming it; keep the pin rules in SERIES.md ("Remakes"); paste any Attribution credits from `SCRIPT.md` into the description.

## Changing the pipeline

A later episode may need a new shot kind or renderer feature. Every published episode must still rebuild byte-identically.
- **Regression check:** with your change stashed (`git stash`), build the audio and render `--preview` at a dozen fixed times for each published episode, and copy the PNGs and `soundtrack.wav` aside. Then `git stash pop`, do the same, `cmp` each pair, and confirm the voice cache made no new clips. Details: `.agents/skills/ai-tiktok-series/references/lessons.md`, "Determinism and regressions". Two published episodes print a name-card warning on every build (`ep01c_deb_consent` shot `film`, 1.07 s; `ep07_the_finale` shot `dale`, 0.84 s). They stay as published; only a new episode must clear it.
- **New kinds:** add each one to `KINDS` in `pipeline/common.py` and to `render()`'s dispatch in `pipeline/render.py`, and to the lower-third and caption rules under it. `build_audio.py` refuses a kind it doesn't know.
- **Sound code** (`sounds.py`, `LEVELS`, the mix in `build_audio.py`) goes through `nobody-moves-sound-design`.

## Troubleshooting

- **`Error processing file ... phontab`:** the espeak-ng data path is longer than about 160 characters. Use a shorter checkout path.
- **`<NAME> is not in the cast`:** add the character to `cast.py` (English presets only; see the write skill), or to the episode's `CAST`.
- **`<WHO> has no ElevenLabs voice yet: the voice_id is the placeholder`:** the v4 voices aren't designed yet (fill them in `cast.py`'s `CAST_V4`). Build without `NM_VOICES` (or with `NM_VOICES=kokoro`) until they are.
- **A caption "shows the audio tag":** the tag belongs only in `L()`'s third argument, the spoken text.
- **`clip changed since build_audio.py: rebuild the audio`:** a clip was filed or replaced after the last audio build. Rebuild the audio, then render.
- **`unknown sound name`:** the valid names are listed in `soundtrack.py`.
- **A new episode crashes at a doorbell or board shot:** check the required fields in the write skill's `references/episode-template.py`.
