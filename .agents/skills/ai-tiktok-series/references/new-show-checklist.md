# New show checklist, file by file

How to turn `shows/nobody-moves/` into `shows/<slug>/`. Paths below are relative to the new show's folder unless they start with `shows/` or `.agents/`. `new_show.sh <slug>` and `git` run from the repo root; `.venv/bin/python ...` commands run from `shows/<slug>/`.

**Never edit `shows/nobody-moves/` for the new show.** Copy it, then change the copy. Every NOBODY MOVES episode must keep rebuilding byte-identically, and the new show should not depend on the old one's files.

## 1. Scaffold

```bash
bash .agents/skills/ai-tiktok-series/scripts/new_show.sh <slug>
```

Run it from the repo root. First note what `git status --short shows/nobody-moves` prints; section 5 compares against it. The script copies the files below, writes `SERIES.md` from `series-bible-template.md`, and creates empty `episodes/` and `stills/`. It skips `.venv/`, `assets/`, `build/`, `stock/`, `sound_kit/`, stills and episodes.

The copy works as is on a fresh show: the self-test writes its own still, so it doesn't wait for images, and the score builds to the last shot marked `"climax": True`.

Last, it prints the NOBODY MOVES-specific lines a grep can find. That list is a starting point, not the whole job: section 3 covers what a grep can't see, such as what the climax and hush lines key on. Re-run the same search at the end (section 5) until it prints nothing you didn't mean to keep.

