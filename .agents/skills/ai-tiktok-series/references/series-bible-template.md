# <SHOW TITLE>: series bible

<!-- Template from the ai-tiktok-series skill. Fill in every section, then delete these comments.
     A future episode writer only knows what this file says, so write it for them.
     The worked example is shows/nobody-moves/SERIES.md. -->

## Premise

<!-- Two or three sentences: the known TV format you are parodying, the tiny stakes you aim it at,
     and the incident that starts season 1. NOBODY MOVES: "A prestige true-crime docuseries about
     one suburban yard, where every witness is a lawn ornament. They saw everything, and none of
     them can move. Yet on June 14th, somebody moved the flamingo." -->

**The rule:** <!-- The one visual constraint, stated as canon. Choose it to match what AI renders
     well: stills, camera moves, no lip-sync, no humans. NOBODY MOVES: "nobody moves on screen.
     Every witness is a single still, and only the camera moves." Then state the episode engine:
     how every episode ends on something viewers can comment on, and that each answer must be
     provable from what was already shown. -->

**Tone:** <!-- How straight you play it (music, narrator, graphics), and where the comedy comes
     from: the gap between the form and the stakes. -->

## The setting: <name>

<!-- One fixed set, described with the same words the image style block uses. A fixed set is
     what makes separately generated stills look like one world. -->

| Where | Who |
|---|---|
| <position on the set> | **<Name>**, <what they are> |

## Cast

The voices are defined in [`cast.py`](cast.py) and shared by every episode.

| Character | Personality and the one comic mechanism | Scratch voice |
|---|---|---|
| Narrator | <register, e.g. a serious true-crime narrator> | `<kokoro preset>` |
| **<Name>** | <Personality>. Mechanism: <the rule every joke comes from>. Catchphrase: "<line>". | `<preset>`, <pitched down / altered> |

<!-- Give each character one mechanism. Escalate it; never swap it. Lorraine is warm and evasive,
     says "hon", and insists she can't go anywhere because she's concrete. A character who doesn't
     speak yet is a promise to the audience, so say when they will. -->

## Image style

Append this to every image prompt so new stills match the existing ones:

> <Photorealistic | a named craft style>, vertical 9:16. <The set, object by object, always in the same words>. <Time of day and light>. <Lens and depth of field>, <color grade>, fine film grain. No people, no text.

<!-- "No text": the pipeline draws every caption and card, and generated text comes out garbled.
     "No people": no likeness risk, and nothing that needs lip-sync. -->

The series library lives in `stills/`: <keys>. Every episode can use it.

Stills wanted for the library (episodes use crop fallbacks until these exist):
- **`<key>`:** <what it shows>. <Which episode needs it, and by when>.

## Clue ledger (continuity)

| Ep | Planted | Status |
|---|---|---|
| 1 | <what the audience was shown or told> | shown / open / running gag / **paid off in Ep. N** (<how>) |
| 1 | **Hidden:** <the answer to the closing comment-bait> | pay off in Ep. 2 |

<!-- Log every planted clue, running gag and promise, and mark each one paid off when it is.
     A payoff has to be provable from frames already shown; otherwise the comment game feels
     rigged. -->

## <Recurring footage>: frame table

<!-- Only needed if clues live in recurring footage (NOBODY MOVES has the doorbell cam). Every
     shot of that footage must agree with this table: who has turned, what is lit, what is gone.
     Delete the section if the show has none. -->

| Frame | Time | What the frame shows | Still and fields |
|---|---|---|---|
| <n> | <hh:mm:ss> | <everything in place> | `<still key>` |

## Episode roadmap

1. **<Pilot title>** (done). <Beats>. New clue: <what it is>.
2. **<Title>.** <Beats>. Pays off Ep. 1's <clue>. New clue: <what it is>.
3. ...
N. **Finale.** <The solution>, provable from <which frames, in which episodes>. Stills it needs: <keys> (plant them early).

<!-- Write the whole season, solution included, before launch. Check every payoff against the
     real stills now. NOBODY MOVES planned "Deb has two legs; she has been standing on one since
     1994", and then the user's stills showed Deb on two legs. -->

## Between episodes

<!-- Short spin-offs of 15-25 s. NOBODY MOVES has "Confessionals": one character airs one
     grudge, and the short ends with "Episode 1 is pinned." They feed the main series without
     needing a new mystery. -->
