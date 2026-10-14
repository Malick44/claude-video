# Notes: Episode 1 remake, "Three Feet, Reenacted"

The build never writes this file. `pipeline/script_md.py` rewrites `SCRIPT.md` from `episode.py` and the timeline on every build, so everything hand-written lives here. `episode.py`'s docstring points here, and `SCRIPT.md` links it.

All timecodes are the **Kokoro scratch timeline**: every line voiced through the pipeline's own `build_audio.voice_line()` (the pinned Kokoro model, then the cast's FX chain for the pitched and disguised voices, then its trim and loudness), so each length is the one a build writes to `timeline.json`. "Look closer." 1.099 s matches Episode 1's measured 1.10 s. Audio tags are stripped before Kokoro, so a tagged line keeps its untagged length. The shipping v4 takes move every timecode; a v4 build rewrites `SCRIPT.md` with the real ones. After any edit, from `shows/nobody-moves`:
- `.venv/bin/python pipeline/build_audio.py episodes/ep01r_three_feet_reenacted --stems` builds the timeline and runs the pipeline's checks: the line checks (a tag in a caption stops the build), and the shot checks, `validate()` before voicing and `check_timeline()` after (the label, `dur`, the hit's pre-roll, name-card legibility, the end card's disclosure);
- `.venv/bin/python episodes/ep01r_three_feet_reenacted/tools/fit_takes.py [--ref <Kokoro build>/timeline.json]` prints what the pipeline doesn't: the runtime against 50 s and the trim trigger, words/min overall and while speaking, the 150 and 165 words/min projections, each take's growth over Kokoro, and for each reenactment the hold time for its motion prompt, the `in` formula, whether the generated take covers `in` + `dur`, and how long a take its clip can absorb;
- `.venv/bin/python episodes/ep01r_three_feet_reenacted/tools/make_prompts_md.py [--takes "locked v4"]` rewrites `REENACTMENT_PROMPTS.md` from `episode.py` and the timeline;
- `./make_episode.sh episodes/ep01r_three_feet_reenacted` rewrites `SCRIPT.md` with the rest of the build.

The decisions D1–D10 behind this version are in [`docs/DECISIONS_EP01R.md`](../../docs/DECISIONS_EP01R.md); the rules it follows are in [`SERIES.md`](../../SERIES.md) ("Reenactments", "3D character references").

## Pace (decided, D1)

**Target (final): brisk, about 165 words/min while someone is speaking, with each v4 take no longer than its Kokoro take +5% (150 is the floor, not the target), and 110–120 overall. Silences stay only where they are the joke.**

- **On the Kokoro scratch voices:** 87 words in 46.9 s, **111 words/min overall**. 31.3 s have someone speaking: **167 words/min while speaking**, faster than the target.
- **Why 165, not 150 (decided after round 3).** Quick deadpan delivery suits Shorts, and it is the only way to keep every joke silence under 50 s. The original 150 target conflicted with the ceiling: At ~150 words/min it would run 50.4 s at 104 words/min overall, 0.4 s over the ceiling. D1's overall target and D2's headroom hold on v4 only if the takes average about **164 words/min or faster while speaking** (159 for the 1.5 s headroom alone), about as quick as Kokoro. At 150 words/min, 110 overall would need the silence cut from 15.6 s to 12.65 s or less, which only cutting the joke silences below could do. So the casting prompts ask for brisk voices ([`docs/AUDIO_ELEVENLABS_V4.md`](../../docs/AUDIO_ELEVENLABS_V4.md), "Casting"), the blind picks prefer the take closest to Kokoro's length, and `tools/fit_takes.py` prints the 150 and 165 words/min projections with OK or WARN (at 150 it warns on the Kokoro timeline).
- The 15.6 s without a voice, all of them part of a joke or a cut:
  - the doorbell: the hop's own silence and the call-to-action hold (5.2 s);
  - the end card (2.6 s, D3);
  - the cut-backs: the silence before each denial, the beats after "Kid." and "hon?", the motionless hold after each denial, and the button's beats (2.8 s);
  - Mr. Basin's silent reaction cutaway (1.6 s, D2);
  - the reenactments' pre-rolls (for the hit) and their action after the line (1.76 s);
  - the lineup's 0.35 s tail, where `reenact_hit`'s reversed suck-in plays before the heist's first frame;
  - the camera flashes on Exhibits A and B, and short beats between and after lines (1.3 s).
- **Trimmed** (1.0 s of dead air; eight pauses and tails in six shots): the cold open's pause 0.15 → 0.1 s and its tail 0.1 → 0; Exhibit A's tail 0.4 → 0.25 (its card is still fully legible for 1.46 s); the chime's lead-in 0.1 → 0 and tail 0.2 → 0.1; the windy beat's tail 0.35 → 0.1 (Exhibit B's flash follows); Exhibit B's tail 0.3 → 0.2; the button's 0.35 → 0.2 (with `min` 1.5, the shot floor). Mr. Basin's line and hold (3.38 s) became the 1.6 s cutaway.
- **Not trimmed, on purpose:** the silence before each denial (0.45 s), the beats after "Kid." (0.4 s) and "hon?" (0.35 s), the motionless hold after "I was facing the other way." and after "I'm concrete." (0.35 s each: the laugh lands on the ornament not moving), the lineup's 0.35 s tail (the hit's 0.35 s suck-in starts there; at 0.15 it played over "goose?", the comment question), the hop's silence (`P(1.2)`), the call to action's 1.95 s hold, and the 2.6 s end card.

**Over 49.5 s on the locked takes: the trim list, in this order.** Stop as soon as the build is back under 49.5 s.
1. The NARRATOR's `voice_settings.speed` (54% of the spoken characters), only if check 6 shows v4 honours it (`docs/AUDIO_ELEVENLABS_V4.md`).
2. The doorbell's `P(1.2)` → 0.9 (−0.3 s), only if Deb's jump, 2.0 s into the shot, still falls between "The real footage." and "Look closer.".
3. The cold open's `P(0.1)` → 0 and Exhibit A's tail 0.25 → 0.15 (−0.2 s; the card stays legible for 1.36 s, over the 1.2 s floor).
4. The lineup's `P(0.15)` → 0.1 and the chime's `P(0.2)` → 0.1 (−0.15 s).

Never trimmed: the cut-back silences and holds, the lineup's 0.35 s pre-roll tail, Mr. Basin's 1.6 s, the reenactments' 0.5 s of action after the line, the call-to-action hold and the 2.6 s end card. If the build is still over 50 s after all four, re-pick faster takes before touching a joke.

## Runtime headroom (decided, D2)

**46.9 s leaves 3.1 s under the 50 s ceiling** on the Kokoro scratch voices (the decision asked for at least about 1.5 s). It is one budget, shared by every longer v4 or human take (the length rule below), and on v4 it holds only if the takes are about as quick as Kokoro's ("Pace").

