# NOBODY MOVES

A true-crime docuseries for TikTok where every witness is a lawn ornament. The episodes are built from AI stills with slow camera moves, captions and scratch voices. The ornaments never move; only the camera does. The series bible (cast, visual style, planted clues, episode roadmap) is in [`SERIES.md`](SERIES.md).

This folder is independent of the `watch` skill in the rest of the repo.

## Quick start

```bash
./setup.sh                                   # once: venv, Kokoro TTS model, fonts (PyPI + GitHub only)
./make_episode.sh episodes/ep01_three_feet   # ~10 min on a laptop CPU
```

You need Python 3.10–3.13, which Kokoro requires. `setup.sh` finds one automatically. On a Mac the built-in `python3` is too old, so run `brew install python@3.12` first if setup says none was found.

Outputs, in `episodes/<episode>/build/` (not committed):

| File | What |
|---|---|
| `<episode>.mp4` | Master render, 1080×1920, 30 fps, about 9 Mbps |
| `<episode>_tiktok.mp4` | Upload copy under 29 MB |
| `soundtrack.wav`, `timeline.json` | The mixed audio and the shot/caption timings |

`make_episode.sh` also rewrites `episodes/<episode>/SCRIPT.md`, the timecoded script.

## Making a new episode

With Claude Code (or any Agent Skills host), three skills in this repo do the whole loop:
- **`nobody-moves-write-episode`** writes the script, the image prompts and the continuity updates.
- **`nobody-moves-produce-episode`** builds, checks and delivers the video.
- **`nobody-moves-sound-design`** changes the score and sound effects and measures the mix.

To start a different show with this pipeline, use the **`ai-tiktok-series`** skill.

Just ask for "the next episode". By hand:

1. Copy an episode folder, or the template at `.agents/skills/nobody-moves-write-episode/references/episode-template.py`, to `episodes/epNN_<name>/episode.py`.
2. Reuse the **series library** in `stills/` (`garrison`, `porch`, `holes`, `yard_before`, `yard_after`, and the derived doorbell frame `yard_gone`); every episode can use it by key. Episode-only stills go in `episodes/<ep>/stills/`, and a still there overrides a library still with the same key. To generate new ones, use the style prompt in `SERIES.md`.
3. Edit `episode.py`: the title, `NEXT_UP`, `ANSWER`, `STILLS` (prompts for any new images) and the `SHOTS` list.
4. Place coordinates with `.venv/bin/python pipeline/grid.py stills/<key>.webp -o episodes/<ep>/build/<key>_grid.png [--box x0,y0,x1,y1] [--bright 2.5]`. It overlays a grid labeled in the same fractions `episode.py` uses. Always pass `-o`: without it the grid image lands next to the still, in the library.
5. Check framing without a full render:
   ```bash
   .venv/bin/python pipeline/build_audio.py episodes/ep02_x --stems
   .venv/bin/python pipeline/mixcheck.py episodes/ep02_x                    # loudness, dialogue over music, music-out, hits
   .venv/bin/python pipeline/render.py episodes/ep02_x --contact            # one frame per shot -> build/contact.png
   .venv/bin/python pipeline/render.py episodes/ep02_x --preview 1,12.5,30  # frames at those seconds
   ```
6. Run `./make_episode.sh episodes/ep02_x`.

The voice clips are cached by line text, so rebuilding after an edit only re-voices the lines you changed.

## `episode.py` reference

Positions are **fractions of the source image**: `(0.5, 0.5)` is the center. Zoom `1.0` shows the whole image and `2.0` is a 2× push-in.

```python
V("still_key", (cx, cy, zoom_start), (cx, cy, zoom_end), look)   # one camera move on one still
L("WHO", "caption text", "optional spoken text")                 # a line; spoken text fixes pronunciation ("1994" -> "nineteen ninety-four")
P(0.5)                                                           # a pause, in seconds
```

`views` is a list of camera moves. The shot uses the first one whose still exists, so list the ideal image first and a crop of one you already have as the fallback. The optional `look` is `"anon"` (blurred and cold, for anonymous sources) or `"longlens"` (a soft stakeout crop).

| `kind` | What it draws | Fields |
|---|---|---|
| `still` | A camera move on a still, captions, and an optional name card | `views`, `items`, `post`, `lower_third=(name, line2, line3)`, `lower_third_at="last"` |
| `evidence` | A still plus a camera flash, an EXHIBIT tag and timestamp, and drawn annotations | as `still`, plus `label`, `stamp`, `annot_arrow={"from","to","label"}`, `annot_circles=[(x, y, r)]` |
| `title` | Series title and episode name | `views`, `min` |
| `qcard` | A black card where the interviewer's question types out | `text`, `min` |
| `board` | Cork board with polaroids, red string and an index card that lands on the last line | `kb`, `card` (default "WHO MOVED DEB?"), `polaroids=[(still, (x0, y0, x1), label, fx, fy, size, rotation, look)]` (the first is the hub). Uses the `cork` still if present, otherwise a drawn board |
| `doorbell` | Night-vision cam: jump-cuts from A to B, flickers after the last line, pauses on B and shows a call to action | `frame_a`, `frame_b`, `kb`, `clock_start` (seconds past 03:11:00, or `"HH:MM:SS"` with `jump_after`), `frames=(a, b)`, `cta=(line1, line2)`, `cta_sub`. For the hidden clue in frame B: `alter_box=(x0, y0, x1, y1)` mirrors a region (it turned around); `alter_glow=(x, y, r)` lights a point (it switched on). `lit=[(x, y, r)]` lights points in both frames, for a light that is already on (continuity, not a clue) |
| `end` | End card with `NEXT_UP` and the AI disclaimer | `min` |

