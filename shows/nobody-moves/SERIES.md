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
| **Lorraine** | Warm, unbothered, calls everyone "hon". Insists she can't go anywhere because she's concrete. Her outfit is "seasonal", and it changes between cuts ("I don't pick them"). When cornered, "hon" becomes "detective". | `af_bella` |
| **Mr. Basin** | Declines to comment. Represents himself ("My client has no comment"). Has never lost a case, and has never had one. | `bm_lewis`, pitched down (from Ep. 2) |
| **The wind chime** | Anonymous source, voice altered. Only talks when it's windy. | `af_nicole`, disguised |
| **Ray** | Solar frog. Can only talk after a full day of sun, and only remembers back to his last full charge. Cheerful once lit. It was cloudy for eleven days after the interview request; on day 12 he lit up (Ep. 4). | `am_puck`, pitched up (from Ep. 4) |

## Image style

Append this to every image prompt so new stills match the existing ones:

> Photorealistic, vertical 9:16. The same suburban house: grey vinyl siding, white porch railing and posts, black front door, brass lantern sconce, silver tubular wind chime, hostas and an echinacea flower bed. Dusk, blue hour or night. Shallow depth of field, muted teal-and-amber grade, fine film grain. No people, no text.

The series library lives in `stills/`: `garrison`, `porch`, `holes`, `yard_before`, `yard_after`, `aerial` (the cul-de-sac from above, behind every title card), `lorraine` (her interview close-up), `chime`, `basin_counsel` (Mr. Basin with his briefcase), `ray` (under grey skies), `ray_lit` (Ray at night with his solar light on) and `ray_sun` (Ray in the first sun in twelve days), `lorraine_bee` and `lorraine_easter` (the `lorraine` close-up in two of her outfits), `cork` (the evidence board), and the derived doorbell frames `yard_gone` (frame 428 on), `yard_turned` (frame 431 on, Garrison mirrored) and `yard_back` (frame 436, Lorraine back on the step), both derived by `episodes/ep05_saturday/make_stills.py`. `ray_night` (`ray` relit at night by `episodes/ep04_only_when_its_sunny/make_stills.py`) is kept as the deterministic fallback behind `ray_lit`. Every episode can use all of it.

Stills still wanted:
- Ep. 5: `mower_shadow`, the Mower seen only as a shadow crossing the lawn in hard Saturday-morning light; and `lorraine_fitting`, the `lorraine` close-up in the outfit she comes back in. The prompts are in the episode's `STILLS`. Until then the reenactment uses a crop of `holes` and the fitting uses `lorraine_easter`.
- A new Lorraine outfit is an edit of `lorraine` with only the outfit changed, so every version keeps the same framing and cuts cleanly.

## Clue ledger (continuity)

| Ep | Planted | Status |
|---|---|---|
| 1 | Deb was moved three feet left at **03:12:00 on 06/14**, captured by the No. 5 doorbell cam (frames 417 to 418). | shown |
| 1 | **Hidden:** in frame 418, **Lorraine has turned around**. | **paid off in Ep. 2** (replay with a push-in on the porch; her defense: "Turning around isn't going anywhere. It's rotating.") |
| 1 | Garrison says he "was facing the other way." | repeated in Ep. 2 ("He would like that on the record"); in Ep. 4's frame 431 it becomes literal: he turned away from Deb at 03:12:21 |
| 1 | The wind chime: "I only talk when it's windy. And that night? It was very windy." | open |
| 1 | EXHIBIT B shows **two drag tracks** in the grass leading from the holes. | not mentioned on screen yet |
| 1 | Ray the solar frog is visible at the edge of the lawn in the doorbell cam. | see Ep. 2 |
| 2 | Mr. Basin is his own lawyer: "My client has no comment." He has never had a case. | running gag |
| 2 | The wind chime starts to say what it saw ("At 3:12, the flamingo was—"), then the wind stops. | open: it finishes the sentence the next windy night |
| 2 | **Hidden:** in frame 423 (03:12:08), **Ray the solar frog is glowing**. He only lights up after a full day of sun, so he was charged, awake and watching. | **paid off in Ep. 3** (replay: "RAY WAS AWAKE."). His testimony, Ep. 4: on day 12 he lights up and says "I don't remember." He only remembers back to his last full charge |
| 3 | Lorraine swears she wore the bumblebee that night; after the next cut she's in an Easter dress. Exhibit A (5:41 AM) shows her wearing nothing: "I was between outfits." "I don't pick them, detective." | open: **who dresses the goose?** The narrator asks if it's whoever moved Deb |
| 3 | Garrison: "Eleven outfits since March. I've had this hat since 1994." He was facing the other way for all eleven. | running gag |
| 3 | Mr. Basin objects. There is no judge. | running gag |
| 3 | **Hidden:** in frame 428 (03:12:16), **the porch step is empty: Lorraine is gone.** She's there in frame 427, a second earlier. The goose who "doesn't go anywhere" left the porch 16 seconds after Deb moved. | **confirmed in Ep. 4** (replay: "LORRAINE LEFT."). Where she went: Ep. 5 ("I was at a fitting, hon") |
| 4 | Mr. Basin appoints himself the frog's counsel: "Until the frog has counsel, the frog has no comment." "The frog has no power." | running gag |
| 4 | Ray only remembers back to his last full charge ("It was a great afternoon"). Garrison: "I've been not remembering for thirty-one years." | running gag |
| 4 | **Hidden:** in frame 431 (03:12:21), **Garrison has turned around**: mirrored, he faces away from Deb. He faces her in frame 430, a second earlier. Five seconds after Lorraine left, the gnome who "was facing the other way" turned the other way. | **paid off in Ep. 5** (replay: "GARRISON TURNED AWAY."). His defense: "I didn't turn away from Deb. I turned toward the street." |
| 5 | **The Mower**, the street's most feared event, comes on Saturdays and is only ever a shadow. June 13th was a Saturday, so it came the morning before Deb moved. Garrison: "Not once have I been put back facing the same way." | open: the Mower means a **person** handles this yard, and puts everything back wrong |
| 5 | Lorraine on where she went at 03:12:16: "I was at a fitting, hon." It's Saturday. Asked who dresses her: "That's a very personal question, detective." | open: **who dresses the goose?** now tied to Saturdays and to whoever the Mower is |
| 5 | Mr. Basin is now the goose's attorney too, retained by nobody. He objects; there is still no judge. | running gag |
| 5 | **Hidden:** in frame 436 (03:12:29), **Lorraine is back on the porch step.** The step is empty in 435, and has been since 428 (03:12:16). She was gone thirteen seconds. Garrison is still turned away in both. | unrevealed; pay off early in Ep. 6 |

