"""Write REENACTMENT_PROMPTS.md from episode.py and a build's timeline.json, so the prompts in the doc
are always the ones in episode.py and its timings are the build's.

Every prompt text comes from episode.py (STILLS, CLIPS, CLIP_SOURCES); every timing (shot spans, take
lengths, where the move falls in each generated take) comes from the timeline, through fit_takes.py.
Re-run it after editing a prompt, and after locking new takes (with --takes naming them):

  .venv/bin/python pipeline/build_audio.py episodes/ep01r_three_feet_reenacted
  .venv/bin/python episodes/ep01r_three_feet_reenacted/tools/make_prompts_md.py [--timeline T] [--takes "locked v4"]
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fit_takes import EP_DIR, load_episode, load_timeline, reenactments, tc, word_time  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("--timeline", help="timeline.json (default: the episode's build/timeline.json)")
ap.add_argument("--takes", default="Kokoro scratch", help='which takes the timeline holds (default "Kokoro scratch")')
args = ap.parse_args()
ep = load_episode()
tl = load_timeline(args.timeline)
TAKES = args.takes
S, C, SRC = ep.STILLS, ep.CLIPS, ep.CLIP_SOURCES
sh = {s["id"]: s for s in ep.SHOTS}
at = {s["id"]: (s["start"], s["end"]) for s in tl["shots"]}
def span(i): return f"{tc(at[i][0])}–{tc(at[i][1])}"
def q(t): return "> " + t
H, A = sh["heist"], sh["action"]
RX = {r["id"]: r for r in reenactments(ep, tl)}
T = {"total": tl["total"], "rx": sum(r["dur"] for r in RX.values())}          # the shots' declared lengths
TK = {i: RX[i]["take"] for i in RX}                                   # take lengths in this build
THEN = RX["heist"]["key_t"]                                            # "Then", seconds into the heist take
H_MOVE = RX["heist"]["move"]                                           # the slide, seconds into the clip
H_SHIFT = RX["heist"]["shift"]                                         # in = S - H_SHIFT
A_LAND = RX["action"]["move"]                                          # the landing, seconds into the clip
A_SHIFT = RX["action"]["shift"]
A_MAX = RX["action"]["max_take"]                                       # longest take with in >= 0
H_MAXKEY = RX["heist"]["max_key"]
DARED = word_time(RX["action"]["caps"], "dared")                       # "dared" starts this far into the take
SECS = {k: SRC[k]["seconds"] for k in SRC}
TAG = re.compile(r"\[[A-Za-z][^\[\]\n]*\]")          # an audio tag (words.TAG)
md = f"""# Reenactment prompts: Episode 1 remake, "Three Feet, Reenacted"

The episode has two reenactments, {H['dur']:.2f} s and {A['dur']:.2f} s ({T['rx']:.1f} s of a {T['total']:.1f} s episode, {T['rx'] / T['total'] * 100:.1f}%). Each one is a single ornament making a single rigid move on a locked camera, starting from stillness and landing on the narration's key word, and each hard-cuts back to that ornament's real, motionless still. Every text below is generated from `episode.py` (`STILLS` holds the keyframes and reference sheets, `CLIPS` the motion prompts, `CLIP_SOURCES` the references, negative prompts and per-tool settings) by `tools/make_prompts_md.py`, and every timing from the build's `timeline.json`, so the two files can't drift. Edit the prompts in `episode.py`, then re-run it.

## How each clip is made