- Mr. Basin is now a **silent 1.6 s reaction cutaway**: no narrator line. His card carries the joke, fully on from the cut to the hard cut (`"lower_third_at": "cut"`), so it is fully legible for the whole 1.6 s: **MR. BASIN** / "Birdbath · Declined to comment" / the yellow punch line, "Facing: up." (11 characters, well under the 32 that 1.6 s allows at 20 characters a second). It still reads as Episode 1 canon: he only declines. "Six feet from Deb" went; Episode 2's question card restates it. If the muted phone check still misses the joke, raising his `min` to 2.0 s leaves 2.7 s of headroom.
- **Kept:** the chime's "That night? Very windy." (its own `windy` shot) and Exhibit B's "Where she stood for thirty years." Episodes 2 and 7 call back to both.

## Voices and recording (decided, D9 and D10)

**The remake ships with Eleven v4 voices** (`cast.py`'s `CAST_V4`, designed per [`docs/AUDIO_ELEVENLABS_V4.md`](../../docs/AUDIO_ELEVENLABS_V4.md); `episode.py`'s `CAST` switches its four speakers to them once all four have a `voice_id`, whatever `FINAL_V4` says), so its A/B against the published Episode 1 changes picture and voice together. The voice change is tested on its own in the re-voiced Garrison Confessional (`TEST_PLAN.md`). Until the voices are designed, or with `NM_VOICES=kokoro`, the episode builds on the Kokoro scratch cast, which leaves the tags out. With `NM_VOICES=v4` and a placeholder `voice_id` still in `cast.py`, `build_audio.py` stops before voicing anything, so an A/B's v4 arm is never Kokoro in disguise.

- **NARRATOR (TRAILER)** is the narrator's own v4 voice; its one tag does the register change. On Kokoro it stays the slower, pitched-down bm_george preset.
- **The CHIME keeps its disguise chain** (pitch 0.72, `altered`) on v4 and on Kokoro, and on any human take or locked v4 take: both casts' CHIME entries (`cast.py`'s `CAST_V4` and `CAST_KOKORO`) carry `fx_on_recordings`.

**Audio tags (D10).** Untagged is the default. A tag goes only on a punchline or button line where the delivery makes the joke: at most one tagged line per shot, at most one NARRATOR tag per episode (NARRATOR (TRAILER) counts separately), and only words from the character's approved list. Tags go in the spoken text (`L()`'s third argument), never in the caption. Five of the 18 lines are tagged, each its shot's last line; the NARRATOR has none:

| Shot | Speaker | Caption | Spoken text |
|---|---|---|---|
| `g_deny` | GARRISON | I was facing the other way. | `[too quickly] I was facing the other way.` |
| `action` | NARRATOR (TRAILER) | In a world where nobody moves... one goose... dared. | `[like a movie trailer] In a world where nobody moves. One goose. Dared.` |
| `l_deny` | LORRAINE | I'm concrete. | `[unbothered] I'm concrete.` |
| `chime` | CHIME | It covers my voice. | `[hushed] It covers my voice.` |
| `button` | GARRISON | They made me look short. | `[with contempt] They made me look short.` |

Left straight on purpose: every setup ("Kid.", "Where would I go, hon?", "I only talk when it's windy."), the plant "That night? Very windy.", and all nine NARRATOR lines, including "Look closer.". Each tagged take is picked blind against one untagged take of the same line, and the tag is dropped if the untagged take wins.

**Takes, then the human fallback.** Each line gets up to 3 v4 takes. A line that no take lands in 3 tries is recorded by a human. Five lines are starred as the likeliest (`HUMAN_TAKES` in `episode.py`): `action_1`, `g_deny_2`, `l_deny_2`, `chime_1`, `chime_2`. None is a NARRATOR line, so a fallback never means re-recording the nine narrator lines to keep the narrator consistent. The trailer voice is its own one-off speaker.

**Same session, unstarred.** If a character falls back to a human, record these with them, so a shot never mixes a human and a v4 voice for one character. With the starred lines that's 9 takes and 42 words.
- Garrison: `g_deny_1` "Kid.", `button_1` "They made me look short."
- Lorraine: `l_deny_1` "Where would I go, hon?"
- The chime: `windy_1` "That night? Very windy."

**Direction** (for a v4 take and for a human one alike).
1. ★ `action_1`, NARRATOR (TRAILER): "In a world where nobody moves... one goose... dared."
   - Full movie-trailer voice, low and gravelly, close to the mic.
   - A real beat after "moves" and a shorter one after "goose", then land "dared" like a threat. The goose lands just after "dared", so the word is the cue.
   - This is the peak, and the joke is the change of register. On v4 the tag `[like a movie trailer]` asks for it (`docs/AUDIO_ELEVENLABS_V4.md`, check 18; the tag is provisional and stays only if its takes win the blind pick); the slowed, pitched-down Kokoro preset is a placeholder.
   - Lock this take before `rx_action_goose` is generated (the length rule below).
2. ★ `g_deny_2` (with `g_deny_1`, `button_1`), GARRISON: "Kid." … "I was facing the other way." … "They made me look short."
   - Gruff and offended, a defensive old-timer. "Kid." is a warning; let the 0.4 s of wounded silence sit.
   - Deliver the alibi a hair too fast and flat on "other way", as if that settles it (`[too quickly]`).
   - "They made me look short." is vanity, not guilt: he objects to the dramatization, not the accusation (`[with contempt]`).
   - A human take is recorded dry. Add his pitch-down with `fx_on_recordings` only if it sounds too young.
3. ★ `l_deny_2` (with `l_deny_1`), LORRAINE: "Where would I go, hon?" … "I'm concrete."
   - Warm, amused, mildly offended that anyone asked, with a smile in "hon".
   - "I'm concrete" as the most obvious fact in the world, gently final (`[unbothered]`).
   - She must not sound evasive. On a rewatch she is lying (frame 418), and the line has to survive that.
4. ★ `chime_1` and ★ `chime_2` (with `windy_1`), CHIME: "I only talk when it's windy." … "It covers my voice." … "That night? Very windy."
   - Whispered close to the mic, paranoid, as if checking over its shoulder. "It covers my voice" is a sensible security measure, hushed (`[hushed]`). "That night?" is a check that nobody is listening; "Very windy." is a plant, read straight.
   - A human take is recorded dry; the CHIME entry's `fx_on_recordings` (in both casts) keeps the voice-altered chain on it.

**Length rule for a line on a reenactment** (`heist_1`, `action_1`).
- **Lock the line before generating its clip.** The clip's motion is timed to the take, so voice and lock `heist_1` and `action_1` (v4, or the human fallback) first. Set the motion prompt's hold time from the locked take: heist, "For the first X seconds" with X = `pre` + the time of "Then" in the take + `in`; action, "At about Y seconds" for the landing, with Y = `pre` + the take's length + `in`. The generated take must cover `in` + `dur`: set `CLIP_SOURCES` `seconds` to 10 (and generate 10 s) when `in` + `dur` > 5. Today's prompts are fitted to the Kokoro takes ("Then" 1.91 s into the heist line; the trailer line 3.78 s); `tools/fit_takes.py` prints X, Y and the `dur` each take needs.
- The shot's `dur` = `pre` + take + pauses + at least 0.5 s of action after the line, and at most 6.0.
- **One budget for every take.** The total growth of all takes over Kokoro stays under the headroom, 3.1 s; a 5.15 s trailer take (`dur` 6.0) uses 1.35 s of it. Over 49.5 s, apply the trim list ("Pace"). A 6.0 s action shot also takes the reenactment share to 21% of 48.3 s, so `build_audio.py` warns.
- **A clip already made against the Kokoro take absorbs very little,** because `in` can fall only to 0: "Then" can come at most 2.16 s into the heist line (+0.25 s), and the trailer take can run to about 3.98 s (+0.20 s). Over about 4.0 s on the trailer line, regenerate the clip as a 10 s take with the landing re-timed: raising `dur` alone freezes the clip's last frame for over a second and lands her before "dared". `tools/fit_takes.py` prints both limits.
- Lines on stills have no cap: the shot grows with the take.

**What the words are, for whoever reads them** (the `say` strings the voices get, tags aside): `cold_1` is "Three twelve AM"; `action_1` is spoken with full stops ("In a world where nobody moves. One goose. Dared.").

## Build notes

- **The `reenactment` kind** (the show's `README.md`, "`episode.py` reference"):
  - covers `clips/`, `CLIPS`, the label and stamp, `dur`, `fallback`, `reenact_hit` + `reenact_swell`, the hard cut and `cut_silence`;
  - **the label is `REENACTMENT · AI` on every reenactment (D4)**, and the stamp under it names the theory: `THEORY #1: THE GNOME`, `THEORY #2: THE GOOSE (DIRECTOR'S CUT)`. The escalation moved from the label into the stamp. `validate()` fails any reenactment label other than exactly `REENACTMENT · AI`, so an escalation can't drift back into it;
  - the red tag is sized to its text: the label is 382 px, but the Director's Cut stamp is 674 px and would clip in a fixed 520 px canvas. It ends at x 738, inside the 930 limit;
  - the end card's AI disclosure fades in with the title on any episode with a reenactment (D3), a locked `kb` by default, and `interp` defaulting to `"nearest"` (retime at intake with optical flow, never by blending);
  - until the clips exist, each reenactment renders its fallback (the 3D keyframe still, else the real still) under the same label. That is fine for review but not for posting, because the reenactment's whole joke is motion.
