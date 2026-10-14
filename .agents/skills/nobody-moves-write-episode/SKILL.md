---
name: nobody-moves-write-episode
description: Write the next episode of NOBODY MOVES, the TikTok true-crime parody where lawn ornaments are the witnesses (Garrison the gnome, Lorraine the porch goose, Deb the flamingo, Mr. Basin the birdbath, the wind chime, Ray the solar frog). Produces a ready-to-build episode.py in shows/nobody-moves/episodes/ (a main episode under 50 s, a remake, or a 15-25 s Confessional), including its labelled 3D reenactments and their prompts, prompts for any new stills, the audio-tag directions, and the continuity (clue ledger) updates. Use this whenever the user asks for a new NOBODY MOVES episode, "episode 4", "the next episode", a Confessional short, a remake of an episode, a reenactment, new lines or jokes for these characters, a script rewrite, or what happens next in the case, even if they don't name the show.
---

# Write a NOBODY MOVES episode

The show lives in `shows/nobody-moves/`. Writing an episode means producing a data file, `episodes/<epNN_slug>/episode.py`, which the pipeline turns into voices, a timeline and a 1080×1920 video. This skill covers the writing. To build and check the video, use the `nobody-moves-produce-episode` skill.

## Read first

1. `SERIES.md`: the premise, **the rule** ("Nobody moves while anyone is watching"), the cast and their running gags, the yard layout, the **reenactment** style guide and its never-rules, the **3D character references**, the **clue ledger**, the doorbell tables with the state any reenactment must match, and the **roadmap**. This is the source of truth for continuity.
2. The previous episode's `episode.py` and `SCRIPT.md`. Match the format, and pick up its cliffhanger: its `ANSWER` is what the audience was asked to spot.
3. The worked example of the current format: `episodes/ep01r_three_feet_reenacted/` (`episode.py`, its `NOTES.md` for the timing and canon reasoning, `REENACTMENT_PROMPTS.md` for how the clips are made). `docs/DECISIONS_EP01R.md` says why each rule below exists.
4. `cast.py`, for who has a voice. `README.md` "episode.py reference", for the shot kinds and fields.
5. `references/episode-template.py` in this skill: an annotated skeleton with every shot kind.
6. For audio tags: `docs/AUDIO_ELEVENLABS_V4.md`, "Audio tags house rules" and its approved vocabulary per character.

## What makes an episode work

These rules come from how the pilot was designed, what the remake test was built to fix, and what Shorts and TikTok reward. Each one says why.

- **Open on the event or a line in the first second, never on a title.** Scrollers decide in about a second. There is **no opening title card** in a main episode: the series title is the small corner label (`CORNER_LABEL = "NOBODY MOVES"`), drawn on every reality shot. A doorbell cold open (the jump at 0:01, `"flicker": False`) or a gnome saying something absurd in deadpan stops the thumb. The published Episode 1 put a 3.2 s title card at 0:05; don't repeat it. (A Confessional may keep its short title card; see Confessionals.)
- **Ask an easy comment question by about 10 s.** One binary question a first-time viewer can answer in one word, with no lore: "Who did it? Gnome, or goose?" Put it on the board's index card (`"card": "COMMENT: GNOME OR GOOSE?"`) and say it. The published Episode 1 asked at 1:13, after most viewers had left. The hidden doorbell change stays as the bonus for people who rewatch.
- **Every episode works for a first-time viewer.** Assume nobody saw the last one. The hook, the question and any reenactment's theory must make sense with no lore ("the gnome did it"); the best-performing Confessionals are self-contained jokes about a recognizable type of person, and the lore-heavy ones do worst. Recaps of earlier clues are allowed once the viewer is in, never as the hook.
- **Answer last episode's clue early, within about 25 seconds** (a sequel episode; a remake or a standalone has none). Commenters who solved it get paid off, and people who missed it get the recap. A doorbell replay's call to action appears about 2 s after its last line ends, so give the shot `"post": 3.6` or more to hold it on screen for at least 1.5 s; Episodes 2 and 3 used 3.0 and held it for 0.95 s.
- **Hide a new change in a doorbell-cam frame at the end, as the bonus.** It must be *fair*: visible on a rewatch at phone size, and not obvious on first view. Supported mechanisms:
  - `alter_box`: mirror a region, so something has turned around.
  - `alter_glow`: light up a point, so something switched on.
  - different `frame_a`/`frame_b` stills: something appears, disappears or moves. Derive frame B from the latest library frame with a pixel edit in a `make_stills.py` beside the episode, and save it in the library (see Stills). Episode 3's `make_stills.py` removes Lorraine from the porch step to make `yard_gone`. Two separately generated images never match, so a generated frame B would change everything at once.

  Every doorbell frame of the night must agree with the doorbell table in SERIES.md: who has turned, what is lit, what is gone. Carry lights that are already on into later frames with `lit=[(x, y, r)]`. Write the answer in `ANSWER`, in the SERIES.md ledger (including which episode pays it off), and add the new frame to the table.
