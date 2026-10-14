"""NOBODY MOVES, Episode 1 remake: "Three Feet, Reenacted".

A standalone remake of the published Episode 1 for first-time viewers, in the format "Nobody moves
while anyone is watching" (SERIES.md). Reality (every still and the doorbell cam) stays still, and
only the camera moves. The narrator's two theories play as labelled 3D REENACTMENTS where an ornament
finally moves, and each one hard-cuts back to the real, motionless ornament denying it.

Same canon as episodes/ep01_three_feet: the night of June 13-14, doorbell frames 417 -> 418, and the
same hidden change (Lorraine turned around in 418, never named on screen). Reenactments are theories,
never evidence: no human, no clue, nothing that shows how Deb was moved, and nothing the SERIES.md
doorbell table or clue ledger contradicts.

Hand-written notes (build notes, timing and laughs, canon checks, recording direction, review log)
live in NOTES.md beside this file, because pipeline/script_md.py rewrites SCRIPT.md on every build.
The decisions D1-D10 behind it are in ../../docs/DECISIONS_EP01R.md; its A/B test is TEST_PLAN.md.

Pipeline features it uses beyond Episode 1's (the show's README.md, "episode.py reference"):
  1. kind "reenactment": clips/, CLIPS, label, stamp, dur, fallback, the reenact_hit + reenact_swell
     cue, a hard cut in picture and sound, the tag sized to its text, the "REENACTMENT · AI" label
     check, and the end card's AI disclosure fading in with the title.
  2. "flicker": False on a doorbell shot (the cold open). Without it the flicker glitches, riser,
     reveal hit and hush spill over exhibit_a.
  3. "lower_third_at": "cut" (Mr. Basin's silent cutaway): the name card is fully on from the shot's
     first frame. Without it the card slides in at 0.35 s and is fully legible for only 0.7 s.
  4. HUMAN_TAKES, read by script_md.py (stars + "Lines to record by a human").
  5. DERIVED_STILLS, the exposure-lifted stills below.
  6. Audio tags in the spoken text (D10): stripped before Kokoro and before caption timing, and a
     build whose caption would show one stops.
  7. A "blender" dict on both reenactments: pipeline/blender_reenact.py renders them in Blender, timed
     to this build's words, and files them as rx_heist_gnome_bl and rx_action_goose_bl
     (../../docs/BLENDER_REENACTMENTS.md). Until a Blender clip is filed (no Blender on the machine),
     each shot plays its fallback still, exactly as before. The image-to-video route stays below
     (STILLS' rx_*_key keyframes, CLIPS, CLIP_SOURCES): to play a generated clip instead, file it under
     its own key and point the shot's "clip" back at it (the AI-route values are in a comment there).
  "jump_after" stays an int: the doorbell clock ticks in whole seconds, and build_audio.py stops on a
  float.

Voices (decision D9): the remake ships with Eleven v4 designed voices (cast.py's CAST_V4, picked up
by CAST below; ../../docs/AUDIO_ELEVENLABS_V4.md). Until all four of its speakers are designed, or with
NM_VOICES=kokoro, it builds on the Kokoro scratch cast, which leaves the audio tags out.

Timings use the Kokoro scratch takes, voiced the way build_audio.py voices them (the pinned model, the
cast's FX, its trim): 46.9 s, 14 shots, two reenactments totalling 8.7 s (18.5%), and 3.1 s under the
50 s ceiling, one budget shared by every longer v4 (or human) take. Pace (D1, final): 111 words/min
overall and 167 while someone is speaking on Kokoro; target ~165 while speaking (each v4 take <= its
Kokoro length +5%; 150 is the floor) and 110-120 overall. At ~150 words/min it would run 50.4 s at
104 words/min overall, 0.4 s over the ceiling: D1's overall target and D2's headroom hold on v4 only
if the takes average about 164 words/min or faster while speaking (NOTES.md, "Pace", and its trim list
over 49.5 s). After any build, tools/fit_takes.py prints these numbers from build/timeline.json. The
only long silences left are jokes: the cut-backs, Mr. Basin's cutaway and the doorbell's call to action.
"""
import os

TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 1: THREE FEET, REENACTED"   # the title as posted (comma form)
CORNER_LABEL = "NOBODY MOVES"     # the only title (416 px wide): no title card before the cold open
NEXT_UP = "NEXT: EPISODE 2 — I WAS RIGHT HERE"
# The hidden clue in the doorbell frame (kept out of the video; SCRIPT.md only).
ANSWER = ("In frame 418 Lorraine the porch goose has turned to face the other way. Deb's jump is the "
          "obvious change; the goose is the hidden one: the same goose who said \"Where would I go, hon? "
          "I'm concrete.\", and the goose the Director's Cut showed dropping a step without ever turning. Paid off "
          "in Episode 2.")

# Voices (decision D9). The remake ships with the Eleven v4 voices designed with Voice Design
# (../../docs/AUDIO_ELEVENLABS_V4.md, "Casting"), so picture and voice change together in the A/B against the
# published Episode 1. They live in the series cast, ../../cast.py's CAST_V4, the same voices the Garrison
# Confessional's voice test uses, so each character keeps one voice all series; nothing here holds an ID.
# The remake switches its four speakers to v4 once all four are designed, whatever FINAL_V4 says
# (the remake ships v4 either way), unless NM_VOICES=kokoro. Until then it builds on the Kokoro scratch
# cast, which leaves the audio tags out (build_audio.voiced_text), so the timeline shape is the same.
# NM_VOICES=v4 puts every speaker on v4 in cast.py, and build_audio.py stops before voicing anything
# while a voice_id is still the placeholder, so the A/B's v4 arm is never Kokoro in disguise.
def _series_cast():
    import sys
    show = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    if os.path.join(show, "pipeline") not in sys.path:
        sys.path.insert(0, os.path.join(show, "pipeline"))
    from common import load_source
    return load_source("cast", os.path.join(show, "cast.py"))


