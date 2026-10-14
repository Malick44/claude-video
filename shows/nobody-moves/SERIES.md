# NOBODY MOVES: series bible

## Premise

A prestige true-crime docuseries about one suburban yard, where every witness is a lawn ornament. They saw everything, and none of them can move. Yet on June 14th, somebody moved the flamingo.

**The rule:** nobody moves while anyone is watching. Reality never moves: every interview, every evidence photo and every doorbell-cam frame is a single still, and only the camera moves. The one place an ornament moves is a **REENACTMENT**. It shows the narrator's dramatized theory of what might have happened, in an openly staged 3D style, with the label on screen. It is always followed by a hard cut back to the real ornament, motionless and back in its spot, denying it. Reenactments are theories and never evidence. Every episode asks an easy question early ("Who did it, gnome or goose?"), and every episode still hides one change in a doorbell-cam frame, as a bonus for viewers who rewatch and comment what changed. Each finale's answer has to be provable from reality frames already shown, never from a reenactment.

Why the rule reads this way:
- **"While anyone is watching."** The doorbell takes a picture about every 1.6 seconds, so reenactments happen in the gaps between frames, where nobody was watching. Inside the story that stays a suspicion and is never confirmed. Season 1's answer is a person, and Season 2's answer is a person bringing Deb company. Canon has never shown an ornament moving by itself, and never will.
- **The easy question comes early.** The published Episode 1 asked for comments at 1:13, after most viewers had left. Now a one-word question ("Gnome, or goose?") lands by about 10 s, and the hidden doorbell change stays as the puzzle for people who rewatch.
- **The bonus asks for a description, not a name.** When the ornament with the hidden change is also an answer to the early question (Episode 1: the goose), "goose" is a vote, not a find. The bonus call to action asks "What else changed?", and a comment counts as a find only when it says how the thing changed or where to look.
- **Proof comes from reality frames only.** No answer can depend on a reenactment.

**Tone:** played completely straight: ominous piano, a narrator taking it all very seriously, evidence photos with a camera flash. The comedy comes from the gap between that style and the stakes. The narrator plays the reenactments straight too: the tone gets louder, but it doesn't change.

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

**Final voices.** The Episode 1 remake ships with Eleven v4 voices designed from text prompts (never cloned, never a soundalike): NARRATOR, GARRISON, LORRAINE and the CHIME, with NARRATOR (TRAILER) on the narrator's own voice. Casting, the audio-tag house rules, locking takes and the rollout are in [`docs/AUDIO_ELEVENLABS_V4.md`](docs/AUDIO_ELEVENLABS_V4.md). Kokoro stays the scratch voice, and `cast.py`'s default cast stays Kokoro until the voice test (the re-voiced Garrison Confessional) decides the series default, character by character. Each designed voice's prompt is kept beside its `voice_id` in `cast.py`; add a "Final voice" column here once the voices exist.

## Image style

Append this to every image prompt so new stills match the existing ones:

> Photorealistic, vertical 9:16. The same suburban house: grey vinyl siding, white porch railing and posts, black front door, brass lantern sconce, silver tubular wind chime, hostas and an echinacea flower bed. Dusk, blue hour or night. Exposed for a phone: the subject clearly lit by the porch lantern or another practical light, readable at thumbnail size; night is deep blue, not black; no large areas of crushed black. Shallow depth of field, muted teal-and-amber grade, fine film grain. No people, no text.