0. **Lock the line first.** A reenactment's clip is fitted to its narration take, so voice its line on v4 (or the human fallback) and lock the take before generating the clip. Then set the motion prompt's hold time from the locked take: heist, "For the first X seconds" with X = `pre` + the time of "Then" in the take + `in`; action, "At about Y seconds" for the landing, with Y = `pre` + the take's length + `in`. The generated take must cover `in` + `dur`: ask for 10 s when that passes 5 s, and set `CLIP_SOURCES` `seconds` to match. The prompts below are fitted to the {TAKES} takes ("Then" {THEN:.2f} s into the heist line; the trailer line {TK['action']:.2f} s long); `tools/fit_takes.py` prints the hold times for the takes in the current build.
1. **Reference sheets.** Generate the three 3D reference sheets at the bottom of this file once, attaching the library photo as image 1, with the canvas set to **16:9** in the tool (they never go on screen). Then generate `ref3d_lineup` from the three sheets, so they share a scale. File all four in the series library as `ref3d_garrison`, `ref3d_deb`, `ref3d_lorraine` and `ref3d_lineup`. Every later reenactment reuses them.
2. **Keyframe.** Generate the keyframe image from its prompt.
   - **Canvas:** set it to 9:16 in the tool; prompt text doesn't set it. Nano Banana: `aspect_ratio` 9:16. GPT Image: generate 1024x1536 and outpaint to 9:16, subject centred. Export at 1080x1920.
   - **Attachments, in the order of the prompt's image map.** Crop ONE view from each 3D sheet before attaching it (Garrison front, Deb side, Lorraine's beak-left three-quarter view; never her back view): a whole turnaround sheet makes the model draw several copies. Crop the library photos as listed.
   - **Who wins:** the library still wins on identity (shape, colours, markings, pose); the 3D sheet and the style suffix win on material and lighting.
   - **Negative:** pass the clip's negative prompt to the image tool wherever it accepts one.
   - File the keyframe in the episode's `stills/` under its key. It is also the shot's fallback.
3. **Clip.** Animate the keyframe image-to-video, for the length in `CLIP_SOURCES` ({SECS['rx_heist_gnome']} s for both here; 10 s whenever `in` + `dur` passes 5 s).
   - **Aspect:** set the image-to-video aspect to 9:16 and confirm the keyframe is already 9:16, so nothing is cropped.
   - **Kling:** paste the negative into `negative_prompt`. Where it offers a motion brush, paint the ornament with its path (sideways left for Garrison; down one step, lower left, for Lorraine) and mark the flamingo, the lasers and the house static.
   - **Seedance:** there is no negative field. Set `camera_fixed` and append the clip's `seedance_suffix` (below) to the motion prompt.
   - Image-to-video gets the keyframe alone; the references were for the keyframe step. Don't use first-and-last-frame mode: it spreads the motion over the whole take, and these clips need stillness first.
   - Never use text-to-video alone, because the ornaments drift off-model. Generate several takes and keep the one where nothing bends, steps or turns and the move comes at the right time. Then set `in` (see each Duration row). Never slow a take down in the episode: the slow motion happens once, in the generator.
   - **Fallback when no take works.** Both moves are rigid translations, so build the clip outside the pipeline: cut the ornament out of the keyframe, animate the cutout along its path over a clean plate of the same keyframe (ffmpeg `overlay`, or any editor), use image-to-video only for the haze, flares and fireball, and file the result as the clip.
