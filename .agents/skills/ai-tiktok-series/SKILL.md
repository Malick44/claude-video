---
name: ai-tiktok-series
description: Create a new AI-generated, faceless comedy series for TikTok, Reels or Shorts, from the channel idea to a built pilot and a reusable episode factory in a new folder under shows/, using NOBODY MOVES (shows/nobody-moves) as the worked example and template. Covers concept research and scoring, the series bible, still-image prompts for the user to generate, the cast's voices, the synthesized score, the pilot (60-90 s, 1080x1920, -14 LUFS, an upload copy under 29 MB) and the show's own write and produce skills. Use this whenever the user asks for a TikTok, Reels, Shorts or YouTube channel idea using AI content, wants to start a new show or series, make a pilot for a new show, spin off another show, or set up a pipeline like NOBODY MOVES for another show, even if they don't name this skill. For anything inside NOBODY MOVES itself (its episodes, Confessionals, re-renders, fixes or sound), use nobody-moves-write-episode, nobody-moves-produce-episode or nobody-moves-sound-design instead.
---

# Create an AI TikTok series

This skill takes a channel idea to a show that produces episodes on demand. The worked example is NOBODY MOVES in `shows/nobody-moves/`. It went from "find me a TikTok channel idea" to a pilot, a pipeline in the repo, shared voices and sounds, and Episodes 2 and 3 written through its own skills. Follow the same stages:

1. **Concept:** 3–5 scored concepts, one recommended.
2. **Scaffold and bible:** `shows/<slug>/` and its `SERIES.md`.
3. **Stills:** prompts the user generates, with fallbacks so nothing waits on them.
4. **Pipeline:** adapt the copied pipeline to the new show.
5. **Pilot:** Episode 1, built, checked and delivered.
6. **Repeatable:** the show's own write and produce skills.

Each stage ends with something the user can react to. Report after each one, unless the user asked you to keep going.

## Ground rules

- **The user makes the images.** Image-generation hosts and image CDNs are blocked in this environment. One pilot attempt generated 9 stills and couldn't download any of them. Write complete prompts; the user generates the images and sends the files. The user asked for exactly that: "just give prompts and I will generate them."
- **Stills only; only the camera moves.** AI renders stillness best: no lip-sync, no rubbery faces, no humans on screen. The user also said "discard the video. just use image to make your video."
- **Never route around a blocked host.** Tell the user, finish everything that doesn't depend on it, and ask them to send the files or allow the host. `setup.sh` downloads only from PyPI and GitHub, which are reachable. The optional stock sources in `pipeline/stock.py` (Freesound, Pexels, any URL) and ElevenLabs voices need hosts that are blocked here; the synthesized sounds and Kokoro voices need none.
- **Never wait on images.** Every shot lists fallback views, and a missing still renders as a labeled placeholder. The first pilot shipped as an animatic with placeholder cards while images were blocked.
- **Measure what you can't watch or hear.** Check loudness, dialogue over music, and phone-size previews. Say plainly what you couldn't check ("I couldn't listen to it here"; "the voices are scratch TTS").
- **Never write API keys, `.env` contents, the user's email or model identifiers** into files, commits or PRs. Keys go in `shows/<slug>/.env`, which is gitignored.

## Stage 1: find the concept

Run the 5-phase method in `references/concept-scorecard.md`:

1. Research the landscape and the operations side with web search.
2. Five writers produce three concepts each, one comedic angle per writer.
3. Three lens judges score every concept.
4. An adversarial prior-art check runs on the top 4.
5. Synthesize the pitch.

Research fresh every time, because trends turn over in weeks. If web search is blocked, say so and use the reference's dated findings as a baseline.

Reject concepts with real people, copyrighted characters, kid targeting, or jokes that only work if viewers don't know it's AI. Those are how AI channels get removed, demonetized or mass-reported. Rank the rest at 0.4 × comedy + 0.3 × feasibility + 0.3 × risk.

