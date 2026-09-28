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
| Side yard, out of the doorbell cam's view | **Dale**, the inflatable Christmas snowman nobody took down (from Ep. 6) |

## Cast

The voices are defined in [`cast.py`](cast.py) and shared by every episode.

| Character | Personality | Scratch voice |
|---|---|---|
| Narrator | A serious true-crime narrator | `bm_george` |
| **Garrison** | Gruff and defensive. "Thirty-one years on the lawn." Says he was facing the other way. | `am_fenrir`, pitched down |
| **Deb** | Plastic pink flamingo, unharmed. "Condition: unharmed. Position: wrong." Silent for six episodes; her first line, in Ep. 7: "It's good to be home." | `bf_isabella` (from Ep. 7) |
| **Lorraine** | Warm, unbothered, calls everyone "hon". Insists she can't go anywhere because she's concrete. Her outfit is "seasonal", and it changes between cuts ("I don't pick them"). When cornered, "hon" becomes "detective". | `af_bella` |
| **Mr. Basin** | Declines to comment. Represents himself ("My client has no comment"). Has never lost a case, and has never had one. | `bm_lewis`, pitched down (from Ep. 2) |
| **The wind chime** | Anonymous source, voice altered. Only talks when it's windy. | `af_nicole`, disguised |
| **Ray** | Solar frog. Can only talk after a full day of sun, and only remembers back to his last full charge. Cheerful once lit. It was cloudy for eleven days after the interview request; on day 12 he lit up (Ep. 4). | `am_puck`, pitched up (from Ep. 4) |
| **Dale** | Inflatable Christmas snowman, still up in June. On a timer: up at 5 PM, flat at 11. Slow, deflated, unbothered. Whatever he's accused of, being flat is his answer ("I don't have hands." "I barely have a shape."). | `am_michael`, slow and slightly low (from Ep. 6) |

## Image style

Append this to every image prompt so new stills match the existing ones:

> Photorealistic, vertical 9:16. The same suburban house: grey vinyl siding, white porch railing and posts, black front door, brass lantern sconce, silver tubular wind chime, hostas and an echinacea flower bed. Dusk, blue hour or night. Shallow depth of field, muted teal-and-amber grade, fine film grain. No people, no text.