_cast = _series_cast()
SPEAKERS_V4 = ("NARRATOR", "GARRISON", "LORRAINE", "CHIME")
DESIGNED_V4 = all(_cast.CAST_V4[w]["voice_id"] != _cast.PLACEHOLDER for w in SPEAKERS_V4)
VOICES_V4 = _cast.VOICES == "v4" or (DESIGNED_V4 and _cast.VOICES != "kokoro")
if VOICES_V4:
    # One-off speaker: the narrator's trailer register for the Director's Cut. On v4 it is the narrator's
    # own designed voice, and its one tag ([like a movie trailer]) does the register change; no pitch
    # shift. Captions don't show speaker names, so on screen it is still the narrator.
    CAST = {**{w: _cast.CAST_V4[w] for w in SPEAKERS_V4}, "NARRATOR (TRAILER)": dict(_cast.CAST_V4["NARRATOR"])}
else:
    # Kokoro scratch: the same bm_george preset, slower and about 3 semitones down, so Kokoro gets the
    # "louder, same narrator" shift it can't do inside one voice.
    CAST = {"NARRATOR (TRAILER)": {"voice": "bm_george", "speed": 0.9, "pitch": 0.84}}

# Audio tags (decision D10). Untagged is the default. A tag goes only on a punchline or button line
# where the delivery makes the joke: at most one tagged line per shot, at most one NARRATOR tag per
# episode (NARRATOR (TRAILER) counts separately; this episode gives the NARRATOR none), and only words
# from that character's approved list (../../docs/AUDIO_ELEVENLABS_V4.md, "Audio tags house rules"). A tag is
# written in the spoken text, L()'s third argument, never in the caption. Tagged here: g_deny_2,
# action_1, l_deny_2, chime_2 and button_1.

# The human fallback (D9). The remake ships with v4 voices; if a v4 take can't land one of these lines
# after 3 tries, record that line by a human. These five gain most from a human, by recording name,
# with one line of direction (also the delivery a v4 take aims for). script_md.py puts a star after
# "record as" on these, plus a "Lines to record by a human" section. Same-session companions and the
# length rule are in NOTES.md ("Voices and recording").
HUMAN_TAKES = {
    "action_1": ("NARRATOR (TRAILER), the peak: full movie-trailer voice, low and close to the mic; real beats "
                 "after \"moves\" and \"goose\", then \"dared\" like a threat. A one-off speaker, so no narrator "
                 "session is needed. Lock this take before the clip is generated (NOTES.md, length rule). Once "
                 "a clip exists it absorbs a take of up to about 4.0 s; over that, regenerate the clip as a 10 s "
                 "take with the landing re-timed: raising dur alone freezes the clip and lands her before "
                 "\"dared\"."),
    "g_deny_2": ("GARRISON: gruff and offended, a hair too fast and flat on \"other way\", as if that settles "
                 "it. Same session: g_deny_1 \"Kid.\" and button_1 \"They made me look short.\""),
    "l_deny_2": ("LORRAINE: \"I'm concrete\" as the most obvious fact in the world, gently final, never evasive "
                 "(on a rewatch she is lying). Same session: l_deny_1 \"Where would I go, hon?\""),
    "chime_1": ("CHIME: whispered close to the mic, paranoid, checking over its shoulder. Record dry; "
                "fx_on_recordings keeps the disguise. Same session: chime_2 and windy_1."),
    "chime_2": ("CHIME: \"It covers my voice\" hushed, as a sensible security measure. Same session as chime_1 "
                "and windy_1 (\"That night? Very windy.\", the plant Episodes 2 and 7 pay off)."),
}

