---
name: nobody-moves-write-episode
description: Write the next episode of NOBODY MOVES, the TikTok true-crime parody where lawn ornaments are the witnesses (Garrison the gnome, Lorraine the porch goose, Deb the flamingo, Mr. Basin the birdbath, the wind chime, Ray the solar frog). Produces a ready-to-build episode.py in shows/nobody-moves/episodes/ (a main episode or a 15-25 s Confessional), prompts for any new stills, and the continuity (clue ledger) updates. Use this whenever the user asks for a new NOBODY MOVES episode, "episode 4", "the next episode", a Confessional short, new lines or jokes for these characters, a script rewrite, or what happens next in the case, even if they don't name the show.
---

# Write a NOBODY MOVES episode

The show lives in `shows/nobody-moves/`. Writing an episode means producing a data file, `episodes/<epNN_slug>/episode.py`, which the pipeline turns into voices, a timeline and a 1080×1920 video. This skill covers the writing. To build and check the video, use the `nobody-moves-produce-episode` skill.

## Read first

1. `SERIES.md`: the premise, the one rule, the cast and their running gags, the yard layout, the **clue ledger** and the **roadmap**. This is the source of truth for continuity.
2. The previous episode's `episode.py` and `SCRIPT.md`. Match the format, and pick up its cliffhanger: its `ANSWER` is what the audience was asked to spot.
3. `cast.py`, for who has a voice. `README.md` "episode.py reference", for the shot kinds and fields.
4. `references/episode-template.py` in this skill: an annotated skeleton with every shot kind.

## What makes an episode work

These rules come from how the pilot was designed and what TikTok rewards. Each one says why.

- **Hook in the first two seconds.** Open on a character's line over a tight close-up, never on a title. Scrollers decide in about a second, and a gnome saying something absurd in deadpan stops the thumb.
- **Answer last episode's clue early, within about 25 seconds.** Commenters who solved it get paid off, and people who missed it get the recap. That's what turns one-off viewers into followers.
- **Plant a new clue in a doorbell-cam frame at the end.** It must be *fair*: visible on a rewatch at phone size, and not obvious on first view. Supported mechanisms:
  - `alter_box`: mirror a region, so something has turned around.
  - `alter_glow`: light up a point, so something switched on.
  - different `frame_a`/`frame_b` stills: something appears, disappears or moves. Derive frame B from the latest library frame with a pixel edit in a `make_stills.py` beside the episode, and save it in the library (see Stills). Episode 3's removes Lorraine from the porch step to make `yard_gone`. Two separately generated images never match, so a generated frame B would change everything at once.

  Every doorbell frame of the night must agree with the doorbell table in SERIES.md: who has turned, what is lit, what is gone. Carry lights that are already on into later frames with `lit=[(x, y, r)]`. Write the answer in `ANSWER`, in the SERIES.md ledger (including which episode pays it off), and add the new frame to the table.