What made NOBODY MOVES win (first of 15 concepts, at 8.05), and what to look for again:
- **A visual rule that matches what AI does well.** Lawn ornaments can't move, so every witness is a still. AI flaws become canon (the goose's outfit changes between cuts).
- **A known TV format aimed at tiny stakes.** Prestige true crime, applied to a flamingo moved three feet. The gap between the two is the joke.
- **A fixed non-human cast, each with one comic mechanism.**
- **A repeatable comment-bait engine.** Every episode ends on a doorbell-cam frame where something changed, and the answer is provable from frames already shown.
- **Label-proof.** The disclaimer is itself a joke: "Reenactments dramatized with AI. The flamingo is real."

Deliver 3–5 concepts, each with its lens scores and a one-line reason, then the pitch: the pick, a format template with timings, six episode ideas, how to make it, growth and money, two runners-up, and what to avoid. Tell the user to search TikTok in the app for the premise and claim the handle, because the prior-art check can't see inside TikTok. Then stop and let them choose.

## Stage 2: scaffold the show and write the bible

From the repo root (the script finds the repo itself, but the `.agents/...` path is relative):

```bash
git status --short shows/nobody-moves     # note what this prints now, for the "untouched" check in Stage 6
bash .agents/skills/ai-tiktok-series/scripts/new_show.sh <slug>
```

This copies the pipeline from `shows/nobody-moves/` into `shows/<slug>/` and writes `SERIES.md` from `references/series-bible-template.md`. Then it prints the NOBODY MOVES-specific lines a grep can find. That list is a starting point, not complete: `references/new-show-checklist.md` covers what a grep can't see, such as `build_audio.py`'s climax and hush, `sound_kit.py` and the key of the score. Keep the slug short (e.g. `late-humans`). espeak-ng fails on data paths over about 160 characters, and the path runs through `shows/<slug>/.venv/`.

Set up the environment right away, because Stage 3's `grid.py` and every build need `.venv`, and a self-test that passes on the untouched copy separates setup problems from your own edits:

```bash
cd shows/<slug>                   # Stages 3-5 run from here
cp -r ../nobody-moves/assets .    # optional: same pinned model and font files, no download
./setup.sh                        # Python 3.10-3.13; venv from PyPI, models and fonts from GitHub
.venv/bin/python pipeline/selftest.py
```

Fill in every section of `SERIES.md`, following `shows/nobody-moves/SERIES.md`. A future episode writer knows only what this file says.

- **Premise, the one rule, and tone.** The rule is the visual constraint, stated as canon.
- **The setting,** with a where/who table. One fixed set is what keeps separately generated stills looking like one world.
- **The cast:** 4–6 characters plus a narrator. Give each one a personality, **one comic mechanism** and a scratch voice. Lorraine the goose is warm, says "hon", and insists she can't go anywhere because she's concrete. A character who hasn't spoken yet is a promise; say when they will.
- **The image style block** (stage 3).
- **The clue ledger:** every planted clue, running gag and promise, with its payoff episode.
- **A frame table,** if clues live in recurring footage.
- **The roadmap through the finale.** Check each payoff against the real stills now. NOBODY MOVES's planned finale needs Deb standing on one leg, and the user's stills show her on two.
- **Between-episode shorts** (NOBODY MOVES "Confessionals", 15–25 s).

## Stage 3: stills

- **The style block** fixes the look. Append it to every prompt. It names the set object by object, in the same words every time, then the light, lens, grade and "No people, no text". The pipeline draws all text, and generated text comes out garbled. NOBODY MOVES's block is in `shows/nobody-moves/SERIES.md` under "Image style".
- **Ask for the minimum first,** most important first, because the user's generation time is the bottleneck and fallbacks cover the rest. The pilot was built from 5 images of one yard: a hero close-up, a detail, a close-up of a second character, and a before/after pair of the same night wide shot, which the clue was built on.
- **Give each request as:** the save-as key, whether it's optional, then the full prompt. The key is the exact file name the pipeline looks for, and "optional" tells the user what they can skip or send later.
  ```
  1. stills/lorraine.webp (optional; the episode uses a crop of yard_before until then)
     Close-up of a white concrete porch goose on the porch step, beak pointing to frame left,
     framed like a documentary interview at 85mm. <style block>
  ```
