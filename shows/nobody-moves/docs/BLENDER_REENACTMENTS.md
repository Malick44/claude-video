# Blender reenactments: `pipeline/blender_reenact.py`

**Blender renders run on your own machine only.** Never in a cloud or remote session: `pipeline/blender_reenact.py` refuses to start Blender when `CLAUDE_CODE_REMOTE` is set, and its selftest reports the rendering half as skipped there. Render finals and previews on your computer, then file the clip with `blender_reenact.py`.

**Status:** integrated in `pipeline/` (driver `blender_reenact.py`, Blender side `rx3d/`), tested with Blender 5.0.1 (`pip install bpy==5.0.1` on Python 3.11) and Cycles on the CPU. The Eevee and GPU paths are written and probed but have not run on a GPU yet. A reenactment shot with a `"blender"` dict is rendered here and **filed like any other clip, through `clips.py add`**, so `render.py` plays it with no change.

**What it does.** The tool renders that shot's 3D reenactment in Blender:
- timed to the episode's own narration (the move lands on a spoken word read from `build/timeline.json`);
- with the ornament **rigid by construction**: only its root is animated and its yaw is never keyed, so it can't bend, turn or grow limbs;
- with **no human possible**: the only assets are the cast's models (`models/`) and procedural set pieces.

The label is `REENACTMENT · AI` like every reenactment (decision D4, `docs/DECISIONS_EP01R.md`): `build_audio.py` and this tool both refuse anything else. A clip made with a stand-in PROXY model is a placeholder that `deliver.py` refuses.

Read with: the README's "Reenactments" and "Blender reenactments", `models/README.md`, `episodes/ep01r_three_feet_reenacted/episode.py` (the two reenactments), `SERIES.md` (the reenactment rules, the 3D references, the never-rules) and `stills/`.

---

## 0. Quick start

From `shows/nobody-moves/`:

```bash
# once: a Blender Python. Either the pip wheel (Python 3.11 only) ...
./setup.sh --blender                       # .venv-bpy: python3.11 -m venv + pip install bpy==5.0.1
# ... or the Blender 5.0 app:  export NM_BLENDER=/path/to/blender

PY=.venv/bin/python; B=pipeline/blender_reenact.py
$PY $B --selftest                                   # ~1-2 min on a CPU; fails if it can't render (--allow-skip)
$PY pipeline/build_audio.py episodes/<ep>           # word times -> build/timeline.json
$PY $B episodes/<ep> --dry-run                      # the plan: beats, frames, engine, cost
$PY $B episodes/<ep> --preview                      # look + timing: build/blender/<clip>/sheet.png
$PY $B episodes/<ep> --build                        # files a draft clip (or "up to date")
$PY $B episodes/<ep> --quality final --require-models   # the deliverable: on a GPU machine (§7.4)
$PY pipeline/build_audio.py episodes/<ep>           # records the filed clip; then render.py as usual
```

A preview never touches `clips/`. `--build` and `--quality draft|final` file a clip. With no mode flag the tool only prints its plan. `make_episode.sh` runs the `--build` pass by itself (§3.1).

---

## 1. Decisions at a glance

