---
name: nobody-moves-sound-design
description: Change, diagnose and measure the sound of NOBODY MOVES (shows/nobody-moves), covering the synthesized piano-and-strings score, trailer hits, stings, foley and ambiences in pipeline/sounds.py, how build_audio.py places and masters them, stock or user files swapped in through soundtrack.py or an episode's SOUNDS, and measuring a mix with mixcheck.py and soundprobe.py. Use this whenever the user wants the show's music or effects more or less dramatic, tense, cinematic or quiet; a different theme, tempo or chords; a new sound or sting; a sound swapped for their own or a stock file; says a line is buried, the music is too loud or a silent beat isn't silent; wants the audio checked before posting or a mixcheck failure explained; or wants the sound kit WAVs, even if they don't name the show or the files. For episodes the pipeline builds, use this, not cinematic-sound-designer, because build_audio.py regenerates all their audio. Rendering afterwards belongs to nobody-moves-produce-episode.
---

# NOBODY MOVES sound design

Every sound in the show is synthesized in code, deterministically, and the mix follows rules driven by the shot list. This skill covers changing that sound and proving the change with numbers.

**You can't listen to audio.** Measure everything, report the numbers, and let the user judge by ear.

Run everything from the show folder:

```bash
cd shows/nobody-moves
PY=.venv/bin/python
PROBE=../../.agents/skills/nobody-moves-sound-design/scripts/soundprobe.py
```

`soundprobe.py` measures the `pipeline/` in the working directory. Run from anywhere else, it falls back to `shows/nobody-moves` and says so on stderr, so a copied show must run it from its own folder.

## When to use this skill

Use it to:
- make the sound more or less dramatic, tense or busy, across the show or in one place;
- change the theme's notes, chords or tempo;
- add a new named sound, or swap one for the user's file, a stock file or an API sound;
- fix a line that's buried under music or an effect;
- check that a `"music": "out"` beat is really silent;
- measure a mix before delivery or after any audio change, and explain a mixcheck failure;
- export the sound kit (`sound_kit/*.wav`) for CapCut, Confessionals or trailers.

Other skills cover the rest:
- **`nobody-moves-produce-episode`:** stills, voices, framing, the full render and the TikTok copy. Hand back to it once the sound is settled here.
- **`nobody-moves-write-episode`:** the script, including each shot's `sfx` from the existing list and where `"music": "out"` goes. This skill checks that the silence lands.
- **`cinematic-sound-designer`:** not for episodes the pipeline builds. It renders an SFX stem from a transcript, and the next `build_audio.py` run regenerates all of the episode's audio from the shot list, so that stem is thrown away (and it skips `LEVELS`, determinism and mixcheck). Use it only for edits made outside the pipeline, e.g. a Confessional cut in CapCut from the sound kit (recipe f).

Come here when the sound itself changes, or to measure or diagnose a mix.

## How the sound is built