- **Receiving files:** images in a normal message get a file path; images sent while you're mid-task arrive as pictures only and are never saved. If you can see an image but can't find its file, ask the user to send the same image again in a new message.
- **Where they go:** recurring sets and cast go in `stills/` (the series library). Episode-only shots go in `episodes/<ep>/stills/`, where `<ep>` is the episode folder (Stage 5). Name each file after its key; `.webp`, `.png` and `.jpg` all work.
- **Clue frames:** derive frame B from the library still with a deterministic pixel edit in `episodes/<ep>/make_stills.py`. Two separately generated images never match, so a generated frame B changes everything at once. Episode 3's `make_stills.py` is the example.
- **Where derived frames go:** if a later episode will replay the frame or derive the next one from it, write it to `stills/` (the library). An episode sees only its own `stills/` and the library, so a frame left in `episodes/<ep>/stills/` is invisible to the next episode. Episode 3 writes `yard_gone` to `../../stills/` for this reason. A frame only one episode uses can stay in that episode's `stills/`.
- **Coordinates:** `mkdir -p episodes/<ep>/build`, then `.venv/bin/python pipeline/grid.py stills/<key>.webp -o episodes/<ep>/build/<key>_grid.png [--box x0,y0,x1,y1] [--bright 2.5]`, and read the fractions off the grid. Placing them by eye failed. Always pass `-o` into `build/` (gitignored): without it, grid.py writes `<key>_grid.png` next to the still, into the library you commit.

## Stage 4: adapt the pipeline

From `shows/<slug>`, work through `references/new-show-checklist.md`, file by file. Never edit `shows/nobody-moves/` for the new show: its episodes must keep rebuilding byte-identically. In short:

- **Reuse unchanged:** `setup.sh` (except its last line), `make_episode.sh`, `requirements.txt`, `tools/`, `deliver.py`, `grid.py`, `script_md.py`, and the voice, timeline and mastering path of `build_audio.py`.
- **Rewrite:**
  - `cast.py`.
  - The theme in `pipeline/sounds.py` (`THEME_NOTES`, `THEME_TURN`, `THEME_STEP`, `PAD_CHORDS`) and its foley. If you change the key, also transpose the pitches hard-coded in A minor: the drone (55 and 82.4 Hz), `shimmer`, `braam(root=33)`, the `sting` cluster, `swell`'s sub and `chimes`. The checklist has the table. You can't hear a clash, so nothing else will catch it.
  - `soundtrack.py`.
  - In `render.py`: the show-specific shot kinds, the end-card disclaimer, `"INTERVIEWER"`, the doorbell and board defaults, and the caption-split abbreviations. An unknown kind silently renders as the end card.
  - In `build_audio.py`: the `sfx` vocabulary, the climax and the hush. The score builds to the last shot marked `"climax": True`; if there is none, to the last `doorbell` shot; if there is neither, to the end card. Mark each reveal shot, or key the fallback on your own reveal kind.
  - `sound_kit.py`: the `typing_line` default and the `doorbell_*` kit names.
  - The names in `selftest.py` and `stock.py`. The self-test fixture's sound names and `sfx` must stay valid, so update it when you drop or rename a sound.
  - A `README.md` for the show.
- **Voices:** use Kokoro presets, English only (`af_*`, `am_*`, `bf_*`, `bm_*`), with `speed`, `pitch` and `altered`. Audition them by building the pilot's audio; clips are cached per line and settings, so a re-run only voices what changed. Freeze a character's entry once an episode is published, because changing it re-voices every episode. The user's own takes beat any TTS: `episodes/<ep>/recordings/<shot>_<n>.m4a`.
- **New sounds and levels:** follow `nobody-moves-sound-design`'s `references/add-a-sound.md`. It walks every file a new sound touches: the generator, `soundbank.SYNTH`, a `LEVELS` entry set by measurement rather than guessed, the `build_audio.py` branch, `mixcheck.cues()` and the kit. Its `references/mix-knobs.md` lists every number that shapes the score. The numbers in both files are NOBODY MOVES's; measure your own.
- **Measure single sounds from the show folder:** `.venv/bin/python ../../.agents/skills/nobody-moves-sound-design/scripts/soundprobe.py <name> ...`. It loads `pipeline/` from the working directory. Run from anywhere else, it falls back to `shows/nobody-moves` (with a note on stderr) and measures the wrong show.
- **Not `cinematic-sound-designer`:** `build_audio.py` regenerates all of an episode's audio from the shot list, so an SFX stem made by that skill bypasses `LEVELS` and mixcheck, and the next build discards it. Use it only for edits made outside the pipeline, such as a short cut in CapCut from the sound kit.
- **Check your edits:** `.venv/bin/python -m py_compile pipeline/*.py cast.py soundtrack.py`, then `.venv/bin/python pipeline/selftest.py` again. `bash ../../.agents/skills/ai-tiktok-series/scripts/new_show.sh --check .` re-lists the leftovers with the scaffold's own pattern.

