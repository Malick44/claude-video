# models/: the cast as 3D figurines, for Blender reenactments

`pipeline/blender_reenact.py` renders a reenactment's subject from `models/<name>.glb` when one is filed
here, and from a procedural **PROXY** otherwise. A clip made with a proxy is a placeholder: its
`clips.json` entry and sidecar say `proxy: true`, `review.py` warns, `deliver.py` refuses it, and under
`NM_FINAL=1` a missing model is an error (`--require-models`). The full guide is
[`docs/BLENDER_REENACTMENTS.md`](../docs/BLENDER_REENACTMENTS.md), section 4.

The `.glb` files are git-ignored (`.gitignore`: `models/*.glb`). `models.json`, the registry, is
committed. To commit a model on purpose (15 MB or less, like a still): `git add -f models/<name>.glb`.

## Conventions (the loader enforces them; the triangle limit only where Blender checks it)

| | |
|---|---|
| File | glTF 2.0 binary (`.glb`): **one figurine**, textures embedded, no lights or cameras, 100k triangles or fewer. Rigs, skins, shape keys and animation are stripped on import: subjects stay rigid. |
| Orientation | glTF standard: **+Y up**, the character's own front facing **+Z** (Garrison's face, Lorraine's and Deb's beak, Mr. Basin's briefcase side). A model facing elsewhere is declared with `--forward +x\|-x\|-z` and/or `--yaw D` (degrees), never fixed by hand. |
| Scale | **Ignored.** The loader scales the model uniformly to the bible's height: Ray 0.152 m, Garrison 0.406, Lorraine 0.508, Mr. Basin 0.711, Deb 0.864 (to the top of her head), the chime 0.914, Dale 2.438 (inflated). Anything else needs `--height-m`. |
| Origin | **Ignored.** The base centre goes to the origin. |
| Names | The cast only: `garrison`, `lorraine` (and `lorraine_bumblebee`, `lorraine_easter`, `lorraine_gingham`), `deb`, `basin`, `ray`, `chime`, `dale`. Anything else is refused, so a human model can't enter the pipeline. |
| Look | `restyle` (the default) keeps the base-colour texture and applies the show's plastic look (clear coat, low roughness, no baked emission), so the model goes through the set's lights like the proxies. `--no-restyle` keeps the file's own materials. |

## Making a GLB, one per ornament

**Higgsfield 3D (image to GLB)**, with the `higgsfield-generate` skill (`multi_image_to_3d`, textured):

1. Start from **one clean view** of the series still: the front view cropped from `stills/ref3d_<name>`
   (SERIES.md, "3D character references"), else the library still cropped to the character alone.
   Garrison: `garrison` cropped to x 0.25-0.72, y 0.25-0.85, so the goose behind him doesn't come along.
   Lorraine: the beak-left three-quarter view, **never the back view**. Deb: the side view. Up to four
   views of the same figurine may go in together (front, three-quarter, side), never a whole sheet.
2. Generate a textured GLB (`--should_texture true`), 100k triangles or fewer:
   `higgsfield generate create multi_image_to_3d --image ./garrison_front.png --should_texture true --wait`
3. File it (below), then check its sheet against the library still. **The library wins on identity**:
   Garrison's fists either side of the bottom of a full white beard, thumbs up, brown paint chips on the
   cap; Deb's **two** rod legs; Lorraine's short orange-yellow beak and webbed feet.

**Any other route** works with the same conventions: another image-to-3D tool, or modelling by hand in
Blender (ideal for Mr. Basin's simple solids; export glTF 2.0 binary, +Y up). File a hand-made model with
`--no-ai`.

## Filing one: `model add`

```bash
python pipeline/blender_reenact.py model add garrison ~/Downloads/garrison.glb \
       --source "Higgsfield 3D from ref3d_garrison front" --ai [--credit Higgsfield] \
       [--forward +z] [--yaw 0] [--height-m H] [--no-restyle] [--out-dir D]
python pipeline/blender_reenact.py model list
python pipeline/blender_reenact.py --showcase garrison --mode sheet --preview   # 4 views + the library still
```

`model add` **checks first and files after**: the GLB goes into a temporary folder, a Blender worker imports
and normalizes it there, prints its height, footprint, triangle count and anything stripped, and renders the
sheet frames (front, three-quarter, side, back; in `build/models/` unless `--out-dir`). Only then does it
replace `models/<name>.glb` and its `models.json` entry. A broken file fails with the importer's own message
and leaves the filed model alone. Without Blender on the machine it files the model unchecked, with a
warning. The sheet's back view is for review only and never goes into an episode or a generator.

To change a model's front, yaw or height, run `model add` again. Never edit `models.json` or swap a `.glb` by
hand: every render measures the file's bytes, and a GLB that differs from its `models.json` sha1 stops the run
with "rerun model add".

## `models.json`

One entry per model, written by `model add` (never by hand). An empty registry (`{}`) means every subject
renders as a proxy.

```json
"garrison": {"file": "garrison.glb", "sha1": "...", "source": "Higgsfield 3D from ref3d_garrison front",
             "ai_generated": true, "credit": "Higgsfield", "height_m": 0.406, "forward": "+z",
             "yaw_offset_deg": 0, "restyle": true, "anchors": {}, "tris": 48210, "added": "2026-10-20"}
```

| Field | Meaning |
|---|---|
| `file` | The GLB in this folder. |
| `sha1` | Its bytes when it was checked. A render stops when the file no longer matches. |
| `source`, `credit` | Where it came from (the episode's credits and the clip's provenance carry them). |
| `ai_generated` | `--ai` / `--no-ai`. Recorded in the clip's `clips.json` entry and sidecar; the on-screen label is `REENACTMENT · AI` either way (decision D4). |
| `height_m`, `forward`, `yaw_offset_deg`, `restyle` | How the loader normalizes it (above). Each one is in the clip's content key, so changing it re-renders. |
| `anchors` | Optional points in normalized metres (base-centred, front −Y): `nose` puts Garrison's sweat bead, `head` lets the prop-in-frame check work. |
| `tris` | Triangles counted at the check. |
| `added` | The date it was filed. |

After filing a model, commit `models.json` (and the GLB with `git add -f` if it is meant for the repo).