- **Runtime 60–90 seconds** (a Confessional is 15–25 s; see Confessionals). TikTok's Creator Rewards needs 60 seconds or more; past about 90, completion drops. After building the audio, the shot table prints the exact runtime; trim lines rather than speeding up voices.
- **Nobody moves.** Every witness is one still with a slow camera move. Never write action that needs animation. The comedy comes from the gap between prestige true-crime form and stakes no bigger than a flamingo three feet to the left.
- **Captions carry the comedy.** Most people watch muted, so every joke has to read as text. Keep lines short, one idea each, and put the punchline last. Use a `P(...)` pause before a punchline; the silence is the joke's timing.
- **Each character has one mechanism; escalate it, don't swap it.** Lorraine is warm and evasive ("hon"; turning around isn't "going anywhere"). Garrison is defensive and "was facing the other way." The chime only talks when it's windy. Mr. Basin is his own lawyer. Ray only talks after a full day of sun. New jokes should come out of these rules.
- **Silence is a sound cue.** The score builds toward the doorbell by itself, and the risers, whooshes and hits are automatic. Your one lever is `"music": "out"` on a shot, which cuts the score for it. Use it once or twice an episode, right before a punchline or a reveal (Episode 2: "The wind stopped."; Episode 3's Exhibit A reveal). The drop is what makes the next beat land; used everywhere, it stops meaning anything. It cuts only the score bed:
  - never put it on a shot with `sting_soft`: the swell keeps playing, it counts as score, and mixcheck's silence check fails;
  - the shot's own `sfx` still sound, so give it none if you want real silence;
  - not right after a sting's tail, which would still be ringing through the drop.

  `nobody-moves-sound-design` recipe (e) verifies the beat with `pipeline/mixcheck.py` (the music-out row must read silent). An episode that doesn't end on a doorbell needs `"climax": True` on its peak shot instead (see Confessionals).
- **End card.** Set `NEXT_UP` to the next roadmap title, so the audience knows there's more.

## Stills

Reuse before generating. `shows/nobody-moves/stills/` is the series library, available to every episode by key:
- `garrison`: the gnome at dusk.
- `porch`: the birdbath close-up, with the porch and chime behind.
- `holes`: the two holes at dawn.
- `yard_before` / `yard_after`: the night yard, with Deb in place and moved.
- `yard_gone`: doorbell frame 428 on, `yard_after` with Lorraine gone from the porch step (derived by `episodes/ep03_the_goose/make_stills.py`). Add Ray's light with `lit=`.

Stills specific to one episode go in `episodes/<ep>/stills/`. A derived clue frame that later episodes replay or build on goes in the library, `stills/`, because a render only looks in its own episode's `stills/` and the library. That's why `yard_gone` is there. A later episode's `make_stills.py` reads the latest frame from `stills/` (per the doorbell table in SERIES.md) and writes its new frame there too. Use numpy and PIL only; SciPy and OpenCV aren't installed.

For each shot, list `views` best-first. Put the ideal new still first and a crop of an existing still as the fallback, so the episode builds before the user has generated anything. Examples:
- a long-lens crop: `"longlens"` look on `yard_before` at about (0.744, 0.245), zoom 3 or more for Lorraine;
- the anonymous-source crop: `"anon"` look on `porch` at about (0.86, 0.13), zoom 3.

For every new still the episode wants, add an entry to the episode's `STILLS` dict: `key -> full image prompt`. End every prompt with the style block from SERIES.md, so it matches the set: the same house, a 9:16 frame, a teal-and-amber grade, no text. Those prompts are what you give the user to generate.

## Writing the file

- Copy `references/episode-template.py` to `episodes/<epNN_slug>/episode.py`. Keep the shot ids short and unique; they become the recording names (`<shot>_<n>`).
- Put spoken numbers and abbreviations in the third argument of `L(...)` for TTS: `L("NARRATOR", "At 3:12 AM", "At three twelve A.M.")`. The caption shows the first text; the voice says the second.
- **New speaker:** add them to `cast.py` so they keep that voice for the rest of the series. For a one-off voice, add a local `CAST` instead.
  - English Kokoro presets only (`af_`, `am_`, `bf_`, `bm_`). `build_audio.py` phonemizes voices starting with "a" as US English and every other voice as British English, so any other language's preset is mispronounced.
  - Pick a preset, or a `pitch`, clearly different from the rest of the cast, so viewers can tell the characters apart by voice alone.
  - Audition by building the audio (`.venv/bin/python pipeline/build_audio.py episodes/<ep>`). Clips are cached by text and settings, so only the changed character's lines re-voice.
  - Never change an entry once an episode that uses it is published. Every episode re-voices that character on its next build, and posted episodes won't match.
  - Ray first speaks in Ep. 4. His suggested entry is commented out in `cast.py`; uncomment it (and tune it) then.
- Leave coordinates approximate while writing. The produce skill places them exactly with `pipeline/grid.py`.

## Confessionals

A Confessional is a 15–25 s short posted between episodes: one ornament airing one grudge, ending on "Episode 1 is pinned." (SERIES.md). Build it with the pipeline, like an episode. This route was tested end to end with a 19 s Garrison Confessional: it built, passed mixcheck 5/5 and rendered.

The rules above apply, except the clue, the recap and the runtime.

- **Folder:** `episodes/epNNc_<slug>/`, numbered after the episode it follows (e.g. `episodes/ep03c_garrison_hat`). It sorts right after that episode, and every `episodes/ep*` pattern still matches it.
- **Runtime:** 15–25 s. The 60–90 s rule exists for Creator Rewards on main episodes; a Confessional's job is to send viewers to Episode 1. The test ran 19.0 s: hook 4.3, title 2.6, grudge 4.9, punchline 3.6, end card 3.6.
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
  .venv/bin/python pipeline/build_audio.py episodes/ep03c_<slug> --stems
  .venv/bin/python pipeline/mixcheck.py episodes/ep03c_<slug>
  .venv/bin/python pipeline/render.py episodes/ep03c_<slug> --contact
  ./make_episode.sh episodes/ep03c_<slug>          # about 2.5 min for 19 s
  ```
  At this length the master is already under 29 MB (23 MB in the test), and `deliver.py` fills its whole 29 MB budget, so the TikTok copy comes out bigger (28.6 MB). Either can be sent.
- **CapCut instead:** if the user wants to cut it by hand, export the sound kit (`nobody-moves-sound-design` recipe f) and give them the stills. `cinematic-sound-designer` (SFX cues from a transcript) and `capcut_video_assembler` exist in this repo for edits made outside the pipeline. Don't use them on a pipeline-built Confessional: the next `build_audio.py` run regenerates all its audio, so an outside SFX stem is thrown away.
- **Continuity:** a Confessional plants no clue. Update the ledger only if the grudge starts a running gag.

## Update continuity

In `SERIES.md`:
- mark the previous clue as paid off;
- add the new clue to the ledger;
- mark the roadmap entry as written;
- adjust later roadmap entries if the story moved.

A future episode's writer only knows what this file says.

## Report back

Tell the user, briefly:
- the episode's beats in plain language;
- the new clue and where it pays off, labeled as a spoiler;
- the list of new stills, with their prompts, marked optional where a fallback exists.

Then offer to build it, or go ahead if they asked for the video.