- **The bonus asks for a description, not a name.** When the hidden change's object is also an answer to the early question (the goose), a bare "goose" is a vote, not a find. Use `"cta": ("SOMETHING ELSE IN", "THIS FRAME MOVED.")` with `"cta_sub": "Rewatch 0:01. What else changed? ↓"` (point at the second where the frame first shows), never "Comment the object + timestamp".
- **Runtime: main episodes under 50 s** (a Confessional is 15–25 s). Retention first while the channel is small; TikTok's 60 s Creator Rewards minimum is revisited near eligibility, not now. Leave about 1.5 s or more of headroom on the Kokoro scratch build, because the final voices run longer: every longer take comes out of that one budget. After building the audio, the shot table prints the exact runtime; trim lines and dead air rather than speeding up voices.
- **Pace: brisk.** About 165 words/min while someone is speaking (150 is the floor, not the target) and 110–120 overall. Keep silence only where it is the joke: the cut-back after a reenactment and its hold, the beat before a denial, the doorbell's call-to-action hold. Trim every other pause and tail. Check both numbers on the final takes, not only on the scratch voice (`review.py`'s pacing table gives words/min overall and the speech share; `episodes/ep01r_three_feet_reenacted/tools/fit_takes.py` shows the full gate for the remake), and keep an ordered trim list in the episode's `NOTES.md` for a build that runs long. At 150 words/min while speaking, 110 overall leaves room for at most about 27% silence.
- **Nobody moves while anyone is watching.** Reality never moves: every interview, evidence photo and doorbell frame is one still with a slow camera move. An ornament moves only in a labelled REENACTMENT of the narrator's theory, within the limits below, and the hard cut back to the motionless real ornament is the punchline. The comedy still comes from the gap between prestige true-crime form and stakes no bigger than a flamingo three feet to the left.
- **Captions carry the comedy.** Most people watch muted, so every joke has to read as text. Keep lines short, one idea each, and put the punchline last. Use a `P(...)` pause before a punchline; the silence is the joke's timing. A caption shows at most two lines of about 20 characters, so a line over about 40 characters is split into chunks, at a full stop or comma when it has one; punctuate where a split should fall. End cards draw no captions, so a closing button line goes on its own still before the end card.
- **Each character has one mechanism; escalate it, don't swap it.** Lorraine is warm and evasive ("hon"; turning around isn't "going anywhere"). Garrison is defensive and "was facing the other way." The chime only talks when it's windy. Mr. Basin is his own lawyer. Ray only talks after a full day of sun. New jokes, denials included, come out of these rules.
- **Silence is a sound cue.** The score builds toward the doorbell by itself, and the risers, whooshes and hits are automatic. Your lever is `"music": "out"` on a shot, which cuts the score for it. Every reenactment's cut-back uses it; beyond those, use it once or twice an episode, right before a punchline or a reveal (Episode 2: "The wind stopped."; Episode 3's Exhibit A reveal). The drop is what makes the next beat land; used everywhere, it stops meaning anything. It cuts only the score bed:
  - never put it on a shot with `sting_soft`, on a doorbell shot or on a reenactment shot: the swell or the flicker's riser keeps playing on the score bus, and mixcheck's silence check fails (a reenactment with it doesn't build);
  - the shot's own `sfx` still sound, so give it none if you want real silence (a cut-back keeps `"sfx": ["crickets"]`, which is the room tone);
  - not right after a sting's tail, which would still be ringing through the drop.

  `nobody-moves-sound-design` recipe (e) verifies the beat with `pipeline/mixcheck.py` (the music-out row must read silent). An episode that doesn't end on a doorbell needs `"climax": True` on its peak shot instead (see Confessionals).
- **End card.** Set `NEXT_UP` to the next roadmap title, so the audience knows there's more. The AI disclosure is drawn for you; on an episode with a reenactment it reads "Footage, reenactments and voices made with AI." and the build fails unless it stays fully legible for 1.8 s, so give that end card `"min": 2.6` (2.45 at the least).

## Reenactments

Read SERIES.md "Reenactments" first; this is the writer's checklist.

- **When:** a stated theory that an ornament did something ("What if the gnome…"), with a short deadpan denial ready from that character's mechanism. Good places: right after the early comment question, one theory per suspect, or in a cold open. Never for a clue, a solution, an interview line, a recap, or anything meant to say "this really happened". A reenactment never goes into the clue ledger.
- **How many:** a main episode has at most **2**, adding up to no more than about **20%** of the runtime, never back to back. A Confessional has at most **1**, 5 s or shorter.
- **Length:** each **3–6 s**, one action and one peak. `dur` = `pre` + the narration + at least 0.5 s of action after the last word, at most 6.0.
- **Narration over it:** one narrator line of about 10 words, with the setup before the key word at most about 2 s of speech. The ornament holds still under the setup and moves on the key word ("Then he made his move.", "…dared."). Nobody speaks inside a reenactment: an ornament's voice only comes from its real still.
- **The label:** `"label": "REENACTMENT · AI"`, exactly, on every reenactment (the build refuses anything else). The theory, and any escalation, goes in the stamp: `"stamp": "THEORY #1: THE GNOME"`, `"THEORY #2: THE GOOSE (DIRECTOR'S CUT)"`. No clock time in the stamp. The tag and stamp must end before x 930, so keep stamps under about 40 characters.
- **The shot before it** ends its last line at least 0.35 s before the cut (`"post": 0.35`): `reenact_hit`'s reversed suck-in starts there, and would otherwise play over the line, usually the comment question. No `sting_soft` on that shot.
- **The hard cut back:** the next shot is a `still` of the same ornament, real, **back in its spot**, at about the same size and angle, with `"music": "out"`, `"sfx": ["crickets"]`, `"pre": 0.3`–`0.6` (the silence before the denial, SERIES.md's 0.3–0.6 s; the remake uses 0.45), the denial, and `"post": 0.35`: the motionless hold after the denial is where the laugh lands. No transition, whoosh or flash.
- **An optional button** from the suspect objects to the dramatization, not the accusation ("They made me look short."), captioned on its own still.
- **No name card, `"music": "out"` or `"climax"` on a reenactment shot** (build errors), and a reenactment is never the last shot.
- **A silent reaction cutaway** (no line, about 1.6 s, like the remake's Mr. Basin) carries its joke on its name card with `"lower_third_at": "cut"`, so the card is fully on from the cut to the cut: the punch alone on the short yellow third line, about 15 characters at most, and the setup in the subtitle. A viewer reads top-down and has 1.6 s.
- **Never** (SERIES.md has the full list): a human or any part or trace of one; how a canon move was done (nothing shows Deb being moved, lifted or dragged); a hidden clue before its payoff (Lorraine never turned, frontal or back-on before Ep. 2); anything the clue ledger or doorbell tables contradict (a theory on a recorded night starts in the earlier frame's state, every window dark until 03:15, the chime swaying on a windy night); an ornament staged as the culprit of a solved case, except in a remake set before the solution; anything photoreal. The narration around a reenactment is reality: check it against the ledger (Garrison faced Deb that night, not for thirty-one years).
- **What to write into `episode.py`:**
  - the shot: `"kind": "reenactment"`, `"clip": "rx_<name>"`, `"in"`, `"speed": 1.0`, `"dur"`, a locked `"kb"` (the same view at both ends), `"label"`, `"stamp"`, `"look": "reenact"`, `"cue": True`, `"cut_silence": 0.6`, `"pre": 0.35`, and `"fallback"` views (the 3D keyframe still first, then a crop of the real still), so it builds and reviews before the clip exists;
  - `STILLS["rx_<name>_key"]`: the keyframe prompt, built in SERIES.md's order (image map, the reference blocks word for word, the first instant of the action, the subject's size and where its top sits, "Exactly one …", a static camera, "Time and state: …" with no date or clock time, every window dark, the still suffix). Keep the top left of the frame clear: the red tag covers about x 64–750, y 190–320, so no cap, beam or key action above about a quarter of the frame height on the side the ornament moves toward;
  - `CLIPS["rx_<name>"]`: the motion prompt (the locked camera first, then how long the ornament holds still and its one rigid move, across the frame and along its facing, then background motion, then the motion suffix word for word). It must name no person: the build's prompt lint refuses one, and it counts hand(s), arm(s), finger(s), figure(s), kid(s), man/men and the like as human words even for an ornament (a negation strips only the words after it, so "his hands never move" fails). Describe the pose instead: "as one rigid piece, his pose unchanged";
  - `CLIP_SOURCES["rx_<name>"]`: `keyframe`, `keyframe_refs` (in the image map's order, each a cropped single view), `seconds` (5, or 10 when `in` + `dur` passes 5), `aspect` "9:16", `camera_fixed`, the shared negative plus the per-clip list, and `seedance_suffix`;
  - new 3D reference sheets (`ref3d_<name>`) in `STILLS` only for a character whose sheet isn't in the library yet.
- **The line comes before the clip.** The clip's motion is timed to the narration take, so the line is voiced and locked before its clip is generated, and the motion prompt's hold time comes from that take: a move on a key word, "For the first X seconds" with X = `pre` + the key word's time in the take + `in`; a landing after the line, "At about Y seconds" with Y = `pre` + the take's length + `in`. Write the scratch-take numbers now; the produce skill refits them to the locked take. A clip made earlier absorbs only what `in` can give up, a fraction of a second.
- **Write a `REENACTMENT_PROMPTS.md`** beside the episode for whoever generates the clips (the remake's is the model; its `tools/make_prompts_md.py` writes it from `episode.py`): per clip, the keyframe prompt, motion prompt, negative, references, per-tool settings and a review checklist.
- **A Blender reenactment** (rendered by `pipeline/blender_reenact.py` from the cast's 3D models, timed to the take's own words; `docs/BLENDER_REENACTMENTS.md`, section 2) fits a theory one of its templates stages: `heist` (a subject dead still, then one rigid glide across a laser grid, cut mid-glide) or `action` (Lorraine rocks on one to three words, tips on the punch word and drops a step in front of a fireball). Write the shot with its own key and a `"blender"` dict; the AI route's prompts can stay beside it:
  - the shot: `"clip": "rx_<name>_bl"` (never an AI clip's key in `CLIPS`), `"in": 0.0`, `"speed": 1.0`, a `"dur"` (required), `"kb": ((0.5, 0.5, 1.0), (0.5, 0.5, 1.0))`, the same label, stamp, cue and `pre`, and `"fallback"` views starting with `V("rx_<name>_bl_key", (0.5, 0.5, 1.0), (0.5, 0.5, 1.0))` (frame 0, written by `--keyframe`);
  - `"blender": {"template", "subject", "props", "move_on", "camera", "options"}`, plus `tip_on`/`land_on` for `action` and `flare_on` for `heist`. The beats name words of this shot's own line: `"move"`, `"goose#2"` (the second one), `["one", "goose"]` (one rock each), or `{"word": "dared", "edge": "end", "offset": 0.26}` for a landing in the silence after a word. Add `move_at`/`tip_at`/`land_at` seconds from the scratch take as the fallback. The remake's two shots are the model;
  - the same rules hold, and the tool checks them: stillness first (the move 1.0 s or more in), the punch word triggers the drop (within 0.1 s), the landing 0.25 s or more after its word and the cut 0.3-1.0 s after the landing, nothing in the AI tag's zone, the cut-back still framed like the clip's first frame. The subject is one ornament from the cast (never Deb: canon never shows how she was moved), across the frame, never along the lens axis; Lorraine stays three-quarter, beak to frame left. Options are per template (the guide's section 5); an unknown key is an error;
  - the label stays `REENACTMENT · AI` (D4), and the subject needs a 3D model in `models/` before the clip can ship (a proxy stand-in renders until then; list the models the episode needs in the hand-off).

## Voices and audio tags

The final voices are Eleven v4 designed voices; Kokoro is the scratch voice every episode builds on first (SERIES.md "Final voices"). Write for both.

- **Untagged is the default.** An audio tag goes only on a punchline or button line where the delivery makes the joke (the denial, the "hon" that turns into "detective"); setups and plants are read straight.
- **At most one tag per line, at its start, and at most one tagged line per shot.** The narrator gets at most one tagged line per episode (`[quietly]` or `[gravely]`, usually none); a one-off register such as NARRATOR (TRAILER) is its own speaker and counts separately.
- **Tags go only in the spoken text,** `L()`'s third argument, never in the caption: `L("GARRISON", "I was facing the other way.", "[too quickly] I was facing the other way.")`. The build stops if a caption would show a tag. Kokoro leaves tags out, so the scratch build is unchanged.
- **Only words from the character's approved list** in `docs/AUDIO_ELEVENLABS_V4.md` (Garrison `[too quickly]`, `[with contempt]`, `[flatly]`…; Lorraine `[unbothered]`, `[sweetly]`, `[coolly]`…; the chime `[hushed]`…). A new tag stays only if it wins a blind pick against the untagged take.
- **Never** a laughter tag (the moment a witness laughs, the show admits the joke), a sound-effect or ambience tag (sound goes in `sfx`), an accent tag, shouting or singing, or SSML `<break>`. Pauses come from `P()` between lines and from punctuation inside one ("They just. Stand there.").
- **Until the house-style lint is built into `build_audio.py`,** check these rules by hand before handing the episode over.
- **Name the human fallback.** In `HUMAN_TAKES`, list the 3–5 lines most likely to need a human take if no v4 take lands them in 3 tries (none of them narrator lines, so the narrator never has to be re-recorded for consistency), each with one line of direction; `script_md.py` stars them in `SCRIPT.md`.

## Stills

Reuse before generating. `shows/nobody-moves/stills/` is the series library, available to every episode by key:
- `garrison`: the gnome at dusk.
- `porch`: the birdbath close-up, with the porch and chime behind.
- `holes`: the two holes at dawn.
- `yard_before` / `yard_after`: the night yard, with Deb in place and moved.
- `yard_gone`: doorbell frame 428 on, `yard_after` with Lorraine gone from the porch step (derived by `episodes/ep03_the_goose/make_stills.py`). Add Ray's light with `lit=`.
- `ray_night`: `ray` at night with his solar light on (derived by `episodes/ep04_only_when_its_sunny/make_stills.py`), the stand-in for a generated `ray_lit`.

The library also has `aerial`, `lorraine` (and `lorraine_bee`, `lorraine_easter`, `lorraine_fitting`), `chime`, `basin_counsel`, `ray`, `ray_lit`, `ray_sun`, `deb`, `cork`, and the 3D reference sheets `ref3d_*` once they exist; SERIES.md lists every still.

Stills specific to one episode go in `episodes/<ep>/stills/` (a reenactment's keyframe `rx_<name>_key` too). A derived clue frame that later episodes replay or build on goes in the library, `stills/`, because a render only looks in its own episode's `stills/` and the library. That's why `yard_gone` is there. A later episode's `make_stills.py` reads the latest frame from `stills/` (per the doorbell table in SERIES.md) and writes its new frame there too. Use numpy and PIL only; SciPy and OpenCV aren't installed.

**Brightness.** Reality stills should average about 80/255 or more per shot; a near-black hold only when the darkness is the joke. Lift a dark library still for one episode with `DERIVED_STILLS` (a gamma curve on the same pixels, computed at render time; the remake's `episode.py` shows the fields) instead of regenerating it, so the doorbell frames keep matching.

For each shot, list `views` best-first. Put the ideal new still first and a crop of an existing still as the fallback, so the episode builds before the user has generated anything. Examples:
- a long-lens crop: `"longlens"` look on `yard_before` at about (0.744, 0.245), zoom 3 or more for Lorraine;
- the anonymous-source crop: `"anon"` look on `porch` at about (0.86, 0.13), zoom 3.

For every new still the episode wants, add an entry to the episode's `STILLS` dict: `key -> full image prompt`. End every reality prompt with the "Image style" block from SERIES.md, so it matches the set: the same house, a 9:16 frame, a teal-and-amber grade, exposed for a phone, no text. End every reenactment keyframe with SERIES.md's still suffix instead. Those prompts are what you give the user to generate.

## Writing the file

- Copy `references/episode-template.py` to `episodes/<epNN_slug>/episode.py`. Keep the shot ids short and unique; they become the recording names (`<shot>_<n>`).
- Put spoken numbers and abbreviations in the third argument of `L(...)` for TTS: `L("NARRATOR", "At 3:12 AM", "At three twelve AM")`. The caption shows the first text; the voice says the second. Write abbreviations without periods (`AM`, `PM`, `TV`, not `A.M.`): the pronunciation engine reads each period as a sentence break, so "A.M." comes out as two letters with a 0.18 s pause between them, while "AM" is read as one word.
- **New speaker:** add them to `cast.py` so they keep that voice for the rest of the series. For a one-off voice, add a local `CAST` instead.
  - English Kokoro presets only (`af_`, `am_`, `bf_`, `bm_`). `build_audio.py` phonemizes voices starting with "a" as US English and every other voice as British English, so any other language's preset is mispronounced.
  - Pick a preset, or a `pitch`, clearly different from the rest of the cast, so viewers can tell the characters apart by voice alone.
  - Audition by building the audio (`.venv/bin/python pipeline/build_audio.py episodes/<ep>`). Clips are cached by text and settings, so only the changed character's lines re-voice.
  - Never change an entry once an episode that uses it is published. Every episode re-voices that character on its next build, and posted episodes won't match.
  - A final v4 voice is designed, never cloned or modelled on a real person (`docs/AUDIO_ELEVENLABS_V4.md`, "Casting"); that's the produce skill's job.
- Leave coordinates approximate while writing. The produce skill places them exactly with `pipeline/grid.py`.
- **Hand-written notes go in the episode's `NOTES.md`,** never in `SCRIPT.md`: `script_md.py` rewrites `SCRIPT.md` on every build (and links `NOTES.md` from it). Put the pace numbers and the trim list, the canon checks, the recording direction and any review log there.

## Remakes

A remake (`episodes/epNNr_<slug>/`) is a new standalone video of an earlier episode in the current format, for first-time viewers; the published original stays up and Seasons 1 and 2 are never re-cut. Keep the same night, the same frames and the same hidden change (never spoiled in text), and keep every plant that later episodes call back to, word for word where they quote it. A remake only uses what existed by its episode (no Dale before Ep. 6, no speaking Deb before Ep. 7). Add it under "Remakes" in SERIES.md's roadmap, with how its test decides the pin.

## Confessionals

A Confessional is a 15–25 s short posted between episodes: one ornament airing one grudge, ending on "Episode 1 is pinned." (SERIES.md; while a remake's test runs, that line points at whichever Episode 1 holds the pin). Build it with the pipeline, like an episode. This route was tested end to end with a 19 s Garrison Confessional: it built, passed mixcheck 5/5 and rendered.

The rules above apply, except the clue, the recap and the runtime. It may have one reenactment of 5 s or less; in a 15–25 s short that is always over the main episode's 20% share, so `build_audio.py` checks a Confessional (an `EPISODE` starting "CONFESSIONAL", or a runtime under 30 s) against this rule instead and warns on a second reenactment or one over 5 s.

- **Folder:** `episodes/epNNc_<slug>/`, numbered after the episode it follows (e.g. `episodes/ep03c_garrison_hat`). It sorts right after that episode, and every `episodes/ep*` pattern still matches it.
- **Runtime:** 15–25 s. Its job is to send viewers to Episode 1. The test ran 19.0 s: hook 4.3, title 2.6, grudge 4.9, punchline 3.6, end card 3.6.
- **Module fields:**
  - `TITLE = "NOBODY MOVES"`.
  - `EPISODE = "CONFESSIONAL: GARRISON"`. Required: `script_md.py` splits it at the colon for the SCRIPT.md heading (`Confessional: "Garrison"`); without a colon the heading repeats the whole string. The title card shows it as written.
  - `NEXT_UP = "EPISODE 1 IS PINNED"`. Required: the end card draws it, and it fits easily. The card always adds "Follow the case." and the AI disclaimer.
  - No `ANSWER`, since there's no clue. `STILLS` only if you want a new still. Both are optional.
- **Shots:**
  1. Hook: a `still` close-up with the grudge's setup line and a `lower_third` (line 3 can read "Confessional").
  2. Optional `title` card with `"sfx": ["sting"]`. The score starts at the first shot with a `sting`; with no title card it runs from the first frame, under the hook.
  3. One or two `still` shots that escalate the grudge from the character's one mechanism.
  4. The punchline shot, marked `"climax": True`. With no doorbell and no mark, the score builds to the end card and peaks after the joke.
  5. `{"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"]}`.

  No doorbell, question card or board. One library still at two or three framings is enough (the test used `garrison` only).
- **Build** from `shows/nobody-moves`, with the produce skill's checks:
  ```bash
  .venv/bin/python pipeline/build_audio.py episodes/epNNc_<slug> --stems
  .venv/bin/python pipeline/mixcheck.py episodes/epNNc_<slug>
  .venv/bin/python pipeline/render.py episodes/epNNc_<slug> --contact
  ./make_episode.sh episodes/epNNc_<slug>          # about 2.5 min for 19 s
  ```
  At this length the master is already under 29 MB (23 MB in the test), and `deliver.py` fills its whole 29 MB budget, so the TikTok copy comes out bigger (28.6 MB). Either can be sent.
- **CapCut instead:** if the user wants to cut it by hand, export the sound kit (`nobody-moves-sound-design` recipe f) and give them the stills. `cinematic-sound-designer` (SFX cues from a transcript) and `capcut_video_assembler` exist in this repo for edits made outside the pipeline. Don't use them on a pipeline-built Confessional: the next `build_audio.py` run regenerates all its audio, so an outside SFX stem is thrown away.
- **Continuity:** a Confessional plants no clue. Update the ledger only if the grudge starts a running gag.

## Update continuity

In `SERIES.md`:
- mark the previous clue as paid off;
- add the new clue to the ledger;
- add each reenactment to the "Reenactments (never in the ledger)" table: the theory, the night and frames it sits between, what it shows, what it keeps out of shot, and the denial line;
- mark the roadmap entry as written;
- adjust later roadmap entries if the story moved.

A future episode's writer only knows what this file says.

## Report back

Tell the user, briefly:
- the episode's beats in plain language, with when the comment question and the first reenactment land;
- the new clue and where it pays off, labeled as a spoiler;
- the list of new stills and clips, with their prompts (or the `REENACTMENT_PROMPTS.md` file), marked optional where a fallback exists; for a Blender reenactment, its template and beats instead, and the 3D models it needs (`models/README.md`);
- the tagged lines and the `HUMAN_TAKES` lines.

Then offer to build it, or go ahead if they asked for the video.