4. **File it** with `pipeline/clips.py add episodes/ep01r_three_feet_reenacted <clip key> <file> --generator "<tool and model>"` (the prompt and negative come from `episode.py`'s `CLIPS` and `CLIP_SOURCES`). Then check `build/review/clips.png` and, after rendering, `build/review/reenact.png` against the checklist under each shot.

The generator never draws the label. The renderer burns `{H['label']}` and the stamp onto every frame of the clip, at the top left, in a red box. Every reenactment carries the same `{H['label']}` label (D4), so the AI marker is on screen whenever an ornament moves; the stamp under it names the theory. The series' yellow corner badge isn't drawn on reenactments, so the red tag is the only badge.

**Keep the top left clear.** The tag and its stamp cover x 64 to about 750 and y 190 to 320 of the 1080x1920 frame. No ornament top, beam or key action goes above about a quarter of the frame height on the side the ornament moves toward, or the move plays behind the AI tag.

## Shared 3D style suffixes

**For stills** (keyframes; from `SERIES.md`, word for word). No "slow motion" here: a still prompt that asks for motion gets motion blur.

{q(ep.STYLE_3D)}

**For clips** (the end of every motion prompt). Slow motion lives here and in the generator only. It has no human words, so `CLIPS` pass the pipeline's prompt lint.

{q(ep.MOTION_STYLE)}

---

## RX1 · `heist` · THEORY #1: THE GNOME (heist movie)

| | |
|---|---|
| **Shot id** | `heist`, {span("heist")}, right after the board asks "Gnome, or goose?" |
| **Clip key** | `rx_heist_gnome` → `episodes/ep01r_three_feet_reenacted/clips/rx_heist_gnome.mp4` |
| **Duration** | {H['dur']:.2f} s on screen (`dur`, fixed). Generate {SECS['rx_heist_gnome']} s; the shot plays source {H['in']:.2f}–{H['in'] + H['dur'] * H['speed']:.2f} s at 1.0x, with no retime. The slide should start about {H_MOVE:.1f} s into the take, on "Then". If it starts at time S, set `in` = S − {H_SHIFT:.2f} and leave `dur` and `speed` alone. Fitted to the {TAKES} take; once the clip exists, "Then" can come at most {H_MAXKEY:.2f} s into a longer take (`in` reaches 0), so lock the v4 take first and fit the hold time to it (step 0). |
| **Narration over it** | NARRATOR, prestige voice: "That night, he was facing her. Then he made his move." On the {TAKES} take it runs {H['pre']:.2f}–{H['pre'] + TK['heist']:.2f} s into the shot, with "Then" at about {H_SHIFT:.2f} s. He holds still under "That night, he was facing her.", slides from "Then", and {H['dur'] - H['pre'] - TK['heist']:.2f} s of slide plays under the swell's peak before the cut. |
| **Character references** (keyframe step, in this order) | 1. {SRC['rx_heist_gnome']['keyframe_refs'][0]}; 2. {SRC['rx_heist_gnome']['keyframe_refs'][1]}; 3. {SRC['rx_heist_gnome']['keyframe_refs'][2]}; 4. {SRC['rx_heist_gnome']['keyframe_refs'][3]} |
| **Camera** | Locked off. `kb` is (0.5, 0.53, 1.0) at both ends, and Seedance gets `camera_fixed`. A push-in on a rigid figure reads as a zoom on a still, which is how reality already looks in this show. |
| **Label** | `{H['label']}`, with the stamp `{H['stamp']}`. No timestamp, so it can't be read against the doorbell table. |
| **Sound cue** | **Automatic:** `reenact_hit` lands its downbeat on the first frame. `reenact_swell` sits at 0.35 under the line and ramps to full at the cut, then stops dead (8 ms declick, no tail). The theme bed is out from the shot's start until 0.6 s after the cut. **Wanted flavour** (needs a per-shot cue name, which the pipeline doesn't have yet, e.g. `"cue": "rx_heist"` → `SOUNDS`): pizzicato heist strings over a low laser hum, and a bright "tick" as the cap clears the beam. |
| **Cuts back to** | `g_deny`: `garrison_lift` (fallback `garrison`), locked off at ({sh['g_deny']['views'][0]['kb'][0][0]}, {sh['g_deny']['views'][0]['kb'][0][1]}), zoom {sh['g_deny']['views'][0]['kb'][0][2]}, about two-thirds of the frame height (cap tip near y 430, clear of the corner badge), back in his spot. Crickets only, then "Kid. … I was facing the other way." |
| **Fallback** | The keyframe still `rx_heist_gnome_key` under the same label; failing that, `garrison`. |

**Keyframe image prompt** (`rx_heist_gnome_key`):

{q(S['rx_heist_gnome_key'])}

**Motion prompt** (`CLIPS["rx_heist_gnome"]`, lint-clean):

{q(C['rx_heist_gnome'])}

**Seedance suffix** (append to the motion prompt; Seedance has no negative field):

{q(SRC['rx_heist_gnome']['seedance_suffix'])}