# ---------------------------------------------------------------------------------------------
# 3D reference blocks and the shared 3D style suffixes, word for word from ../../SERIES.md
# ("3D character references"). Never paraphrase them; the prompt lint reads the suffixes from there. The library still wins on identity (shape,
# colours, markings, pose); the 3D sheet and the style suffix win on material and lighting.
REF_GARRISON = (
    "GARRISON: a classic garden gnome figurine about 16 inches tall, standing upright in a flower bed "
    "of echinacea. Tall pointed brick-red cap with chipped paint at the brim and the tip; full curly white "
    "beard and white handlebar moustache; round rosy cheeks, a big round nose, small black eyes, a faint "
    "fixed smile; slate-blue knee-length tunic; black belt with a square brass buckle; both hands resting "
    "on his belly, one on each side of the bottom of his beard, thumbs up; dark brown boots. Glossy painted "
    "resin, the chips on the cap kept as painted detail."
)
REF_DEB = (
    "DEB: a classic pink plastic lawn flamingo about 34 inches tall, standing on two thin straight "
    "galvanized metal rod legs stuck into the lawn. Hollow blow-molded plastic body in warm coral-pink with "
    "molded feather relief on the wings, a long S-curved neck, a small head with a black bead eye, and a "
    "down-bent beak, pale cream at the base and black at the tip. Glossy plastic, a little too pink."
)
REF_LORRAINE = (  # BARE: no outfit block. Every reenactment of the night of 13-14 June uses BARE.
    "LORRAINE: a porch goose statue about 20 inches tall, standing upright on her orange webbed feet on the "
    "concrete front step. Cast concrete with a glossy white glaze and fine hairline crazing; a long upright "
    "neck, a small round head, black bead eyes, a short orange-yellow beak, orange-yellow webbed feet, folded "
    "wing feathers molded on her sides. Glossy glazed concrete, warm lantern light on her."
)
# For stills (keyframes): no "slow motion" here, because a still prompt that asks for motion gets blur.
STYLE_3D = (
    "Stylized 3D CG reenactment in the deliberately cheesy look of a true-crime TV dramatization: glossy, "
    "plasticky, toy-like materials with smooth, too-perfect specular highlights. The lawn ornaments are rigid "
    "figurines that keep their molded faces and never bend, blink or change expression. The same suburban "
    "yard rebuilt as an obvious soundstage set: grey vinyl siding, white porch railing and posts, black front "
    "door, brass lantern sconce, silver tubular wind chime, hostas and an echinacea flower bed, an over-green "
    "manicured lawn, a bright painted twilight sky in saturated blue-violet with an oversized glowing moon, "
    "the whole set floodlit. Theatrical lighting: bright hard rim lights, magenta and cyan gels, volumetric "
    "haze and god-rays, anamorphic lens flares, saturated high-contrast colour, brightly lit, never murky. "
    "Dramatic low hero angle, shallow depth of field. Vertical 9:16. Not photorealistic. No people, no human "
    "hands, feet, silhouettes or shadows, no text, no letters, no logos. No on-screen graphics, no banners, "
    "no lower thirds, no subtitles, no letterbox bars; the picture fills the whole vertical frame."
)
# For clips (motion prompts). Slow motion lives here and in the generator only: the shot plays the take
# at 1.0x, so nothing is slowed twice. Lint-clean (no human words), so CLIPS pass the pipeline's prompt lint.
MOTION_STYLE = (
    "Glossy plastic toy-like 3D CG in the look of a cheesy true-crime TV reenactment. Rigid figurines that "
    "never bend, blink or change expression; whatever moves, moves as one solid piece, like an object on a "
    "hidden track. Theatrical rim light, haze, anamorphic lens flares, bright and saturated, never murky. "
    "Slow motion, vertical 9:16, the picture filling the whole frame, with no bars and no on-screen graphics."
)
# Reference sheets aren't reenactments, so they don't take the yard set. They never go on screen, so
# they're generated wide (set the canvas to 16:9 in the tool). Before attaching a sheet to a keyframe,
# crop ONE view from it (Garrison front, Lorraine's beak-left three-quarter view, Deb side): a whole
# turnaround sheet makes image models draw several copies. Never pass Lorraine's back view to a video
# generator, or to any keyframe set before Episode 2's payoff (frame 418).
SHEET_3D = (
    "Shown four times in a row at the same scale on a plain neutral grey ground: front, three-quarter, side "
    "and back views, the same pose in every view, evenly lit with a soft key light and a clean rim light; "
    "beside each view, a plain grey vertical bar of the same length in every panel, with no marks or "
    "lettering. Show the figurine alone: no flowers, no lawn, no step, no lantern, no set; plain grey ground, "
    "even studio light. Glossy, plasticky, toy-like CG materials with smooth, too-perfect specular highlights; "
    "a rigid figurine with a molded face. Image 1 is a photo of the real figurine: copy its shape, "
    "proportions, colours, paint wear and pose exactly, but not its photographic look; render it as glossy, "
    "toy-like CG. Wide 16:9 sheet. Not photorealistic. No people, no human hands, no text, no letters, no logos."
)

# New stills. Generate these, then file them with the keys below. A shot uses the first view whose
# still exists, so the episode builds before any of them do. Keyframes: set the canvas to 9:16 in the
# tool and export 1080x1920 (REENACTMENT_PROMPTS.md, step 2); prompt text alone doesn't set the canvas.
STILLS = {
    # Series library (shows/nobody-moves/stills/), reused by every later reenactment. Attach the
    # library photo as image 1.
    "ref3d_garrison": ("3D character turnaround reference sheet. " + REF_GARRISON + " Hands in the same place "
                       "in every view. " + SHEET_3D),
    "ref3d_deb": "3D character turnaround reference sheet. " + REF_DEB + " Both rod legs visible in every view. " + SHEET_3D,
    "ref3d_lorraine": ("3D character turnaround reference sheet. " + REF_LORRAINE + " Bare: no outfit, no "
                       "accessories. The three-quarter view has the beak pointing to frame left, as in image 1. "
                       + SHEET_3D),
    # One shared-scale still, so the three separately generated sheets agree on size. Attach the three
    # sheets as images 1-3.
    "ref3d_lineup": ("3D scale lineup. Image 1: 3D sheet of Garrison. Image 2: 3D sheet of Lorraine. Image 3: 3D "
                     "sheet of Deb. " + REF_GARRISON + " " + REF_LORRAINE + " " + REF_DEB + " Garrison, Lorraine "
                     "and Deb side by side on the same grey ground at relative heights 16, 20 and 34 inches: "
                     "Garrison and Deb in front view, Lorraine in three-quarter view with the beak to frame left. "
                     "Show the figurines alone: no flowers, no lawn, no step, no lantern, no set; plain grey "
                     "ground, even studio light. Glossy, plasticky, toy-like CG materials with smooth, too-perfect "
                     "specular highlights. Wide 16:9. Not photorealistic. No people, no text, no letters, no logos."),
    # This episode (episodes/ep01r_three_feet_reenacted/stills/): the 3D keyframes the clips start from.
    # Each one is also the clip's fallback still under the same REENACTMENT · AI label. Every keyframe opens
    # with an image map, because with several attachments the model only knows them by order.
    "rx_heist_gnome_key": (
        "Image 1: 3D sheet view of Garrison (front). Image 2: photo of Garrison. Image 3: 3D sheet view of Deb "
        "(side). Image 4: photo of Deb. " + REF_GARRISON + " " + REF_DEB + " Action: a heist-movie moment, the "
        "instant before the move. Garrison stands perfectly still in his flower bed, upright and rigid, facing "
        "straight into the lens, matching image 2 in shape, colours and pose. A criss-cross grid of glowing red "
        "laser beams, made visible by stage haze drifting in the wind, surrounds him; the lowest beam crosses "
        "about an inch above the tip of his red cap. A single painted bead of sweat shines on his nose. "
        "Garrison, centred left to right, fills about two-thirds of the frame height, his boots near the bottom "
        "edge and the tip of his cap about a quarter of the way down the frame; above that, the top left of the "
        "frame holds only haze and the upper beams. Out of focus in the right "
        "foreground, Deb's pink neck enters from the top of the frame, and her head, in profile with the beak "
        "pointing left toward Garrison, sits in the upper right of the frame, above its lower half and inset "
        "from the right edge by at least a tenth of the frame width. Nothing touches her. Exactly one gnome and "
        "one flamingo in frame; no goose, no birdbath, no frog, no porch steps. Camera: at grass height beside "
        "Deb, tilted slightly up, locked off. Time and state: night. Deb upright on both legs, Garrison facing "
        "Deb. Every window of the house is dark, no light inside the house. " + STYLE_3D),
    "rx_action_goose_key": (
        "Image 1: 3D sheet view of Lorraine (three-quarter view, beak to frame left). Image 2: photo of "
        "Lorraine. " + REF_LORRAINE + " Action: the first instant of an action-movie moment, framed like an "
        "action-movie poster: the goose alone, centred, the fireball behind her. Lorraine stands on the very "
        "edge of the top porch step, tipped slightly forward, about to drop off it toward the lower left of "
        "frame in the direction her beak points, her beak pointing to frame left in three-quarter view exactly "
        "as in image 2. No dust yet. Behind the roofline, filling the sky right of the frame's centre line, a "
        "stage-pyrotechnic fireball has just ignited: a bright orange core with the first sparks; nothing burns "
        "or breaks, and the sky left of centre stays plain. The brass lantern sconce glows beside the black "
        "front door, which stays shut and dark, and the silver wind chime beside the door sways in the wind. "
        "Exactly one goose in the frame; no other ornament. Lorraine, centred, fills about 60% of the frame height, "
        "beak to frame left. Camera: low angle from the front walk, static. Time and state: night. Lorraine "
        "bare, no outfit, no accessories. Every window of the house is dark, no light inside the house. "
        + STYLE_3D),
}