## Stage 5: the pilot

Write `episodes/<ep>/episode.py` as data, where `<ep>` is `ep01_` plus the episode's title in lowercase with underscores (`ep01_three_feet`), not the show slug. The folder name becomes the output names, `episodes/<ep>/build/<ep>.mp4` and `<ep>_tiktok.mp4`. Start from `references/pilot-template.py`: it uses only the generic shot kinds, defines a placeholder speaker `WITNESS`, and builds on a fresh scaffold. Replace `WITNESS` with names from your `cast.py` and delete its `CAST` line. Put each new still's prompt in `STILLS`. Model the pacing on `shows/nobody-moves/episodes/ep01_three_feet/episode.py`. One file drives both the audio and the video, so a changed line updates both.

Follow "What makes an episode work" and "Writing the file" in `.agents/skills/nobody-moves-write-episode/SKILL.md`. Each rule there says why, and each holds for any show in this format: read NOBODY MOVES's cast, rule and doorbell as your show's own, from your `SERIES.md`. For a pilot, these differ:

- **There is no earlier clue to answer.** The pilot plants the first one.
- **Title card at about 5 seconds,** right after the hook, with `"sfx": ["sting"]`. The score starts there. The hook gets its setup and punchline first, then the title names the show while new viewers are still deciding. The NOBODY MOVES episodes reach it at 4.8–6 s.
- **The clue can sit in any shot kind,** not only a doorbell frame. Derive its frames as in Stage 3. `SCRIPT.md` prints `ANSWER`, and the video never shows it.
- **Mark the reveal shot `"climax": True`.** The score builds to the last marked shot. With no mark it builds to the last `doorbell` shot, and with neither to the end card, which is too late.

Build the audio, measure it, look, then render:

```bash
.venv/bin/python pipeline/build_audio.py episodes/<ep> --stems     # timing table, soundtrack and stems
.venv/bin/python pipeline/mixcheck.py episodes/<ep>                # exit 1 = a HARD check failed
.venv/bin/python pipeline/render.py episodes/<ep> --contact        # episodes/<ep>/build/contact.png
.venv/bin/python pipeline/render.py episodes/<ep> --preview 0.5,4,30
./make_episode.sh episodes/<ep>                                    # about 10 minutes
```

- **Run mixcheck right after the `--stems` build.** Its dialogue-over-music, music-out and hit checks read the stems. `make_episode.sh` rebuilds the soundtrack without stems, so stems read after it may describe an older mix. After any sound or timing change, run both lines again.
- **mixcheck also checks loudness and true peak** (−14 ± 1 LUFS, −1.0 dBTP or lower), so there is no separate loudness step.
- **On exit 1, fix it before rendering.** For a failure or a line under 8 dB, use `nobody-moves-sound-design` from `shows/<slug>`: recipe (d) for a buried line, (e) for a music-out shot that isn't silent.

Before `make_episode.sh`, open the contact sheet and previews and look at them:

- **The hook frame** is a strong close-up.
- **Captions** (y about 1050–1240, at most two lines) don't collide with name cards or overlays.
- **Text fits:** the title, the cards and the end-card lines fit the width.
- **The clue** is findable in a frame scaled to about 360 px wide.

Run `make_episode.sh` in the background and watch its output for `wrote|MB|Traceback|Error`. Then check the video. There is no ffprobe, so use the bundled ffmpeg:

```bash
FF=$(.venv/bin/python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
$FF -i episodes/<ep>/build/<ep>_tiktok.mp4   # 1080x1920, 30 fps, AAC 48 kHz stereo
ls -l episodes/<ep>/build/                     # the _tiktok.mp4 under 29 MB ($FF -i doesn't print the size)
```

