---
name: nobody-moves-write-episode
description: Write the next episode of NOBODY MOVES, the TikTok true-crime parody where lawn ornaments are the witnesses (Garrison the gnome, Lorraine the porch goose, Deb the flamingo, Mr. Basin the birdbath, the wind chime, Ray the solar frog). Produces a ready-to-build episode.py in shows/nobody-moves/episodes/, prompts for any new stills, and the continuity (clue ledger) updates. Use this whenever the user asks for a new NOBODY MOVES episode, "episode 3", "the next episode", a Confessional short, new lines or jokes for these characters, a script rewrite, or what happens next in the case, even if they don't name the show.
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
  - different `frame_a`/`frame_b` stills: something appears, disappears or moves. Derive frame B from the library still with a pixel edit in a `make_stills.py` beside the episode; Episode 3's removes Lorraine from the porch step. Two separately generated images never match, so a generated frame B would change everything at once.

  Every doorbell frame of the night must agree with the doorbell table in SERIES.md: who has turned, what is lit, what is gone. Carry lights that are already on into later frames with `lit=[(x, y, r)]`. Write the answer in `ANSWER`, in the SERIES.md ledger (including which episode pays it off), and add the new frame to the table.
- **Runtime 60–90 seconds.** TikTok's Creator Rewards needs 60 seconds or more; past about 90, completion drops. After building the audio, the shot table prints the exact runtime; trim lines rather than speeding up voices.
- **Nobody moves.** Every witness is one still with a slow camera move. Never write action that needs animation. The comedy comes from the gap between prestige true-crime form and stakes no bigger than a flamingo three feet to the left.
- **Captions carry the comedy.** Most people watch muted, so every joke has to read as text. Keep lines short, one idea each, and put the punchline last. Use a `P(...)` pause before a punchline; the silence is the joke's timing.
- **Each character has one mechanism; escalate it, don't swap it.** Lorraine is warm and evasive ("hon"; turning around isn't "going anywhere"). Garrison is defensive and "was facing the other way." The chime only talks when it's windy. Mr. Basin is his own lawyer. Ray only talks after a full day of sun. New jokes should come out of these rules.
- **Silence is a sound cue.** The score builds toward the doorbell by itself, and the risers, whooshes and hits are automatic. Your one lever is `"music": "out"` on a shot, which cuts the score for it. Use it once or twice an episode, right before a punchline or a reveal (Episode 2: "The wind stopped."; Episode 3's Exhibit A reveal). The drop is what makes the next beat land; used everywhere, it stops meaning anything. It cuts only the score: never put it on a shot with `sting_soft` (the swell keeps playing and the silence check fails), and remember the shot's own `sfx` still sound.
- **End card.** Set `NEXT_UP` to the next roadmap title, so the audience knows there's more.

## Stills

Reuse before generating. `shows/nobody-moves/stills/` is the series library, available to every episode by key:
- `garrison`: the gnome at dusk.
- `porch`: the birdbath close-up, with the porch and chime behind.
- `holes`: the two holes at dawn.
- `yard_before` / `yard_after`: the night yard, with Deb in place and moved.

Stills specific to one episode go in `episodes/<ep>/stills/`.

For each shot, list `views` best-first. Put the ideal new still first and a crop of an existing still as the fallback, so the episode builds before the user has generated anything. Examples:
- a long-lens crop: `"longlens"` look on `yard_before` at about (0.744, 0.245), zoom 3 or more for Lorraine;
- the anonymous-source crop: `"anon"` look on `porch` at about (0.86, 0.13), zoom 3.

For every new still the episode wants, add an entry to the episode's `STILLS` dict: `key -> full image prompt`. End every prompt with the style block from SERIES.md, so it matches the set: the same house, a 9:16 frame, a teal-and-amber grade, no text. Those prompts are what you give the user to generate.

## Writing the file

- Copy `references/episode-template.py` to `episodes/<epNN_slug>/episode.py`. Keep the shot ids short and unique; they become the recording names (`<shot>_<n>`).
- Put spoken numbers and abbreviations in the third argument of `L(...)` for TTS: `L("NARRATOR", "At 3:12 AM", "At three twelve A.M.")`. The caption shows the first text; the voice says the second.
- New speaker? Add them to `cast.py` so they keep that voice for the rest of the series. For a one-off voice, add a local `CAST` instead.
- Leave coordinates approximate while writing. The produce skill places them exactly with `pipeline/grid.py`.

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