**Brightness.** Episode 1 measured a mean of 50/255, with 26 of its 80 s nearly black, which reads as nothing on a phone. The working target is a mean of about 80/255 or more per shot; a near-black hold is fine only when the darkness is the joke. Existing stills are lifted deterministically (a gamma curve on the same pixels, as the Episode 1 remake's `DERIVED_STILLS` does), never regenerated, so the doorbell frames keep matching. Tune the number after the remake's test.

This prompt is for reality only. Reenactments have their own look and their own suffixes (see "Reenactments" and "3D character references").

The series library lives in `stills/`: `garrison`, `porch`, `holes`, `yard_before`, `yard_after`, `aerial` (the cul-de-sac from above, behind every title card), `lorraine` (her interview close-up), `chime`, `basin_counsel` (Mr. Basin with his briefcase), `ray` (under grey skies), `ray_lit` (Ray at night with his solar light on) and `ray_sun` (Ray in the first sun in twelve days), `lorraine_bee` and `lorraine_easter` (the `lorraine` close-up in two of her outfits), `cork` (the evidence board), `snowman_flat` and `timer` (Dale and his timer, Ep. 6), `deb` (Deb's interview close-up, Ep. 7), and the derived doorbell frames `yard_gone` (frame 428 on), `yard_turned` (frame 431 on, Garrison mirrored) and `yard_back` (frame 436, Lorraine back on the step), both derived by `episodes/ep05_saturday/make_stills.py`. `ray_night` (`ray` relit at night by `episodes/ep04_only_when_its_sunny/make_stills.py`) is kept as the deterministic fallback behind `ray_lit`. Every episode can use all of it.

Stills still wanted:
- (done) Ep. 6: `snowman_flat`, Dale deflated in a heap on the side-yard grass; and `timer`, the mechanical outdoor timer with one lone pin pushed in. The prompts are in the episode's `STILLS`. Both are generated and in the library (GPT Image 2.5, 2026-09-27).
- A new Lorraine outfit is an edit of `lorraine` with only the outfit changed, so every version keeps the same framing and cuts cleanly.
- The 3D reference sheets `ref3d_garrison`, `ref3d_deb`, `ref3d_lorraine` and the shared-scale `ref3d_lineup` (prompts in `episodes/ep01r_three_feet_reenacted/episode.py`'s `STILLS`; see "3D character references"). They go in the library because every later reenactment of these characters starts from them. The other characters' sheets wait for their first reenactment.

Reenactment clips live like stills: `clips/` is the series library (recurring reenactments) and `episodes/<ep>/clips/` holds episode-only clips; an episode clip overrides a library clip with the same key. Clip keys start with `rx_`.

## Reenactments

### What they are
A reenactment is the narrator's theory, staged the way true-crime TV stages it: an earnest but cheap 3D dramatization with slow motion, lens flares and swelling music. The ornaments finally move. Then the edit cuts back to reality, where they haven't moved. The joke is the gap between the reenactment's ambition and the real gnome's thirty-one years of standing in one spot. The narrator presents every reenactment completely straight and never admits it's absurd.

### When to use one
- **When someone states a theory that an ornament did something:** "Police have one theory." / "What if the gnome…". The theory has to make sense with no lore, like "the gnome did it" or "the goose did it". The best-performing Confessionals (Garrison's doorbell grudge, the anonymous chime) are self-contained jokes about types of people everyone recognizes; the ones that lean on lore (Ray's solar memory, Mr. Basin's record) do worst.
- **Only when the denial is ready.** Use a reenactment only if the real ornament has a short deadpan line to cut back to, and that line comes from the character's one mechanism.
- **Good places for one:** right after the early comment question, one theory per suspect ("Gnome or goose?"), or in a cold open.
- **Not for:** revealing a clue (doorbell frames are reality), a case's solution, interview lines, recapping established facts, or anything meant to say "this really happened".
- **Not from the doorbell's angle or in night vision.** That view belongs to the evidence, so the theory has to look different from it.

### Length and share
- **Each reenactment:** 3–6 s, with one action and one peak. Its length is `pre` + the narration + at least 0.5 s of action after the last word. Lock the narration take before the clip is generated: the clip's motion is timed to that take, and a clip made earlier absorbs only a fraction of a second of a longer one.
- **A main episode (under 50 s):** at most **2** reenactments, adding up to no more than about **20%** of the runtime (10 s or less in a 50 s episode).
- **A Confessional:** at most **1**, 5 s or shorter.
- **Never back to back.** A hard cut back to reality always comes between two reenactments.
- **Why the cap:** stillness is the brand. If the ornaments move a lot, the cut back stops being a punchline. Each clip is also the most expensive and least consistent asset in the episode.

### The label
- **When it shows:** `REENACTMENT · AI` is on screen from the clip's first frame to its last, and disappears on the hard cut. The label vanishing is part of the cut.
- **The AI marker:** the label reads exactly `REENACTMENT · AI` on every reenactment, so the AI disclosure is on screen whenever an ornament moves, not only on the end card. The build (`build_audio.py`) refuses any other label on a reenactment, so an escalation can't drift back into it.
- **Where and how it looks:** the renderer's tag, in the EXHIBIT tag's slot at the upper left (inside every app's safe zone), as a **red** box with white capitals in the show's tag font. Red means theory; yellow (the EXHIBIT tags) means evidence. The box is sized to its text and must end before x 930, the apps' button column. It is the only badge on a reenactment: the series' yellow corner label isn't drawn there.
- **Keep the top left clear.** The tag and its stamp cover x 64 to about 750 and y 190 to 320 of the 1080x1920 frame. No ornament top, beam or key action goes above about a quarter of the frame height on the side the ornament moves toward, or the move plays behind the AI tag (keyframe prompts give the subject's size and where its top sits, e.g. "the tip of his cap about a quarter of the way down the frame"); a background effect such as a fireball stays right of the frame's centre line.
- **The stamp:** a second line names the theory, e.g. `THEORY #1: THE GNOME`. Any escalation goes here, since the label never changes: `THEORY #2: THE GOOSE (DIRECTOR'S CUT)`. **No timestamp**, so a theory can never be read against the doorbell table.
- **How it's made:** the renderer burns the label in. It is never generated inside the 3D image, because generated text drifts and gets misspelled. A reenactment frame used as a cover or thumbnail keeps its label.
- **The disclosure widens.** On any episode with a reenactment, the end card's first line reads "Footage, reenactments and voices made with AI." whatever the voices, over "The flamingo is real.". Once reenactment frames say "· AI" and the doorbell says "NOT A REENACTMENT", a line that named only reenactments would teach viewers that unlabelled means real, and the photoreal stills and doorbell frames are AI images too. It fades in with the end card's title and stays fully legible for at least 1.8 s (the renderer fades it in with the title; `build_audio.py` refuses a card that shows it for under 1.8 s). An episode without a reenactment keeps "Reenactments dramatized with AI.", or "Reenactments and voices made with AI." when the soundtrack holds an ElevenLabs voice (a line voiced by one, or a locked v4 take; the build records which in `timeline.json`). The "Altered or synthetic content" label stays on every platform.

### The look: reality vs. reenactment
A viewer should be able to tell the two apart in one frame, at thumbnail size, with the sound off. If a reenactment frame could pass for a reality still, it's wrong.

| | Reality (photoreal stills) | Reenactment (3D) |
|---|---|---|
| Image | Photographs, made with the "Image style" prompt | Obviously computer-generated: glossy, plasticky and toy-like, like a cable-TV reenactment or a game cutscene |
| Motion | Only the camera moves (slow push-ins and drifts) | Only the ornament moves, as a rigid object (see below). The camera is locked off while it moves |
| Light | Natural dusk, blue hour or night, lit by the porch lantern | Stage lighting: hard rim lights, magenta and cyan gels, haze, god-rays, anamorphic lens flares, a bright painted twilight sky with an oversized moon, the whole set floodlit. **Bright, never murky** (mean luma 100 or more) |
| Surfaces | Weathered: chipped paint, moss, dew, film grain | Clean and too perfect, with an even shine. Each character's signature marks are kept as painted detail |
| Colour | A muted teal-and-amber grade | Saturated and high-contrast, with blown highlights |
| Set | The real yard | The same yard rebuilt as an obvious set: an over-green lawn, a painted sky, a fog machine |
| Camera | Long lens, slow push-ins, doorbell night vision | Low "hero" angles, framed like a poster, and **locked off**: a push-in on a rigid figure reads as a zoom on a still, which is what reality looks like |
| Time | Real time | Slow motion, made once, by the generator. The episode plays the take at 1.0x; slowing it again in the edit leaves the action off screen and ghosts the frames |
| Text | Captions, name cards and EXHIBIT tags, all added by the renderer | The `REENACTMENT · AI` label and its theory stamp, added by the renderer. Nothing generated: no chyron, lower third, title card or letterbox bars |
| Sound | The piano theme, crickets, wind | A trailer-style cue (see "Sound") |

### How the ornaments move
- **As rigid bodies only.** An ornament moves the way the object would if it could: it tips, drops, hops, slides, spins or levitates, as one solid piece, like an object on a hidden track. It never bends a limb, blinks, moves its mouth or changes expression, so the molded face stays deadpan even mid-leap. This also keeps the 3D characters on-model, because deformation is where AI video drifts.
- **Stillness first, then the move, on the word.** The ornament holds dead still while the narrator sets up the theory, and moves on the line's key word ("Then he made his move.", "…dared."). The cut comes mid-move or half a second after it lands. A move that starts on the first frame is background by the time the punchline arrives.
- **Across the frame, never along the lens axis.** A rigid figure coming straight at the camera only grows, which reads as a zoom. Slide it sideways, or drop it down a step, against a background that doesn't move.
- **Along its facing.** An ornament travels only the way it faces (Lorraine: the way her beak points). Image-to-video models turn a figure to face where it travels, which would break a "never turns" rule.
- **One action per clip.** A rigid statue gets one readable action in a 3–6 s clip. Background motion (haze, a fireball, a swaying chime) is fine.
- **Each character has a fixed set of moves,** listed in its reference below, so the same theory looks the same every time.
- **Nobody speaks in a reenactment.** The narrator can talk over it. An ornament's voice only ever comes from its real still, so the denial belongs to reality, and there's no lip-sync to build.

### Sound
- **The reenactment's own cue, kept separate from the piano theme:** a riser into the clip; a slowed heartbeat and a sub "whoomp" on the slow motion; a braam and an impact on the peak; a swell of strings or brass; exaggerated foley (a plastic clack, a concrete thud, a chime clang, a howling gust). The pipeline places the core of it on every reenactment by itself: `reenact_hit` (a reversed suck-in into a slowed-down impact and braam, landing on the first frame) and `reenact_swell` (a crescendo that peaks on the cut).
- **The hard cut back is also a sound cut.** The cue stops dead on the cut, with no tail and no reverb. The real shot gets only room tone or crickets (`"music": "out"`) for 0.3–0.6 s, then the denial. The existing mix rule still applies: the silent shot must not inherit a ringing tail.
- **No other swell into a reenactment.** A `sting_soft` on the shot before peaks on the reenactment's first frame and muddies the hit.
- **Leave the hit its pre-roll.** The hit's reversed suck-in starts 0.35 s before the reenactment, so the shot before it ends its last line at least 0.35 s before the cut. Otherwise the suck-in plays over that line, which is usually the comment question.

### Structure: the hard cut back
1. **The theory** (in reality; can be skipped in a cold open). One narrator line at most: "Police have one theory."
2. **The reenactment, 3–6 s.** The label is on. The ornament holds still under the setup, moves on the key word, and at least 0.5 s of action plays under the swell's peak after the line.
3. **The hard cut,** mid-move or just after the landing. No transition, whoosh or flash. Cut to the real ornament at the same size and angle, **back in its spot**: the instant we cut to reality, it never moved.
4. **Silence,** 0.3–0.6 s.
5. **The denial:** one short line from the character's mechanism, then a motionless hold of about 0.35 s: the laugh lands on the ornament not moving. "Where would I go, hon? I'm concrete." / "I was facing the other way." / "My client has no comment." / "I don't have hands."
6. **An optional button,** from the narrator or the suspect. The best one objects to the dramatization, not the accusation ("They made me look short.").

*Example (the Episode 1 remake):*
- **Question.** NARRATOR: "Who did it? Gnome, or goose?"
- **Reenactment, 4.05 s.** Locked camera at grass height. A glossy 3D Garrison stands dead still in a grid of red lasers, facing Deb. NARRATOR: "That night, he was facing her." On "Then he made his move." he slides sideways like a chess piece, rigid, and passes under the lowest beam on a lens flare. Nothing touches Deb.
- **Hard cut** mid-slide to the real Garrison, back in his flower bed. Crickets only.
- GARRISON: "Kid." … "I was facing the other way."

### Never
- **Never a human.** No person, hand, glove, arm, foot, shoe, face, silhouette, reflection or human shadow in any reenactment, ever. That covers both the person who puts the yard back and the Mower. A reenactment that needs the Mower shows only what it leaves behind: fresh stripes, or an ornament now facing the wrong way. No car, no lit window or lit interior of No. 7, and nothing that hints at who the person is.
- **Never how a canon move was done.** Canon says a person put Deb back at 3:12 on 06/14 and turned her on 06/21, and never says how. No reenactment shows Deb being moved, lifted or dragged; a theory cuts away before its suspect reaches her. Any "how" implies the hands that did it.
- **Never canon.** No clue, timestamp or answer may rest on a reenactment. It is never replayed as proof, the narrator never says "this is what happened", and it never goes into the clue ledger. Because canon never confirms that an ornament moved by itself, every reenactment is unconfirmed by design, and the cut back denies it.
- **Never reveal a hidden clue.** A reenactment can't show any doorbell-frame change that hasn't been paid off by that point in the story. For a remake, that means by the episode being remade. The ornament with the hidden change never shows that change (Lorraine: no turned, frontal or back view before Episode 2).
- **Never contradict the clue ledger or the doorbell tables.** A reenactment set on a recorded night happens between two doorbell frames. It starts in the earlier frame's state, and nothing it shows can disagree with the later frame. It can cut away early, since the hard cut ends it. See "The night of 13–14 June: the state any reenactment must match", under the doorbell table.
- **Never contradict Season 1's solution, or Season 2's.** No human, as above. Only reenact questions that are still open at that point in the story. Once a case is solved, don't stage an ornament as its culprit again, except in a remake set before the solution.
- **Never contradict a narration fact either.** The narrator's lines around a reenactment are reality, not theory. Check them against the ledger like any other line (Garrison faced Deb that night, not for thirty-one years).
- **Never photoreal.** If it could pass for footage, restyle it. And the other way round: a photoreal still is never called a reenactment.
- **Never damage.** Nothing chips, cracks or breaks, and no new holes or tracks appear that reality doesn't show afterwards.

### On screen and in descriptions
- **No announcement inside an episode.** The first reenactment, in the Episode 1 remake, teaches the format by itself: the label, the overacted 3D, then the hard cut to the motionless real ornament and its denial. A first-time viewer needs nothing more, and a returning viewer gets it in one beat.
- **No title card up front.** A main episode opens on the event or a line, never on a title. The series title is a small corner label (`CORNER_LABEL`) on every reality shot; none on reenactments, and none on the end card, whose title already says it.
- **Descriptions and the pinned comment** of an episode with a reenactment get one line: "Reenactments are theories. Nothing in this yard moves while anyone is watching." The description's disclosure line follows the end card: "Written by [NAME]. Footage, reenactments and voices made with AI. The flamingo is real."

## 3D character references

**How to build a keyframe prompt** (the still the clip starts from). In this order:
- an **image map** naming each attachment by its position ("Image 1: 3D sheet view of Garrison (front). Image 2: photo of Garrison."). With several attachments, a model only knows them by order, never by a repo key;
- the reference block for each character in the shot, copied word for word and never paraphrased;
- one sentence of action, written as **the first instant** of the moment, before anything moves (no dust yet, the fireball just ignited);
- the subject's size as a fraction of the frame height, matched to the real still the reenactment cuts back to, and "Exactly one gnome and one flamingo in frame" (or whatever the count is), naming the ornaments that must stay out;
- one static camera;
- the time and state, **with no date or clock time**: "Time and state: night. Deb upright on both legs, Garrison facing Deb. Every window of the house is dark, no light inside the house." Image models draw dates and times as text;
- the **still suffix**.

**How to build a motion prompt** (image to video): the camera first ("Locked-off camera; the camera never moves"), then how long the ornament holds still and the one move that follows, in seconds of the take, ending where the shot needs it, then any background motion, then the **motion suffix**. Describe the allowed motion positively, as a rigid translation: models that are only told what not to do often leave the figure frozen and move the haze. The hold time comes from the locked narration take (the write skill has the formula). The prompt lint (`pipeline/clips.py`, run on every build) treats hand(s), arm(s), finger(s), figure(s), kid(s), man/men and the like as human words even when they describe an ornament. A negation strips only the words after it, so "his hands never move" still fails: describe the pose instead ("as one rigid piece, his pose unchanged"), as the remake's `CLIPS` do.

**Build each character once, as a reference sheet.** Make a 3D turnaround sheet for each character: front, three-quarter, side and back views on a plain grey ground, with a plain grey bar of the same length beside each view and no lettering. Generate sheets at 16:9 (they never go on screen), showing the figurine alone, with no set. Attach the library photo as image 1, with the instruction to copy its shape, proportions, colours, paint wear and pose exactly, **but not its photographic look**. Then make one lineup still of the main characters side by side at their relative heights, so the sheets share a scale. File them in `stills/` as `ref3d_<name>` and `ref3d_lineup`. Generate every clip from a keyframe made with these (image to video), never from text alone.
- **When attaching a sheet, crop one view from it.** A whole turnaround sheet makes image models draw a lineup of copies.
- **Crop the library photos to the character.** `garrison` has Lorraine on the porch in its background; attached whole, it invites a goose into a gnome-only shot.
- **Who wins:** the library still wins on identity (shape, colours, markings, pose); the 3D sheet and the suffix win on material and lighting.
- **Set the canvas in the tool,** not in the prompt: 9:16 for keyframes and clips, exported at 1080x1920 (Nano Banana `aspect_ratio` 9:16; GPT Image 1024x1536 outpainted to 9:16). Keep anything important away from the outer tenth of the frame and out of the lower right, where the apps' buttons sit.

**Scale for the 3D set** (heights from the ground):

| Character | Height |
|---|---|
| Ray | 6 in |
| Garrison | 16 in |
| Lorraine | 20 in |
| Mr. Basin | 28 in |
| Deb | 34 in to the top of her head |
| The wind chime | 36 in from its top disc to the sail, hung at door height |
| Dale | 8 ft inflated; a knee-high heap when flat |

### Garrison, the garden gnome (matches `garrison`)
> GARRISON: a classic garden gnome figurine about 16 inches tall, standing upright in a flower bed of echinacea. Tall pointed brick-red cap with chipped paint at the brim and the tip; full curly white beard and white handlebar moustache; round rosy cheeks, a big round nose, small black eyes, a faint fixed smile; slate-blue knee-length tunic; black belt with a square brass buckle; both hands resting on his belly, one on each side of the bottom of his beard, thumbs up; dark brown boots. Glossy painted resin, the chips on the cap kept as painted detail.

- **Never changes:** the cap is always on and always the same ("I've had this hat since 1994"); his hands stay where they are, one on each side of the bottom of his beard, thumbs up; his expression never changes.
- **Moves:** he hops or slides sideways like a chess piece, **without ever rotating**, facing the same way the whole time. To move something, he balances it on his cap, and his hands never move. He never turns himself (the Ep. 5c note: his facing is always done *to* him).
- **Default:** in the flower bed, left. **His usual direction is the street** (Ep. 7: put back facing the street, "The way I like it"). On the night of 13–14 June he faces Deb in every doorbell frame until 431 (03:12:21), then faces away from her. Never write that he faced or watched Deb for years.

### Deb, the pink flamingo (matches `deb` and the doorbell frames)
> DEB: a classic pink plastic lawn flamingo about 34 inches tall, standing on two thin straight galvanized metal rod legs stuck into the lawn. Hollow blow-molded plastic body in warm coral-pink with molded feather relief on the wings, a long S-curved neck, a small head with a black bead eye, and a down-bent beak, pale cream at the base and black at the tip. Glossy plastic, a little too pink.

- **Never changes:** **two legs** (the one-leg reveal was dropped); her head is in profile; she faces left, as seen from No. 5, for all of Season 1. On 06/21 she faces the other way from 03:12:00.
- **Moves:** she's the victim. Canon never says how she was moved, so **no reenactment shows Deb being moved, lifted or dragged** at 3:12 on either night. In a theory she is a still prop, rigid and dignified, and the cut comes before anything reaches her. If a future theory ever needs her to move herself at some other moment (a Confessional fantasy, say), she hops on both rods together like a pogo stick, the tips pulling out of the turf with a small "plip", or glides.
- **Default:** center lawn.

### Mr. Basin, the birdbath (matches `basin_counsel` and `porch`)
> MR. BASIN: a pedestal birdbath about 28 inches tall in weathered off-white cast concrete with grey-green lichen speckles. A wide shallow bowl with a scalloped, petal-edged rim and a fluted underside, holding still water; a fluted column with a ringed collar under the bowl; a round stepped base. Leaning against his base, a tiny brown leather briefcase with a brass clasp and handle. Smooth stone-grey plastic with painted lichen speckle; the water a glossy blue-tinted disc.

- **Never changes:** the briefcase is always with him (from Ep. 2), though it's too small to see in the doorbell frames; there is always water in the bowl.
- **Moves:** he slides perfectly upright on his base, as if on a hidden track, and never tilts, for his dignity. The water rises in a slow-motion arc and lands back in the bowl, never spilled. The briefcase scoots along beside him.
- **Default:** on the right, by the hostas, six feet from Deb. Facing: up (he's a birdbath).

### Lorraine, the porch goose (matches `lorraine`, `lorraine_bee`, `lorraine_easter`, `lorraine_fitting`)
> LORRAINE: a porch goose statue about 20 inches tall, standing upright on her orange webbed feet on the concrete front step. Cast concrete with a glossy white glaze and fine hairline crazing; a long upright neck, a small round head, black bead eyes, a short orange-yellow beak, orange-yellow webbed feet, folded wing feathers molded on her sides. Glossy glazed concrete, warm lantern light on her.

Add one outfit block, or none:
- **BARE** (the default): no outfit. Use this for **every reenactment of the night of 13–14 June**. The doorbell frames show her bare, and so does Exhibit A at 5:41 AM.
- **BUMBLEBEE** (Ep. 3): "wearing a snug chunky knitted sweater in yellow and black stripes over her body, two small sheer veined wings on her back, and a black knit headband with two antennae ending in yellow pompoms."
- **EASTER** (Ep. 3): "wearing a pastel-yellow dress with a small lavender floral print, a white lace collar and lace hem, and a straw bonnet trimmed with lavender flowers, tied under her beak with a lavender ribbon."
- **GINGHAM** (the fitting, Ep. 5 onward): "wearing a blue-and-white gingham pinafore dress with a gathered skirt and a royal-blue satin bow at her neck."

Rules for her outfits:
- **New outfits get designed first.** The show says "twelve outfits since March", but only these four are designed. A new one is made the way "Image style" already says (an edit of `lorraine` with only the outfit changed), and its block is added here before any reenactment uses it.
- **The outfit never changes during a reenactment.** It may change across the hard cut, which is her running gag ("I don't pick them"). Do it on purpose, never by accident.
- **She is never staged swiveling,** facing the camera or showing her back in any reenactment set before Ep. 2's payoff (frame 418: "rotating isn't moving"). Never attach her sheet's back view to a keyframe or a clip.

Movement and position:
- **Never changes:** she's concrete and heavy, so every landing is a thud. She stands on her webbed feet; she never sits. Her beak points to frame left as seen from No. 5, except where the doorbell table says she has turned.
- **Moves:** a heavy side-to-side rock-waddle with a concrete thud on each step. In a clip, give her one rigid move instead (a tip, a drop, a slide), **only in the direction her beak points**: a rock-waddle invites leg movement, and travelling off her facing makes models turn her.
- **Default:** on the porch step.

### The wind chime, the anonymous source (matches `chime`)
> THE WIND CHIME: a tubular wind chime about 36 inches long hanging beside the black front door: five brushed-silver aluminium tubes of staggered lengths hung on fine black cords from a round dark-stained wooden top disc, a round wooden striker at mid-height, and a long cord down to a flat teardrop-shaped grey wind sail. Chrome-bright tubes that catch every flare.

- **Never changes:** five tubes and a teardrop sail (some wide stills show a round sail; follow the `chime` close-up); it never leaves its hook, so a chime theory is about what it saw or hit, never where it went.
- **Moves:** it swings and spins, and the tubes clang in slow motion, **only in wind**: leaves blowing past and the hostas flattened. No wind means no motion. **The night of 13–14 June was very windy** (its own testimony), so in any reenactment of that night a visible chime sways; it never hangs still. In a reenactment it gets a cheap pixelation mosaic ("identity protected") that hides nothing, the same joke as its blurred interviews.

### Ray, the solar frog (matches `ray`, `ray_lit`, `ray_sun`)
> RAY: a small solar garden frog figurine about 6 inches tall, crouched in the grass at the front edge of the lawn by the sidewalk. Speckled sage-green glazed resin with brown flecks, a cream throat, big round eyes with gold rims and black pupils, front legs straight and back legs tucked; a round black solar-panel puck set into his back.
> Unlit: dull, the panel dark. Lit: he glows warm yellow-green from inside, the panel's tiny lights shine, and the grass around him glows green. Translucent glowing plastic when lit.

- **Never changes:** he lights only after a full day of sun; on 06/14 he is unlit until 03:12:08 and lit from then on (a hidden clue until Ep. 3).
- **Moves:** slow-motion frog leaps, with a glow trail when he's lit. He's the one ornament for whom moving is almost believable, so his reenactments can go biggest. He's tiny, so shoot him from ground level.
- **Default:** at the front edge of the lawn.

### Dale, the inflatable snowman (matches `snowman_flat` and `timer`)
> DALE: an inflatable Christmas lawn snowman, 8 feet tall when inflated, still up in June in the side yard. Shiny white nylon in two stacked rounded sections with visible seams; a black top hat; a red scarf; two black dot eyes, an orange carrot nose and a stitched black smile; black dot coal buttons; no arms. He glows softly from inside when inflated. A small dark-green electric blower at his base, a green extension cord running off toward the house.
> Deflated: a crumpled white heap on the grass, hat folded over, scarf in the folds, the face still readable.

- **Never changes:** **no arms, no hands** ("I don't have hands"); he's always in the side yard, outside No. 5's view; he's inflated only when his timer allows: 5–11 PM, plus the extra pin, 3:00–3:15 AM. At any other time he's flat.
- **Moves:** he inflates (his big moment: rising to eight feet in a god-ray) and deflates; he sways, bows at the middle and falls flat. He can't carry or push anything.

### Shared 3D style suffixes
Two suffixes, each added word for word. The pipeline's prompt lint reads both from this section, so edit them here, not in an episode.

**The still suffix**, at the end of every keyframe and still prompt. It has no "slow motion": a still prompt that asks for motion gets motion blur.
> Stylized 3D CG reenactment in the deliberately cheesy look of a true-crime TV dramatization: glossy, plasticky, toy-like materials with smooth, too-perfect specular highlights. The lawn ornaments are rigid figurines that keep their molded faces and never bend, blink or change expression. The same suburban yard rebuilt as an obvious soundstage set: grey vinyl siding, white porch railing and posts, black front door, brass lantern sconce, silver tubular wind chime, hostas and an echinacea flower bed, an over-green manicured lawn, a bright painted twilight sky in saturated blue-violet with an oversized glowing moon, the whole set floodlit. Theatrical lighting: bright hard rim lights, magenta and cyan gels, volumetric haze and god-rays, anamorphic lens flares, saturated high-contrast colour, brightly lit, never murky. Dramatic low hero angle, shallow depth of field. Vertical 9:16. Not photorealistic. No people, no human hands, feet, silhouettes or shadows, no text, no letters, no logos. No on-screen graphics, no banners, no lower thirds, no subtitles, no letterbox bars; the picture fills the whole vertical frame.

**The motion suffix**, at the end of every motion prompt. Slow motion lives here and in the generator only. It contains no human words, so motion prompts pass the pipeline's prompt lint.
> Glossy plastic toy-like 3D CG in the look of a cheesy true-crime TV reenactment. Rigid figurines that never bend, blink or change expression; whatever moves, moves as one solid piece, like an object on a hidden track. Theatrical rim light, haze, anamorphic lens flares, bright and saturated, never murky. Slow motion, vertical 9:16, the picture filling the whole frame, with no bars and no on-screen graphics.

### Shared negative prompt
Every keyframe and clip gets this, plus a per-clip list (the ornament "coming alive": legs walking, a beak opening, a neck bobbing, a cap flopping; wrong limb counts: a one-legged flamingo, extra fingers, two heads; the ornaments that must stay out of shot; and the forbidden turn: facing the camera, back view).
> person, people, man, woman, child, human, human figure, human body, human silhouette, crowd, gloves, human face, silhouette, human shadow, reflection of a person, car, headlights, lit window, light inside the house, text, letters, numbers, captions, timestamp, logo, watermark, chyron, lower third, banner, title card, subtitles, on-screen graphics, TV logo, letterbox, black bars, film frame border, split screen, security-camera view, night vision, photorealistic, realistic photo, murky, crushed blacks, bending, squashing, stretching, melting, morphing, melted plastic, warped surface, rubbery, jelly-like wobble, glaze dripping, blinking, mouth moving, changing expression, extra limbs, duplicate ornament, new damage, shattering, pieces breaking off, flying fragments, footprints, drag marks, tracks in the grass, new holes, torn turf, camera movement, zoom

### Prompt rules learned
- **Don't give image models dates, clock times or archetypes.** "3:12 AM" becomes a clock in the frame; "like a hero walking away from an explosion" becomes a human.
- **Name graphics in the negative.** "True-crime TV", "heist movie" and "anamorphic" invite chyrons, title cards and letterbox bars inside the 9:16 frame, on top of the burned-in label.
- **Negatives name whole bodies, not parts.** A "human" modifier doesn't reliably parse in a negative prompt, so "human hands" or "shoes" also push against the gnome's hands, his boots and the goose's webbed feet. Use "human figure, human body, human silhouette, crowd".
- **Negatives must not fight the design.** "chipped" or "cracked" erases the gnome's painted chips and the goose's crazing over the clip; "debris" thins out wanted dust. Use "new damage, shattering, pieces breaking off".
- **Seedance has no negative field.** Use `camera_fixed` and append a short positive line ("Only the goose moves, as one rigid piece. No people, no text, no graphics.") to the motion prompt. Kling takes the negative in `negative_prompt`.
- **Don't use first-and-last-frame generation for a still-then-move clip.** It spreads the motion over the whole take.
- **Give the subject's size and where its top sits, and keep the top left clear.** "Fills about two-thirds of the frame height … the tip of his cap about a quarter of the way down": at 80% the cap and the beam above it played behind the red AI tag ("The label", above).
- **Fit the motion prompt to the locked narration take.** The hold time comes from the take ("Length and share"), so voice and lock the line before generating the clip.
- **Tune timing with the take's start (`in`), never by slowing it down.** If no take lands the move on time, animate a cutout of the keyframe ornament over a clean plate (the moves are rigid translations), and use image-to-video only for haze, flares and fire.

### The 3D yard model (deferred)
Not in the format yet ([`docs/DECISIONS_EP01R.md`](docs/DECISIONS_EP01R.md), D5); the Episode 1 remake doesn't use it. The design, for when it lands: a clean, Lume-style forensic 3D model of No. 7's front yard and No. 5's doorbell across the street, in matte grey clay outlined with thin glowing lines on a dark slate ground, with labels in the caption font. It is a **diagram, not a reenactment**: it carries facts, so it counts as evidence and must match canon exactly.
- **It shows:** the lot (house block, porch, steps, the window beside the porch, the lawn with a faint 1 ft grid, flower bed, hostas, sidewalk, street, side yard); the ornaments as matte tokens at their spots with name tags; the doorbell's view cone as a teal wedge (the side yard outside it, which is why Dale is never in the frames); facing cones where facing matters; evidence in amber (Deb's two positions as a ghost and a solid, a dashed `3 FT` line, the holes as pins, a clock `03:11:59 → 03:12:00 · ONE FRAME`).
- **Nothing moves in it.** Positions change by a cut or a dissolve between states, never by a token travelling. Only the camera orbits or pushes.
- **Exact to canon:** a virtual camera at No. 5's doorbell reproduces `yard_before`; Deb is 3 ft from the Saturday holes and Mr. Basin 6 ft from Deb (measured off `yard_after`), in every episode. It shows only what has been shown: no hidden change before its payoff, no Dale before he's introduced, no footprints and no path to or from the house.
- **Label:** `YARD MODEL`, in the upper-left slot, in the **yellow** of the EXHIBIT tags (yellow means evidence, red means theory).
- **Use:** at most once per episode, for 2–4 s, for spatial facts a phone viewer can't read in a dark wide still. Never for punchlines, and it never replaces the doorbell frames: the clue is always found in the doorbell frame itself. Build it deterministically (Blender or three.js, from one layout file), never generated, and file it as a clip.

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

### Reenactments (never in the ledger)
A reenactment is a theory, so it never goes into the ledger above. This table keeps the next writer from staging the same theory differently or reusing a denial.

| Ep | Theory | Night, between frames | What it shows | Kept out of shot (hidden) | Denial line |
|---|---|---|---|---|---|
| 1 (remake) | The gnome did it (heist movie) | 06/14, between 417 (03:11:59) and 418 (03:12:00) | Garrison stands still in red lasers facing Deb, then slides sideways like a chess piece, rigid, hands unmoved. Deb is untouched, and the cut comes mid-slide. | The porch and Lorraine (turned in 418), Ray, the holes, any move of Deb | GARRISON: "Kid. … I was facing the other way." Button: "They made me look short." |
| 1 (remake) | The goose did it (action movie, Director's Cut) | the same | Lorraine, bare, stands still on the top step as a stage fireball blooms, then drops one step toward the lower left, along her beak. She never turns, and the cut comes while she is on the lower step. | Deb, Garrison, Ray, any turned, frontal or back view of Lorraine | LORRAINE: "Where would I go, hon? … I'm concrete." |

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

### The night of 13–14 June: the state any reenactment must match
This comes from the doorbell table and the ledger. "Hidden" marks a change that a reenactment can't show before its payoff episode. **All night it is very windy** (the chime's testimony): haze drifts and a visible chime sways.

| Window | Deb | Garrison | Lorraine | Ray | Dale | No. 7 window |
|---|---|---|---|---|---|---|
| Before 03:00 | In the Saturday holes, 3 ft right of home, facing left | Flower bed, facing Deb | Porch step, beak left, bare | Unlit | Flat | Dark |
| 03:00–03:11:59 | Same | Same | Same | Unlit | Up, 8 ft, glowing | Dark |
| 03:12:00 (417→418) | Back in her home spot, 3 ft left (toward the flower bed). How she got there is never said or shown | Facing Deb | Turned around (hidden until Ep. 2) | Unlit | Up | Dark |
| 03:12:07–03:12:15 | Home | Facing Deb | Facing front again (422) | Lit from 03:12:08 (hidden until Ep. 3) | Up | Dark |
| 03:12:16–03:12:28 | Home | Turns away from Deb at 03:12:21, facing the street (hidden until Ep. 5) | Gone from the step (hidden until Ep. 4) | Lit | Up | Dark |
| 03:12:29–03:14:59 | Home | Street | Back on the step (hidden until Ep. 6) | Lit | Up | Dark |
| 03:15:00 on | Home | Street | Step | Lit | Flat (the timer clicks off) | Lit (hidden until Ep. 7) |

Rules that follow from it:
- **No reenactment shows Deb being moved, lifted or dragged at 3:12.** This bible never says how she was put back, only that a person did it. (A drag would also leave tracks Exhibit B doesn't show: its two drag tracks are the Mower's, made on Saturday at 9 AM, and they lead *into* the holes, Ep. 7.)
- **"Three feet left" means left as seen from No. 5,** toward the flower bed and Garrison. From any other angle, she moves toward the flower bed.
- **Garrison faced Deb that night, not for years.** His usual direction is the street. Narration around a reenactment is reality and has to match this.
- **Every window is dark until 03:15:00.** Every keyframe prompt for that night says so, because a lit window points at the unseen person (Eps. 6–7).
- **Everything ends where the next reality frame shows it,** or the hard cut ends it first. Ornaments that aren't part of the theory stay frozen in the background, or out of shot.
- **A remake only uses what existed by its episode:** before Ep. 7, Deb has never spoken, so her cut back is silence, read by the narrator; before Ep. 2, Mr. Basin only "declined to comment" (the lawyer gag starts in Ep. 2); before Ep. 4, Ray has never spoken; before Ep. 6, there is no Dale.

### Season 2, night of June 20–21 (reconstructed; check before relying on it)
Season 2 is published, but its episodes and stills aren't in this repo. This table is reconstructed from YouTube's auto-captions, so check it against the videos and their stills before staging anything on 06/21.

| Frame | Time | What the frame shows | Paid off in |
|---|---|---|---|
| 417 | 03:11:59 | As left on the 14th | – |
| 418 | 03:12:00 | Deb faces the other way | S2E1 |
| 431 | 03:12:21 | A second flamingo, "same plastic, same pink, not the same place", standing in Season 1's spare holes | S2E2 |
| 436 | 03:12:29 | A label on the newcomer, its back toward the camera | S2E3 |
| 441 | ~03:12:37 | The other flamingo faces away | S2E4 |
| 449 | ~03:12:50 | The other flamingo is gone, and the holes are empty | S2E5 |
| 453 | ~03:12:57 | She's back in the same holes, with the tag | S2E6 |
| 515 | 03:14:36 | The front of the tag is readable: "For Deb", tied to her leg | S2E7 |
| 530 | 03:15:00 | Both flamingos are still there | season end |

Season 2's answer (S2E7) is that somebody brought Deb company. Deb's reaction: "Finally."
- Lorraine had no fitting that Saturday ("They were busy").
- Dale lit the yard from 3:00 to 3:15 again; the extra pin is still in.
- Garrison faced the street throughout ("I have faced the street through all of this"). In S2E1: "31 years, I faced the other way."
- Ray only remembers "back to lunch".
- Mr. Basin: "Two cases, two wins." His record is 2–0 after Season 2.

**The other flamingo,** if a reenactment ever needs her: she's identical to Deb by design. Only her position (the spare holes) and her tag tell them apart. The tag's front stays unreadable in any reenactment set before frame 515's payoff. As with Deb, no reenactment shows how she arrived or left.

**Open before staging anything on 06/21** (the captions can't settle these; they don't apply to the Episode 1 remake, which is set on 06/14):
- **Ray:** the 06/21 table above says he's unlit at frame 417, but in S2E1 he calls it the "best charge of my life", on the longest day of the year. Is he lit in any Season 2 frame?
- **The window:** is No. 7's window lit at 03:15:00 on 06/21?
- **Lorraine's outfit on 06/21:** she says "So does my dress", but which dress?
- **Which way Deb faces:** "the other way" is probably right, as seen from No. 5, toward the spare holes and the newcomer. It needs confirming.
- **The wind on 06/21:** nothing in the captions says. Leave the chime still unless an episode establishes wind.

## Episode roadmap

1. **Three Feet** (done). Deb has moved. The witnesses are introduced. Something else moved in frame 418.
2. **I Was Right Here** (written). Every witness gives the same alibi. The frame-418 replay: Lorraine turned around, and she argues that rotating isn't moving. Mr. Basin represents himself. The wind chime almost talks. New clue: in frame 423, Ray is lit.
3. **The Goose** (written). Lorraine swears she wore the bumblebee costume that night; after the next cut she's in an Easter dress, and Exhibit A shows her in nothing: "I was between outfits." "I don't pick them, detective." Pays off Ep. 2 (Ray was awake; it's been cloudy for nine days). New clue: in frame 428 the porch step is empty.
4. **Only When It's Sunny** (written). Pays off Ep. 3 (frame 428: "LORRAINE LEFT."). Ray, the one witness awake at 3:12, can only talk after a full day of sun: day ten, cloudy; day eleven, cloudier. Mr. Basin appoints himself the frog's counsel. On day 12 Ray lights up: "I don't remember." He only remembers back to his last full charge. New clue: in frame 431 Garrison has turned around.
5. **Saturday** (written). Pays off Ep. 4 (frame 431: "GARRISON TURNED AWAY."), and his defense opens the episode out: he turned toward the street, because June 13th was a Saturday. The Mower appears only as a shadow crossing the lawn (photoreal stills, not a reenactment; see below) — eleven minutes, and nobody is put back facing the same way. Lorraine on where she went: "I was at a fitting, hon." It's Saturday. Who dresses her is "a very personal question, detective." New clue: in frame 436 Lorraine is back, after thirteen seconds.
6. **The Inflatable** (written). Pays off Ep. 5 (frame 436: "SHE CAME BACK." "They had my size, hon."). Dale, the inflatable snowman nobody took down after Christmas, has an airtight alibi: flat from 11 to 5 on his timer. "Nothing about me is airtight." Then his timer turns up with one extra pin, 3:00 to 3:15 AM: at 3:12 he was eight feet tall. He didn't set it; he doesn't have hands. Somebody was in this yard. New clue: in frame 530 the window beside the porch lights up.
7. **The Finale** (written). Pays off Ep. 6 (frame 530: "SOMEBODY WAS AWAKE."). Ep. 1's EXHIBIT B, reread: the drag tracks lead *to* the holes. The Mower dragged Deb three feet right on Saturday morning, and at 3:12 somebody put her back, lit by Dale. The chime finishes its sentence ("…put back."), Mr. Basin dismisses the case, and Deb speaks for the first time: "It's good to be home." New clue: a week later, frame 418 again, Deb faces the other way. The one-leg reveal was dropped: `deb` (Ep. 7) shows her on two legs.
8. **Season 2** (published; not in this repo). Opens on the 06/21 frame 418 (Deb turned around) and ends with somebody bringing Deb company (see "Season 2, night of June 20–21"). The person who puts the yard back is still unseen; keep it that way.

**Seasons 1 and 2 stay as published.** Nothing is re-cut or re-uploaded with reenactments. Their frames, clue ledger, solutions and lines all stand.
- Episode 5's stage directions call the Mower shadow shots a "REENACTMENT". They are photoreal stills with no label on screen, and they stay as they are. From now on a photoreal still is never called a reenactment; if the Mower shadow is reused, caption it as evidence (e.g. "SATURDAY, 9 AM").
- The original Episode 1 stays up, because Season 1's later episodes refer back to it.
- The person who puts the yard back is never seen, never named and never reenacted, and neither is how they did it.

### Remakes

A remake is a new standalone video in the same canon, for first-time viewers, in the reenactment format. It keeps every plant later episodes call back to.

- **`ep01r_three_feet_reenacted`, "Three Feet, Reenacted"** (written; builds on the Kokoro scratch voices at 46.9 s, with fallback stills under the reenactment tag until its two clips are generated). The same night, the same frames 417 and 418 and the same hidden change (Lorraine turned around in 418), never spoiled in text. A cold open on the doorbell jump, "Gnome, or goose?" by about 10 s, two reenactments (the gnome's heist, the goose's Director's Cut), Mr. Basin as a silent cutaway, the real footage stamped NOT A REENACTMENT, and the button "They made me look short." It keeps Exhibit A, Exhibit B with "where she stood for thirty years" (which Ep. 7 corrects) and the drag tracks, the chime's "I only talk when it's windy" and "That night? Very windy.", and "I was facing the other way." It ships with Eleven v4 voices and runs under 50 s. Its test against the published Episode 1 and the voice test beside it are in its `TEST_PLAN.md`; the decisions behind it are in [`docs/DECISIONS_EP01R.md`](docs/DECISIONS_EP01R.md).
- **The pin:** "Episode 1 is pinned" keeps pointing at the current pin through the remake's 7-day test. After that read the remake is pinned only if it won the package test (criteria 1–4 in its `TEST_PLAN.md`); otherwise the current pin stays.
- **The Episode 2 remake** comes next only if the series converts (the remake wins and the replication Confessional below also beats its baseline).

Between episodes, post 15–25 second **Confessionals**: one ornament airing one grudge, ending with "Episode 1 is pinned." (Once the remake's test is read, that line points at whichever Episode 1 holds the pin.)

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

**Planned: Garrison watches his 3D double** (not written). Garrison reacts to his reenactment from the remake: "That isn't me. … They cleaned my hat." It's about a type everyone knows, someone who hates how they look on camera, and it needs no lore. It has one reenactment of 5 s or less, and it is the remake test's replication, voiced to match its baseline (the remake's `TEST_PLAN.md`, criterion 5). Post it only after the remake's 7-day read. It ends on "Episode 1 is pinned." only if the remake was pinned; if the published Episode 1 kept the pin, it ends on "Three Feet, Reenacted is in the playlist." The remake's own button, "They made me look short.", is the same type; don't reuse the line.