**Negative prompt** (keyframe step, and Kling's `negative_prompt`):

{q(SRC['rx_heist_gnome']['negative'])}

**Review checklist** (every cell of `clips.png` and `reenact.png`):
- **No human:** no person, hand, glove, foot, shoe or face; no human silhouette, shadow or reflection.
- **Garrison:**
  - stands still for about the first 2.5 s of the take, then slides sideways toward frame left as one rigid piece, and is still sliding at the cut;
  - faces the camera in every frame; never rotates, steps, dips or ducks;
  - his hands never move (one on each side of the bottom of his beard, thumbs up, as in `garrison`), his cap stays on and unchanged, and his face never changes;
  - fills about two-thirds of the frame height, and his size doesn't change;
  - his cap tip and the lowest beam stay below the top quarter of the frame, clear of the red tag, for the whole slide.
- **The camera** never moves: the lasers, the flower bed and the house hold still in frame.
- **Deb:** stands still on two legs, in the upper right, inside the frame, and nothing touches her.
- **The scene:**
  - exactly one gnome and one flamingo; the porch steps, the goose, the birdbath and the frog are out of frame;
  - Ray is not lit, and every window is dark;
  - no text, banner, lower third or letterbox bars in the picture apart from the burned-in label;
  - no torn turf, no tracks and no new holes.
- **Light:** mean luma at least 100. It must look obviously CG at thumbnail size.
- **The cut:** the frame after the cut is the real, unmoved `garrison`, back in his spot, at about the same size.

---

## RX2 · `action` · THEORY #2: THE GOOSE (action movie, Director's Cut)

| | |
|---|---|
| **Shot id** | `action`, {span("action")}, right after Mr. Basin's silent cutaway. This is the episode's peak, placed around the middle, where Shorts retention sags. |
| **Clip key** | `rx_action_goose` → `episodes/ep01r_three_feet_reenacted/clips/rx_action_goose.mp4` |
| **Duration** | {A['dur']:.2f} s on screen (`dur`, fixed). Generate {SECS['rx_action_goose']} s; the shot plays source {A['in']:.2f}–{A['in'] + A['dur'] * A['speed']:.2f} s at 1.0x. The landing should come about {A_LAND:.2f} s into the take, just after "dared". If it comes at time T, set `in` = T − {A_SHIFT:.2f}. That must be 0 or more; if she lands before {A_SHIFT:.2f} s, regenerate or use the cutout fallback. Fitted to the {TAKES} take ({TK['action']:.2f} s): once the clip exists it absorbs a trailer take of up to about {A_MAX:.2f} s. Over that, regenerate the clip as a 10 s take with the landing re-timed; raising `dur` alone freezes the clip and lands her before "dared". So lock the trailer take first (step 0). |
| **Narration over it** | NARRATOR (TRAILER): "In a world where nobody moves... one goose... dared." On the shipping Eleven v4 voice the register change comes from the line's one audio tag, `{TAG.findall(A['items'][0][3])[0]}`, in the spoken text only. On the {TAKES} take it runs {A['pre']:.2f}–{A['pre'] + TK['action']:.2f} s into the shot, with "dared" at about {A['pre'] + DARED:.2f} s. "In a world where nobody moves..." plays over a motionless goose in front of an explosion; she lands at about {A['pre'] + TK['action']:.2f} s, and the cut comes {A['dur'] - A['pre'] - TK['action']:.2f} s later. |
| **Character references** (keyframe step, in this order) | 1. {SRC['rx_action_goose']['keyframe_refs'][0]}; 2. {SRC['rx_action_goose']['keyframe_refs'][1]} |
| **Camera** | Locked off, low angle. `kb` is (0.5, 0.5, 1.0) at both ends; Seedance gets `camera_fixed`. A camera that dollies back at her pace keeps her the same size and hides the move. |
| **Label** | `{A['label']}`, with the stamp `{A['stamp']}`. The label is the same on every reenactment (D4), so the escalation lives in the stamp. At 674 px the stamp needs the renderer's text-sized tag (it ends at x 738, inside the x 930 limit), so the fireball stays right of the frame's centre line. |
| **Sound cue** | **Automatic:** `reenact_hit` on the first frame, and `reenact_swell` ramping to full at the cut, then dead silence. **Wanted flavour** (needs a per-shot cue name; not in the pipeline yet): a distorted guitar sting, a slow-motion whoosh, a concrete thud on her landing, and the fireball's boom on the swell's peak. |
| **Cuts back to** | `l_deny`: `lorraine_lift` (fallback `lorraine`), locked off at (0.52, 0.53), zoom 1.35, about 60% of the frame height, her beak to frame left, back on her step. Crickets and the porch-light hum, then "Where would I go, hon? … I'm concrete." |
| **Fallback** | The keyframe still `rx_action_goose_key` under the same label; failing that, `lorraine`. |

**Keyframe image prompt** (`rx_action_goose_key`):

{q(S['rx_action_goose_key'])}

**Motion prompt** (`CLIPS["rx_action_goose"]`, lint-clean):

{q(C['rx_action_goose'])}

**Seedance suffix:**

{q(SRC['rx_action_goose']['seedance_suffix'])}

**Negative prompt** (keyframe step, and Kling's `negative_prompt`):

{q(SRC['rx_action_goose']['negative'])}

**Why no aviators.** The escalation draft gave her sunglasses. `SERIES.md` says every reenactment of the night of 13–14 June uses her BARE, because the doorbell frames and Exhibit A show her bare. It also says new outfits have to be designed before any reenactment uses one. The joke survives without them: she never looks back because she can't turn.

**Why she drops toward the lower left, not toward the camera.** Image-to-video models turn a subject to face the way it travels. Travelling toward the lens with her beak to frame left invites a swing to face the camera, which would break "never turns", the rule that protects frame 418. Along her beak, nothing needs to turn.

**Review checklist:**
- **No human** anywhere.
- **Lorraine:**
  - no outfit or accessory;
  - stands still on the top step for about the first 4 s of the take, then tips off as one rigid piece and lands on the step below, toward the lower left, with a puff of dust;
  - her beak points to frame left in every frame; her body angle never changes; she never faces the camera and never shows her back (this protects frame 418, which pays off in Episode 2);
  - her legs, feet, neck, beak and wings never move, and she stands on her webbed feet, never sits;
  - she is on the lower step at the cut, never on the lawn.
- **The camera** never moves.
- **No other ornament:** Deb, Garrison, Mr. Basin and Ray are all out of shot. The chime beside the door sways in the wind; it never hangs still.
- **The fireball:** reads as a stage effect behind the roofline, right of the frame's centre line; the sky left of centre stays plain (under the red tag and its stamp, which reaches x 0.69). Nothing burns, chars, breaks or falls.
- **The scene:** every window dark, and no text, banner, lower third or letterbox bars in the picture apart from the burned-in label.
- **Light:** mean luma at least 100, and obviously CG at thumbnail size.
- **The cut:** the frame after the cut is the real, unmoved `lorraine`, back on her step, beak left, at about the same size.

---

## 3D character references needed for this episode

These sheets go in the series library (`shows/nobody-moves/stills/`), because every later reenactment of these characters starts from them. Each one copies its reference block from `SERIES.md` word for word.
- Mr. Basin and the chime don't appear in this episode's reenactments, so their sheets can wait.
- On `SERIES.md`'s 3D scale, Garrison is 16 in, Lorraine 20 in and Deb 34 in to the top of her head. `ref3d_lineup` puts the three side by side, so the separately generated sheets agree on scale.
- Generate the sheets at 16:9. Each figure then gets enough width; on a 9:16 canvas models stack the views 2x2 or shrink them.

### `ref3d_garrison` (image 1: the library still `garrison`)

{q(S['ref3d_garrison'])}

His moves: he hops or slides sideways like a chess piece and never rotates himself. If he moves something, he balances it on his cap; his hands never move.

### `ref3d_deb` (image 1: the library still `deb`)

{q(S['ref3d_deb'])}

She always has two legs. In this episode she is only a still prop in the heist's foreground. SERIES.md never says how she was put back at 3:12. No reenactment shows Deb being moved, lifted or dragged.

### `ref3d_lorraine`, BARE (image 1: the library still `lorraine`)

{q(S['ref3d_lorraine'])}

How she moves, in the bible: a heavy side-to-side rock-waddle, with a concrete thud on each landing. In a clip, give her one rigid move (a tip, a drop, a slide) in the direction her beak points; a rock-waddle invites leg movement. The sheet includes a back view only because a turnaround needs one: crop single views before attaching, and never pass the back view to any keyframe or video generator for a scene set before Episode 2's payoff.

### `ref3d_lineup` (images 1–3: the three sheets above)

{q(S['ref3d_lineup'])}

---

## Reenactment ledger rows (in SERIES.md)

These rows are in `SERIES.md`'s reenactment table, after the clue ledger, so the next writer doesn't restage these theories differently or reuse these denials. Neither row is a clue, and neither plants anything.

| Ep | Theory | Night, between frames | What it shows | Kept out of shot (hidden) | Denial line |
|---|---|---|---|---|---|
| 1 (remake) | The gnome did it (heist movie) | 06/14, between 417 (03:11:59) and 418 (03:12:00) | Garrison stands still in red lasers facing Deb, then slides sideways like a chess piece, rigid, hands unmoved. Deb is untouched, and the cut comes mid-slide. | The porch and Lorraine (turned in 418), Ray, the holes, any move of Deb | GARRISON: "Kid. … I was facing the other way." Button: "They made me look short." |
| 1 (remake) | The goose did it (action movie, Director's Cut) | the same | Lorraine, bare, stands still on the top step as a stage fireball blooms, then drops one step toward the lower left, along her beak. She never turns, and the cut comes while she is on the lower step. | Deb, Garrison, Ray, any turned, frontal or back view of Lorraine | LORRAINE: "Where would I go, hon? … I'm concrete." |
"""
open(os.path.join(EP_DIR, "REENACTMENT_PROMPTS.md"), "w").write(md)
print("wrote", len(md), "chars")