| File | Owns |
|---|---|
| `pipeline/sounds.py` | The library. `SR` (48000); `LEVELS` (mix gain per sound, in dB); the theme (`THEME_NOTES`, `THEME_TURN`, `THEME_STEP`, `PAD_CHORDS`); `_rng`; the filters; the hall (`_hall`, `reverb`); the instruments (`piano_note`, `string_pad`, `heartbeat`, `shimmer`, `theme_layers`, `motif_bed`); the hits (`impact`, `braam`, `riser`, `whoosh`, `sting`, `swell`); the foley and ambiences (`shutter`, `typewriter_click`, `carriage_ding`, `wind`, `chimes`, `crickets`, `glitch`, `jump`) |
| `pipeline/soundbank.py` | `SYNTH` (sound name to generator), `LOOPED`, `fit()`. `Bank.get(name, seconds, i)` returns the stock file if one is set, otherwise the synthesized sound. Unknown names exit |
| `soundtrack.py` | `SOUNDS`: show-wide name to stock source. An episode's own `SOUNDS` overrides names; `common.load_episode` merges them |
| `pipeline/stock.py` | `fetch()` (file, url, freesound, freesound_search, elevenlabs_sfx; pinned in `stock/sources.lock.json`) and `decode_audio(path, sr, channels)` |
| `pipeline/build_audio.py` | The timeline, the three buses, `put()`, the intensity curve, `dip()` gating, automatic placement, ducking, `--stems`, `master()` |
| `pipeline/common.py` | `CTA_DELAY` (1.9 s from flicker to call to action, shared by the renderer and the mix) and `doorbell_clock()` |
| `pipeline/sound_kit.py` | `KIT` (kit file name to sound); writes `sound_kit/*.wav`, which is gitignored |
| `pipeline/mixcheck.py` | Measures a built episode; exits 1 on a HARD failure |
| `scripts/soundprobe.py` (this skill) | Measures single sounds (`--episode` for an episode's `SOUNDS`), checks determinism, measures the stems' low end, splits the bed under each line (`--lines`) |

**Buses.** `build_audio.main()` builds three, each stereo at 48 kHz:
- **dialogue** (`vox`): every line is RMS-matched to -17 dBFS in `voice_line()`.
- **score:** `score` plus `under`, both ducked under dialogue by up to 8 dB.
  - `score` is the theme bed: shaped by the intensity curve, the gate and the end fade, highpassed at 45 Hz, and set at `LEVELS["bed"]`. Only the bed is gated by `dip()`.
  - `under` holds the risers and the `sting_soft` swell.
- **effects** (`fxbus`): stings, impacts, braams, whooshes, shutter, typewriter, bell, glitches, jump and ambiences. Never ducked, never gated.

The buses are summed and peak-normalized to -1 dBFS. `master()` then applies a 30 Hz highpass, a gentle compressor and a limiter, and normalizes loudness in two passes to -14 LUFS and -1.5 dBTP. So `LEVELS` are relative to each other and to the dialogue, which is fixed at -17 dBFS RMS. The master only sets overall loudness: raising every entry by x dB lowers dialogue over bed by x dB. `put(buf, at, y, gain_db)` places a sound at `at` seconds.

**Automatic.** These come from the shot kinds, with no fields needed:
- **Score:** the bed runs from the title (the first shot with `sting` in its `sfx`) to 0.4 s into the end card. Its intensity builds from 0.3 to 1.0 at the climax and holds there; the heartbeat enters at 0.5 and the shimmer at 0.8. The climax is the start of the **last** shot marked `"climax": True`; with none, the last doorbell shot; with neither, the end of the bed.
- **Question cards** (`qcard`): a whoosh 0.45 s before, one typewriter key per character, then the bell.
- **Every `doorbell`,** replays included:
  - 6 glitches from `flicker_at`;
  - a `jump` at the cut to frame B;
  - a riser across the flicker into an impact and braam at `flicker_at + CTA_DELAY`;
  - the score hushed to 0.3 under the flicker.

**Chosen per shot** in `episode.py`: `"music": "out"` (recipe e), `"climax": True` (recipe a, "One moment only"), plus these `sfx` names. Any other `sfx` name exits.
- `sting`: a riser runs into it;
- `sting_end`;
- `sting_soft`: under the shot's last line;
- `shutter`: over an impact;
- `wind`, `chimes`, `crickets`: the whole shot, stopping dead at the cut.

Per-sound detail is in `references/sound-catalog.md`; every tunable number is in `references/mix-knobs.md`.

## Rules

- **Seed every random draw with `_rng(...)`.** Key it by the sound's name and any parameter that changes it, e.g. `_rng("riser", dur)`. Never use:
  - Python's `hash()`, which is salted per process, so the sound changes every run;
  - the `random` module or the `np.random.*` globals;
  - one stream shared by several generators, which makes a sound depend on what was generated before it.

  Why: the same sting in every episode is the show's identity, and rebuilds must reproduce exactly so that a diff means something. `$PY $PROBE --determinism` catches all three.
- **Never modify a cached result in place.** `piano_note` and `_hall` are `lru_cache`d, so `note *= 0.5` on their output would silently change every later use. Copy it, or build a new array.
- **Generators return peak-normalized audio,** mono `(n,)` or stereo `(n, 2)` at `SR`. Loudness lives only in `LEVELS`, so the balance is set in one place, and stock files (which `Bank` normalizes) drop in at the same level.
- **Editing the library changes every episode.** That covers `sounds.py`, `LEVELS`, `soundbank.SYNTH`, the mix code in `build_audio.py` and `soundtrack.py`: all change every episode's audio on its next build. Rebuild and re-measure all of them, re-render or remux every MP4 (see below), re-export the sound kit if the user uses it, and tell the user that already-posted episodes won't match the new ones. Adding a new sound that no episode uses leaves every episode bit-identical.
- **Measure; don't claim.** Never say something "sounds" better. Report the numbers and describe the change in words, then ask the user to listen on a phone speaker and on headphones.
- **Don't route around blocked hosts.** Freesound, ElevenLabs and other stock APIs are blocked in cloud sessions. The blocks are a deliberate boundary, and working around them breaks the environment's rules. Ask the user for the file, or to allow the host.

## Phone speakers and mud

Most viewers hear one phone speaker, which plays little below about 250 Hz.

- **Sub-only hits vanish on phones.** A hit that is all sub is huge on headphones and gone on a phone; the first impact was. A mid body, a noise boom, saturated harmonics and a shorter sub fixed it (before and after in `references/baselines.md`, "Measured changes"). `impact`, `braam` and `jump` all use this pattern:
  ```python
  harmonics = highpass(np.tanh(6 * normalize(low)), 220, 2)   # the low end's overtones, audible on phones
  ```
- **Check with numbers.** `$PY $PROBE <name>` shows each sound's share of energy above 250 Hz; keep hits at 15% or more. mixcheck's "phone presence" row gives the effects stem and the mix; compare them with the baselines.
- **For mud, highpass rather than stack lows.** Energy below 60 Hz masks dialogue. The score's mud came down after four changes: less drone and cello, a 45 Hz highpass on the bed, a 30 Hz highpass on the master, and an added violin layer. Keep the score stem at about 25% or less below 60 Hz; check with `$PY $PROBE --stems episodes/<ep>`.
- **Mono.** A phone plays the mono sum, so mixcheck's mono sum should stay within about 1 LU of stereo. Wide sounds made from independent left and right noise, like `wind`, are fine. A phase-inverted copy is not.

## Measure

After any audio change, run these back to back for each affected episode:

```bash
$PY pipeline/build_audio.py episodes/<ep> --stems     # 40-60 s with cached voices
$PY pipeline/mixcheck.py episodes/<ep>                # table; --json for one JSON object; exit 1 on a HARD failure
```

| Check | Target |
|---|---|
| HARD loudness | -14 ± 1 LUFS |
| HARD true peak | ≤ -1.0 dBTP (the master aims at -1.5) |
| HARD dialogue over bed | median ≥ 12 dB, aim for 15+; a line under 8 dB is a warning |
| HARD music-out silence | the score's loudest 100 ms < -60 dBFS (0.25 s at each edge ignored) |
| HARD length | soundtrack ≥ timeline total |
| info hits | the reveal hits and stings on top, within about 1 dB of each other; shutters, then jumps, well below |
| info phone presence, mono, tail, LRA | see above; the tail well under the mix average |

The current values for ep01–ep03 are in `references/baselines.md`; compare every result with them.

- **Always rebuild with `--stems` right before mixcheck.** Its dialogue, music-out and hit checks read the stems, and it can't tell stems from an earlier mix of the same timeline. After a level change and a plain build, the old stems still correlate with the new soundtrack as well as fresh ones would, so mixcheck reports the old hit list and passes. "stems: stale" only catches a changed timeline. A NOTE flags stems over 30 s older than `soundtrack.wav`, but don't rely on it. `make_episode.sh` rebuilds the soundtrack without `--stems`, so never trust stems left from before it ran. The soundtrack runs 5 ms behind the stems because of the limiter's look-ahead; that's expected.
- **Single sounds:** `$PY $PROBE [name ...]` gives, for each sound:
  - its loudest 0.5 s window;
  - its "placed" level: that window plus its `LEVELS` gain. For a sound placed alone, this predicts its row in mixcheck's hit list to within about 1 dB. For sounds placed together, power-sum their placed levels, `10*log10(10**(a/10) + 10**(b/10))`; the reveal (impact plus braam) is worked through under "Measured" in `references/sound-catalog.md`, which also lists every sound's current values;
  - its share of energy above 250 Hz and below 60 Hz.

  Add `--episode episodes/<ep>` to resolve names as that episode does, with its own `SOUNDS`.
- **Per line:** `$PY $PROBE --lines episodes/<ep>` splits the bed under each line into score and effects; see recipe (d).

## Recipes

### (a) More or less dramatic, across the show

Pick the lever that matches what the user asked for, change one or two things, and measure. Locations and current values are in `references/mix-knobs.md`.
- **Tense from the start:** raise the intensity floor and lower the span with it, keeping them summed to 1 (`0.3 + 0.7 * ...` becomes `0.45 + 0.55 * ...`), so the climax stays at 1.0. Or lower the curve's exponent (`** 1.3`).
- **Earlier or stronger heartbeat:** lower the pulse threshold (`intensity - 0.5`), or raise its weight (0.7).
- **Bigger climax:** raise the shimmer weight, or make the reveal hush a full drop (the 0.3 in the doorbell `dip(...)` becomes 0.0).
- **Bigger hits:** raise `LEVELS` by 1–3 dB. `sting` is the title card, `sting_end` the end card. Raising `impact` also raises every shutter hit, which is placed at `LEVELS["impact"] - 4`.
  - **The reveal alone:** raise `LEVELS["braam"]`, which only the reveal uses (`sting()` calls `snd.braam()` directly). The reveal gains less than the offset, because the impact under it doesn't move; the power sum predicts how much, and "Measured changes" in `references/baselines.md` has a tested +3 dB. For more, add the same offset to both reveal lines in `build_audio.py` (`put(fxbus, flick + CTA_DELAY, bank.get("impact"), LEVELS["impact"])` and the `braam` line under it). That leaves the shutters alone.
  - The master re-normalizes, so everything else gets quieter. Check that the dialogue median stays at 15 dB or more and the reveal hits stay at the top of the hit list.
- **Louder bed:** raise `LEVELS["bed"]`. Every dB it gains costs a dB of dialogue clarity.
- **Faster or darker theme:** change `THEME_STEP` (which also moves the heartbeat and the chord length), `THEME_NOTES` or `PAD_CHORDS`. Keep the minor key and the flat five; they are the show's unease.
- **Less dramatic:** the reverse. For example, set the shimmer weight to 0, raise the pulse threshold, and lower the hits by 2–3 dB.
- **One moment only:** leave the library alone. Use `"music": "out"` (recipe e), move a line, or drop an `sfx`. A synthesized sound has no per-episode level: `gain_db` only trims a stock source, and `{"gain_db": -3}` alone exits with "unknown stock source". To trim one in a single episode, freeze it to a file ("Per-episode trim" in `references/mix-knobs.md`).
  - **Move the score's peak** with `"climax": True` on a shot. The score builds to the last marked shot instead of the last doorbell, then holds at full intensity to the end. Use it in an episode with no doorbell ending, such as a Confessional: without a mark, its build runs all the way to the end card, so it peaks after the punchline. In a doorbell episode a mark overrides the doorbell, so the score peaks early and stays at full through the reveal; leave it off there unless that's the point.

Then rebuild and mixcheck every episode, compare with the baselines, and describe the change in plain words, e.g. "the heartbeat now comes in a third of the way through instead of halfway".

### (b) Add a new named synthesized sound

`references/add-a-sound.md` is a full worked example, with code for every file and measured results.
1. **Generator** in `sounds.py`: seeded with `_rng("<name>", ...)`, peak-normalized, and sent through `reverb()` if it belongs in the hall. If it's a hit, give it energy above 250 Hz.
2. **`soundbank.SYNTH`:** add `"<name>": lambda sec, i: snd.<gen>(...)`. Add the name to `LOOPED` if it fills a shot.
3. **`LEVELS["<name>"]`:** set it by comparing its placed level with its neighbors in `$PY $PROBE <name> shutter jump`, not by guessing. A short knock at a sensible-looking -12 landed under the doorbell jump.
4. **Placement** in `build_audio.py`: a new `elif name == "<name>":` branch in the `sfx` chain if it's chosen per shot, or an `if s["kind"] == ...` block if it's automatic. Use `fxbus` for hits and foley, and `under` for tonal builds.
5. **`mixcheck.cues()`:** add the cue, so the hit list and `$PROBE --lines` name it. For an `under` sound, add it to `placed_over()` in `scripts/soundprobe.py` instead.
6. **`sound_kit.KIT`:** add the export.
7. **Docs:**
   - the "Names:" docstrings in `soundtrack.py` and `soundbank.py`;
   - `README.md`: the sound table, the `sfx` options, the stock names and the kit list;
   - the write skill's template, if the sound is chosen per shot.
8. **Measure:** probe it with `--determinism`, rebuild an episode that uses it, and run mixcheck. Check that it lands in the hit list at the level you intended, after any nearby line rather than under it.

### (c) Replace a sound with a stock file or an API sound

- **Scope:** for the whole show, set the name in `soundtrack.py`'s `SOUNDS`. For one episode, set it in that episode's `SOUNDS`.
- **Sources:** `{"file": "stock/audio/x.wav", "credit": "..."}` works offline. `url`, `freesound`, `freesound_search` and `elevenlabs_sfx` need the network and keys in `.env`, and those hosts are blocked in cloud sessions. Ask the user to send the file in a normal message, because attachments sent mid-task may not be saved to disk.
- **Level:** `Bank` peak-normalizes the file, then applies `"gain_db"`, then `LEVELS`. Match the old sound's loudness with `gain_db`: probe the name before and after (`$PY $PROBE <name>`), and bring its 0.5 s level close to the old one. For an episode's `SOUNDS`, add `--episode episodes/<ep>`. Without it the probe reads only `soundtrack.py` and measures the synthesized sound both times.
- **Length:** only `theme`, `wind`, `chimes` and `crickets` are looped or trimmed to fit.
  - A stock `riser` plays at its own length, so trim it to about 1.9–2.0 s, peaking at its very end.
  - A stock `theme` loses the layer-by-layer build and can only swell in level.
- **Side effects:** replacing `impact` also changes every shutter hit.
- **Licensing:** CC0 or CC-BY only, because a monetized TikTok counts as commercial use.
- **Pinning and credits:** fetched files are pinned in `stock/sources.lock.json`, so commit `stock/`. Re-run `pipeline/script_md.py` so that `SCRIPT.md` lists the credits.

### (d) Fix a buried line

1. **Find it.** mixcheck's worst lines and warnings give the shot, start time and speaker.
2. **Find the cause** with `$PY $PROBE --lines episodes/<ep>`, on fresh stems. mixcheck can't show it: its `bed_dbfs` is score and effects together, and its hit list reads only the effects stem. For each worst line, the probe gives the score and effects levels, says which is louder, and lists what's placed over the line on each stem.
   - **Score louder:** the bed, or something on `under` (`sting_soft` or a riser). `sting_soft` is why the board line is among the worst lines in every episode: it starts 0.1 s before the board's last line and sits well above the bed there. `references/baselines.md` has the split and what the line reads without it.
   - **Effects louder:** a hit's tail or the shot's ambiences. Ep03's Ray line sits under the braam tail of the replay reveal, placed just before the line.
   - **Both:** the chime lines, with wind and chimes over the bed.
3. **Fix it,** trying these in order:
   - **Move the line off the sound** with a `P(0.4)` before it or a `"pre"` on its shot. This changes the timeline, so the episode needs a full render.
   - **Trim the sound show-wide** with its `LEVELS` entry. `LEVELS["sting_soft"]` changes every board shot; "Measured changes" in `references/baselines.md` has what -3 and -6 dB do to the board lines. Its placement is the "Board swell" row in `references/mix-knobs.md`.
   - **Trim it in one episode** by freezing it to a file with a `gain_db` ("Per-episode trim" in `references/mix-knobs.md`). There's no other per-episode level for a synthesized sound.
   - **Drop an ambience.** `wind` and `chimes` together is the usual culprit. Lines under deliberate ambience can sit a few dB under the median, as the chime lines do; under 8 dB (mixcheck's warning) they're buried.
   - **Deepen the duck** from 0.6 to 0.7, but only if many lines are low in every episode. A deeper duck makes the score pump audibly in every episode.
4. **Never turn the voices up.** Lines are RMS-matched and the master re-normalizes loudness, so louder voices only push the limiter and flatten the hits.

### (e) Silence the score for one shot

Add `"music": "out"` to the shot in `episode.py`. The bed fades out over the 0.2 s before the shot and back in over the 0.4 s after it.
- **It cuts only the score bed.** The shot's own `sfx` and the effects bus still play. Ep03's `exhibit` cuts the music as its shutter fires, so the flash lands in silence.
- **`under` sounds aren't cut either.** `sting_soft` and the risers play on, but mixcheck counts them as score, so a music-out shot that contains one fails the check. Don't combine them.
- **For true silence,** give the shot no `sfx`, and check that the previous shot's sting tail has died away.
- **Use it once or twice an episode,** right before a punchline or a reveal. A drop used everywhere stops landing.
- **Verify** with mixcheck's music-out row: it should read silent, under -60 dBFS.

### (f) Export the sound kit

Run `$PY pipeline/sound_kit.py`. It writes every `KIT` entry to `sound_kit/*.wav` as 16-bit, 48 kHz, mono or stereo as generated (5 of the 17 are mono: `camera_shutter`, `typewriter_key`, `typewriter_bell`, `doorbell_glitch`, `doorbell_jump`), using the same sources as the episodes (including any stock overrides in `soundtrack.py`).
- **Levels:** each file is peak-normalized to -1 dBFS, so the mix balance isn't in the files. Tell the user to set levels in their editor; `LEVELS` gives the show's relative gains.
- **The theme** (`theme_60s`) comes from `motif_bed`, a fixed-intensity mixdown, not the building bed of an episode.
- **To send it,** zip the folder somewhere outside the repo, so a large binary can't end up committed, e.g. `$PY -c "import shutil; shutil.make_archive('/tmp/nobody_moves_sound_kit', 'zip', 'sound_kit')"`.

## Re-render or remux

**Remux** when both are true:
- the change touched only audio;
- `episodes/<ep>/build/timeline.json` has the same `total`, `shots` and `captions` as before. Copy it aside before rebuilding and compare; those are the only keys `render.py` reads. Each caption's `words` (the highlight timing) come from the voice clips alone, so a change to the score or effects leaves them the same.

Remuxing swaps the new audio into the existing MP4 in about 9 s, instead of a 10-minute render, with the same audio encoding `render.py` uses. The TikTok copy still takes about 4 minutes:

```bash
FF=$($PY -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
B=episodes/<ep>/build; E=<ep>
$FF -y -loglevel error -i $B/$E.mp4 -i $B/soundtrack.wav -map 0:v -map 1:a -c:v copy \
    -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart $B/remux.mp4 && mv $B/remux.mp4 $B/$E.mp4
$PY pipeline/deliver.py episodes/<ep>                 # the TikTok copy, under 29 MB
```

**Re-render** with `./make_episode.sh episodes/<ep>` if there's no MP4 yet, or if the timeline or `CTA_DELAY` changed.

## Validate before committing

```bash
$PY -m py_compile pipeline/*.py soundtrack.py        # silent when every file parses
$PY pipeline/selftest.py                             # "all stock-source checks passed" (15 checks)
$PY pipeline/sound_kit.py                            # every KIT entry exports (17 today)
$PY $PROBE --determinism                             # determinism: PASS
for ep in episodes/*/; do [ -f $ep/episode.py ] || continue
  $PY pipeline/build_audio.py $ep --stems >/dev/null && $PY pipeline/mixcheck.py $ep || echo "FAIL $ep"; done
```

- **Unused names and typos:** py_compile only catches syntax errors. pyflakes isn't in `requirements.txt`, so install it once (`$PY -m pip install -q pyflakes`), then run `$PY -m pyflakes pipeline/*.py soundtrack.py`; it should print nothing.
- **Every episode folder,** not just `ep*`: a Confessional or other short under `episodes/` uses the same library.
- **Commit** the code, `soundtrack.py`, the docs, and `stock/` if it changed.
- **Never commit** `build/`, `sound_kit/` (it's gitignored) or `.env`.

## Report back

Tell the user:
- **What changed,** in plain words.
- **The numbers that matter, before and after:** the dialogue median and the worst line, the order and levels of the hit list, phone presence, and pass or fail.
- **What was redone:** which episodes' audio changed, which MP4s were re-rendered or remuxed, and that already-posted episodes won't match.
- **That you judged by measurement only.** Ask them to listen on a phone speaker and on headphones. Send `episodes/<ep>/build/<ep>_tiktok.mp4`, and the kit WAVs if they asked for them.