# Brighter reality without regenerating anything. These are deterministic exposure lifts of library
# stills, with the same pixels and framing, so every later episode and the doorbell frames still match.
# render.py derives them in memory from the "from" still (nothing is written to stills/):
#   out = (src / 255) ** (1 / gamma); "blur" is a GaussianBlur radius applied first; "tint"/"gain" multiply.
# "cork" keeps its library key on purpose: an episode still overrides the library one, and the board
# always loads "cork". Means are measured whole-still luma, 0-255: before -> after.
DERIVED_STILLS = {
    "yard_after_lift": {"from": "yard_after", "gamma": 1.8},                  # 33 -> 78 (Exhibit A only; the doorbell keeps yard_after)
    "garrison_lift": {"from": "garrison", "gamma": 1.5},                      # 59 -> 88
    "lorraine_lift": {"from": "lorraine", "gamma": 1.5},                      # 59 -> 89
    "porch_lift": {"from": "porch", "gamma": 1.5},                            # 67 -> 96
    "holes_lift": {"from": "holes", "gamma": 1.5},                            # 59 -> 89
    "chime_anon_lift": {"from": "chime", "blur": 5, "gamma": 1.6,
                        "tint": (0.62, 0.78, 1.0), "gain": 1.15},             # today's "anon" look: 13 -> 72
    "cork": {"from": "cork", "gamma": 1.5},                                   # 53 -> 80
}

# Reenactment clips (CLIPS works like STILLS). Each one is an image-to-video motion prompt for the
# keyframe named in CLIP_SOURCES. Every move is a rigid translation that starts from stillness and lands
# on the narration's key word: the camera is locked, so the motion reads as the ornament, not the lens.
# The take is played at 1.0x; the timings below are seconds into the generated take.
CLIPS = {
    "rx_heist_gnome": (
        "Locked-off camera at grass height; the camera never moves, and the laser grid, the flower bed and the "
        "house behind him stay perfectly still in frame. The red laser beams hum in drifting haze. For the first "
        "two and a half seconds the garden gnome stands perfectly still, staring into the lens. Then he slides "
        "sideways toward frame left like a chess piece, upright and rigid, still facing the lens, never turning, "
        "never stepping, never bending; he passes beneath the lowest beam without dipping, and a lens flare "
        "blooms as he clears it. He is still sliding on the last frame, about a quarter of the frame width from "
        "where he started. The pink flamingo in the soft foreground stays perfectly still. " + MOTION_STYLE),
    "rx_action_goose": (
        "Slow motion. Locked-off low-angle camera; the camera never moves. The white concrete porch goose stands "
        "perfectly still and rigid on the edge of the top porch step, beak pointing to frame left, while an "
        "orange stage fireball blooms behind the roofline and rolls upward with drifting sparks; nothing burns "
        "or breaks. At about four seconds she tips forward off the step as one solid, rigid piece and drops onto "
        "the step below, moving toward the lower left of frame in the direction her beak points, her body angle "
        "unchanged from the first frame, and lands with a puff of concrete dust. She stays on the lower step for "
        "the rest of the take while the fireball keeps growing. Beside the door the wind chime sways in the "
        "wind and the haze drifts. " + MOTION_STYLE),
}
# Negative prompts. Plain "hands", "feet" or "shoes" would also strip the gnome's hands and boots and
# the goose's webbed feet, and a "human" modifier doesn't reliably parse in a negative, so human terms
# name whole bodies only. "new damage" rather than "chipped"/"cracked": the gnome's chips and the goose's
# crazing are part of the design, and the goose's landing dust is wanted.
_NEG = ("person, people, man, woman, child, human, human figure, human body, human silhouette, crowd, gloves, "
        "human face, silhouette, human shadow, reflection of a person, car, headlights, lit window, light "
        "inside the house, text, letters, numbers, captions, timestamp, logo, watermark, chyron, lower third, "
        "banner, title card, subtitles, on-screen graphics, TV logo, letterbox, black bars, film frame border, "
        "split screen, security-camera view, night vision, photorealistic, realistic photo, murky, crushed "
        "blacks, bending, squashing, stretching, melting, morphing, melted plastic, warped surface, rubbery, "
        "jelly-like wobble, glaze dripping, blinking, mouth moving, changing expression, extra limbs, duplicate "
        "ornament, new damage, shattering, pieces breaking off, flying fragments, footprints, drag marks, "
        "tracks in the grass, new holes, torn turf, camera movement, zoom")