Every shot also takes `note` (the stage direction for `SCRIPT.md`), `sfx`, `"music": "out"` to cut the score for that shot, and `"climax": True` to make the score build to that shot instead of the last doorbell shot (for an episode without a doorbell ending, like a Confessional). The `sfx` options are `sting`, `sting_end`, `sting_soft`, `shutter`, `wind`, `chimes` and `crickets`. The score, the typewriter clicks, and the risers, whooshes and hits are added automatically.

## Voices

Every line is spoken by [Kokoro](https://github.com/thewh1teagle/kokoro-onnx), an open-weight text-to-speech model that runs locally on the CPU with no API key. Each character is a Kokoro preset voice plus a little post-processing: a speaking rate, a pitch shift, and for the anonymous source a "voice altered" filter.

The voices are defined once, in [`cast.py`](cast.py), and every episode uses them. Kokoro is deterministic, so the same line with the same settings and model files always produces the same audio. `setup.sh` checks the model files against pinned checksums, and `requirements.txt` pins the TTS packages. That keeps Garrison sounding like Garrison in Episode 12.

- **A new character:** add an entry to `cast.py`. Use an English preset (`af_`, `am_`, `bf_`, `bm_`): `build_audio.py` pronounces voices starting with "a" as US English and all others as British English, so other languages come out wrong. Pick one that's clearly different from the rest of the cast. `cast.py` has a commented-out suggestion for Ray.
- **A one-off speaker in a single episode:** define `CAST = {...}` in that episode's `episode.py`. It's merged over the series cast.
- **Changing an existing voice:** edit its `cast.py` entry. That character changes in every episode the next time each one is built.

The voices are scratch tracks. Recording your own takes is the biggest quality upgrade.

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
| Night crickets | Three crickets at 4.4, 4.75 and 5.1 kHz in different positions, plus a faint 60 Hz porch-light hum |
| Doorbell glitch, jump | A square-wave buzz in noise; the jump cut adds a short sub hit |

**Automatic hits.** The mix places most effects from the shot kinds, so an episode gets the cinematic treatment without any extra fields:

- a riser sweeps into the title card and lands on the title sting;
- every question card is preceded by a whoosh, then its question types out;
- every `shutter` lands on an impact;
- the doorbell jump cut gets a sub hit;
- a riser runs across the flicker, and a braam and impact land on the call to action.

**Dynamics.** The score starts quietly on the title card and builds toward the last shot marked `"climax": True`, else the last doorbell shot, else the end card: the pad swells, the heartbeat fades in around the middle, and the shimmer enters in the last stretch. It hushes under the doorbell flicker so the reveal hit lands. Give a shot `"music": "out"` to cut the score for that shot: silence before a punchline or a reveal is the most dramatic sound there is. The score and risers duck automatically under dialogue.

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

**Sounds and music.** Point a name in [`soundtrack.py`](soundtrack.py) at a source, and every episode uses it. An episode can override a name with its own `SOUNDS = {...}`. The names are `theme`, `sting`, `sting_end`, `sting_soft`, `riser`, `impact`, `braam`, `whoosh`, `shutter`, `typewriter`, `ding`, `wind`, `chimes`, `crickets`, `glitch` and `jump`. Stereo files stay stereo.

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

**Voices.** Any character in [`cast.py`](cast.py) can use an ElevenLabs voice instead of Kokoro. Your own takes beat both: save a line as `recordings/<name>.m4a` in the episode folder. `SCRIPT.md` shows the name for every line, for example `hook_1` or `chime_3`. A recording replaces that line's text-to-speech; the other lines keep their generated voice.

**Images.** Stills are already local files: put any image in `stills/` (the series library) or `episodes/<ep>/stills/`. To pull one from a stock library into an episode:

```bash
.venv/bin/python pipeline/stock.py image episodes/ep02_x aerial --pexels "suburban cul-de-sac at night"
.venv/bin/python pipeline/stock.py image episodes/ep02_x aerial --url https://.../photo.jpg --credit "Name, license"
```

**Keys.** Copy `.env.example` to `.env` (it's gitignored) and fill in only the services you use: `FREESOUND_API_KEY`, `ELEVENLABS_API_KEY`, `PEXELS_API_KEY`. The keys are never written anywhere else.

**Pinned and credited.** Anything fetched over the network is saved once in `stock/` and recorded in `stock/sources.lock.json` with its license and author. Every later build and every episode reuses that exact file with no API call; a Freesound search, for example, keeps the sound it found the first time. Commit `stock/` so the pins travel with the show. To fetch something again, delete its lock entry. `stock/CREDITS.md` lists everything, and each episode's `SCRIPT.md` ends with the credits for the sounds it used.

**Licensing.** Freesound searches only return CC0 and Attribution sounds, never NonCommercial ones, because a monetized TikTok counts as commercial use. Paste Attribution credits into the video description. For files you add yourself, record the license with `"credit"`.

**Self-test.** `.venv/bin/python pipeline/selftest.py` checks every source type against a local mock of Freesound, ElevenLabs and Pexels. It needs no keys or network and doesn't touch `stock/` or your episodes.

## Posting

Turn on TikTok's **AI-generated** label, and pin a comment that points at the hidden clue without giving it away. Main episodes run over 60 seconds, which TikTok's Creator Rewards program requires.