Send the user the `_tiktok.mp4` and the episode's `SCRIPT.md`; the master is about 9 Mbps and too big for chat. Report:
- the runtime and the beats, in plain language;
- the clue, labeled as a spoiler;
- the mixcheck `RESULT` line and the dialogue-over-bed median;
- the stills still using fallbacks, with their prompts;
- what you couldn't verify.

## Stage 6: make it repeatable

Go back to the repo root first (`cd ../..` from the show folder): the skill paths and the symlinks below are relative to it.

- **Write the show's skills.** Create `.agents/skills/<slug>-write-episode/` (with `references/episode-template.py`) and `.agents/skills/<slug>-produce-episode/` by copying the `nobody-moves-*` skills. Replace every show fact: paths, cast and mechanisms, library keys, shot kinds and fields, clue mechanics, fallback crops. Keep their structure and their "why" for each rule. Name the show and its characters in each description, and end it with "even if they don't name the show". Descriptions are how the skill gets found.
- **The produce copy must measure the mix:** `build_audio.py episodes/<ep> --stems`, then `mixcheck.py episodes/<ep>`, before the previews and `make_episode.sh`, and no delivery on exit 1. Every later episode follows that skill, so a step it lacks never runs.
- **Offer an optional `<slug>-sound-design` skill** once the show's sound has settled, copied from `nobody-moves-sound-design`. Re-measure every number in it on the new show's episodes (`references/baselines.md`, the "Measured" table in `references/sound-catalog.md`), and point the fallback in `scripts/soundprobe.py`'s `_pipeline_dir()` at `shows/<slug>`. Until it exists, use `nobody-moves-sound-design` from `shows/<slug>` (Stage 4).
- **Link them for Claude Code:** `ln -s ../../.agents/skills/<name> .claude/skills/<name>`, relative like the existing links, because a relative link keeps working in any checkout path and an absolute one breaks on every other machine. `.agents/skills/` holds the real files; the link is how Claude Code finds them.
- **Test the skills** by writing Episode 2 through the write skill and building it through the produce skill. That's how the NOBODY MOVES skills were validated; any gap in them shows up at once.
- **Register the show:** add a line for `shows/<slug>/` under Structure in `AGENTS.md`, naming its skills as the `shows/nobody-moves/` line does. `shows/` is already export-ignored in `.gitattributes` and `.skillignore`, so the user's images never ship with the `watch` skill.
- **What to commit:** `shows/<slug>/`, the show's skills and their symlinks. That covers `SERIES.md`, `README.md`, `cast.py`, `soundtrack.py`, `pipeline/`, `tools/`, each episode's `episode.py`, `SCRIPT.md` and `make_stills.py`, `stills/`, and `stock/` if anything was fetched. Never commit `build/`, `.venv/`, `assets/`, `sound_kit/` or `.env`. Open PRs as drafts and merge only when the user says so, because they review the pilot first and say "merge it" when ready. Use a merge commit, like the repo's earlier PRs, so each show's history stays intact.
- **Check the old show is untouched:** `git status --short shows/nobody-moves` should print what it printed before Stage 2. It may not be empty, because the tree can hold unrelated changes; nothing new should appear.
- **Keep the ledger.** After every episode, update `SERIES.md`: mark the paid-off clue, add the new one, mark the roadmap entry written. The next writer depends on it.

## When things go wrong

`references/lessons.md` has the full list. The ones that bite first:

- **`Error processing file ... phontab`:** the path is too long for espeak-ng. Use a shorter checkout path or slug.
- **`<NAME> is not in the cast`:** the speaker isn't in `cast.py` or the episode's `CAST`. The pilot template's `WITNESS` lives in its own `CAST` line until you replace it.
- **A shot draws as the end card:** its kind is missing from `render()`'s dispatch.
- **`unknown sfx`:** add a branch for the name in `build_audio.py`.
- **The preview shows old text:** re-run `build_audio.py`. The renderer reads `episodes/<ep>/build/timeline.json`.
- **Runtime over 90 s:** cut narration that repeats the screen, and fold narration into character lines.
- **The render is over 30 MB:** send `_tiktok.mp4`, not the master. `pipeline/deliver.py --max-mb` sets the cap.

Posting, labeling, licensing and the launch plan are in `references/posting-playbook.md`. Give the user its short version with the pilot: turn on the AI-generated label, pin a hint comment and never the answer, and finish 8–10 episodes before launch.