- **The doorbell field `"flicker": False` on the cold open.**
  - The problem: `build_audio.py` sets `flicker_at` for every doorbell and places six glitches, a riser, the reveal braam and impact, and a score hush after its last line, even after the shot has cut away. Without the flag, all of that lands over Exhibit A.
  - The fix in the pipeline: gate the `flicker_at` assignment, the `dip` and those effects on `s.get("flicker", True)`; `render_doorbell` treats a missing `flicker_at` as "never"; `review.beats()` and `review.pacing` only read `doors[0]` as last episode's payoff when it flickers. Without that last gate, review labels the cold open's last frame as a clue payoff.
- **`"lower_third_at": "cut"` on Mr. Basin.** `render.py` brings a name card in at 0.35 s, or with the last line; a silent 1.6 s cutaway needs it fully on from the first frame, or it is fully legible for only 0.7 s. With the field it is on from the first frame to the hard cut, with no fade-out either (the shot ends on the Director's Cut's hit), so it is legible for the whole 1.6 s. `build_audio.py` warns, once the lines are voiced, about any name card fully legible for under 1.2 s, and about a silent shot whose card note runs over 20 characters a second of legible time (Mr. Basin's "Facing: up." is 11 of the 32 allowed).
- **The hit's pre-roll.** `reenact_hit` starts 0.35 s before a cued reenactment, so the shot before it ends its last line at least 0.35 s before the cut: the lineup's tail is 0.35 s, and the suck-in starts as "goose?" ends. `build_audio.py` warns when a line ends closer than that (with a millisecond's tolerance, since `timeline.json` rounds times and a `post` of exactly 0.35 can measure 0.34999).
- **`jump_after` must be an int.** The flicker branch of `render_doorbell` formats `base + jump` with `:02d`, so a float would crash it; `build_audio.py` stops on one before voicing anything. The closing doorbell starts its clock at 03:11:58 with `jump_after` 2, so frame 417 still reads 03:11:59 and frame 418 03:12:00 in the flicker; the first second shows the frame before 417, which looks the same.
- **"NOT A REENACTMENT" uses the doorbell's existing `camera` label** (top right, mono), which reads as a camera ID on a phone. Optional renderer follow-up (not built): a doorbell `tag` field that draws it in the reenactment tag's red box, so the third tag looks like the first two.
- **The prompt lint no longer conflicts.** `CLIPS` end with `MOTION_STYLE`, `SERIES.md`'s motion suffix, word for word, and they contain no human words. The still suffix (`STYLE_3D`, with its "No people, no human hands…") and the reference blocks (Garrison's "both hands resting…") live in the keyframe prompts in `STILLS`, which the lint checks only for the still suffix, a date or clock time (aspect ratios such as "9:16" aside) and "slow motion", never for human words. The lint strips negated clauses and checks `CLIPS` for human words and the motion suffix, so `pipeline/clips.py lint` passes all four prompts with no warning.
- **Clip timing is tuned with `in`, never `speed`.** The takes play at 1.0x, so the slow motion happens once, in the generator.
  - Heist: the slide should start about 2.5 s into the take, on "Then". If it starts at time S, set `in` = S − 2.26.
  - Action: the landing should come about 4.33 s into the take, just after "dared". If it comes at time T, set `in` = T − 4.13, which must be 0 or more. If she lands earlier than 4.13 s, regenerate or use the cutout fallback (`REENACTMENT_PROMPTS.md`, step 3).
  - These are fitted to the Kokoro takes; on the shipping takes, fit them to the locked v4 takes (the length rule).
- **No `sting_soft` on the lineup.** It peaks 2.4 s after the last line starts, which is the heist's first frame, stacking a second swell on `reenact_hit`. `validate()` warns about any `sting_soft` on the shot before a reenactment.
- **Mr. Basin's cutaway keeps the score out** (`"music": "out"`, crickets), so the silence runs from Garrison's denial into the Director's Cut's hit.
- **The corner label is "NOBODY MOVES"** (416 px). "NOBODY MOVES · EP. 1" was a 564 px solid yellow box, half the frame width, brighter than anything else in the night-vision cold open. It shows on every reality shot, but not on the reenactments (where it would sit under the red AI tag, bigger and brighter than it, and against the goose's head) or on the end card, whose title already says it (`render.py` skips the badge on both).
- **The Garrison cut-backs are framed for the badge and the tag.** `g_deny` and `button` sit at (0.47, 0.49), zoom 1.37: Garrison fills about two-thirds of the frame, his cap tip near y 430, clear of the corner badge (y 216–298), his boots near y 1790. The heist keyframe matches that size and keeps his cap tip and the lowest beam a quarter of the way down the frame, so the slide toward frame left never passes behind the red tag (x 64 to about 750, y 190–320).
- **The end card reads "Footage, reenactments and voices made with AI." / "The flamingo is real."** (`render.py`'s end card): on any episode with a reenactment the first line names everything made with AI, whatever the cast. Every reenactment frame says "· AI" and the doorbell says "NOT A REENACTMENT", so a line naming only reenactments and voices would teach viewers that the unlabelled photoreal stills are real; they are AI images too. It is 689 px wide, inside the 780 px limit, and fully legible for 1.95 s of the 2.6 s card.
- **Brightness without new stills.** Reality keeps the same photos, lifted with deterministic gamma curves (`DERIVED_STILLS`), so later episodes and the doorbell frames still match. The lifted `cork` keeps its library key, because the board always loads `cork`; the lift applies to this episode only. Mean luma measured on each shot's crop, out of 255:

  | Shot | Mean luma |
  |---|---|
  | Exhibit A | 76 |
  | Board | about 86 |
  | Garrison (g_deny, button) | 84 (at the new zoom 1.37; 77 at the old 1.6) |
  | Mr. Basin | 89 |
  | Lorraine | 99 |
  | Anonymous chime (chime, windy) | 75 (13 with today's `anon` look) |
  | Exhibit B | 83 |
  | Doorbell night vision | 70–72 |
  | Reenactments | target 100 or more (the keyframe sky is now "bright painted twilight", so the target is reachable) |

  The weighted mean comes out at about 80 before the film grade, against Episode 1's 50. The only near-black seconds are the 2.6 s end card (Episode 1 had 26 s).
- **The Lume-style yard model: deferred (D5).** It is out of v1, which keeps the A/B down to one family of changes. When it lands, it goes in place of the board, before the question (No. 5's camera cone, a glowing 3 FT path, GNOME and GOOSE pins), never replaces Exhibit A, and is tagged `YARD MODEL` in the evidence yellow.

## Timing, cuts and laughs

All on the Kokoro scratch timeline; the shipping v4 takes move them, and the test plan reads the shipped build's own timecodes.

- **Runtime:** 46.9 s in 14 shots, against a 35–50 s target, with 3.1 s of headroom (D2).
- **Cuts:** every shot runs 1.5–4.65 s, except the closing doorbell (7.6 s), where the hold is the puzzle. The chime's third beat has its own tighter shot (`windy`), Mr. Basin is a 1.6 s cutaway, and the button has a 1.5 s floor (`min`).
- **Reenactments:** two, 4.05 s and 4.65 s, 8.7 s in all, which is 18.5% of the runtime. They are never back to back. The first motion comes at 0:13.0 (the slide on "Then"); the first plastic frame at 0:10.7.
- **Comment question:** the card lands at 0:08.4 and the spoken question ends at 0:10.4. Episode 1 asked at 1:13. The bonus call to action lands at 0:40.9 and holds 1.95 s.
- **Frame 418** is on screen from 0:01.0 to 0:04.1 in the cold open, and paused under the call to action at the end.
- **AI disclosure:** "REENACTMENT · AI" on every reenactment frame (D4), and "Footage, reenactments and voices made with AI." fully legible for 1.95 s of the 2.6 s end card (D3; Episode 1 gave about 1.8 s).
- **Laughs (estimated):**

  | Time | Laugh |
  |---|---|
  | 0:01.0 | the jump: Deb three feet left, nobody there |
  | 0:04.1 | "Somebody moved the flamingo." |
  | 0:06.0 | "To the left." with "Position: wrong." |
  | 0:08.3 | "Zero knees." |
  | 0:10.7 | the first plastic frame |
  | 0:14.3 | "Then he made his move." over a rigid sideways slide |
  | 0:14.8 | the hard cut: he's back in his spot |
  | 0:17.5 | "I was facing the other way." right after "That night, he was facing her." |
  | 0:17.8 | Mr. Basin's silent cutaway: "Declined to comment" over the yellow "Facing: up." |
  | 0:19.4 | the Director's Cut stamp and the fireball |
  | 0:23.5 | "…dared." and the one-step drop |
  | 0:26.7 | "I'm concrete." |
  | 0:30.2 | "It covers my voice." |
  | 0:32.0 | "That night? Very windy." |
  | 0:35.0 | "Still warm." |
  | 0:37.2 | the hop, a few pixels, in silence |
  | 0:44.1 | "They made me look short." |

  The longest gap is 6.9 s, from the hop (0:37.2) to "They made me look short." (0:44.1), with the call-to-action reveal at 0:40.9 in between. The button is captioned, so it works with the sound off.

## Canon checks

- **The doorbell.**
  - Both doorbell shots go from frame 417 (`yard_before`, 03:11:59) to frame 418 (`yard_after` with `alter_box` on Lorraine, 03:12:00). The jump lands on the integer tick, and the frame stays wide and centred. Ray is unlit and the window is dark.
  - No text names the goose. The bonus call to action asks "What else changed?", a description, not a suspect.
- **Plants that later episodes call back to:**
  - Exhibit A (`yard_after` at 5:41 AM, the holes circled, the 3 FT arrow), which Episode 3 pushes in on;
  - Exhibit B (`holes` at 6:52 AM, with the drag tracks in shot) and "Where she stood for thirty years", which Episode 7 corrects ("These holes weren't thirty years old. They were one day old.");
  - the chime's "I only talk when it's windy", word for word (Episode 2's wind-stops gag), and "That night? Very windy.", the second half of the ledger's plant that makes the chime a witness to 3:12 (Episode 2's "At 3:12, the flamingo was—", Episode 7's "…put back.");
  - Garrison's "I was facing the other way", word for word (Episodes 2, 4 and 5).
- **Garrison's facing.** "That night, he was facing her." is true: Garrison faces Deb in every doorbell frame of that night until 431 (03:12:21). His usual direction is the street (Ep. 7: put back facing the street, "The way I like it"; S2E1: "31 years, I faced the other way"). The name card "Neighborhood watch, 31 years" is about tenure, not direction.
- **Who says what.**
  - Mr. Basin only declines, and now only on his card ("Birdbath · Declined to comment"); the lawyer gag starts in Episode 2. Its yellow punch line, "Facing: up.", is about the birdbath, and needs no lore.
  - Ray, Dale and the Mower have no lines. Deb doesn't speak (her first line is Episode 7).
  - "They made me look short." objects to the dramatization; Garrison never says he moved.
- **The reenactments.**
  - They are theories only, always labelled `REENACTMENT · AI`, with no timestamp in the stamp, so they can't be read against the doorbell table.
  - They never show a human. Nothing touches Deb, and nothing shows how she was moved: canon never says how she was put back at 3:12.
  - Garrison never rotates and his hands never move (one on each side of the bottom of his beard, thumbs up, as in `garrison`).
  - Lorraine wears no outfit, never turns, never faces the camera and never shows her back; she travels only the way her beak points. That protects frame 418.
  - Every window is dark (it stays dark until frame 530). It was very windy that night: the haze drifts and the chime sways.
  - Neither uses the doorbell's angle or night vision.
- **Season 2** (06/21) doesn't apply: this remake is set on 06/14 (D8). The open Season 2 facts in `SERIES.md` ("Season 2, night of June 20–21") are for future episodes only.

## Review history

The tables below record what each review round did, as it was done. Where the decisions D1–D10 and the third review changed something since (Mr. Basin's line and card, the labels, the voices, the pauses, the runtime), the sections above and [`docs/DECISIONS_EP01R.md`](../../docs/DECISIONS_EP01R.md) are current.

The reviews ran on the proposal package, before it was merged. Its files now live here: the decisions in [`docs/DECISIONS_EP01R.md`](../../docs/DECISIONS_EP01R.md); the bible changes (the package's rule update, cited below as SERIES.md) in [`SERIES.md`](../../SERIES.md) and the write skill; the renderer spec (cited below as "spec", with its section numbers) in `pipeline/`, documented in the show's `README.md`; the voices proposal (AUDIO below) in [`docs/AUDIO_ELEVENLABS_V4.md`](../../docs/AUDIO_ELEVENLABS_V4.md); and the v4 tags patch in `pipeline/`, `cast.py` and `README.md`. The package index (its README; its summary of D1–D10 is in `docs/DECISIONS_EP01R.md`) and its scratch scripts were not kept: `build_audio.py` now measures the lines and runs the caption/bracket tag checks and the shot checks; the house-style tag rules (counts, approved words, provisional tags) are still checked by hand (AUDIO, "Where each change lands": house-style lint, To do); `tools/fit_takes.py` prints the pace and clip numbers the timing script did, and `tools/make_prompts_md.py` writes `REENACTMENT_PROMPTS.md` (`SCRIPT.md` comes from `script_md.py`).

### Where the judges' notes went (round 1)

| From | Note | What this draft does |
|---|---|---|
| escalation (the base) | (kept) | The cold open "3:12 AM. Somebody moved the flamingo." with the jump at 0:01. "Zero knees." The escalation from heist, to action movie as a Director's Cut, to the real footage stamped NOT A REENACTMENT. Lorraine never looking back. Silence and ambience on each cut-back. |
| proposed rule | Four reenactments, 15.8 s | Two, 8.7 s in all: a main episode allows at most 2 and about 20%. |
| comedy | Lorraine spends "I'm concrete" on the setup | There is no setup shot. "Where would I go, hon? I'm concrete." is only the denial. |
| comedy | Garrison loses the boast-then-contradiction | The theory says "That night, he was facing her." (true to canon), the name card says "Neighborhood watch, 31 years", then he says "I was facing the other way." |
| comedy, retention | "Unless..." three times | No template line: prestige narration for theory 1, the trailer voice for theory 2. |
| comedy, retention | A four-way banner for 11 s, and the chime named at 0:05 | A binary index card on the board and no banner. The chime and Mr. Basin stay off the board. |
| comedy, feasibility | "...Not that windy" walks back a clue | Dropped. The chime gives itself away instead, and keeps the ledger's "very windy". |
| comedy | Hands around Deb's neck | Nothing touches Deb, and Garrison's hands never move. |
| comedy | No closing button | "They made me look short.", captioned, on its own still before the end card. |
| retention | Optimistic timings | Measured Kokoro takes; both reenactments have a fixed `dur`. |
| retention | No rewatch instruction | "Rewatch 0:01. What else changed?" under the call to action, with frame 418 on screen for 3.2 s at the start. |
| feasibility | Clips with several subjects, scale problems and impossible camera moves | Each clip is one ornament making one rigid move from its keyframe, on a locked camera. |
| feasibility | Exhibit B and the chime's rule dropped | Both restored, because Episodes 7 and 2 depend on them. |
| feasibility | A "ceramic" goose who says "I'm concrete" | Her block now reads "Glossy glazed concrete" (the first fix left "ceramic-plastic" in the block). |
| feasibility | Renderer features the draft didn't list | NOT A REENACTMENT is the existing `camera` label; the jump lands on a whole-second tick. New fields are listed in spec §11. |

### Review round 2: findings and where each fix went

52 findings (25 major, 27 minor; no blockers). Every major is fixed. C2 is fixed by a different means than the reviewer proposed; K2, P1 and P9 are fixed with one part not taken. One minor is rejected (K6), and T6 is covered by C2. Each exception gives its reason.

| # | Check, severity | Finding | What changed | Where |
|---|---|---|---|---|
| C1 | continuity, major | "Thirty-one years, staring at her" contradicts the finale | "That night, he was facing her. Then he made his move." Canon bullet rewritten; lower third kept | episode.py `heist`, SCRIPT.md, NOTES.md canon checks, SERIES.md (Garrison's facing) |
| C2 | continuity, major | AI disclosure readable 0.8 s | **Fixed differently.** The disclosure fades in with the end card's title on any episode with a reenactment, and `validate()` fails a build where it's fully visible for under 1.8 s. At 2.6 s it's readable 1.95 s (A: about 1.8). `"min": 3.6` would add 1 s of silent end card and take the runtime to 50.8 s, past the ceiling | spec §6.7a, §4 validate; TEST_PLAN row |
| C3 | continuity, minor | Keyframes don't say the windows are dark; "hero" invites a human | Both keyframes: "Every window of the house is dark, no light inside the house." The hero phrase is gone; `_NEG` goes to the keyframe step too | episode.py `STILLS`, `CLIP_SOURCES`; REENACTMENT_PROMPTS |
| C4 | continuity, minor | "goose" is both a vote and the bonus | Finds count only when the comment says how she changed or points to the porch, 0:01 or 418; `cta_sub` is "Rewatch 0:01. What else changed? ↓" | episode.py `doorbell`; TEST_PLAN |
| C5 | continuity, minor | Ep. 7 corrects a claim the remake dropped | "Where she stood for thirty years. Still warm." | episode.py `exhibit_b` |
| C6 | continuity, minor | The chime's "very windy" plant cut | New shot `windy`: "That night? Very windy." RX2: the chime sways; "chime hanging still" in the negative | episode.py `windy`, `CLIPS`, `CLIP_SOURCES` |
| C7 | continuity, minor | "lifted, never dragged" states a mechanism | "SERIES.md never says how she was put back at 3:12. No reenactment shows Deb being moved, lifted or dragged." Same in the bible proposal | REENACTMENT_PROMPTS, SERIES.md |
| C8 | continuity, minor | "ceramic-plastic" in Lorraine's block | "Glossy glazed concrete" everywhere | episode.py `REF_LORRAINE`, REENACTMENT_PROMPTS, SERIES.md |
| K1 | comedy, major | The heist's move plays as background, reads as a zoom | Locked camera (`kb`, prompt, `camera_fixed`). Still for 2.5 s of the take, then a rigid sideways slide that starts on "Then"; the cut catches him mid-slide | episode.py `heist`, `CLIPS`; REENACTMENT_PROMPTS RX1 |
| K2 | comedy, major | The goose's drop has happened before "dared" | Locked camera; she holds still under "In a world where nobody moves...", tips on "dared" and lands just after it; cut 0.5 s later. **Not taken: splitting the line into three takes.** Measured, three Kokoro takes end 4.97–5.12 s into the shot against the 3.9 s ceiling the finding sets (even without the second pause), which would push the runtime past 50 s. The single take already has 0.25 s and 0.3 s beats at "moves." and "goose." (measured), and the human take is starred | episode.py `action`, `CLIPS`; REENACTMENT_PROMPTS RX2 |
| K3 | comedy, major | A third flat denial, uncaptioned | New captioned still `button`: GARRISON "They made me look short." The end card has no voice (2.6 s, not 2.0, for the disclosure); laugh table corrected | episode.py `button`, `end`; NOTES.md |
| K4 | comedy, major | The hop has no beat of its own | `clock_start` "03:11:58", `jump_after` 2, `P(1.2)` between the lines. The red third tag is an optional spec field | episode.py `doorbell`; spec §11 |
| K5 | comedy, major | Basin's card gives the punchline away early | "Closest witness. Facing: up." | episode.py `basin` |
| K6 | comedy, minor | "Still warm." has no setup | **Rejected the callback** ("The holes also declined to comment.") in favour of C5, which gives "Still warm." its setup and keeps the claim Episode 7 corrects | — |
| K7 | comedy, minor | Scorecard and runtime | Re-run with measured takes: 49.8 s, longest laugh gap 6.9 s, reenactments 17.5% | NOTES.md, SCRIPT.md |
| P1 | prompts, major | Slowed twice | `speed` 1.0, no `interp`; "Slow motion." in the RX2 prompt and the motion suffix only. **Timing sentences adapted:** the reviewer's "within the first second" and "a third of the distance" assumed early action; K1/K2 need stillness first, which 1.0x playback now puts on screen, so the prompts give "still for N seconds, then…" matched to the narration | episode.py, REENACTMENT_PROMPTS |
| P2 | prompts, major | The goose travels off her facing | She drops toward the lower left, the way her beak points, body angle unchanged; negative adds "facing the camera, frontal view, turning toward camera, body rotating" | episode.py, REENACTMENT_PROMPTS |
| P3 | prompts, major | "Hands clasped", "sitting" contradict the stills | "both hands resting on his belly, one on each side of the bottom of his beard, thumbs up"; "standing upright on her orange webbed feet"; sheet and negative wording | episode.py, REENACTMENT_PROMPTS, SERIES.md |
| P4 | prompts, major | The photo wins on look; references by repo key | "copy its shape … but not its photographic look"; identity vs material rule in step 2; image maps open each keyframe | episode.py `SHEET_3D`, `STILLS`; REENACTMENT_PROMPTS |
| P5 | prompts, major | Date and 3:12 AM in image prompts | "Time and state: night. …" only | episode.py, REENACTMENT_PROMPTS |
| P6 | prompts, major | Cues invite TV graphics and letterbox | No-graphics sentence in both suffixes; graphics and bars in `_NEG` | episode.py, REENACTMENT_PROMPTS, SERIES.md |
| P7 | prompts, major | Negatives miss "comes alive", limb counts, warping | Added per clip and to `_NEG` | episode.py `_NEG`, `CLIP_SOURCES` |
| P8 | prompts, major | Push-in plus Ken Burns reads as a zoom | Locked `kb`, "Camera: locked off … completely static", `camera_fixed` | episode.py, REENACTMENT_PROMPTS |
| P9 | prompts, major | Size targets don't match the cut-backs | Sizes as fractions: Garrison 80%, Lorraine 60%. `g_deny` and `button` zoom 1.9 → 1.6 (about 82%) to match. **Not taken: first-and-last-frame generation**, which spreads the motion over the whole take and would undo the still-then-move timing; sideways and one-step moves keep the size constant anyway | episode.py, REENACTMENT_PROMPTS |
| P10 | prompts, major | RX2's keyframe describes a whole sequence | "the first instant": on the edge, no dust, fireball just ignited, static camera; `STYLE_3D` has no "slow motion" | episode.py, REENACTMENT_PROMPTS |
| P11 | prompts, major | Three beats in one clip | One action, static camera; the rock-waddle stays in the bible's description | episode.py `CLIPS`, SERIES.md |
| P12 | prompts, major | `garrison.webp` has the goose in it | Crop x 0.25–0.72, y 0.25–0.85; "Exactly one gnome and one flamingo"; goose, birdbath, frog, porch steps in the negative | episode.py, REENACTMENT_PROMPTS |
| P13 | prompts, major | Negatives fight positives | "new damage, shattering, pieces breaking off, flying fragments"; "flames on the goose, flames on the house, scorch marks, charred wood" | episode.py `_NEG`, `CLIP_SOURCES` |
| P14 | prompts, major | 9:16 only in text; Deb at the crop edge | Canvas set in the tool (steps 2 and 3); Deb in the upper right, inset from the edge | REENACTMENT_PROMPTS, episode.py |
| P15 | prompts, major | Whole turnaround sheets make duplicates | Crop one view per sheet; "Exactly one …" | episode.py, REENACTMENT_PROMPTS |
| P16 | prompts, minor | Six sheet-prompt problems | All six: figurine alone, plain bars, 16:9, `ref3d_lineup`, beak-left three-quarter view, note moved to a comment | episode.py `SHEET_3D`, `STILLS` |
| P17 | prompts, minor | "human X" in negatives | "human figure, human body, human silhouette, crowd"; also dropped "sneakers" for the same reason as "shoes" | episode.py `_NEG` |
| P18 | prompts, minor | Seedance has no negative field | Step 3 per tool; `seedance_suffix`; `CLIP_SOURCES` comment | episode.py, REENACTMENT_PROMPTS |
| P19 | prompts, minor | Negatives can freeze the figurine | Motion described positively as rigid translation; motion brush; cutout fallback | episode.py `MOTION_STYLE`, REENACTMENT_PROMPTS step 3 |
| P20 | prompts, minor | "slips under" means ducking | "crosses just above the tip of his cap"; "passes beneath … without dipping" | episode.py, REENACTMENT_PROMPTS |
| P21 | prompts, minor | "like a hero" | "framed like an action-movie poster: the goose alone …" | episode.py, REENACTMENT_PROMPTS |
| P22 | prompts, minor | A night sky can't reach luma 100 | "a bright painted twilight sky … the whole set floodlit" | episode.py `STYLE_3D`, SERIES.md |
| P23 | prompts, minor | "above the porch rail and clear of the house" | "Behind the roofline … the top-left corner stays plain sky" | episode.py, REENACTMENT_PROMPTS |
| P24 | prompts, minor | Camera behind Deb can't see her profile | "at grass height beside Deb, tilted slightly up" | episode.py, REENACTMENT_PROMPTS |
| T1 | timing, major | 110 wpm vs ~150 | Raised as an open decision (SCRIPT.md top, here, the package index). Tightening applied except Exhibit A's `post` (kept 0.4 for the lower third) and the doorbell pause (now 1.2, K4) | episode.py, SCRIPT.md, NOTES.md |
| T2 | timing, major | A build wipes the hand-written SCRIPT.md | This file; `HUMAN_TAKES`; script_md.py change in the spec | NOTES.md, episode.py, spec §11 |
| T3 | timing, major | Length caps contradict the direction | One rule: `dur` = pre + takes + pauses + 0.5, max 6.0; raise `dur` and re-time `in` when a human take lands | NOTES.md "Voices and recording", `HUMAN_TAKES` |
| T4 | timing, minor | Wrong line estimates | Measured takes everywhere; the timing script (now `tools/fit_takes.py`) uses them; action tail 0.52 s | all four files |
| T5 | timing, minor | CTA held 1.55 s | `post` 4.0: held 1.95 s | episode.py `doorbell` |
| T6 | timing, minor | End card too short for the disclosure | See C2 | — |
| T7 | timing, minor | Eight stars, not 3–5 | Five, none a NARRATOR line; companions listed | episode.py `HUMAN_TAKES`, NOTES.md |
| T8 | timing, minor | "Longest gap about 4 s" was wrong | 6.9 s, hop to button, captioned | NOTES.md |
| T9 | timing, minor | `sting_soft` stacks on the reenactment hit | Removed; `validate()` warns | episode.py `lineup`, spec §4 |
| T10 | timing, minor | The Director's Cut label clips | `rx_tag` canvas sized to the text; error past x 930; selftest | spec §6.5, §4, §8 |
| T11 | timing, minor | Corner label too big | "NOBODY MOVES" | episode.py |
| T12 | timing, minor | "(REENACTED)" title-cases wrong | "EPISODE 1: THREE FEET, REENACTED" | episode.py, SCRIPT.md, TEST_PLAN |
| T13 | timing, minor | `review.beats()` reads the cold open as a payoff | Gate on `flicker` | spec §11 |

### Review round 3: how D1–D10 were applied

34 findings (8 major, 26 minor; no blockers), numbered here in the order received. Every major is fixed. Five findings overlap others and share their fix (R17 = R9 plus a check, R21 = R6, R22 and R34 = R8, R24 = parts of R13 and R14). Three are taken with one part changed (R3, R7, R23), each with its reason; none is rejected outright.

| # | Severity | Finding | What changed | Where |
|---|---|---|---|---|
| R1 | major | D1/D2 shown only on Kokoro; at 150 words/min the build nearly hits 50 s; allowances not budgeted together; slow casting prompts | The timing script prints the 150 words/min projection's overall pace and headroom with OK/WARN, and the speaking pace D1 and D2 need (now 50.4 s, 104 overall: WARN; about 164 words/min needed). One shared budget for all takes (the 3.1 s headroom; the finding's "3.5 s" was the headroom before the restores below). Brisk casting prompts; blind picks prefer the take closest to Kokoro's length. The trim list over 49.5 s (merged with R19; the stricter trigger) | the timing script (now `tools/fit_takes.py`), "Pace", length rule, AUDIO (Casting, check 18, Phase 2, Blind picks, What to measure), TEST_PLAN gate, `docs/DECISIONS_EP01R.md`, the package index, SCRIPT header, `episode.py` docstring and `HUMAN_TAKES` |
| R2 | major | The D6 pin can't be carried out: Convert needs the replication, which comes later | "B wins" (criteria 1–4 at its 7-day read) pins B; Convert needs criterion 5 at the replication's own read; A keeps the pin otherwise. The replication Confessional ends on "Three Feet, Reenacted is in the playlist." if A kept the pin | TEST_PLAN, the package index step 9, `SERIES.md` |
| R3 | minor | Which voices the follow-ups use | "New episodes" means outside the reenactment test; the Episode 2 remake uses the remake's v4 voices, re-voiced first if the voices are redesigned. **Changed:** the replication Confessional is not "the remake's v4 voices whatever the voice test says": R27 voices it to match its baseline, which is what lets it isolate the reenactment | TEST_PLAN, AUDIO "Decision" |
| R4 | minor | §6.7a wording ambiguous; ep99; step 1 understated | The wording rule counts characters with a voiced (non-recorded) line, and is independent of the fade; ep99 draws the "voices" wording at `a3`; ep98's Kokoro copy moves NARRATOR and DEB; step 1 lists `CAST_V4`, `NM_VOICES` and the end-card change | spec §6.7a, §8 check 10, TEST_PLAN "Order" |
| R5 | minor | The label validator is looser than D4 | The label must equal `CLIP_KINDS['reenactment']['label']`; selftest case `"REENACTMENT (DIRECTOR'S CUT) · AI"` must fail | spec §0, §2, §4, §8; `SERIES.md`; this file |
| R6, R21 | minor | The trailer's tag vocabulary was invented to fit, with an unused `[dramatically]` | One provisional tag, `[like a movie trailer]`, pending check 18's blind pick; `[dramatically]` removed; the tag checker flags provisional tags | AUDIO vocabulary and tags tables, `docs/DECISIONS_EP01R.md` D10, the tag checker (not kept; its house-rule checks wait for the house-style lint) |
| R7 | minor | Shared docs teach `[deadpan]` and `[laughs]` | `[too quickly]`, *(too quickly)* and `[exhales]` in the README, `cast.py` and `build_audio.py` doc hunks and AUDIO's `script_md` row; the patch still applied to the unpatched tree. **Kept as is:** the selftest cases, the `words.py` parser vocabulary and its docstring (it describes how `[laughs]` is timed, which is still true), and `check_lines()`'s error-message example (code, outside the finding's three hunks) | the v4 tags patch (now in `pipeline/`, `cast.py`, `README.md`) |
| R8, R22, R34 | minor | Read points and runtimes come from the Kokoro timeline | Labelled "Kokoro scratch timeline/build" everywhere; the gate copies the shipped build's read points into metrics #2, #4 and the results sheet before posting | TEST_PLAN, the package index, `SERIES.md`, SCRIPT header |
| R9, R17 | minor | Trimming the lineup's tail put `reenact_hit`'s suck-in over "goose?" | The lineup's tail is back to 0.35 s; `validate()` and the timing script check the pre-roll; the NOTES wording is fixed | `episode.py`, "Pace", Build notes, spec §0, §4, §5, the timing script (now `tools/fit_takes.py`), `SERIES.md` |
| R10 | minor | `NM_VOICES=v4` with no IDs silently builds on Kokoro | `episode.py` exits with "fill V4_VOICE_IDS first"; the tag checker tests it; the arm script says so (since merged: the IDs live in `cast.py`, and `build_audio.py` stops on a placeholder `voice_id`) | `episode.py`, the tag checker (not kept; `build_audio.py`'s line checks now stop on a placeholder `voice_id`), AUDIO |
| R11 | minor | Phase 4 said the switch could start at Season 2 | "…or the switch starts with the next new episodes (Season 3)"; Season 2's seven published episodes stay as posted | AUDIO Phase 4 |
| R12 | minor | D9 overstated how clean the voice test is | The end-card line is named as the one on-screen change | `docs/DECISIONS_EP01R.md` D9, the package index item 9 |
| R13, R24 | minor | Stale wording | The build print reads `heist 10.73 -> 14.78` (the finding's 10.53 predates the lineup restore, R9); the yard model is "deferred" in §3; "The AI disclosure lives on the end card."; "the same REENACTMENT · AI label" | spec §3, §4; `episode.py` |
| R14 | minor | Small inconsistencies | The trim count now reads "eight pauses and tails in six shots" (eleven in nine before the restores); "an internal gate before posting, not the public test"; Ep. 1's `basin_1`; `cast.py`'s default `CAST` stays Kokoro with `CAST_V4` beside it | `docs/DECISIONS_EP01R.md` D1, AUDIO, `SERIES.md` |
| R15 | major | Clips are fitted to the Kokoro takes and absorb almost nothing | Voice and lock `heist_1` and `action_1` before generating the clips (README steps 6 and 7 swapped); the hold-time formula; 10 s takes when `in` + `dur` > 5; "over about 4.0 s, regenerate", not "raise `dur`"; the timing script asserts each clip covers `in` + `dur` and prints what it can absorb (heist: "Then" up to 2.16 s; trailer: about 3.98 s) | length rule, `HUMAN_TAKES`, AUDIO check 18 and Phase 2, TEST_PLAN gate, REENACTMENT_PROMPTS step 0 and Duration rows, spec §4 guidance, `SERIES.md`, the package index, the timing script (now `tools/fit_takes.py`) |
| R16 | minor | `MEASURED` held pre-FX lengths; the button fell under 1.5 s | All 18 lines re-measured through the patched `voice_line()` (also `action_1`, +0.005 s); the button has `min` 1.5; the timing script warns under 1.5 s; `--voice` uses `voice_line()`, FX included | the measuring script (now `build_audio.py`), the timing script (now `tools/fit_takes.py`), `episode.py`, the tag checker (now `build_audio.py`'s line checks) |
| R18 | minor | Garrison's and Lorraine's holds after the denial were trimmed | Both back to 0.35 s, and out of the trimmed list | `episode.py`, "Pace", `docs/DECISIONS_EP01R.md` D1, `SERIES.md` (structure step 5) |
| R19 | minor | No plan for a v4 build over 50 s | The ordered trim list over 49.5 s (merged with R1's), and what is never trimmed | "Pace", TEST_PLAN gate, AUDIO Phase 2 |
| R20 | minor | Mr. Basin's card fades out before a hard cut | `lower_third_at: "cut"` holds the card at full opacity for the whole shot; `validate()` and the timing script use legible = `end - start`; 1.6 s | spec §4, §8, §11; the timing script (now `tools/fit_takes.py`); this file |
| R23 | minor | `heist_1` is 11 words against "10 words or fewer" | **Changed:** the guidance now reads "about 10 words; the setup before the key word at most about 2 s of speech". The line stays: "That night, he was facing her." sets up "I was facing the other way.", and "he faced her" weakens that echo | spec §4, `SERIES.md` |
| R25 | major | The heist's key beat plays behind the AI tag; the cut-back cap sits under the badge | Keyframe: two-thirds of the frame height, cap tip a quarter of the way down, the beam an inch above it, the top left only haze. `g_deny` and `button` at (0.47, 0.49), zoom 1.37 (mean luma 84). Generator rows and checklist updated; the general top-left rule written down | `episode.py`, REENACTMENT_PROMPTS, `SERIES.md`, Build notes |
| R26 | major | Mr. Basin's silent joke can't be read in 1.35 s | ("MR. BASIN", "Birdbath · Declined to comment", "Facing: up."); `validate()` and the timing script warn past 20 characters a second on a silent card; the write-skill rule says about 15 characters | `episode.py`, this file, TEST_PLAN, the package index, `docs/DECISIONS_EP01R.md` D2, spec §4, §11, `SERIES.md`, the timing script (now `tools/fit_takes.py`) |
| R27 | major | The replication differs from its baseline in voice and reenactment | Voiced to match its baseline: on v4 against B2 if the voice test won, otherwise on Kokoro against A2 | TEST_PLAN criterion 5 and "Not attributable", AUDIO "Decision", `SERIES.md` |
| R28 | major | A voice loss can't condemn the format; no row for an inconclusive voice test | The reading table splits loss from flat and adds "inconclusive"; Stop defers to the Kokoro replication after a voice loss | TEST_PLAN, AUDIO "Decision" |
| R29 | major | The voice test is a Garrison test | Attributable to Garrison's v4 voice; on a win GARRISON joins `FINAL_V4`, the others only after the internal check, recorded as untested in public | TEST_PLAN, AUDIO Phase 3, "Decision", Blind picks |
| R30 | minor | Both voice-test biases push toward a loss | A second baseline (the other five Confessionals' median): a loss needs B2 under both; returning viewers % and a limited-distribution check on the results sheet | TEST_PLAN |
| R31 | minor | Three stacked badges; the series badge outshines the AI marker | No corner badge on reenactments, nor on the end card when `CORNER_LABEL == TITLE`; selftest checks y 344-426; the fireball stays right of centre | spec §0, §6.9, §8; `SERIES.md`; `episode.py`; REENACTMENT_PROMPTS |
| R32 | minor | Labelling teaches that unlabelled means real | "Footage, reenactments and voices made with AI." on any episode with a reenactment (689 px, measured with the show's Inter 30); episodes without one unchanged (or R4's "voices" wording); description line to match | spec §0, §6.7a, §8; AUDIO; `SERIES.md`; TEST_PLAN; `episode.py`; Build notes; `docs/DECISIONS_EP01R.md` D9 |
| R33 | minor | B's description asked for "the object" | "Something else in frame 418 moved. Comment what changed before Episode 2.", recorded as a difference | TEST_PLAN |