## Doorbell cam: No. 5, night of June 13–14

Every doorbell shot of that night must agree with this table. Frames tick roughly every 1.6 seconds.

| Frame | Time | What the frame shows | Still and fields |
|---|---|---|---|
| 417 | 03:11:59 | Everything in place | `yard_before` |
| 418 | 03:12:00 | Deb moved three feet left; **Lorraine turned around** | `yard_after` + `alter_box` on Lorraine |
| 422 | 03:12:07 | Lorraine facing front again (nobody has noticed she turned back) | `yard_after` |
| 423 | 03:12:08 | **Ray lit**, and he stays lit from here on | `yard_after` + `alter_glow` on Ray |
| 427 | 03:12:15 | As 423 | `yard_after` + `lit=[Ray]` |
| 428 | 03:12:16 | **Lorraine gone from the porch step** | `yard_gone` (library; made by `ep03_the_goose/make_stills.py`) + `lit=[Ray]` |
| 430 | 03:12:17–20 | As 428 | `yard_gone` + `lit=[Ray]` |
| 431 | 03:12:21 | **Garrison turned around**, facing away from Deb | `yard_gone` + `lit=[Ray]` + `alter_box` on Garrison, `(0.112, 0.486, 0.215, 0.612)` |
| 435 | 03:12:25–28 | As 431: step still empty, Garrison still turned away | `yard_turned` (library) + `lit=[Ray]` |
| 436 | 03:12:29 | **Lorraine is back on the porch step**, Garrison still turned away | `yard_back` (library) + `lit=[Ray]` |

Ray's light in `yard_after` is `(0.183, 0.768, 0.02)`. For a later frame that changes something else, derive a new still from the latest one with a pixel edit, as Ep. 3 does, and save it in `stills/`, where every episode can replay it. Two separately generated images never match.

## Episode roadmap

1. **Three Feet** (done). Deb has moved. The witnesses are introduced. Something else moved in frame 418.
2. **I Was Right Here** (written). Every witness gives the same alibi. The frame-418 replay: Lorraine turned around, and she argues that rotating isn't moving. Mr. Basin represents himself. The wind chime almost talks. New clue: in frame 423, Ray is lit.
3. **The Goose** (written). Lorraine swears she wore the bumblebee costume that night; after the next cut she's in an Easter dress, and Exhibit A shows her in nothing: "I was between outfits." "I don't pick them, detective." Pays off Ep. 2 (Ray was awake; it's been cloudy for nine days). New clue: in frame 428 the porch step is empty.
4. **Only When It's Sunny** (written). Pays off Ep. 3 (frame 428: "LORRAINE LEFT."). Ray, the one witness awake at 3:12, can only talk after a full day of sun: day ten, cloudy; day eleven, cloudier. Mr. Basin appoints himself the frog's counsel. On day 12 Ray lights up: "I don't remember." He only remembers back to his last full charge. New clue: in frame 431 Garrison has turned around.
5. **Saturday** (written). Pays off Ep. 4 (frame 431: "GARRISON TURNED AWAY."), and his defense opens the episode out: he turned toward the street, because June 13th was a Saturday. The Mower is reenacted as a shadow crossing the lawn — eleven minutes, and nobody is put back facing the same way. Lorraine on where she went: "I was at a fitting, hon." It's Saturday. Who dresses her is "a very personal question, detective." New clue: in frame 436 Lorraine is back, after thirteen seconds.
6. **The Inflatable.** Pays off Ep. 5 (frame 436: Lorraine came back). The holiday inflatable nobody took down has an airtight alibi ("I was flat from 11 to 6"). Then its timer turns up, set for 3:10 AM — which is a Saturday setting, and someone sets it.
7. **Finale.** The original pitch was "Deb has two legs. She has been standing on one since 1994." The current Deb stills show her on two legs, so either rework this reveal or make one-leg Deb stills early and plant them.

Between episodes, post 15–25 second **Confessionals**: one ornament airing one grudge, ending with "Episode 1 is pinned."