| Decision | Choice |
|---|---|
| Where the episode declares it | A `"blender"` dict **on the reenactment shot** (§2), because its timing words belong to that shot's lines. `CLIPS` stays for the image-to-video prompts. |
| Output | Filed by `clips.add()`: `clips/<key>.mp4` (the same mezzanine as a generated clip) and its `clips/clips.json` entry, plus `clips/<key>.blender.json` (the provenance sidecar). The key is the clip's own, ending in `_bl`; a Blender render never takes an AI clip's key. |
| Label | `REENACTMENT · AI`, always (D4). Whether AI made the models is recorded (`ai_generated` in the entry and the sidecar), not shown. |
| Timing | Word times from `build/timeline.json`, mapped onto **`render.py`'s own frame grid** (§3.2); `*_at` seconds as the fallback. `dur` is **required**. |
| Subjects | `models/<name>.glb` registered in `models/models.json`; a procedural **proxy** stands in until a model exists. Proxies are marked, and `deliver.py` refuses them. |
| Templates | `heist`, `action` (episode use) and `showcase` (model checks), in `rx3d/templates.py`. |
| Process model | A driver (any Python 3.10+, no `bpy`; normally the show's `.venv`) and a worker (inside Blender), **always a subprocess**. |
| Engines | Eevee (GPU) or Cycles (CPU or GPU). The look lives in the compositor, so both engines match. |
| Caching | A **content key** (what the clip shows) and a **render key** (how it was rendered). A final rendered on a GPU and committed stays current everywhere (§7.6). |
| Build | `make_episode.sh`: build_audio → `blender_reenact --build` → build_audio → render. No Blender is a warning (the fallback still plays) unless `NM_FINAL=1`. Episodes without a `"blender"` dict build exactly as before. |
| Blender | 5.0.x (tested 5.0.1, `pip install bpy==5.0.1` on Python 3.11, or the app). |

Conflicts with the brief, resolved toward the bible:
- The heist glides **sideways**, never toward the lens ("Across the frame, never along the lens axis"). A `toward` option exists and warns above 0.35.
- "Dark" heist means a **dark palette with a bright subject**, not a dark exposure ("Bright, never murky").
- **Deb is not in the heist frame.** From grass height her head is about 34 cm above the top of the frame, so only two blurred pink blobs showed. The locked lens *is* her point of view, and a pink kicker light from frame right says she's there. Garrison staring into the lens carries "he was facing her".
- **Lorraine's rock-waddle is allowed here**, because a rigid roll can't move a leg. AI clips still get one rigid move.

---

## 2. Declaring a Blender reenactment in `episode.py`

### 2.1 The Episode 1 remake's two shots

```python
{
    "id": "heist", "kind": "reenactment",
    "clip": "rx_heist_gnome_bl", "in": 0.0, "speed": 1.0, "dur": 4.05,   # its own key: never an AI clip's key
    "blender": {
        "template": "heist", "subject": "garrison", "props": [],       # Deb is the lens, not a prop
        "move_on": "move", "move_at": 3.23,          # the word first; seconds when there is no timeline
        "flare_on": "move",                          # the lens flare peaks 2 frames after "move"
        "camera": "beside_deb",                      # grass height, where Deb stands, locked off
        "options": {"path": "left", "travel": 0.25, "accel_s": 0.12},   # a rigid zip, a quarter frame by the cut
    },
    "kb": ((0.5, 0.5, 1.0), (0.5, 0.5, 1.0)),
    "label": "REENACTMENT · AI", "stamp": "THEORY #1: THE GNOME",
    "fallback": [V("rx_heist_gnome_bl_key", ...), V("rx_heist_gnome_key", ...), V("garrison", ...)],
    ...
},
{
    "id": "action", "kind": "reenactment",
    "clip": "rx_action_goose_bl", "in": 0.0, "speed": 1.0, "dur": 4.65,
    "blender": {
        "template": "action", "subject": "lorraine",
        "move_on": ["one", "goose"],                                  # one rock-waddle on each word
        "tip_on": "dared",                                            # the punch word triggers the drop
        "land_on": {"word": "dared", "edge": "end", "offset": 0.26},  # the thud lands in the silence after it
        "move_at": [2.80, 3.04], "tip_at": 3.56, "land_at": 4.34,
        "camera": "hero_low",
        "options": {"outfit": None, "steps_down": 1},                 # BARE: the night of 13-14 June
    },
    ...
},
```

With the Kokoro take, the heist holds dead still under "That night, he was facing her. Then he made his", zips on "move" (3.23 s) with the lens flare, and is cut 0.82 s later, mid-glide, 0.58 s after the line ends (**option B**: the slide punctuates the line). The action holds under "In a world where nobody moves...", rocks on "one" (2.80 s) and "goose" (3.04 s), tips on "dared" (3.56 s), dives one step in slow motion and lands at 4.34 s, 0.26 s after "dared" ends. The cut comes 0.31 s later.

Two values differ from the prototype's, so that the episode builds exactly as before while no Blender clip is filed: the action keeps the remake's `dur` 4.65 (the prototype ran 5.0), so the landing offset is 0.26 s instead of 0.37 s (the rule is 0.25 s or more after the word, and a cut 0.3-1.0 s after the landing). `"dur": 5.0` with `"offset": 0.37` restores the longer silence before the thud, at 0.35 s of the 3.1 s headroom. And the cut-back `l_deny` keeps the AI keyframe's framing `(0.52, 0.53, 1.35)`: once the Blender clip plays, its views go to `(0.50, 0.50, 1.0)` (§6, "Cut-back match", which prints that kb).

**Option A** for the heist (the slide illustrates the line: it starts on "Then" with a 0.35 s ease-in, about 15% of the frame width a second for 1.8 s) is one line away: `"move_on": "Then", "move_at": 2.26` and `"accel_s": 0.35` in the options.

### 2.2 The `blender` dict

| Key | Default | Meaning |
|---|---|---|
| `template` | required | `"heist"` or `"action"`. `"showcase"` is CLI only. |
| `subject` | the template's (`garrison`, `lorraine`) | The one ornament that moves: a model in `models.json`, else its proxy. Deb can never be a subject (canon never shows how she was moved). |
| `props` | the template's (both `[]`) | Static ornaments. They never move (checked every frame). A prop whose head would be off the frame warns. |
| `move_on` | none | The word in **this shot's** lines the motion starts on: `"Then"`, `"goose#2"` (the second one), or `{"word", "nth", "edge": "start"/"end", "offset": s}`. For `action`, a list of 1-3 words: one rock-waddle each. |
| `tip_on` | none | `action`: the word the tip starts on. Without it, the tip is derived from the slow-motion fall. |
| `land_on` | none | `action`: the landing thud. Default edge `"end"`. Land at least 0.25 s after the word ends. |
| `flare_on` | none | `heist`: the lens flare peaks 2 frames after this word's onset. Without it, at 60% of the glide. |
| `move_at`, `tip_at`, `land_at`, `flare_at` | none | Shot-local seconds for the same beats (a list for a list `move_on`). Used when there is no timeline or the word isn't found. |
| `camera` | the template's preset | A preset name, or `{"preset", "lens", "dist", "height", "tilt", "pan", "fill", "top_at", "fstop", "anchor", "start_cx", "start_cy"}`. **Always static.** |
| `seed` | `crc32(clip key)` | Seeds every random choice. |
| `options` | the template's | Per-template knobs (§5). Unknown keys are errors. |

### 2.3 The existing clip fields on a Blender shot

| Field | Meaning here |
|---|---|
| `clip` | The output key. Use a new key ending in `_bl` (`rx_<theory>_bl`): an AI clip's key (one in `CLIPS`) is an error, a key without `_bl` warns, and `--build` refuses to overwrite a clip that `clips.py add` filed from a generator (its `clips.json` entry has no `sidecar`) unless `--force`. `.gitignore` keeps `*_bl.mp4` drafts out of git. |
| `dur` | **Required.** The clip has `ceil((in + dur) * 30) + 1` frames (the extra one covers `render.py`'s clamp). Changing it re-renders. |
| `in` | Use 0. Anything else renders and wastes the first `in` seconds (a warning). |
| `out` | Must be absent. |
| `speed` | Must be 1.0. Slow motion is authored in the scene (`options.slowmo`, or the beats). |
| `kb` | Locked `(0.5, 0.5, 1.0)`: the camera lives in Blender. |
| `label` | `"REENACTMENT · AI"`, as on every reenactment (D4). Anything else is an error here and in `build_audio.py`. |
| `stamp` | Unchanged. Its width sets the **tag zone** every template stages around (§6). |
| `fallback` | Unchanged; plays until the MP4 exists. `--keyframe` writes frame 0 to `stills/<clip>_key.png`, so list `V("<clip>_key", (0.5, 0.5, 1.0), (0.5, 0.5, 1.0))` first. |

`build_audio.py` runs these checks (`blender_reenact.validate_shot`, no `bpy` needed) on every build, so a mistyped `blender` dict stops the build before anything is voiced. While the clip is missing it warns `render it with pipeline/blender_reenact.py <ep> --build`.

---

## 3. Timing

### 3.1 Build order (`make_episode.sh`)

```bash
"$PY" pipeline/build_audio.py "$EP"                                    # pass 1: voices; dur fixes the shot lengths
if [ "$("$PY" pipeline/blender_reenact.py "$EP" --has-shots)" = yes ]; then   # "yes" if a shot has "blender"
  QUALITY=${NM_RX_QUALITY:-draft}                                      # final under NM_FINAL=1
  rc=0
  "$PY" pipeline/blender_reenact.py "$EP" --build --quality "$QUALITY" [--require-models under NM_FINAL=1] \
      ${NM_BLENDER_FLAGS:-} || rc=$?
  if [ "$rc" = 2 ] || [ "$rc" = 3 ]; then                              # no Blender / over the time budget
    [ "${NM_FINAL:-}" = 1 ] && exit "$rc"
    echo "WARN blender_reenact.py exited $rc: the reenactments play their fallback stills"
  elif [ "$rc" != 0 ]; then exit "$rc"; fi
  "$PY" pipeline/build_audio.py "$EP"                                  # pass 2: records the clip (voices cached)
fi
"$PY" pipeline/script_md.py "$EP"; "$PY" pipeline/render.py "$EP"
"$PY" pipeline/deliver.py "$EP" [--allow-draft unless NM_FINAL=1]
```

An episode without a `"blender"` dict skips the whole block, so its build is the same as before. `--build` is "up to date" when a filed clip with the same content at that quality or better is already there, so this pass costs nothing on most builds. Because `dur` fixes the shot length and the voice cache fixes the word times, pass 2 writes the same times and the next run is a cache hit. On a CPU-only machine a draft estimate runs over the 30-minute budget, so the pass exits 3 with a warning and the fallback still plays: render drafts and finals on a GPU, or run `--build --yes` by hand.

### 3.2 Resolving a beat on `render.py`'s frame grid

1. Take the shot's words from `build/timeline.json` (absolute seconds), normalized: lowercase, outer punctuation and ellipses stripped (`"dared."` matches `dared`).
2. Pick the `nth` match, its `edge` (start for move/tip/flare, end for land) plus `offset`: absolute time `w`.
3. `render.py` shows clip frame `floor(30*in + fi - 30*S + 1e-6)` on global frame `fi`, where `S` is the shot's start. The first global frame at or after the word is `f_w = ceil(30*w - 1e-6)`, which shows clip frame `k`.
   - A **start beat** (`move`, each rock, `tip`) is stored as `k - 1`, the last still frame, so the first moving frame is on screen from the word's first frame.
   - An **event beat** (`land`, `flare`) is `k`.
4. **Beats are frames before they are hashed**, so a new take that leaves a beat on the same frame doesn't re-render.

(The first version rounded `30*t` and ignored the shot start's sub-frame phase: moves landed 0.5-2.5 frames late. The selftest now checks 400 random shot starts.)

### 3.3 Fallbacks and staleness

| Situation | Behaviour |
|---|---|
| No `timeline.json` | `*_at` seconds (with `S = 0`); without them a template default with `WARN timing is a guess`. An error at `final`. |
| The word isn't in the shot | With `*_at`: a warning and the seconds. Otherwise an error listing the shot's words and times. |
| Stale timeline (lines changed, or the shot length differs from `dur` by more than a frame) | As a missing word, "run build_audio.py first". |
| **Synthetic timeline** (`"synthetic": true`, estimated word times) | Source recorded as `synthetic`; a WARN for previews and drafts; **an error for a filed final** ("a published clip is timed to its voiced take: run build_audio.py"). |
| `move_on` and `move_at` differ by over 0.4 s | A drift warning; the word wins. |

### 3.4 Timing rules (checked before and after rendering)

Errors: `dur` missing; `speed` not 1.0; unknown template/subject/preset/option; a beat outside `[0.3, dur - 0.2]`; beats out of order (move < rocks < tip < land); Deb as a subject; an undesigned outfit; Lorraine facing the camera or showing her back.

Warnings:
- **Stillness first:** the move starts less than 1.0 s into the shot.
- Heist: the cut comes less than 0.5 s after the glide starts or after the last word.
- Action: the cut comes outside 0.3-1.0 s after the landing.
- **The punch word triggers the drop:** the tip or the fall starts more than 0.1 s from the trigger word's onset (`tip_on`, else `land_on`'s word).
- **The thud lands after the word:** less than 0.25 s between the land word's end and the landing.

---

## 4. Models

### 4.1 Layout and conventions

```
models/
  README.md        how to make and file a model (Higgsfield 3D or any modelling tool), and the models.json fields
  models.json      the registry, one entry per model, written by `model add` (committed; {} when empty)
  garrison.glb  lorraine.glb  deb.glb  basin.glb   (git-ignored; later lorraine_bumblebee.glb, ray.glb, dale.glb ...)
```

`models/README.md` is the reference for the conventions (one figurine per glTF 2.0 binary, +Y up and the character's front on +Z, scale and origin ignored, cast names only, `restyle`) and for `models.json`. Two notes beyond it:
- `models/` is the cast's 3D figurines; `assets/models/` is the Kokoro voice model. They never mix.
- `anchors` (optional, in normalized metres, base-centred, front −Y): `nose` puts the sweat bead on Garrison; `head` lets the prop-in-frame check work.

### 4.2 Making a GLB

**Higgsfield 3D** (`higgsfield-generate`, `multi_image_to_3d` with `--should_texture true`) from **one clean view**: the front view cropped from `stills/ref3d_<name>`, else the library still cropped to the character (Garrison: x 0.25-0.72, y 0.25-0.85, so the goose behind him doesn't come along; Lorraine: the beak-left three-quarter view, **never the back view**; Deb: the side view). 100k triangles or fewer. Then file it and check the sheet against the library still: **the library wins on identity** (Garrison's fists either side of the bottom of a full beard, thumbs up, brown paint chips on the cap; Deb's **two** rod legs; Lorraine's short orange-yellow beak and webbed feet).

**Other routes**: any image-to-3D tool, or modelling by hand in Blender (ideal for Mr. Basin's simple solids), with the same conventions and `--no-ai`. A hand-made model is `ai_generated: false`.

### 4.3 Filing: `model add`

```bash
.venv/bin/python pipeline/blender_reenact.py model add garrison ~/Downloads/garrison.glb \
       --source "Higgsfield 3D from ref3d_garrison front" --ai [--forward +z] [--yaw 0] [--height-m H] [--out-dir D]
.venv/bin/python pipeline/blender_reenact.py model list
```

`model add` **checks first and files after**: the GLB goes into a temporary models folder, a worker imports and normalizes it there, renders the front, three-quarter, side and back sheet frames, and reports height, footprint, triangles and anything stripped. Only on success does it replace `models/<name>.glb` and its `models.json` entry (both atomically). A broken file fails with the importer's own message first (for example `the glTF importer rejected garrison.glb: struct.error: ...`) and **leaves a good model filed**. Without Blender it files unchecked, with a warning.

Edit a model's `forward`, `yaw` or `height` by re-running `model add`. Every render measures each GLB's bytes; if they don't match `models.json` it stops: `models/garrison.glb changed since it was filed: rerun model add`.

```bash
.venv/bin/python pipeline/blender_reenact.py --showcase garrison --mode sheet --preview      # 4 views + the library still
.venv/bin/python pipeline/blender_reenact.py --showcase lorraine --mode turntable            # 4 s orbit
```

The sheet (in the show's `build/models/`, git-ignored) is a review file. Its back view never goes into an episode or a generator.

### 4.4 Proxies: the pipeline works before any model exists

`rx3d/proxies.py` builds Garrison, Lorraine, Deb and Mr. Basin from primitives at the bible's height, front −Y, plastic look. Everything is named `*_PROXY`, carries a faint 45° stripe, and the sidecar says `proxy: true`: `deliver.py` refuses it and `--require-models` (set by `make_episode.sh` when `NM_FINAL=1`) makes a missing model an error.

| Proxy | Reads as (checked with `--showcase <name> --mode sheet` beside the library still) |
|---|---|
| Garrison | Red cap 40% of his height with a few irregular brown chips at the brim and tip; bead eyes (r 0.02 H) under the brim, a catchlight from a 3 W eye light at the lens; a full white beard from under the moustache to the belly, leaning back so it never covers the nose; fists at its lower corners, each thumb on the fist's inner top edge tilted 15° outward, with three curled-finger ridges (a raised digit never reads as a middle finger); slate trousers and dark boots showing under the tunic. |
| Lorraine | White glaze; plump egg body; an S-curved neck (base r 0.085 H); a round head (r 0.086 H); a chunky #F7A600 beak (0.13 H) and matching webbed feet; three molded feather ridges per wing; an upturned tail. |
| Deb | Two galvanized rod legs, coral body, S-neck, down-bent two-tone beak, in profile. |
| Mr. Basin | Stepped base, fluted column, scalloped bowl, water disc, a tiny briefcase. |
| Chime (set prop) | Wooden disc, five brushed tubes, striker, sail; its parts swing as rigid pieces. |

---

## 5. Templates

### 5.1 Rules every template keeps (the worker checks them; a failure is a STAGING error and nothing renders)

- **Rigid only.** A subject's root gets location keys and, for a rock or a tip, X/Y rotation about a contact point. Its yaw lives on a static parent and is never keyed. No mesh deforms (hashed every frame).
- **Locked camera.** Never keyed (showcase excepted).
- **Stillness first.** Nothing moves before the move beat.
- **Nothing touches the subject.** No beam comes within a quarter inch of its surface on any shown frame (tested against the mesh surface with a BVH, not just its vertices).
- **Opaque glare sources.** Nothing that feeds the glare (an emitter or an AOV writer) is `BLENDED`: Eevee writes no render passes for blended materials, so a flare would vanish from an Eevee final. A sprite that must disappear is keyed to scale 0.
- **Rough dark surfaces.** Doors and windows (`look.dark`) have roughness 0.45 or more and no coat. A glossy black door mirrored the key light as "a light under the door".
- **Determinism.** Randomness only from the seeded `ctx.rng`; one motion sample per frame; no timestamps (render metadata stamps are off).
- **No text in the picture.** The label and stamp are burned in by `render.py`.
- **The top left stays clear**, and **the first frame matches the cut-back** (§6).

### 5.2 Shared look (`rx3d/look.py`): glossy, saturated, cheesy TV

- **Plastic**: Principled, saturated base, roughness 0.25-0.35, coat 1.0 (roughness 0.03). Metals: metallic 1.0, roughness 0.15-0.3.
- **Ground seen from grass height** (lawn, soil): roughness 0.95 and specular 0.05. At a grazing angle a rough dielectric still mirrors the sky and reads grey instead of green.
- **AgX - Punchy, calibrated.** Measured in Blender 5.0.1, AgX desaturates bright emitters toward white: `#FF1A1A` reads (212,54,34) at strength 1.5 but salmon-pink (255,166,157) at 9. So "saturated" emitters keep their body at strength 0.8-2.0 and only a thin core goes hot:
  - **lasers** (`look.beam`): one cylinder, strength `mix(1.4, 6.0, core^4)` where core = 1 − Layer Weight Facing, so the sheath stays red and only the core blooms;
  - **fire** (`look.fire`): heat from 4D noise through stops `#2A0A00`@0 (smoke), `#C22A00`@1.0, `#FF6A00`@1.8, `#FFB000`@3.5, `#FFF1C0`@8, multiplied by core^1.5 so the rim stays dark smoke;
  - sparks at 5, embers at 3.
  - Standard keeps the red but clips the white glaze and the beard, so the view transform stays AgX. The selftest renders a swatch and fails if a laser sheath or the fire's mid-tones drop under 0.6 sRGB saturation.
- **Glare** comes from the compositor, so Eevee and Cycles match. It is fed from the Emission pass (never the beauty pass, which streaked the clear-coat highlights): Streaks (2, at 0°, threshold 1.2), Bloom (threshold 1.0, strength 0.7: only hot cores bloom). The `glint` AOV feeds Ghosts plus a long anamorphic Streaks, so a flare reads at least 40% of the frame wide.
- **Light linking.** A subject's key, rims, top and kicker shade only the subject (`look.link`), so the set stays dark and the ornament carries the frame.
- **Haze**: final, a Principled Volume whose density drifts with 4D noise (0.016 × `haze` for the heist, 0.008 × `haze` for the action); preview and draft, the compositor's mist pass × drifting noise. The drift runs 3× faster than v1, so a long hold before the move reads as video, not a still. Only the god-ray scatters in the volume: a 700 W fire backlight scattering in it fogged the whole action frame orange.
- **Palettes per template** (`look.PALETTES`, inherited by later episodes):
  - **heist, red/violet**: sky `#3A2C8C`→`#241A5E`, siding `#5A6074`, lawn `#3BD45A`, haze `#D6D2E6`, moon `#E8ECFF` at 1.6, set flood `#6E5BD6` 110 W, pink kicker `#FF6F9A`;
  - **action, teal/orange (the Director's Cut)**: sky `#1F5A7A`→`#0E2A47`, siding `#4E5868`, a dark fascia `#262B36` behind her head, set flood `#7FB8D8` 70 W, fire backlight `#FF6A00`, cyan fill-rim `#2DE2FF`. The fire is the only warm thing in the frame.

### 5.3 `heist`: Garrison in the laser grid, cut mid-glide

| | |
|---|---|
| **Set** | Over-green lawn from his boots to the lens; a dark-soil echinacea bed behind him; the house flat with dark windows; violet sky; the moon. **Exactly one gnome** (checked). |
| **Camera `beside_deb`** | Grass height (0.08 m), 35 mm, locked. He fills 0.68 of the frame height with his cap tip a quarter of the way down, and his frame-0 box is centred at x 0.51: the hard cut to `g_deny` (kb `(0.47, 0.49, 1.37)`) lands within 0.006 in x and 6% in height. |
| **Laser grid** | `beams` (7) emissive cylinders, 2.5 mm, hum ±12% at 2 Hz. The **lowest beam descends toward his travel** (about 20°): 1.5 in over his cap tip at the start, 0.30 in at the cut, so the cut lands just before contact. Two **foreground beams** 0.3 m in front of him (one at boot height, one across the upper right) sandwich him in the grid. Mid and back beams are re-drawn from the seed until none crosses the tag zone. |
| **Motion** | Dead still until `move`, then an ease-in glide along the camera's −X (`accel_s`, then constant speed), no ease-out: the cut lands mid-glide at `travel` (0.25) of the frame width. Upright, never rotating. |
| **Flare** | On `flare_on` (peak 2 frames after the word), a glint sprite (a horizontal sliver and a dot, opaque, hidden by scale outside the spike) where the low beam crosses a back beam right over his cap tip: Ghosts + a long anamorphic streak. A vertical bar in the sprite streaked sideways into a white box at final quality, so the sprite has none. |
| **Lights** | Warm key 150 W, magenta/cyan gel rims 220 W (size 0.12) raking the cap edge and the bell, top spot 250 W at 22°, fill 8 W, pink kicker 40 W from frame right (Deb), a 3 W eye light at the lens for catchlights; all subject lights linked to him. Set flood 110 W, god-ray 450 W. |
| **Options** | `path` (left), `toward` (0), `travel` (0.25), `accel_s` (0.35), `beams` (7), `beam_hex`, `clearance_in` (1.5), `clearance_end_in` (0.30), `front_beams` (true), `glint` (true), `glint_strength` (150), `haze` (0.5), `slowmo` (0.5), `fill` (0.68), `top_at` (0.25), `fstop` (2.8), `start_cx` (0.51), `kicker` (true), `sweat_mm` (6). |

**Move A/B.** Variant A moves on "Then" with a 0.35 s ease-in (15% of the frame width a second for 1.8 s: the slide illustrates the line). Variant B holds through "Then he made his" and zips on "move" (0.12 s ease-in, 31% a second for 0.82 s: the slide punctuates the line, and the flare lands with it). **The episode uses B**; A is one line away (`"move_on": "Then", "move_at": 2.26`, `"accel_s": 0.35`). The prototype's A/B sheets are in its `previews/` (not committed).

### 5.4 `action`: Lorraine off the porch step, an action-movie poster

| | |
|---|---|
| **Composition** | An action poster: she faces left, **walking away from the explosion** behind her. The fireball sits upper right **below the tag band**, its lower part hidden by a low roofline (38% down the frame); her white head stands against the dark fascia and siding. |
| **Set** | Three concrete steps (rise 0.18 m, run 0.28 m) to the porch floor; the house flat 4.8 m back (so a full 2.05 m door fits under that roofline); the black door and dark windows; a brass lantern; the chime under the soffit over the door, swaying ±15° (tubes ±8°) with its own small spot so it reads against the dark door. |
| **Fireball** | **One shape**: an icosphere (subdivision 5) with an animated Clouds displacement (0.3 r) and the calibrated fire material, on a plane 4 m behind the wall, centred at screen (0.82, 0.31). Its radius grows from 0.10 to 0.20 of the frame width by the land beat. **Ignites with a flash** on frames 0-4 (fire light ×3, decaying over 0.3 s, in sync with `reenact_hit`), **billows the whole clip** (noise ×4 faster, rolling 0.3→1.5 rad, the displacement field boiling upward), and **booms again on the landing** (+25% over 6 frames, emission ×1.6, backlight ×2). Its growth is capped so its silhouette never reaches the tag zone (+20 px). 60 sparks at strength 5. |
| **Embers** | 24 small embers (4-6 mm, strength 3) drifting slowly upward (0.05-0.1 m/s) in front of her and between her and the wall, never within 0.35 m of her path: the visible "super slow motion". |
| **Subject** | `lorraine`, BARE by default, three-quarter with the beak to frame left: her front makes `facing_deg` (50°) with the image plane (15-60 allowed; anything else is a STAGING error: frame 418's secret). |
| **Camera `hero_low`** | 0.30 m high on the front walk, 35 mm, locked. Solved so she fills `fill` (0.50), then **anchored**: trucked so her frame-0 box is centred at x 0.59 and tilted so it is centred at y 0.55, where the `l_deny` still shows the real goose. It then dollies back (level) only as far as needed to keep the whole move inside x 0.04-0.96. |
| **Motion (rigid, yaw constant)** | 1. **Rock-waddles** on the rock words (`move_on` list): ±`roll_deg` (10°) about the outer edge of one foot, each advancing `step_len` (2.5 cm), holding between rocks. 2. **Tip** on `tip_on`: `tip_s` (0.20 s) pitching 12° about the front edge of her feet, the farthest-back front corner on the lip. 3. **Dive** to `land`: z on a parabola from rest (ballistic, slow-motion gravity), pitch held until the last 4 frames, level on landing. The horizontal motion is the gentlest ease (1.0 is constant speed) that keeps every footprint corner clear of the top tread; at a 12° pitch a constant speed sank the back of a three-quarter footprint 3-6 cm into the tread. 4. **Land** on `land`: a 2-frame 5 mm settle, no bounce. |
| **Dust** | 40 low puffs (r 1.2-2 cm, `#8E877D`, peak alpha 0.25 × core², soft-edged) running along the tread at 0.12-0.30 m/s, rising 3 cm at most, spawned 3 cm behind her toe line so her orange feet stay visible on the last frame. |
| **Lights** | Soft warm key 70 W from her beak side (its reflection stays off the door), a 150 W 25° spot where she lands, cyan fill-rim 150 W from front left, fire backlight 700 W `#FF6A00` (flickering ±15% with the fireball, ×3 on ignition, ×2 on the boom), set flood 70 W, top spot, god-ray (the only light that scatters in the haze). |
| **Options** | `steps_down` (1), `rocks` ("auto"), `roll_deg` (10), `pitch_deg` (12), `step_len` (0.025), `tip_s` (0.20), `rock_max_s` (0.5), `slowmo` (0.29; used only without `tip_on`), `land_depth` (0.06, raised by the solver), `sparks` (60), `embers` (24), `dust` (40), `chime` (true), `outfit`, `fill` (0.50), `fstop` (2.8), `haze` (0.5), `facing_deg` (50), `allow_facing`, `start_cx` (0.59), `start_cy` (0.55), `fire_at` ([0.82, 0.31]), `fire_r` ([0.10, 0.20]), `fire_burst` (1.25). |

### 5.5 `showcase` (CLI only)

`--showcase <model> --mode sheet|turntable|pushin` on the `SHEET_3D` grey ground. Output in `build/models/` (or `--out-dir`); never filed as a clip.

---

## 6. Machine checks (so a new episode warns instead of repeating a mistake)

The worker writes `motion.json` for every clip frame: each mover's matrix, the screen box **and convex hull** of every tracked thing (subject, fireball, each beam), headings, mesh hashes, beam clearances, props' head anchors on screen, and the subject's feet visibility on the last shown frame. The driver checks it in 1080×1920 px. These are WARNs (a staging error is an ERROR) and go into the sidecar's `checks`. An up-to-date run re-runs them on the cached `motion.json`.

| Check | Rule |
|---|---|
| **Tag zone** | No tracked hull the template names (subject, beams, fireball) enters x 44 to 64 + tag width + 20, y 170-340 on any shown frame. Hulls, not boxes: a round fireball whose box touches the zone's corner is clear. |
| **Cut-back match** | The reenactment's **first** frame matches the still the hard cut lands on. The next shot's first view's subject box (`stills/subject_boxes.json`, derived stills use their source's) is mapped through its starting `kb` exactly as `render.py` crops it. WARN when the x-centres differ by more than 0.06 of the frame or the heights by more than 12%, with the kb that would match (`suggest_kb`: zoom 1.0 or more, the crop inside the still). |
| **Effect coverage** | The fireball covers at least 6% of the frame by the land beat (or it won't read on a phone). |
| **Prop head in frame** | A prop with a `head` anchor whose head projects off the frame warns: only an unreadable body would show. |
| **Feet visible** | On the last shown frame, at most 50% of the subject's base may be hidden by effects (dust, embers ...); ray-tested from the camera. |
| **Timing** | §3.4: the drop starts within 0.1 s of its word; the landing comes 0.25 s or more after the word ends. |
| Button column, edges, captions | The subject's centre stays at x 930 or less, inside the inner 80%, with 30% or less of its box in the caption band. |
| Stillness, facing | Camera and props static; yaw constant; Lorraine at 15-60° to the image plane, beak to frame left. |
| Luma | Mid-frame mean 100-120 (WARN under 60), with subject and backdrop luma reported separately. Measured in the worker with `bpy` + numpy. |

---

## 7. Rendering

### 7.1 Commands

```
.venv/bin/python pipeline/blender_reenact.py <episode_dir> [--shot ID] MODE [options]
  MODE: --preview | --build [--quality draft|final] | --quality draft|final | --still K[,K] [--quality Q]
        | --keyframe | --dry-run | (none: print the plan)
  --frames every:N | a-b | a,b,c     preview/still frame choice (filed clips need every frame)
  --scale PCT                        percent of 1080x1920; sizes must be even (yuv420p): 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 100
  --engine auto|eevee|cycles         --device auto|cpu|gpu      --samples N
  --force / --rerender               ignore the cache    --yes  allow an estimate over 30 min
  --require-models                   a missing GLB is an error (make_episode.sh adds it under NM_FINAL=1)
  --save-blend                       keep build/blender/<clip>/<key>/scene.blend (git-ignored, like all of build/)
  --no-mux                           a silent preview.mp4
  --blender PATH                     a blender binary or a python with bpy (also $NM_BLENDER)
  --reprobe                          probe Blender again (after a driver or Blender upgrade)
.venv/bin/python pipeline/blender_reenact.py <episode_dir> --has-shots          # prints yes or no
.venv/bin/python pipeline/blender_reenact.py --showcase <model> [--mode sheet|turntable|pushin] [--preview] [--out-dir D]
.venv/bin/python pipeline/blender_reenact.py model add|list ...
.venv/bin/python pipeline/blender_reenact.py --selftest [--allow-skip]
blender -b --factory-startup --python-exit-code 1 -P pipeline/blender_reenact.py -- <episode_dir> [flags]
```

- Where Blender is looked for: `--blender`, then `$NM_BLENDER` (either one, when set, must be an executable: no silent fall-through), then `.venv-bpy/` in the show folder (`./setup.sh --blender`), the running Python if it has `bpy`, `blender` on `PATH`, and the platform's default app path.
- `--preview` writes `build/blender/<clip>/preview.mp4` (each rendered frame held, so timing reads true, with the shot's slice of `build/soundtrack.wav` when it exists), `sheet.png` (frame 0, each beat, move + 0.5 s, the cut; tag zone and button column drawn) and `contact.png` (every rendered frame).
- `--dry-run` prints each beat (word → shot seconds → clip frame), the frame count, engine and device, the cache status and a cost estimate.
- `blender -b -P` runs driver and worker in Blender's own Python. `--python-exit-code 1` matters (without it Blender exits 0 on an error). There is no PIL or imageio-ffmpeg there, so no sheets, ffmpeg comes from `$NM_FFMPEG` or `PATH`, and the tag zone falls back to measured font metrics (a different content key: file finals from the show's `.venv`, as `make_episode.sh` does).

### 7.2 Quality

| Quality | Resolution | Cycles | Eevee | Haze | Use |
|---|---|---|---|---|---|
| `preview` | 25%, 270×480 | 12 spp + OIDN | 16 TAA | mist | look and timing; never filed |
| `draft` | 50%, 540×960 | 24 spp + OIDN | 32 TAA | mist | end-to-end builds; filed, flagged, blocked from delivery |
| `final` | 1080×1920 | 128 spp + denoise (OptiX on NVIDIA, else OIDN) | 64 TAA, ray tracing | volume | publishing |

### 7.3 Engines and devices

- `--engine auto`: Eevee if the probe says it works on a real GPU, else Cycles (with a note).
- `--device auto`: GPU if the probe found Cycles devices (OptiX > CUDA > HIP > Metal > oneAPI), else CPU. `--device gpu` with none is exit 2. `--engine eevee --device cpu` is exit 2 (Eevee is GPU only).
- **The worker proves the GPU is used.** It selects the device type, refreshes the device list, enables only that type and asserts `has_active_device()`. With no device of that type it fails (`--device gpu: the worker found no OPTIX device (devices seen: ...)`) instead of quietly rendering on the CPU. The device actually used is in `result.json` and the sidecar.
- **The probe** (`--worker-probe` plus a throwaway Eevee render in its own process, because a missing EGL aborts the whole process) is cached in `assets/blender_probe.json`, **one entry per Blender path**. It is keyed by what that path runs: for the pip route, `bpy`'s own module file (the venv's `python` is a symlink whose modification time never changes when `bpy` is upgraded); for the app, the binary. Every worker job also reports its Blender version and build hash; if they differ from the probe, the cache entry is dropped and the run stops with "run again". A software rasterizer (llvmpipe, softpipe, SwiftShader, Microsoft Basic Render, or a 64×64 Eevee frame over 2.5 s) counts as **no Eevee**.
- A watchdog kills a worker that runs over max(120 s, 3 × the estimate + 90 s), so a hung GPU driver can't hang `make_episode`.

### 7.4 Rendering finals on a GPU machine

1. **Install Blender**: the Blender 5.0 app (recommended for GPUs; `export NM_BLENDER=/path/to/blender`), or `./setup.sh --blender` (`.venv-bpy` with `pip install bpy==5.0.1` on Python 3.11; Linux/Windows with CUDA/OptiX/HIP drivers; on Windows the tool looks for `.venv-bpy\Scripts\python.exe`). NVIDIA: a driver recent enough for OptiX in Blender 5.0; AMD: HIP; Apple Silicon: Metal.
2. **Check the machine**: `.venv/bin/python pipeline/blender_reenact.py --selftest` (all green; the Eevee AOV check runs only where Eevee works) and `.venv/bin/python pipeline/blender_reenact.py episodes/<ep> --dry-run --reprobe`. The plan line must say `eevee gpu` or `cycles gpu OPTIX` (or CUDA, HIP, METAL). If it says `cycles cpu`, fix the drivers before going on: a final on 4 CPU cores takes many hours a clip (about 113 hours for the heist's 123 frames by the driver's estimate, §12.2).
3. **Voice the episode for real** (`build_audio.py` with the v4 or human takes). A synthetic timeline can't make a final.
4. **File the models** (`model add`, §4.3, `models/README.md`), so the run has no PROXY warning.
5. **Render**: `NM_FINAL=1 ./make_episode.sh episodes/<ep>` (final quality, `--require-models`, and `deliver.py` without `--allow-draft`), or by hand `.venv/bin/python pipeline/blender_reenact.py episodes/<ep> --quality final --require-models` (add `--engine cycles --device gpu` to force Cycles on the GPU) and then the usual build. Eevee is seconds per frame, Cycles GPU tens of seconds.
6. **Check** `clips/<clip>.blender.json`: `quality: final`, `proxy: false`, `device_used` names your GPU, `checks` without failures, `timing.source` not `synthetic`. `review.py` warns about a proxy or draft clip; `deliver.py` refuses one.
7. **Commit** the clip on purpose (drafts are git-ignored): `git add -f episodes/<ep>/clips/<clip>.mp4 episodes/<ep>/clips/<clip>.blender.json` with `clips/clips.json`. On any other machine (CI, a laptop), `--build` now reports the clip **up to date**: the content key doesn't include the engine, device or Blender build.

### 7.5 Determinism

- Everything that shapes the picture is in `job.json` and the picture code. Seeds come from the clip key; motion is sampled per frame; the worker starts from factory settings; the Cycles seed and thread count are fixed; PNG metadata stamps are off; the lossless intermediate is written bitexact.
- **Guaranteed**: the same job gives byte-identical `motion.json` in any process (tested with two worker processes). The same frame from two processes on one machine matches within 1/255 (Cycles' threaded sampling can flip a last bit). Across machines, compare motion data exactly and pixels with a tolerance. The filed MP4 is `clips.py add`'s x264 encode, so the cache trusts the sidecar's `mp4_sha1` for the file on this machine, never a re-encode elsewhere.

### 7.6 Caching

- **Content key** (SHA-256 of canonical JSON): template and version; each asset's identity (a GLB: name, kind, **measured** sha1, height, forward, yaw, restyle, anchors, outfit; a proxy: its name and outfit); beat **frames**; `dur`, `in`, fps; camera; options; seed; the tag zone; the picture code (`rx3d/worker, templates, look, proxies, geo` plus the encoder settings). Editing a test, a message or the driver's CLI doesn't re-render a final.
- **Render key**: quality, engine, device, samples, scale, denoise, haze, bounces, glare, Blender version.
- Frame folders are `build/blender/<clip>/<sha256(content+render)[:12]>/`, so a preview, a draft and a final never mix, and an interrupted render resumes.
- **Up to date** (`--build`, `--quality`): the MP4's sha1 matches its sidecar, the content key matches, and the filed quality is at least the one asked (final > draft > preview). `--force`/`--rerender` overrides.

### 7.7 Filing goes through `clips.py add`

A filed clip is filed exactly like a generated one. The rendered PNG frames are packed into a **lossless intermediate** (`build/blender/<clip>/<key>/frames.mkv`, PNG in Matroska, deleted after filing), and `clips.add()` makes the mezzanine from it, with its usual checks (1-10 s, black ends, a dark middle frame, the low-width warning, which here advises `--quality final`) and its own `clips.json` writer. The entry carries the Blender provenance as extra fields (below). `add()` encodes to a temp file and swaps the MP4 in only once it checks out; the sidecar is then written through a temp file. An interrupted run leaves either the old pair, or a new MP4 whose sha1 no longer matches the old sidecar, which the next `--build` renders again. `clips.json` (`clips.record_entry()`), `models.json` and the probe cache all go through a temp file.

### 7.8 Errors and exit codes

| Situation | Exit | Message (abridged) |
|---|---|---|
| No Blender found | 2 | the install hint (pip `bpy==5.0.1` on Python 3.11, or the app + `NM_BLENDER`, or `blender -b -P`) |
| `--blender`/`$NM_BLENDER` not an executable | 2 | `--blender /opt/blender-4.1/blender: not an executable (expected a blender binary or a python with bpy)`; no fall-through |
| Blender older than 5.0 | 2 | `needs Blender 5.0+ (found 4.1.1)` |
| Blender changed since the probe | 2 | `... now runs Blender 5.0.2 ...: the cache is refreshed; run again` |
| `--engine eevee` without a GPU / with `--device cpu` | 2 | `Eevee needs a GPU ...` / `--engine eevee runs on the GPU only ...` |
| `--device gpu` with no device (driver side or in the worker) | 2 / 1 | lists what was found |
| No ffmpeg | 2 | `pip install imageio-ffmpeg ... or set NM_FFMPEG` |
| Estimate over 30 min without `--yes` | 3 | the estimate and the faster flags |
| Bad episode fields, bad `--scale`/`--frames`/`--shot` | 1 | names the field and the accepted values (e.g. `--scale 33 gives 356x633; yuv420p needs even sizes: use 30, 35, ...`) |
| Word not found / stale / synthetic timeline at final | 1 | lists the shot's words / `run build_audio.py` |
| GLB changed since filing | 1 | `rerun model add` |
| A staging rule broken | 1 | `STAGING: yaw changed: garrison never turns` (and the other §5.1 rules), at the head of the error |
| The worker crashed or timed out | 1 | the job's own errors first, then the last 40 lines of `worker.log` |
| A clip filed from a generator holds the key | 1 | `clips/<key>.mp4 was filed by clips.py add from <generator> (clips.json), not rendered here: use a new key such as <key>_bl, or --force`; an AI clip's key in `CLIPS` fails validation first |

---

## 8. Outputs

- `clips/<clip>.mp4`: `clips.py add`'s mezzanine: H.264, yuv420p, CRF 17, constant 30 fps, `+faststart`, no audio. 1080×1920 for `final`, 540×960 for `draft`.
- `clips/<clip>.blender.json`, the sidecar (deterministic, no timestamps): `generator`, `blender_version` and `blender_hash` **as reported by the worker**, `device_used` (engine, device, GPU type, device names), `script_sha1`, `picture_sha1`, `ffmpeg` (first line of `ffmpeg -version`), `encoder`, `git` (commit, and whether the tool or the models have uncommitted edits, checked before the clip is written), `episode`, `shot`, `dur`, `in`, `template`, `template_version`, `seed`, `subject` and `props` (the full asset identities with measured sha1s), `engine`, `device`, `quality`, `samples`, `render` (every render setting), `w`, `h`, `fps`, `frames`, `timing` (source, timeline sha1, synthetic, shot start, each beat), `camera`, `camera_solved`, `options`, `zones`, `checks`, `ai_generated`, `proxy`, `content_key`, `render_key`, `cache_key`, `mp4_sha1`.
- The `clips/clips.json` entry, written by `clips.add()`: its usual fields (`file`, `source`, `source_sha1`, `sha1`, `generator` such as "Blender 5.0.1, blender_reenact action v2", `prompt` (an auto-written description of the scene, which no generator reads, so the prompt lint skips it), `references` (the GLBs, or `proxy:<name>`), `date`, `w`, `h`, `seconds`, `ai_generated`) plus `quality`, `proxy`, `render` (engine, device, samples) and `sidecar`. The `sidecar` field is what marks a clip as a Blender render.

Where the rest of the pipeline reads it (`render.py` doesn't change):
- `build_audio.py` checks the `blender` fields on every build (§2.3) and, for a filed Blender clip, writes `"clip_blender": {"quality", "proxy", "sidecar"}` into the shot's `timeline.json` entry, with a warning for a proxy or draft clip.
- `deliver.py` refuses a timeline whose `clip_blender` says `proxy: true` or a quality other than `final` (`--allow-draft` for a test upload; `make_episode.sh` passes it unless `NM_FINAL=1`). `review.py` warns about both.
- `script_md.py` lists the clip with its generator and description under "Reenactment clips", or "rendered by pipeline/blender_reenact.py, not filed yet".
- `make_episode.sh` runs the pass of §3.1. `.gitignore` covers `.venv-bpy/`, the show's `build/` (model sheets), `*.blend`, `models/*.glb` and `episodes/*/clips/*_bl.mp4` with their sidecars.

---

## 9. Tests: `blender_reenact.py --selftest`

```bash
.venv/bin/python pipeline/blender_reenact.py --selftest                # both parts; exit 4 if part B can't run
.venv/bin/python pipeline/blender_reenact.py --selftest --allow-skip   # part B skipped cleanly without Blender
.venv/bin/python pipeline/selftest.py                                  # runs it with --allow-skip, plus the
                                                                       # pipeline-side checks below
```

**A. Pure Python, always (under a second):** word resolution; **`render.py`'s frame grid** (including a heist shot at the remake's start, 10.734 s, and 400 random shot starts); content and render keys (the same frame, an option, swapping the subject or a prop, a GLB's `forward`, new GLB bytes, a GLB changed behind `models.json`'s back; a preview and a final share content; engine and device don't change it); the up-to-date rules; validation (`dur`, `speed`, template, options, Deb, outfit, showcase, preset, the label (only `REENACTMENT · AI`), an AI clip's key, a key without `_bl`, beats on the wrong template, rock lists); the synthetic-timeline gate; Blender discovery errors (`NM_BLENDER` and `--blender` pointing nowhere: exit 2 with no fall-through; no Blender at all: the install hint); engine resolution with fake probes; `--scale` and `--frames` validation; a mistyped `--shot`; the cut-back mapping (`l_deny` and `g_deny` numbers) and its suggested kb; polygon clipping; the timing check.

**B. Rendering (about 70 s here; fails without Blender unless `--allow-skip`):** one worker for heist, action and a showcase cell per proxy (108×192, 4 spp). It checks:
- frame statistics from the worker (no PIL);
- stillness to the frame and motion after it;
- a locked camera, constant yaw, no mesh deformation, the cast count;
- the beam clearance (never under a quarter inch, and closing in);
- tag-zone hulls;
- the action's step drop, facing, swaying chime, fireball and feet measurements, two rocks and the tip on its word;
- proxy heights;
- determinism across two worker processes;
- timing without a timeline;
- the real `--build` path through `clips.py add`: a key filed from a generator is refused before anything renders; then a 31-frame draft (1.03 s, `add()`'s minimum is 1 s) at 30 fps yuv420p, the sidecar fields and its `mp4_sha1`, the `clips.json` entry (`add()`'s fields plus `quality`, `proxy`, `sidecar`), no temp file or intermediate left, a second `--build` up to date in about 0.1 s, a draft not counting as a final, no mode → plan only;
- tripwires (a keyed yaw, a beam through the cap, a `BLENDED` emitter);
- the GPU check (a `gpu` job with no OptiX device fails in the worker);
- the emitter swatch (saturation ≥ 0.6);
- `model add` (a GLB from another tool normalized; a broken GLB fails with the importer's message and leaves the good model filed; `dale` works);
- nothing left in the show's `build/models`.

On a GPU machine it also builds the heist on Eevee with the opaque glint.

**`pipeline/selftest.py`** adds the pipeline side on a throwaway episode with a Blender shot: `--has-shots`, a bad `blender` dict stopping `build_audio.py`, an AI clip's key refused, the missing-clip warning naming `blender_reenact.py --build`, a Blender clip filed through `clips.add()` recorded as `clip_blender` in the timeline, `review.py` warning and `deliver.py` refusing a proxy draft. Then it runs `blender_reenact.py --selftest --allow-skip` and prints whether the rendering half ran.

---

## 10. Rules learned (general: they hold for any reenactment, generated or rendered)

1. **The cut-back matches the reenactment's FIRST frame.** The real ornament on the hard cut sits where, and as big as, the reenactment showed it at the start: x-centre within 0.06 of the frame, height within 12%. Otherwise the cut reads as a punch-in, not "it never moved". Frame the start pose, not the whole move. (Checked by `blender_reenact.py`; the produce-episode skill's cut-back check.)
2. **Keep the top left clear, effects included.** No subject, beam or effect (fireball, flare) enters the AI tag's box plus 20 px on any frame; a background effect sits **below the tag band** as well as right of centre. (`SERIES.md` "Keep the top left clear".)
3. **The punch word triggers the motion.** The decisive movement (the tip, the drop, the zip) starts within 0.1 s of its word; the landing or impact lands in the silence after the word (0.25 s or more). (`SERIES.md` "Stillness first, then the move, on the word".)
4. **An effect has to read on a phone.** A hero effect (an explosion) is one shape with a hot core and a dark edge, covers at least 6% of the frame, keeps moving the whole clip, and peaks again on the beat.
5. **Saturated emitters stay saturated.** Under AgX, keep a coloured light source's body at strength 0.8-2.0 and let only a thin core go hot. Lasers and fire are calibrated against a rendered swatch, not by eye.
6. **A prop whose head can't be in frame is not in the shot.** Make the lens its point of view and light the subject as if it were there.
7. **Nothing hides the subject's feet at the cut.** Dust, smoke or debris stays low, soft-edged and behind the toe line on the frame the cut leaves in memory.
8. **Dark surfaces are rough.** Doors and windows at night are rough and uncoated, so no light's reflection reads as a light inside the house.
9. **Light the subject, not the set.** Link the subject's key, rims and kicker to it, so the ornament stays the brightest thing in the frame (subject about 140 luma, backdrop 60-80).
10. Engineering lessons, for any pipeline that drives Blender:
    - probe Eevee in a subprocess (a missing EGL aborts the process);
    - `--python-exit-code 1`;
    - feed glare from emission, not the beauty pass;
    - never make a glare source `BLENDED`;
    - map beats onto the player's own frame grid;
    - key caches by content and by render separately;
    - hash the real asset bytes;
    - a tilted camera dollies back level.

Where each rule lives now: rules 1-3 and 6 are machine checks in `blender_reenact.py` (§6: the cut-back match with its suggested kb, the tag-zone hulls, the timing check, the prop head in frame); 4, 5, 7, 8 and 9 are built into `rx3d/` (`templates.py`, `look.py`) and checked by the selftest; the lessons in 10 are in the code and the selftest. `SERIES.md` already carries the bible's side of 2 and 3 ("Keep the top left clear", "Stillness first, then the move, on the word"); rules 1, 6, 7, 8 and 9 are not in `SERIES.md` yet.

Where each piece lives:

| Piece | File |
|---|---|
| Fireball, dust, embers, chime, action lights and camera anchor, dive solver, rocks/tip beats | `pipeline/rx3d/templates.py` (`action`) |
| Lasers, front beams, Deb out, kicker, eye light, flare beat, heist lights and lawn | `pipeline/rx3d/templates.py` (`heist`) |
| Palettes, calibrated `beam`/`fire`, `dust`, `dark`, light linking, compositor thresholds, GPU device check, stamps off | `pipeline/rx3d/look.py` |
| Garrison and Lorraine proxies, Dale's height, importer errors | `pipeline/rx3d/proxies.py` |
| Hulls, BVH beam clearance, feet visibility, prop anchors, material rules, frame stats, Blender version per job, Eevee software-GL probe, emitter swatch, level dolly + anchoring | `pipeline/rx3d/worker.py` |
| Keys, `--build`, beat grid, probe cache, discovery, `model add`, watchdog, checks (tag hull, cut-back + suggested kb, coverage, feet, timing), `--scale`/`--frames`, synthetic gate, provenance, filing through `clips.add()` | `pipeline/blender_reenact.py` |
| `add()`'s keyword options for a rendered clip, `record_entry()`, `clip_entry()` | `pipeline/clips.py` |
| The `blender` fields checked on every build, `clip_blender` in the timeline | `pipeline/build_audio.py` |
| Refusing a proxy or draft clip / warning about one | `pipeline/deliver.py`, `pipeline/review.py` |
| The build pass | `make_episode.sh` (and `setup.sh --blender`) |
| Subject boxes for the cut-back check | `stills/subject_boxes.json` |
| Models and their registry | `models/README.md`, `models/models.json` |
| Tests | `pipeline/rx3d/selftest.py`, `pipeline/selftest.py` |
| Episode data (beats, camera, options, the `_bl` keys) | `episodes/ep01r_three_feet_reenacted/episode.py` |

---

## 11. Open decisions

1. **The cut-back framing for the Blender action.** `l_deny` keeps the AI keyframe's framing `(0.52, 0.53, 1.35)` so the fallback build doesn't change. With `rx_action_goose_bl` playing, the check warns (the reenactment shows her about 41% tall at x 0.59, the cut-back about 60% at x 0.52) and suggests `(0.50, 0.50, 1.0)`, the uncropped still. Switch the views when the Blender clip is the one that ships. The heist's `g_deny` already matches.
2. **The action's length.** `dur` stays 4.65 (the remake's timing); 5.0 with `offset` 0.37 gives the thud the prototype's longer silence (§2.1).
3. **The dive's horizontal ease.** Constant forward speed (the brief) can't clear the step at a 12° pitch with Lorraine's footprint. The solver picks the gentlest ease that clears (1.8-2.3 here); a steeper pitch (about 24°) would allow constant speed but reads as a nosedive.
4. **Forward axis**: glTF +Z front (Blender −Y), not the brief's "+Y forward", which can't hold in a GLB (+Y is up).
5. **Models in git or LFS**: GLBs are git-ignored and committed on purpose (`git add -f`), plain git up to about 100 MB of them, then LFS.

Settled: the label is `REENACTMENT · AI` on every clip, Blender or not (D4; the prototype's plain-`REENACTMENT` path for an all-procedural clip is gone). The heist zips on "move" (option B); option A is in §2.1.

---

## 12. Evidence

### 12.1 The integrated tool on the remake's Kokoro take (Blender 5.0.1 via `pip install bpy`, Python 3.11, 4 cores, Cycles CPU)

`.venv/bin/python pipeline/blender_reenact.py episodes/ep01r_three_feet_reenacted --preview`, both shots, on the real `build/timeline.json` (the prototype ran on an estimated one). Its sheets are in `build/blender/<clip>/` (git-ignored).

| | heist (`rx_heist_gnome_bl`) | action (`rx_action_goose_bl`) |
|---|---|---|
| Beats | still to clip frame 96, first moving frame 97 on "move" (3.228 s), flare peak frame 99 | rocks from frames 83 ("one", 2.802 s) and 90 ("goose", 3.036 s), tip from 106 ("dared", 3.560 s), landing on 130 (4.340 s) |
| Frames | 123 (shows 0-121) | 141 (shows 0-139) |
| Tag zone | clear (subject and all 7 beams) | clear (subject and fireball) |
| Cut-back | to `g_deny`: Δx −0.006, Δh −5.9%, OK | to `l_deny` at `(0.52, 0.53, 1.35)`: Δx +0.070, Δh −33%, WARN, suggests `(0.50, 0.50, 1.0)` (§11.1) |
| Other checks | beam clearance 1.39 in at the start, 0.276 in at the cut (never under 0.25) | fireball 6.3% of the frame at the landing, feet 28% hidden by effects (limit 50%), drop 0.027 s before "dared" (limit 0.1), landing 0.253 s after it (0.25 or more), facing 47-51° |
| Luma (mid frame) | mean 96, subject 144, backdrop 77 | mean 98, subject 135, backdrop 91 |
| Render | 25 frames at 270×480, 12 spp: 3.3 s/frame, worker 90 s | 31 frames: 2.4 s/frame, worker 78 s |

`--selftest`: 129/129 in 68 s with the show's `.venv` as the driver and `NM_BLENDER` pointing at the `bpy` Python; 129/129 in 79 s with the `bpy` Python itself as the driver (no PIL, no imageio-ffmpeg: filing through `clips.add()` takes ffmpeg from `PATH` and skips the luma check); 70/70 with the rendering half skipped where no Blender is found (exit 4 without `--allow-skip`). `pipeline/selftest.py` passes with it. And `make_episode.sh` end to end on a copy of the remake (`NM_BLENDER_FLAGS="--scale 10 --samples 4"`): pass 1, both clips rendered and filed through `clips.add()` (108×192 drafts, PROXY), pass 2 recording them as `clip_blender` (the soundtrack byte-identical to the fallback build's), `render.py` playing them under the tag, and `deliver.py --allow-draft` warning about both; with `NM_FINAL=1` and no Blender it stops after pass 1 with exit 2.

### 12.2 The prototype's measurements (before integration, on an estimated timeline)

The prototype's evidence files (`previews/`) were not committed. Its before (v1) and after (v2) table and render times:

| | v1 | v2 |
|---|---|---|
| Fireball | 7 orange balls in the top 19% of the frame, drifting out of the top edge and into the tag zone; peach under AgX, (225,112,63) to (246,154,122) | one billowing shape, centre (0.82, 0.31), below the tag band (hull clear on every frame), 6.1% of the frame at the land beat; fire mid-tones (178,70,0), saturation 1.0 in the swatch; ignition flash, a second boom on the landing |
| Laser red | (255,166,157) salmon at strength 9 | sheath (232,87,69), saturation 0.70; only the core blooms |
| Action cut-back (`l_deny`) | frame-0 box x 0.47-0.90, 40% tall, against the still's 0.22-0.84, 59%: a 1.5× punch-in | frame-0 box x 0.384-0.797 (centre 0.59), 40.6% tall; still box 0.305-0.765, 44.5%: Δx +0.056, Δh −8.6% (within 0.06 / 12%) |
| Heist cut-back (`g_deny`) | centre 0.48, 65% tall vs 0.515, 71% | Δx −0.006, Δh −5.9% |
| Action timing | 1 rock (±6°) from "one", the tip on "goose...", in the air during "dared", thud 0.10 s after it; L-shaped fall (13.7 cm forward at constant height, then down) | rocks (±10°) on "one" (2.70 s) and "goose" (3.00 s), the first tip frame on "dared" (3.70 s; check −0.036 s), a 0.63 s dive (z on a parabola, implied slow motion 0.30), the thud 0.37 s after "dared" ends, the cut 0.5 s later (`dur` 5.0) |
| Heist timing | first moving frame 2 frames after "Then" (rounding) | first moving frame on screen from the word's first frame; B zips on "move", flare peak on frame 98 |
| Heist frame | Deb as two pink blobs top right; lavender veil; mean 115, subject and backdrop alike | one gnome; dark violet set with a lit subject: final frame subject 146, backdrop 82, mean 100; lawn green to the lens |
| Action frame | lavender wash, mean 119-127, no orange rim, the landing in shadow, a glow under the door | teal/orange: subject 135-141, mean 98-99 (preview and final), a lit landing, no door glow (rough door) |
| Low beam | level, 1 in over the cap, all beams behind him | descends ~20°: 1.39 in at the start, 0.28 in at the cut (minimum 0.276 in, never under 0.25); two foreground beams |
| Dust at the cut | white 4-6 cm spheres hiding her feet ("eggs") | 40 low grey-brown puffs; 16% of her base hidden by effects on the last frame (limit 50%) |
| Garrison proxy | beard as a moustache band, boots hidden, polka-dot chips, eyeless, single-digit "thumbs" | full beard to the belly with fists at its corners, trousers and boots, dark wear marks, eyes with catchlights, thumbs on the inner edge plus finger ridges (`garrison_proxy_sheet.png`) |
| Lorraine proxy | straight thick neck, small head, pale small beak | S-neck, rounder head, chunky #F7A600 beak and feet, wing ridges, upturned tail (`lorraine_proxy_sheet.png`) |

Remaining gaps, measured: the heist preview's mid-frame mean is 96 (the final frame reaches 100); with the subject at about 140 and the backdrop held to 60-80, a 4-in-10 frame-height subject can't lift the whole-frame mean much past 95-100. The action's frame-0 box is 8.6% smaller than the real goose: the drop's sideways drift limits how big the start can be while the landing stays inside x 0.04.

Render times (this container was **shared with other workloads**, load average 4-20 on 4 cores, so they are upper bounds):

| Run | v1 | v2 |
|---|---|---|
| Heist preview, 270×480, 12 spp (25 frames) | 6.05 s/frame | 6.7 s/frame (6.3-9.0); worker 175 s including the motion dump |
| Action preview, 270×480, 12 spp (33 frames) | 4.79 s/frame | 3.1 s/frame (2.3-3.6) on a quieter machine; 12.7 s/frame under load |
| Heist final frame, 540×960, volume haze | 348 s at 128 spp | 163 s at 64 spp |
| Action final frame, 540×960, volume haze | 300 s at 128 spp | 88 s at 64 spp |
| Selftest | 29/30 (pip route) | 123/123 in 60 s, with the system Python and with the pip-bpy Python (no PIL) |

A full-resolution final on this CPU takes many hours per clip. For the heist's 123 frames at 1080×1920, 128 spp, volume haze, the driver estimates about 113 hours on the CPU, about 6 hours with Cycles on OptiX and about 35 minutes with Eevee on a GPU (`cycles cpu` 3,320 s a frame; `cycles gpu` OptiX 167 s; `eevee gpu` 17 s at 64 spp). Scaling the measured final frame in the table above (163 s at 64 spp, 540×960) by 2× the samples and 4× the pixels gives about 1,300 s a frame, or about 45 hours a clip. The driver prints its estimate before rendering and asks for `--yes` above 30 minutes, so finals belong on a GPU (§7.4), on the user's own machine.