# Not read by the pipeline. What to feed the generators, and what clips.json should record.
# "keyframe_refs" are for the keyframe (image) step only, in the order of the keyframe prompt's image map.
# Image-to-video gets the keyframe alone. "negative" goes to the keyframe step and to Kling's
# negative_prompt; Seedance has no negative field, so use camera_fixed and append "seedance_suffix".
CLIP_SOURCES = {
    "rx_heist_gnome": {
        "keyframe": "rx_heist_gnome_key",
        "keyframe_refs": ["ref3d_garrison, front view cropped from the sheet",
                          "garrison, cropped to x 0.25-0.72, y 0.25-0.85 (the gnome only; no goose, no porch)",
                          "ref3d_deb, side view cropped from the sheet",
                          "deb"],
        "seconds": 5, "aspect": "9:16", "camera_fixed": True,
        "negative": _NEG + (", gnome rotating, turning around, walking, running, hands moving, hands joining, "
                            "living gnome, animated cartoon character, legs walking, feet stepping, arms swinging, "
                            "beard blowing, cap flopping, cap bending, ducking, extra fingers, fused fingers, "
                            "deformed hands, one-legged flamingo, three legs, extra legs, bent legs, flamingo head "
                            "turning, flamingo moving, flamingo lifted, goose, white bird, birdbath, frog, porch "
                            "steps, lasers moving, push-in, fire, explosion"),
        "seedance_suffix": "Only the gnome moves, as one rigid piece. No people, no text, no graphics.",
    },
    "rx_action_goose": {
        "keyframe": "rx_action_goose_key",
        "keyframe_refs": ["ref3d_lorraine, the beak-left three-quarter view cropped from the sheet (never the back view)",
                          "lorraine"],
        "seconds": 5, "aspect": "9:16", "camera_fixed": True,
        "negative": _NEG + (", turning, head turn, rotation, body rotating, facing the camera, frontal view, "
                            "turning toward camera, back view, looking back, real goose, live bird, animal walking, "
                            "legs stepping, feet lifting, beak opening, honking, neck bobbing, head bobbing, "
                            "feathers ruffling, wings spreading, flapping wings, bending neck, extra feet, extra "
                            "beak, two heads, outfit, clothing, sunglasses, hat, bow, dress, flamingo, gnome, "
                            "flames on the goose, flames on the house, scorch marks, charred wood, broken railing, "
                            "ash, chime hanging still, dolly"),
        "seedance_suffix": ("Only the goose moves, as one rigid piece; the fireball, the haze and the swaying chime "
                            "are the only other motion. No people, no text, no graphics."),
    },
}

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731

# Doorbell frames: SERIES.md table, night of June 13-14. 417 = yard_before; 418 = yard_after + alter_box on Lorraine.
LORRAINE_TURNED = (0.7163, 0.2129, 0.7800, 0.2787)