Keep the slug short. espeak-ng (Kokoro's pronunciation engine) fails with `Error processing file ... phontab` when its data path, inside `.venv/`, is longer than about 160 characters.

## 2. Reuse unchanged

These files are show-neutral. Don't touch them unless you have a reason.

| File | What it does |
|---|---|
| `make_episode.sh` | Runs audio, then `SCRIPT.md`, the master render and the TikTok copy. Only its usage comment names `ep01_three_feet`. |
| `requirements.txt` | Pins `kokoro-onnx` and `espeakng-loader`, which shape how every voice sounds. |
| `tools/common.sh` | `find_python` (3.10–3.13), `download`, sha256-pinned Kokoro model files, `check_espeak_path`. |
| `tools/install-kokoro.sh`, `tools/kokoro_say.py` | The user-wide `kokoro` command. It is shared by every show, so a user who installed it for NOBODY MOVES already has it. Only the example lines mention Garrison and Lorraine. |
| `.gitignore`, `.env.example` | Ignore `.venv/`, `assets/`, `episodes/*/build/`, `sound_kit/`, `.env`; list the three stock-API keys. |
| `pipeline/deliver.py` | Two-pass H.264 copy under `--max-mb 29` (default). |
| `pipeline/grid.py` | Coordinate grid overlay: `grid.py <still> -o episodes/<ep>/build/<key>_grid.png [--box x0,y0,x1,y1] [--bright 2.5]`. Without `-o` it writes next to the still, into the library you commit. |
| `pipeline/safezones.py` | Renders sample moments with and without text and flags any text under TikTok's, Reels' or Shorts' UI (`ZONES`); `review.py` runs it. Writes `build/review/zones.png`. |
| `pipeline/script_md.py` | Writes the timecoded `SCRIPT.md`, with the `ANSWER`, voices, recording names and credits. |
| `pipeline/soundbank.py` (mechanism) | Resolves each named sound: synthesized, or stock per `soundtrack.py`. Edit `SYNTH`/`LOOPED` only when you rename or add sounds. |
| `pipeline/build_audio.py` (voice path) | Recordings, then Kokoro or ElevenLabs. Pitch via rubberband, the "altered" chain, a trim at −45 dB, RMS at −17 dB per line, a cache keyed by line and settings, the timeline (`pre`, `post`, `min`), and `master()` (two-pass loudnorm to −14 LUFS, −1.5 dBTP). |
| `pipeline/render.py` (generic parts) | Kinds `still`, `title`, `qcard`, `end`. Also `grade` (grain, vignette), captions, `pick_view` fallbacks, `placeholder`, `--preview`, `--contact`, and the encoder (crf 21, `-maxrate 9M`). |
| `pipeline/sounds.py` (toolkit) | `_rng` (sha256-seeded per sound), filters, `reverb`/`_hall`, `piano_note`, `_ensemble`, `impact`, `braam`, `riser`, `whoosh`, `swell`, `LEVELS`. |

## 3. Rewrite

### `SERIES.md`
Fill in every section of the template. See the skill's stage 2.

### `README.md` (new file)
Write one for the show, with the same sections as `shows/nobody-moves/README.md`: quick start, making an episode, the `episode.py` reference (list your shot kinds and their fields), voices, score and sound effects, stock assets, and posting. Say that it is independent of the `watch` skill.

### `cast.py`
- Replace `CAST` with the new cast, including the `CHIME` entry and the commented-out `RAY` line. Keep the docstring; it documents the ElevenLabs and recordings options.
- Only use English presets for an English show: `af_*`/`am_*` (American) and `bf_*`/`bm_*` (British). `build_audio.py` phonemizes `a*` voices as en-us and everything else as en-gb, so the Spanish, French, Hindi, Italian, Japanese, Portuguese and Chinese presets would be mispronounced. List all 54 with `kokoro --voices`, or from Python with `Kokoro(...).get_voices()`.
- Fields: `speed` (1.0 is the preset's rate), `pitch` (a rubberband ratio that keeps the tempo; 0.86 is about 2.6 semitones down), `altered: True` (the documentary "voice altered" chain).
- Give each character a clearly different preset or pitch. Muted viewers read captions, but sound-on viewers need to tell the voices apart instantly.
- Once a character has spoken in a published episode, freeze their entry. Changing it re-voices them in every episode on the next build.

### `soundtrack.py`
Empty `SOUNDS`. Update the docstring's list of names if you rename or add sounds.

### `pipeline/sounds.py`: the show's signature
- `THEME_NOTES` (MIDI numbers, played an octave down), `THEME_TURN` (the note that replaces index 6 on every other bar), `THEME_STEP` (seconds per note), `PAD_CHORDS` (four chords, two ostinato bars each). NOBODY MOVES is A minor, `[69, 72, 76, 72, 69, 72, 75, 72]`, with the D♯ as the unease. Choose a motif that matches the new format's genre: a nature doc wants something warmer, a news parody wants a stab-and-pulse.
- **The key is also hard-coded outside those names.** Change the key and these stay in A minor, and you can't hear the clash:

  | Where | Value | Notes |
  |---|---|---|
  | `theme_layers`, the drone | `55` and `82.4` Hz | A1 and E2 (root and fifth) |
  | `shimmer` | MIDI `(81, 88, 93)` | A5, E6, A6 |
  | `braam(dur=3.2, root=33)` | MIDI `33` | A1; the chord is root, fifth, octaves |
  | `sting`, the piano cluster | MIDI `33, 40, 45, 48, 52` | A1 E2 A2 C3 E3; 48 (C) is the minor third |
  | `swell`, the sub | `55` Hz | A1 |
  | `chimes`, if you keep it | `1318.5 … 2349.3` Hz | E6 G6 A6 C7 D7, A-minor pentatonic |

  Transpose all of them with the key, by the same `k` semitones: add `k` to MIDI numbers and multiply Hz by `2 ** (k / 12)`. Simplest is one constant at the top, `KEY = 0` (semitones from A), written into each (`midi(33 + KEY)`, `55 * 2 ** (KEY / 12)`). For a major key, also raise the sting's third (48 to 49) and rebuild `PAD_CHORDS` as major-key chords.
- The foley functions (`shutter`, `typewriter_click`, `carriage_ding`, `chimes`, `wind`, `crickets`, `glitch`, `jump`) are NOBODY MOVES sounds. Keep what fits, and add your own foley in the same style. Before dropping or renaming one, check the self-test fixture (below): it uses `shutter`, `crickets` and `ding`.
- Every new sound seeds its own stream with `_rng("<name>", ...)`. Never use a shared RNG or Python's `hash()`. That's why episode 12 sounds like episode 1.
- **For each new sound, follow `nobody-moves-sound-design`'s `references/add-a-sound.md`.** It is a worked example that touches every file: the generator, `soundbank.SYNTH`, a `LEVELS` entry set by measuring the sound next to its neighbors (a guessed level landed a knock under the doorbell jump), the `build_audio.py` branch, `mixcheck.cues()`, `KIT` and the docs. Its `references/mix-knobs.md` lists every number that shapes the score. The numbers in both files are NOBODY MOVES's; measure your own.
- **Run that skill's `scripts/soundprobe.py` from `shows/<slug>`:** `.venv/bin/python ../../.agents/skills/nobody-moves-sound-design/scripts/soundprobe.py <name> ...`. It loads `pipeline/` from the working directory; run from the repo root, it falls back to `shows/nobody-moves` (with a note on stderr) and measures the wrong show.
- Rewrite the "doorbell-cam" comments on `crickets`, `glitch` and `jump` if you keep them for something else.
- Mirror renamed sounds in `pipeline/soundbank.py` (`SYNTH`, and `LOOPED` for beds that fill a shot), in `pipeline/sound_kit.py` (`KIT`), in `mixcheck.cues()` and in the `soundtrack.py` docstring.

### `pipeline/sound_kit.py`
It exports the sounds as WAVs for the user. `typing_line`'s default text is NOBODY MOVES's first question ("Where were you on the night of June 13th?"), and `KIT` names two files `doorbell_glitch` and `doorbell_jump`. Rewrite the line in your show's voice, and rename or drop the entries for kinds you don't keep, because the kit is what the user edits with.

### `pipeline/build_audio.py`: the effects vocabulary and the climax
- **`sfx` names are hardcoded.** In the `for name in s.get("sfx", [])` chain, `sting`, `sting_end`, `sting_soft`, `shutter`, `wind`, `chimes` and `crickets` are handled. Any other name exits with `unknown sfx`. Add a branch for each new effect.
- **Automatic hits are keyed to shot kinds.** A `qcard` gets a whoosh, typing and a bell. A `doorbell` gets glitches, a jump, a riser and a braam plus impact at `flicker_at + CTA_DELAY`. Add the equivalent for your show-specific kinds.
- **The score** starts at the first shot whose `sfx` has `sting` (`bed_start`) and ends at the `end` shot. Its intensity builds toward `climax`: the last shot marked `"climax": True`; if there is none, the last `doorbell` shot; if there is neither, the end of the bed (the end card plus 0.4 s). Put `"climax": True` on each episode's reveal shot, or point the `doorbells` fallback at your own reveal kind. Otherwise the build peaks on the end card, too late.
- The `doorbell` hush (`dip`, under the flicker before the reveal hit) keys on the kind only. Point it at your reveal kind, or drop it if the reveal has no hit to land.

### `pipeline/render.py`: show-specific kinds and strings
- **Unknown kinds render as the end card.** `render()` sends any kind it doesn't list to `render_end`, with no error. Add every new kind to that dispatch, and to the lower-third and caption rules below it.
- **Hardcoded strings to change:**
  - `render_qcard`: `"INTERVIEWER"`.
  - `render_end`: `"Follow the case."`, `"Reenactments dramatized with AI."` and `"The flamingo is real."`. Write your own call to follow, and your own disclaimer written as a joke. Keep the phrase "dramatized with AI" or an equivalent: the label is part of the brand, not a confession.
  - `board_sources`: the card default `"WHO MOVED DEB?"`.
  - `render_doorbell`: the defaults for `camera` (`"FRONT DOOR · NO. 5"`), `date` (`"06/14/2026"`), `cta` and `cta_sub`.
- **Show-specific kinds:** `evidence` (EXHIBIT tag, flash, `annot_arrow`/`annot_circles`), `board` (cork, polaroids, red string) and `doorbell` (night vision, REC, frame numbers, `alter_box`/`alter_glow`/`lit`). Keep them if your format uses them, reskin them, or delete them. Model new kinds on them: a function `render_<kind>(shot, lt, fi, dur)` that returns an RGBA frame, with per-shot caches keyed by the shot id (a global cache made Episode 2's second doorbell reuse the first one's frames).
- **Looks:** `apply_look` has `anon` and `longlens`. Add looks for the format, such as a news-cam grade or a nature-doc long lens.
- **Palette and fonts:** `YELLOW (242, 194, 48)` and `RED (208, 52, 44)`. The fonts are Oswald, Inter, PlexMono, PermanentMarker and SpecialElite, from `assets/fonts/`. If you change fonts, change the downloads in `setup.sh` too (Google Fonts from `raw.githubusercontent.com/google/fonts/main/`, which is reachable).
- **Caption splitter:** `split_words` breaks long captions at sentence ends, skipping the abbreviations in `ABBREV` (`No.`, `Mr.`, `Mrs.`, `Ms.`, `Dr.`, `St.`). Add your show's own, or "Sgt. Pebble" becomes two captions. `legacy_chunks` (for timelines built before word timing) has its own lookbehinds for `No.` and `Mr.`.
- **Caption style:** `CAP_SIZE` (68 px), `CAP_Y` (1052) and `CAP_MAX_LINES` (2) keep captions above the name card at y 1262. The spoken word is drawn in `YELLOW`. Change them together if you move the name card.

### `pipeline/common.py`
- The docstring names NOBODY MOVES.
- `doorbell_clock` assumes 03:11:00 for an integer `clock_start`, and `CTA_DELAY = 1.9` is the doorbell's flicker-to-reveal time. Keep them only if you keep a timed-footage kind.

### `pipeline/stock.py` and `pipeline/selftest.py`
- `stock.py`: the environment variable `NOBODY_MOVES_STOCK_DIR`, the `.env` path in its messages, and the User-Agent. Rename them consistently, including in `selftest.py`.
- `selftest.py`: its fixture episode (the `EPISODE` string) uses `TITLE = "NOBODY MOVES"`, a still keyed `garrison`, and a `GARRISON` line from the series cast. The fixture writes its own still (`garrison.jpg`), so it never needs a library file. Rename the key, and change `GARRISON` to one of your cast once `cast.py` is rewritten; otherwise the self-test fails with `GARRISON is not in the cast`. Also rename the `nm-selftest-` temp prefix.
- **The fixture also depends on sound names and a kind.** Its `SOUNDS` uses `sting`, `shutter`, `crickets`, `theme` and `ding`; its shots use the `sfx` `sting`, `shutter`, `crickets` and `sting_end`, and the kind `evidence`. Every `SOUNDS` name must stay in `soundbank.SYNTH` (else `unknown sound name(s)`), and every `sfx` name needs its branch in `build_audio.py` (else `unknown sfx`). If you drop or rename one, swap in one of your own names of the same type (a one-shot for `shutter`, a looped bed for `crickets`), and keep four network sources so the `len(lock) == 4` check still holds. If you delete the `evidence` kind, change that shot to `still`: an unknown kind renders as the end card without an error, so the test would pass while checking the wrong thing.

### `pipeline/mixcheck.py`
It imports `CTA_DELAY` and `doorbell_clock`, and it labels the loud hits it finds using the automatic cues of the `qcard` and `doorbell` kinds. Keep `common.py`'s names or update the import, and add a label for each automatic hit you add to `build_audio.py`.

### `setup.sh`
The last `echo` names `ep01_three_feet`. Keep the model pinning exactly as it is: the checksums are what keep a character's voice identical across episodes and machines.

## 4. Environment

Set it up right after scaffolding, before stills or edits: `grid.py` and every build need `.venv`, and a passing self-test on the untouched copy separates environment problems from your own edits.

```bash
cd shows/<slug>                  # the .venv/bin/python commands in this file run from here
cp -r ../nobody-moves/assets .   # optional: identical pinned files; setup.sh skips downloading them and still checks the checksums
./setup.sh                       # venv from PyPI, Kokoro model and fonts from GitHub
.venv/bin/python pipeline/selftest.py
```

A venv can't be copied between folders; always create it with `setup.sh`.

## 5. Verify

1. `.venv/bin/python -m py_compile pipeline/*.py cast.py soundtrack.py` compiles cleanly.
2. `.venv/bin/python pipeline/selftest.py` passes.
3. The pilot builds and measures: `pipeline/build_audio.py episodes/<ep> --stems`, then right away `pipeline/mixcheck.py episodes/<ep>`, which must exit 0 (it also checks loudness and true peak), then `pipeline/render.py episodes/<ep> --contact` and `./make_episode.sh episodes/<ep>`. mixcheck goes before `make_episode.sh` because that script rebuilds the soundtrack without stems, and mixcheck's dialogue, music-out and hit checks read the stems. `<ep>` is the pilot's folder, e.g. `ep01_three_feet`.
4. No leftovers. Re-run the scaffold's own search (one pattern, so the two can't drift apart). From the show folder:
   ```bash
   bash ../../.agents/skills/ai-tiktok-series/scripts/new_show.sh --check .
   ```
   Lines for kinds you kept (doorbell, evidence, board) can stay. Then re-read section 3 for what a grep can't see.
5. The old show is untouched. From the repo root, `git status --short shows/nobody-moves` prints the same lines as before you scaffolded (section 1). It isn't always empty, because the tree can hold unrelated changes; what matters is that nothing new appears.

## 6. Register the show in the repo

- **Packaging:** `.gitattributes` already has `shows/ export-ignore` and `.skillignore` has `shows/`, so the new show's images never ship to people who install the `watch` skill. Check that both lines are still there.
- **`AGENTS.md`:** add a one-line entry for `shows/<slug>/` under Structure, next to the `shows/nobody-moves/` entry.
- **Skills:** write `.agents/skills/<slug>-write-episode/` and `<slug>-produce-episode/` (with the mixcheck step), optionally `<slug>-sound-design/`, and link each from `.claude/skills/`. See the skill's stage 6.