The series library lives in `stills/`: `garrison`, `porch`, `holes`, `yard_before`, `yard_after`, `aerial` (the cul-de-sac from above, behind every title card), `lorraine` (her interview close-up), `chime`, `basin_counsel` (Mr. Basin with his briefcase), `ray` (under grey skies), `ray_lit` (Ray at night with his solar light on) and `ray_sun` (Ray in the first sun in twelve days), `lorraine_bee` and `lorraine_easter` (the `lorraine` close-up in two of her outfits), `cork` (the evidence board), `snowman_flat` and `timer` (Dale and his timer, Ep. 6), `deb` (Deb's interview close-up, Ep. 7), and the derived doorbell frames `yard_gone` (frame 428 on), `yard_turned` (frame 431 on, Garrison mirrored) and `yard_back` (frame 436, Lorraine back on the step), both derived by `episodes/ep05_saturday/make_stills.py`. `ray_night` (`ray` relit at night by `episodes/ep04_only_when_its_sunny/make_stills.py`) is kept as the deterministic fallback behind `ray_lit`. Every episode can use all of it.

Stills still wanted:
- (done) Ep. 6: `snowman_flat`, Dale deflated in a heap on the side-yard grass; and `timer`, the mechanical outdoor timer with one lone pin pushed in. The prompts are in the episode's `STILLS`. Both are generated and in the library (GPT Image 2.5, 2026-09-27).
- A new Lorraine outfit is an edit of `lorraine` with only the outfit changed, so every version keeps the same framing and cuts cleanly.

## Clue ledger (continuity)

| Ep | Planted | Status |
|---|---|---|
| 1 | Deb was moved three feet left at **03:12:00 on 06/14**, captured by the No. 5 doorbell cam (frames 417 to 418). | shown |
| 1 | **Hidden:** in frame 418, **Lorraine has turned around**. | **paid off in Ep. 2** (replay with a push-in on the porch; her defense: "Turning around isn't going anywhere. It's rotating.") |
| 1 | Garrison says he "was facing the other way." | repeated in Ep. 2 ("He would like that on the record"); in Ep. 4's frame 431 it becomes literal: he turned away from Deb at 03:12:21 |
| 1 | The wind chime: "I only talk when it's windy. And that night? It was very windy." | open |
| 1 | EXHIBIT B shows **two drag tracks** in the grass leading from the holes. | **paid off in Ep. 7**: they lead *to* the holes. The Mower dragged Deb three feet right on Saturday morning; the holes were one day old |
| 1 | Ray the solar frog is visible at the edge of the lawn in the doorbell cam. | see Ep. 2 |
| 2 | Mr. Basin is his own lawyer: "My client has no comment." He has never had a case. | running gag |
| 2 | The wind chime starts to say what it saw ("At 3:12, the flamingo was—"), then the wind stops. | **finished in Ep. 7**: "…put back." |
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
| 5 | **Hidden:** in frame 436 (03:12:29), **Lorraine is back on the porch step.** The step is empty in 435, and has been since 428 (03:12:16). She was gone thirteen seconds. Garrison is still turned away in both. | **paid off in Ep. 6** (replay: "SHE CAME BACK."). Her defense: "They had my size, hon." |
| 6 | **Dale**, the inflatable snowman in the side yard, nobody took down after Christmas. It's June. Alibi: on a timer, up at 5 PM, flat at 11, so flat at 3:12. "An airtight alibi." "Nothing about me is airtight." | running gag: being flat is his answer to everything |
| 6 | EXHIBIT C: his mechanical timer has one extra pin pushed in, **3:00 to 3:15 AM**. At 3:12, Dale was eight feet tall, the tallest witness in the yard. He didn't set it: "I don't have hands." | open: **who set the timer?** Somebody was in this yard; ties to the Mower and to whoever dresses the goose. What Dale saw from eight feet up is also open |
| 6 | Mr. Basin claims Dale as a client. "He isn't your client." "Then he has no counsel. And no comment." | running gag |
| 6 | **Hidden:** in frame 530 (03:15:00), the moment the timer clicks off, **the window beside the porch of No. 7 lights up.** It's dark in 529 and in every earlier frame. Somebody inside No. 7 is awake. | **paid off in Ep. 7** (replay: "SOMEBODY WAS AWAKE."): the person who puts the yard back went inside at 3:15 |
| 7 | **The solution.** Nobody moved Deb: at 3:12 somebody put her back where she'd stood since 1994, by the light of Dale on his timer ("I'm not a witness. I'm the lighting."). Lorraine's fitting took thirteen seconds ("They know my size"); Garrison was put back facing the street ("The way I like it"). The person is never seen and never named. | solved; the person stays offscreen |
| 7 | Mr. Basin: "Case dismissed." "There is no judge." "I dismissed it." His record is now 1–0. | running gag |
| 7 | **Hidden:** one week later, 06/21 at 03:12:00, **frame 418 again: Deb faces the other way** (mirrored). She faces left in 417. Somebody is in the yard again, on a Saturday night. | unrevealed; Season 2 |

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
| 529 | 03:14:58 | As 436 | `yard_back` + `lit=[Ray]` |
| 530 | 03:15:00 | **The window beside the porch of No. 7 is lit** (the snowman's timer has just clicked off) | `yard_back` + `lit=[Ray]` + `alter_glow` on the window, `(0.685, 0.078, 0.022)`. Later frames carry it as `lit` |

**Night of June 20–21 (Ep. 7's cliffhanger).** Frame numbers restart each night. The yard is as it was left at 3:15 on the 14th; Ray is unlit and the window is dark.

| Frame | Time | What the frame shows | Still and fields |
|---|---|---|---|
| 417 | 03:11:59 | Everything as left on the 14th | `yard_back`, `date="06/21/2026"` |
| 418 | 03:12:00 | **Deb faces the other way** | `yard_back` + `alter_box` on Deb, `(0.262, 0.44, 0.478, 0.612)` |

Ray's light in `yard_after` is `(0.183, 0.768, 0.02)`. For a later frame that changes something else, derive a new still from the latest one with a pixel edit, as Ep. 3 does, and save it in `stills/`, where every episode can replay it. Two separately generated images never match.

## Episode roadmap

1. **Three Feet** (done). Deb has moved. The witnesses are introduced. Something else moved in frame 418.
2. **I Was Right Here** (written). Every witness gives the same alibi. The frame-418 replay: Lorraine turned around, and she argues that rotating isn't moving. Mr. Basin represents himself. The wind chime almost talks. New clue: in frame 423, Ray is lit.
3. **The Goose** (written). Lorraine swears she wore the bumblebee costume that night; after the next cut she's in an Easter dress, and Exhibit A shows her in nothing: "I was between outfits." "I don't pick them, detective." Pays off Ep. 2 (Ray was awake; it's been cloudy for nine days). New clue: in frame 428 the porch step is empty.
4. **Only When It's Sunny** (written). Pays off Ep. 3 (frame 428: "LORRAINE LEFT."). Ray, the one witness awake at 3:12, can only talk after a full day of sun: day ten, cloudy; day eleven, cloudier. Mr. Basin appoints himself the frog's counsel. On day 12 Ray lights up: "I don't remember." He only remembers back to his last full charge. New clue: in frame 431 Garrison has turned around.
5. **Saturday** (written). Pays off Ep. 4 (frame 431: "GARRISON TURNED AWAY."), and his defense opens the episode out: he turned toward the street, because June 13th was a Saturday. The Mower is reenacted as a shadow crossing the lawn — eleven minutes, and nobody is put back facing the same way. Lorraine on where she went: "I was at a fitting, hon." It's Saturday. Who dresses her is "a very personal question, detective." New clue: in frame 436 Lorraine is back, after thirteen seconds.
6. **The Inflatable** (written). Pays off Ep. 5 (frame 436: "SHE CAME BACK." "They had my size, hon."). Dale, the inflatable snowman nobody took down after Christmas, has an airtight alibi: flat from 11 to 5 on his timer. "Nothing about me is airtight." Then his timer turns up with one extra pin, 3:00 to 3:15 AM: at 3:12 he was eight feet tall. He didn't set it; he doesn't have hands. Somebody was in this yard. New clue: in frame 530 the window beside the porch lights up.
7. **The Finale** (written). Pays off Ep. 6 (frame 530: "SOMEBODY WAS AWAKE."). Ep. 1's EXHIBIT B, reread: the drag tracks lead *to* the holes. The Mower dragged Deb three feet right on Saturday morning, and at 3:12 somebody put her back, lit by Dale. The chime finishes its sentence ("…put back."), Mr. Basin dismisses the case, and Deb speaks for the first time: "It's good to be home." New clue: a week later, frame 418 again, Deb faces the other way. The one-leg reveal was dropped: `deb` (Ep. 7) shows her on two legs.
8. **Season 2.** Open on the 06/21 frame 418 (Deb turned around). The person who puts the yard back is still unseen; keep it that way.

Between episodes, post 15–25 second **Confessionals**: one ornament airing one grudge, ending with "Episode 1 is pinned."

### Confessionals (written)

Each is a folder under `episodes/`, numbered after the episode it follows, and builds like an episode. None plants a clue.

| Folder | Post after | Grudge | Continuity |
|---|---|---|---|
| `ep01c_deb_consent` | Ep. 1 | Deb never speaks, so the narrator asks for her and reads each silence as a yes: "Can we delete Episode 1?" … "Didn't think so." | Deb has still never spoken. Name card: "Consent: implied" |
| `ep02c_chime_anonymous` | Ep. 2 | The anonymous source was promised nobody would know it was the chime. "They altered my voice. Then they added wind chimes." "I am not a wind—" and the wind stops | The chime's Ep. 2 sentence stays unfinished |
| `ep04c_ray_hat` | Ep. 4 | Ray reports Garrison's hat for stealing his sun at sunset. He remembers only today's sunset: "Worst one of my life!" | Ray's memory resets at each full charge |
| `ep04c_basin_frog` | Ep. 4 | Mr. Basin, the frog's self-appointed counsel: "The frog talked. Without his attorney present." "He represented himself. … Amateur." | Mr. Basin's record: 0–0 |
| `ep05c_garrison_doorbell` | Ep. 5 | Garrison calls the No. 5 doorbell nosy and knows its specs by heart ("a picture every 1.6 seconds"), yet "was facing the other way." | Name card "Facing: the doorbell"; the "Facing:" line so far is "the other way" (Eps. 2, 4), "the street" (Ep. 5), "the doorbell" (5c). Never write it as Garrison turning himself: the open Mower thread says a person handles this yard |
| `ep05c_lorraine_changed` | Ep. 5 | "Everyone says I've changed, hon." Jump cuts through her outfits: "I haven't changed. I've been changed." "Twelve outfits since March." | Twelve outfits since March (Garrison said eleven in Ep. 3; the fitting makes twelve) |