SHOTS = [
    # --- 0:00 COLD OPEN: the event in second one. No title card; the corner label is the title.
    {
        "id": "cold", "kind": "doorbell",
        "note": ("COLD OPEN, no title card. NO. 5 DOORBELL CAM, night vision. 03:11:59, frame 417: everything in "
                 "place. At 0:01 the clock ticks to 03:12:00 and the feed jumps (sub hit) to frame 418: Deb is "
                 "three feet to the left, and nobody is seen. In 418 Lorraine has turned around, the hidden "
                 "change, never mentioned. Wide and centred, no push toward any ornament. No flicker, no call "
                 "to action. Frame 418 stays up about 3.1 s, so the bonus is findable on the loop."),
        "frame_a": "yard_before", "frame_b": "yard_after",
        "clock_start": "03:11:59", "jump_after": 1, "frames": (417, 418),   # int: the jump lands on the clock tick
        "flicker": False,   # a jump only: no flicker, CTA, glitches, riser, reveal hit or hush
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.5, 1.05)),
        "alter_box": LORRAINE_TURNED,
        "items": [
            L("NARRATOR", "3:12 AM.", "Three twelve AM."),
            P(0.1),
            L("NARRATOR", "Somebody moved the flamingo."),
        ],
        "post": 0.0,   # Exhibit A's flash beat follows
        "sfx": ["crickets"],
    },
    # --- EXHIBIT A: the first laugh, plus the plant Episode 3 pushes in on (the porch at 5:41 AM)
    {
        "id": "exhibit_a", "kind": "evidence", "label": "EXHIBIT A", "stamp": "06/14 · 5:41 AM",
        "note": ("CAMERA FLASH. EXHIBIT A: the yard at 5:41 AM, the same photo as the published Episode 1 with its "
                 "exposure lifted for a phone. Yellow circles mark the two empty holes; a dashed '3 FT' arrow draws "
                 "from the holes to where Deb stands now."),
        "views": [V("yard_after_lift", (0.53, 0.64, 1.45), (0.52, 0.645, 1.62)),
                  V("yard_after", (0.53, 0.64, 1.45), (0.52, 0.645, 1.62))],
        "items": [P(0.1), L("NARRATOR", "Three feet. To the left.")],
        "post": 0.25,   # the lower third ("Position: wrong.") is this beat's joke: fully legible 1.46 s
        "sfx": ["shutter"],
        "annot_arrow": {"from": (0.695, 0.626), "to": (0.43, 0.626), "label": "3 FT"},
        "annot_circles": [(0.673, 0.604, 0.018), (0.717, 0.607, 0.018)],
        "lower_third": ("DEB", "Lawn flamingo · Center lawn, No. 7", "Condition: unharmed. Position: wrong."),
        "lower_third_at": "last",
    },
    # --- THE EASY QUESTION, at about 8.4 s (Kokoro): binary, no lore, one-word answer. No sting_soft: its swell
    # would peak on the heist's first frame, on top of reenact_hit (validate() now warns about that).
    {
        "id": "lineup", "kind": "board", "card": "COMMENT: GNOME OR GOOSE?",
        "note": ("EVIDENCE BOARD, lifted. Deb's polaroid is the hub, with red string to two suspects only: GNOME and "
                 "GOOSE. The chime and Mr. Basin stay off the board, so neither reveal is spent here. On the last "
                 "line the index card lands: 'COMMENT: GNOME OR GOOSE?'"),
        "kb": ((0.5, 0.45, 1.0), (0.5, 0.5, 1.1)),
        # (still, square crop (x0, y0, x1), label, center fx, fy, size, rotation, look); the first is the hub
        "polaroids": [
            ("deb", (0.15, 0.28, 0.95), "DEB (MOVED)", 0.50, 0.30, 600, -2.5, None),
            ("garrison", (0.228, 0.335, 0.717), "GNOME", 0.26, 0.56, 440, 4, None),
            ("lorraine", (0.240, 0.310, 0.820), "GOOSE", 0.74, 0.56, 440, -5, None),
        ],
        "items": [
            L("NARRATOR", "Two suspects. Zero knees."),
            P(0.15),
            L("NARRATOR", "Who did it? Gnome, or goose?"),
        ],
        # 0.35 s: reenact_hit's reversed suck-in starts 0.35 s before the heist's first frame, so it begins
        # as "goose?" ends instead of playing over the comment question (NOTES.md, "Pace").
        "post": 0.35,
    },
    # --- THEORY 1, the gnome: HEIST MOVIE. The first thing that moves, at about 13.0 s (Kokoro). Stillness is the
    # setup and the move is the punch: he holds dead still under "That night, he was facing her. Then he made his"
    # and zips on "move" (about 3.23 s into the shot; option B). The cut catches him mid-slide, 0.58 s after the
    # line ends; reality has him back in his spot.
    {
        "id": "heist", "kind": "reenactment",
        "note": ("REENACTMENT · AI, THEORY #1, HEIST MOVIE. A glossy plastic 3D Garrison stands dead still in a grid "
                 "of red laser beams, staring into the lens. Locked-off camera. On 'move' he zips sideways like a "
                 "chess piece, rigid, never turning, and passes under the lowest beam on a lens flare. The lens is "
                 "Deb's point of view (she is off screen: a pink kicker light from frame right). Hard cut mid-slide."),
        # Rendered by pipeline/blender_reenact.py, timed to the take (no trim, so "in" is 0). A key of its own: a
        # Blender render never takes the AI clip's slot (rx_heist_gnome stays the image-to-video route; to play a
        # generated clip instead: "clip": "rx_heist_gnome", "in": 0.25, "kb": ((0.5, 0.53, 1.0), (0.5, 0.53, 1.0))).
        "clip": "rx_heist_gnome_bl", "in": 0.0, "speed": 1.0, "dur": 4.05,
        "blender": {
            "template": "heist", "subject": "garrison", "props": [],   # Deb is the lens, not a prop
            # Option B: dead still through "...Then he made his", then a rigid zip on "move" (0.12 s ease-in, about
            # 31% of the frame width a second) with the flare. Option A (slides on "Then", the line's illustration):
            # "move_on": "Then", "move_at": 2.26, and "accel_s": 0.35 in the options.
            "move_on": "move", "move_at": 3.23,            # the word first; seconds if there is no timeline
            "flare_on": "move",                            # the lens flare peaks 2 frames after "move"
            "camera": "beside_deb",                        # grass height, where Deb stands, locked off
            "options": {"path": "left", "travel": 0.25, "accel_s": 0.12},   # a quarter of the frame width by the cut
        },
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.5, 1.0)),          # locked: a native 9:16 render, the identity crop
        "label": "REENACTMENT · AI", "stamp": "THEORY #1: THE GNOME",   # every reenactment is marked AI (D4)
        "look": "reenact", "cue": True, "cut_silence": 0.6,
        "fallback": [V("rx_heist_gnome_bl_key", (0.5, 0.5, 1.0), (0.5, 0.5, 1.0)),   # blender_reenact.py --keyframe
                     V("rx_heist_gnome_key", (0.5, 0.55, 1.0), (0.5, 0.52, 1.35)),
                     V("garrison", (0.47, 0.52, 1.6), (0.47, 0.50, 2.3))],
        "pre": 0.35,
        "items": [L("NARRATOR", "That night, he was facing her. Then he made his move.")],
    },
    {   # the cut-back: the real gnome, still, in silence
        "id": "g_deny", "kind": "still", "music": "out", "pre": 0.45,
        "note": ("HARD CUT: the real Garrison, back in his spot, locked off, cap to boots at about the size the "
                 "reenactment showed him. The score is gone, leaving only crickets. Nothing moves, not even the "
                 "camera. His name card lands in the silence."),
        # About two-thirds of the frame height, like the keyframe: the cap tip near y 430, clear of the
        # corner badge (y 216-298), the boots near y 1790.
        "views": [V("garrison_lift", (0.47, 0.49, 1.37), (0.47, 0.49, 1.37)),
                  V("garrison", (0.47, 0.49, 1.37), (0.47, 0.49, 1.37))],
        "items": [L("GARRISON", "Kid."), P(0.4),
                  L("GARRISON", "I was facing the other way.", "[too quickly] I was facing the other way.")],
        "post": 0.35,   # the motionless hold after the denial is where the laugh lands (D1 keeps it)
        "sfx": ["crickets"],
        "lower_third": ("GARRISON", "Garden gnome · Flower bed, No. 7", "Neighborhood watch, 31 years"),
    },
    # --- THE CLOSEST WITNESS, a silent 1.6 s reaction cutaway (D2). Episode 1 canon: he only declines;
    # the lawyer gag starts in Episode 2. No line: his card carries the joke, fully on from the cut, and
    # the crickets run on from Garrison's denial into the Director's Cut's hit.
    {
        "id": "basin", "kind": "still", "music": "out",
        "note": ("SILENT REACTION CUTAWAY: Mr. Basin, the birdbath, six feet from Deb, at sunset with the porch and "
                 "chime behind; a short push-in, no line. His name card is up from the cut: 'Birdbath · Declined "
                 "to comment', and the yellow punch line 'Facing: up.' Crickets only, then the hard hit into the "
                 "Director's Cut."),
        "views": [V("porch_lift", (0.6, 0.64, 1.1), (0.62, 0.63, 1.22)),
                  V("porch", (0.6, 0.64, 1.1), (0.62, 0.63, 1.22))],
        "items": [],
        "min": 1.6, "sfx": ["crickets"],
        # The punch gets the short yellow line to itself (11 characters, readable in the 1.6 s); "Six feet
        # from Deb" goes, since Episode 2's question card restates it.
        "lower_third": ("MR. BASIN", "Birdbath · Declined to comment", "Facing: up."),
        "lower_third_at": "cut",   # fully on from the first frame to the cut, no fade either way
    },
    # --- THEORY 2, the goose: ACTION MOVIE, the Director's Cut. The peak, at about 19.4 s (Kokoro). "In a world
    # where nobody moves..." plays over a motionless goose in front of an explosion; she rocks on "one" and on
    # "goose...", tips on "dared" (the punch word triggers the drop) and lands in the silence after it (about
    # 4.34 s in). Cut 0.31 s after the landing.
    {
        "id": "action", "kind": "reenactment",
        "note": ("REENACTMENT · AI, THEORY #2 (DIRECTOR'S CUT), ACTION MOVIE. A glossy plastic 3D Lorraine, bare, "
                 "stands dead still on the top porch step as a stage fireball blooms behind the roofline. Locked-off "
                 "camera. She rocks once on 'one' and once on 'goose', and on 'dared' she tips off the step as one "
                 "rigid piece and drops onto the step below, toward the lower left, the way her beak points, never "
                 "turning. Concrete dust. Trailer voice. Hard cut a third of a second after she lands."),
        # Rendered by pipeline/blender_reenact.py under its own key (the AI route: "clip": "rx_action_goose",
        # "in": 0.2). "dur" stays 4.65, so the episode builds exactly as before while no clip is filed; that leaves
        # the landing 0.26 s after "dared" ends (the rule is 0.25 s or more) and the cut 0.31 s after it (0.3-1.0).
        # The prototype's 0.37 s of silence before the thud needs "dur": 5.0 and "offset": 0.37 (a 0.35 s longer
        # episode, inside the 3.1 s headroom).
        "clip": "rx_action_goose_bl", "in": 0.0, "speed": 1.0, "dur": 4.65,
        "blender": {
            "template": "action", "subject": "lorraine",
            "move_on": ["one", "goose"],                                   # one rock-waddle on each word
            "tip_on": "dared",                                             # the tip starts on "dared"
            "land_on": {"word": "dared", "edge": "end", "offset": 0.26},   # the thud: in the silence after it
            "move_at": [2.80, 3.04], "tip_at": 3.56, "land_at": 4.34,     # the Kokoro take's times, as a fallback
            "camera": "hero_low",                                          # low on the front walk, locked off
            "options": {"outfit": None, "steps_down": 1},                  # BARE: the night of 13-14 June
        },
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.5, 1.0)),
        # The escalation lives in the stamp now: the label is "REENACTMENT · AI" on every reenactment (D4).
        "label": "REENACTMENT · AI", "stamp": "THEORY #2: THE GOOSE (DIRECTOR'S CUT)",
        "look": "reenact", "cue": True, "cut_silence": 0.6,
        "fallback": [V("rx_action_goose_bl_key", (0.5, 0.5, 1.0), (0.5, 0.5, 1.0)),   # blender_reenact.py --keyframe
                     V("rx_action_goose_key", (0.5, 0.5, 1.0), (0.5, 0.46, 1.35)),
                     V("lorraine", (0.5, 0.5, 1.2), (0.5, 0.47, 1.6))],
        "pre": 0.35,
        # One take: measured, Kokoro already leaves 0.25 s and 0.3 s beats at the periods, and three
        # separate takes ran 1.2 s longer (NOTES.md, review log). The trailer register is its tag on v4;
        # the human fallback is starred.
        "items": [L("NARRATOR (TRAILER)", "In a world where nobody moves... one goose... dared.",
                    "[like a movie trailer] In a world where nobody moves. One goose. Dared.")],
    },
    {   # the cut-back. Its kb matches the AI keyframe's framing (Lorraine about 60% of the frame height). The
        # Blender clip's first frame shows her about 41% tall at x 0.59 (hero_low), so once rx_action_goose_bl plays,
        # set both views to (0.50, 0.50, 1.0), the uncropped still, or the cut reads as a punch-in instead of "she
        # never moved": blender_reenact.py's cut-back check warns until then and prints that kb.
        "id": "l_deny", "kind": "still", "music": "out", "pre": 0.45,
        "note": ("HARD CUT: the real Lorraine back on her step in the porch light, locked off, her beak to frame left, "
                 "the size the reenactment showed her. No fireball and no score, only crickets and the porch-light "
                 "hum. Her name card lands in the silence."),
        "views": [V("lorraine_lift", (0.52, 0.53, 1.35), (0.52, 0.53, 1.35)),
                  V("lorraine", (0.52, 0.53, 1.35), (0.52, 0.53, 1.35)),
                  V("yard_before", (0.744, 0.245, 3.0), (0.744, 0.245, 3.0), "longlens")],
        "items": [L("LORRAINE", "Where would I go, hon?"), P(0.35),
                  L("LORRAINE", "I'm concrete.", "[unbothered] I'm concrete.")],
        "post": 0.35, "sfx": ["crickets"],   # the motionless hold after "I'm concrete." is the laugh (D1 keeps it)
        "lower_third": ("LORRAINE", "Porch goose · Front steps, No. 7", "Hasn't left the porch since 1998"),
    },
    # --- THE ANONYMOUS SOURCE gives itself away (the 107-view Confessional's joke, with no lore needed)
    {
        "id": "chime", "kind": "still", "pre": 0.0,
        "note": ("ANONYMOUS SOURCE: the wind chime, blurred and cold-tinted but exposed for a phone, never near-black. "
                 "It is obviously a wind chime. Wind and chimes swell under every word."),
        "views": [V("chime_anon_lift", (0.545, 0.44, 1.1), (0.6, 0.42, 1.3)),
                  V("chime", (0.545, 0.44, 1.1), (0.6, 0.42, 1.3), "anon"),
                  V("porch", (0.86, 0.13, 3.0), (0.86, 0.12, 3.35), "anon")],
        "items": [L("CHIME", "I only talk when it's windy."), P(0.2),
                  L("CHIME", "It covers my voice.", "[hushed] It covers my voice.")],
        "post": 0.1, "sfx": ["wind", "chimes"],
        "lower_third": ("ANONYMOUS SOURCE", "Voice altered", "Identity protected"),
    },
    # --- ...and plants the clue-ledger line Episodes 2 and 7 pay off. Its own cut, tighter, on a gust,
    # so no shot holds longer than 4.5 s outside the doorbell.
    {
        "id": "windy", "kind": "still", "pre": 0.0,
        "note": "Tighter on the blurred chime as a gust hits. The source as good as says it was talking at 3:12.",
        "views": [V("chime_anon_lift", (0.6, 0.42, 1.45), (0.62, 0.41, 1.6)),
                  V("chime", (0.6, 0.42, 1.45), (0.62, 0.41, 1.6), "anon"),
                  V("porch", (0.86, 0.12, 3.35), (0.86, 0.12, 3.6), "anon")],
        "items": [L("CHIME", "That night? Very windy.")],   # a plant: read straight, untagged
        "post": 0.1, "sfx": ["wind", "chimes"],   # Exhibit B's flash beat follows
    },
    # --- EXHIBIT B: back to evidence. "Where she stood for thirty years" is the claim Episode 7 corrects
    # ("These holes weren't thirty years old. They were one day old."), and the drag tracks are its plant.
    {
        "id": "exhibit_b", "kind": "evidence", "label": "EXHIBIT B", "stamp": "06/14 · 6:52 AM",
        "note": ("CAMERA FLASH. EXHIBIT B: the two holes at dawn, circled in yellow. It starts wide enough to show the "
                 "two drag tracks in the grass, then pushes in."),
        "views": [V("holes_lift", (0.62, 0.55, 1.1), (0.665, 0.6, 1.45)),
                  V("holes", (0.62, 0.55, 1.1), (0.665, 0.6, 1.45))],
        "items": [P(0.1), L("NARRATOR", "Where she stood for thirty years. Still warm.")],
        "post": 0.2, "sfx": ["shutter"],
        "annot_circles": [(0.562, 0.619, 0.052), (0.769, 0.619, 0.052)],
    },
    # --- THE REAL FOOTAGE, after two blockbusters: a few pixels, with a silence of its own. Then the bonus.
    {
        "id": "doorbell", "kind": "doorbell",
        "note": ("NO. 5 DOORBELL CAM again; its camera label now reads 'NO. 5 · NOT A REENACTMENT'. 03:11:58. 'The real "
                 "footage.' Then nothing. At 0:02 into the shot the clock ticks to 03:12:00 and Deb hops three feet "
                 "(sub hit): a few pixels, after two blockbusters, in silence. Half a second later: 'Look closer.' "
                 "Frames 417 and 418 flicker, then the footage pauses on 418 (Lorraine turned around, never named). "
                 "Call to action: 'SOMETHING ELSE IN THIS FRAME MOVED.' / 'Rewatch 0:01. What else changed?' "
                 "Wide and centred, no push toward any ornament."),
        "frame_a": "yard_before", "frame_b": "yard_after",
        # 03:11:58 + 2 s keeps frame 417 at 03:11:59 and frame 418 at 03:12:00 (SERIES.md); "03:11:59" with
        # jump_after 2 would show 03:12:00 over frame 417.
        "clock_start": "03:11:58", "jump_after": 2, "frames": (417, 418),
        "camera": "NO. 5 · NOT A REENACTMENT",
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.5, 1.06)),
        "alter_box": LORRAINE_TURNED,
        "cta": ("SOMETHING ELSE IN", "THIS FRAME MOVED."),
        # Asks for a description, not a name: "goose" is also a poll answer, so a bare "goose" is a vote.
        "cta_sub": "Rewatch 0:01. What else changed? ↓",
        "items": [L("NARRATOR", "The real footage."), P(1.2), L("NARRATOR", "Look closer.")],
        "post": 4.0,   # the call to action lands 2.05 s after the last line; 4.0 holds it about 1.95 s
        "sfx": ["crickets"],
    },
    # --- THE BUTTON: the suspect objects to the dramatization, not the accusation. Captioned (end cards
    # aren't), in the same locked framing as g_deny. Pays off the cap clearing the laser.
    {
        "id": "button", "kind": "still", "music": "out", "pre": 0.2,
        "note": "HARD CUT back to the real Garrison, same locked framing as his denial. Crickets.",
        "views": [V("garrison_lift", (0.47, 0.49, 1.37), (0.47, 0.49, 1.37)),
                  V("garrison", (0.47, 0.49, 1.37), (0.47, 0.49, 1.37))],
        "items": [L("GARRISON", "They made me look short.", "[with contempt] They made me look short.")],
        "post": 0.2, "min": 1.5, "sfx": ["crickets"],   # min: the 1.5 s floor, whatever the take
    },
    # --- END CARD: the AI disclosure (now literally true). On an episode with a reenactment the renderer fades
    # the disclosure in with the title (fully legible from 0.65 s), so 2.6 s keeps it readable for 1.95 s
    # (D3); validate() fails the build below 1.8 s. On any episode with a reenactment the first line names
    # everything made with AI, whatever the cast: the photoreal stills and doorbell frames are AI images too,
    # so "unlabelled" must never read as "real" (render.py's end card).
    {
        "id": "end", "kind": "end",
        "note": ("END CARD: NOBODY MOVES · NEXT: EPISODE 2 — I WAS RIGHT HERE · 'Follow the case.' · "
                 "'Footage, reenactments and voices made with AI. The flamingo is real.'"),
        "items": [],
        "min": 2.6, "sfx": ["sting_end"],
    },
]
