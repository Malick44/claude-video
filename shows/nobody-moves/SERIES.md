# NOBODY MOVES: series bible

## Premise

A prestige true-crime docuseries about one suburban yard, where every witness is a lawn ornament. They saw everything, and none of them can move. Yet on June 14th, somebody moved the flamingo.

**The rule:** nobody moves on screen. Every witness is a single still, and only the camera moves. Every episode ends on a doorbell-cam frame where something has changed, so viewers comment the object and the timestamp. Each finale's answer has to be provable from frames already shown.

**Tone:** played completely straight: ominous piano, a narrator taking it all very seriously, evidence photos with a camera flash. The comedy comes from the gap between that style and the stakes.

## The yard: No. 7 Birchwood Court

It's a grey-sided house with a white porch, a black front door, a brass lantern sconce, hostas, and an echinacea and hydrangea flower bed. The house sits on a cul-de-sac. The doorbell camera across the street at No. 5 sees the whole yard.

| Where | Who |
|---|---|
| Flower bed, left | **Garrison**, the garden gnome |
| Center lawn | **Deb**, the pink flamingo (the victim) |
| Right, by the hostas | **Mr. Basin**, the birdbath, six feet from Deb |
| Porch steps | **Lorraine**, the white porch goose |
| Beside the front door | **The wind chime**, the anonymous source |
| Front edge of the lawn | **Ray**, the solar frog (seen in the doorbell cam, not interviewed yet) |

## Cast

The voices are defined in [`cast.py`](cast.py) and shared by every episode.

| Character | Personality | Scratch voice |
|---|---|---|
| Narrator | A serious true-crime narrator | `bm_george` |
| **Garrison** | Gruff and defensive. "Thirty-one years on the lawn." Says he was facing the other way. | `am_fenrir`, pitched down |
| **Deb** | Plastic pink flamingo, unharmed. "Condition: unharmed. Position: wrong." Doesn't speak (yet). | none |
| **Lorraine** | Warm, unbothered, calls everyone "hon". Insists she can't go anywhere because she's concrete. Her outfit is "seasonal". | `af_bella` |
| **Mr. Basin** | Declines to comment. Represents himself ("My client has no comment"). Has never lost a case, and has never had one. | `bm_lewis`, pitched down (from Ep. 2) |
| **The wind chime** | Anonymous source, voice altered. Only talks when it's windy. | `af_nicole`, disguised |
| **Ray** | Solar frog. Can only talk after a full day of sun. | not cast yet |

## Image style

Append this to every image prompt so new stills match the existing ones:

> Photorealistic, vertical 9:16. The same suburban house: grey vinyl siding, white porch railing and posts, black front door, brass lantern sconce, silver tubular wind chime, hostas and an echinacea flower bed. Dusk, blue hour or night. Shallow depth of field, muted teal-and-amber grade, fine film grain. No people, no text.

The series library lives in `stills/`: `garrison`, `porch`, `holes`, `yard_before`, `yard_after`. Every episode can use it.

Still wanted for the library (episodes use crop fallbacks until these exist; the full prompts are in `episodes/ep02_i_was_right_here/episode.py`, `STILLS`):
- **`lorraine`:** a close-up of the goose on the porch step, beak pointing to frame-left, framed like a documentary interview at 85mm.
- **`chime`:** the wind chime backlit by the porch light, as a silhouette.
- **`aerial`** and **`cork`:** the user has generated these, but they still need to be sent as files and saved into `stills/`.

## Clue ledger (continuity)

| Ep | Planted | Status |
|---|---|---|
| 1 | Deb was moved three feet left at **03:12:00 on 06/14**, captured by the No. 5 doorbell cam (frames 417 to 418). | shown |
| 1 | **Hidden:** in frame 418, **Lorraine has turned around**. | **paid off in Ep. 2** (replay with a push-in on the porch; her defense: "Turning around isn't going anywhere. It's rotating.") |
| 1 | Garrison says he "was facing the other way." | open; repeated in Ep. 2 ("He would like that on the record") |
| 1 | The wind chime: "I only talk when it's windy. And that night? It was very windy." | open |
| 1 | EXHIBIT B shows **two drag tracks** in the grass leading from the holes. | not mentioned on screen yet |
| 1 | Ray the solar frog is visible at the edge of the lawn in the doorbell cam. | see Ep. 2 |
| 2 | Mr. Basin is his own lawyer: "My client has no comment." He has never had a case. | running gag |
| 2 | The wind chime starts to say what it saw ("At 3:12, the flamingo was—"), then the wind stops. | open: it finishes the sentence the next windy night |
| 2 | **Hidden:** in frame 423 (03:12:08), **Ray the solar frog is glowing**. He only lights up after a full day of sun, so he was charged, awake and watching. | unrevealed; pay off in Ep. 4 |

## Episode roadmap

1. **Three Feet** (done). Deb has moved. The witnesses are introduced. Something else moved in frame 418.
2. **I Was Right Here** (written). Every witness gives the same alibi. The frame-418 replay: Lorraine turned around, and she argues that rotating isn't moving. Mr. Basin represents himself. The wind chime almost talks. New clue: in frame 423, Ray is lit.
3. **The Goose.** Lorraine swears she wore the bumblebee costume that night. After the next cut she's in an Easter dress. "I don't pick them, detective."
4. **Only When It's Sunny.** The key witness is Ray, who can only talk after a full day of sun. Pays off Ep. 2's frame 423: he was lit at 3:12, so he saw it. On day 12 he lights up: "I don't remember."
5. **Saturday.** A tense reenactment of the street's most feared event, The Mower, shown only as a shadow.
6. **The Inflatable.** The holiday inflatable nobody took down has an airtight alibi ("I was flat from 11 to 6"). Then its timer turns up, set for 3:10 AM.
7. **Finale.** The original pitch was "Deb has two legs. She has been standing on one since 1994." The current Deb stills show her on two legs, so either rework this reveal or make one-leg Deb stills early and plant them.

Between episodes, post 15–25 second **Confessionals**: one ornament airing one grudge, ending with "Episode 1 is pinned."
