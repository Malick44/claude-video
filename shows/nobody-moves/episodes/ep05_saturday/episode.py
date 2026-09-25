"""NOBODY MOVES, Episode 5: "Saturday".

Pays off Ep. 4's hidden clue early (frame 431: Garrison has turned around, away from Deb), and his
defense turns it into the episode: he didn't turn away from Deb, he turned toward the street,
because June 13th was a Saturday. The street's most feared event, The Mower, is reenacted as a
shadow crossing the lawn: eleven minutes, and nobody is where they were. Garrison has never once
been put back facing the same way. Then Lorraine, on where she went at 03:12:16: "I was at a
fitting, hon." It's Saturday. Who dresses her is "a very personal question, detective."
New clue: in frame 436 Lorraine is back on the step. She was gone thirteen seconds.

The two doorbell frames (library keys yard_turned and yard_back) are pixel edits of the library
frames, derived by make_stills.py; run it before building.
"""

TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 5: SATURDAY"
NEXT_UP = "NEXT: EPISODE 6 — THE INFLATABLE"
ANSWER = ("In frame 436 (03:12:29) Lorraine is back on the porch step. The step is empty in frame 435, "
          "and has been since frame 428 at 03:12:16. The goose who doesn't go anywhere was gone for "
          "thirteen seconds. Garrison is still turned away in both frames, as he has been since 431. "
          "Pays off in Episode 6, 'The Inflatable'.")

_STYLE = ("Photorealistic, vertical 9:16. The same suburban house: grey vinyl siding, white porch railing "
          "and posts, black front door, brass lantern sconce, silver tubular wind chime, hostas and an "
          "echinacea flower bed. Dusk, blue hour or night. Shallow depth of field, muted teal-and-amber grade, "
          "fine film grain. No people, no text.")

# New stills this episode would like (all optional: every shot falls back to the series library).
# The Mower is never seen, only its shadow, so the reenactment needs no new character.
STILLS = {
    # The Mower is never seen, only ever its shadow, so the prompt has to say that twice: name the
    # shadow's silhouette, and rule the objects themselves out of the frame.
    "mower_shadow": ("The same front lawn, low and wide, in hard low Saturday-morning sun. The lawn is completely "
                     "empty of objects: no mower, no machine, no ornaments, no people anywhere in the picture. "
                     "Stretching across the cut grass toward the camera is one long, crisp, unmistakable CAST "
                     "SHADOW: the silhouette of a walk-behind rotary lawn mower with its two wheels and its tall "
                     "curved push handlebar, and behind it the silhouette of a person leaning into that handlebar, "
                     "arms straight. The shadow is sharp-edged and clearly readable as that shape, thrown from far "
                     "outside the frame by the low sun. The objects casting it are outside the picture and never "
                     "visible, not even a wheel at the edge. Fresh mower stripes in the turf, cut clippings in the "
                     "air. Ominous, like a surveillance still. " + _STYLE),
    "lorraine_fitting": ("The exact same close-up as the lorraine still, same framing and pose, with only her "
                         "outfit changed: a crisp new gingham dress with a fresh ribbon at her neck, obviously "
                         "just put on. (Best made by editing lorraine and changing only the outfit.) " + _STYLE),
}

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731

RAY_LIGHT = (0.183, 0.768, 0.02)             # Ray's solar light, on since frame 423
GARRISON_BOX = (0.112, 0.486, 0.215, 0.612)  # Garrison in yard_gone: mirrored, he faces away from Deb
MOWER_VIEWS = [V("mower_shadow", (0.5, 0.62, 1.2), (0.48, 0.60, 1.38)),
               V("holes", (0.42, 0.55, 1.5), (0.40, 0.54, 1.68))]
LORRAINE_VIEWS = [V("lorraine_fitting", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22)),
                  V("lorraine_easter", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22)),
                  V("lorraine", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22))]
BOARD_POLAROIDS = [
    ("yard_before", (0.478, 0.380, 0.829), "DEB (MOVED)", 0.50, 0.40, 620, -2.5, None),
    ("yard_turned", (0.228, 0.335, 0.717), "GARRISON (AWAY)", 0.24, 0.24, 420, 4, None),
    ("yard_back", (0.680, 0.200, 0.808), "LORRAINE (BACK)", 0.77, 0.23, 420, -5, None),
    ("porch", (0.234, 0.466, 0.978), "MR. BASIN, ESQ.", 0.29, 0.58, 420, -3, None),
    ("mower_shadow", (0.300, 0.400, 0.800), "SATURDAY", 0.72, 0.58, 420, 5, None),
]

SHOTS = [
    # --- hook: the gnome names the thing he's actually afraid of, and it isn't the case
    {
        "id": "hook", "kind": "still", "note": "EXTREME CLOSE-UP: Garrison.",
        "views": [V("garrison", (0.5, 0.5, 1.2), (0.5, 0.47, 1.36))],
        "items": [
            L("GARRISON", "You want to know what scares me, kid?"),
            P(0.5),
            L("GARRISON", "It isn't whoever moved Deb."),
            P(0.45),
            L("GARRISON", "It's Saturday."),
        ],
        "post": 0.3,
        "lower_third": ("GARRISON", "Garden gnome · Flower bed, No. 7", "Afraid of: Saturday"),
    },
    {
        "id": "title", "kind": "title", "note": "Title card over a piano sting.",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 3.2, "sfx": ["sting"],
    },
    # --- pay off Ep. 4: replay frames 430/431, the gnome turned away
    {
        "id": "replay", "kind": "doorbell",
        "note": ("DOORBELL CAM REPLAY: frames 430 to 431 again, the camera pushing in on the flower bed. "
                 "Frame 431: Garrison is mirrored, facing away from Deb. Pauses on 'GARRISON TURNED AWAY.'"),
        "frame_a": "yard_gone", "frame_b": "yard_gone",
        "clock_start": "03:12:17", "jump_after": 5, "frames": (430, 431),
        "lit": [RAY_LIGHT],
        "alter_box": GARRISON_BOX,
        "kb": ((0.5, 0.5, 1.0), (0.22, 0.55, 2.1)),
        "cta": ("GARRISON", "TURNED AWAY."), "cta_sub": "You found it. Frame 431.",
        "items": [
            L("NARRATOR", "Last week, you found a gnome."),
            P(0.4),
            L("NARRATOR", "Frame 431.", "Frame four thirty-one."),
        ],
        "post": 3.6, "sfx": ["crickets"],
    },
    # --- his defense reframes the whole episode
    {
        "id": "defense", "kind": "still", "note": "INTERVIEW: Garrison, not defensive for once.",
        "views": [V("garrison", (0.5, 0.56, 1.0), (0.49, 0.53, 1.18))],
        "items": [
            L("GARRISON", "I didn't turn away from Deb."),
            P(0.5),
            L("GARRISON", "I turned toward the street."),
        ],
        "post": 0.35,
        "lower_third": ("GARRISON", "Garden gnome · Flower bed, No. 7", "Facing: the street"),
    },
    {"id": "q1", "kind": "qcard", "text": "What comes down the street on Saturdays?", "items": [], "min": 2.6,
     "note": "BLACK CARD."},
    # --- the reenactment: the Mower, shown only as a shadow
    {
        "id": "saturday", "kind": "still", "note": "REENACTMENT: hard morning light, the empty lawn.",
        "views": MOWER_VIEWS,
        "items": [
            L("NARRATOR", "June 13th was a Saturday.", "June thirteenth was a Saturday."),
            P(0.45),
            L("NARRATOR", "On this street, that means one thing."),
        ],
        "post": 0.4,
    },
    {
        "id": "mower", "kind": "still", "note": "REENACTMENT, closer: the shadow crosses the grass.",
        "views": [V("mower_shadow", (0.46, 0.58, 1.55), (0.44, 0.57, 1.75)),
                  V("holes", (0.38, 0.52, 1.9), (0.36, 0.51, 2.1))],
        "items": [
            L("NARRATOR", "At 9 AM, a shadow crosses the lawn.", "At nine AM, a shadow crosses the lawn."),
            P(0.5),
            L("NARRATOR", "It takes eleven minutes."),
            P(0.55),
            L("NARRATOR", "Nobody is where they were."),
        ],
        "post": 0.45,
    },
    # --- the punchline lands in silence: the score cuts for this shot only
    {
        "id": "putback", "kind": "still", "note": "Garrison, quiet. No score under this one.",
        "views": [V("garrison", (0.5, 0.52, 1.28), (0.5, 0.5, 1.44))],
        "items": [
            L("GARRISON", "Thirty-one years, I've watched it come."),
            P(0.6),
            L("GARRISON", "Not once have I been put back facing the same way."),
        ],
        "post": 0.5, "music": "out",
    },
    {"id": "q2", "kind": "qcard", "text": "Lorraine. Where did you go at 3:12 AM?", "items": [], "min": 2.6,
     "note": "BLACK CARD."},
    # --- where the goose went
    {
        "id": "lorraine", "kind": "still", "note": "INTERVIEW: Lorraine, warm and unbothered, in a new outfit.",
        "views": LORRAINE_VIEWS,
        "items": [
            L("LORRAINE", "I was at a fitting, hon."),
            P(0.6),
            L("NARRATOR", "A fitting."),
            P(0.4),
            L("LORRAINE", "It's Saturday."),
        ],
        "post": 0.35,
        "lower_third": ("LORRAINE", "Porch goose · Front steps, No. 7", "Whereabouts: a fitting"),
    },
    {
        "id": "dresser", "kind": "still", "note": "Lorraine, tighter. Cornered, 'hon' becomes 'detective'.",
        "views": [V("lorraine_fitting", (0.5, 0.47, 1.35), (0.5, 0.45, 1.5)),
                  V("lorraine_easter", (0.5, 0.47, 1.35), (0.5, 0.45, 1.5)),
                  V("lorraine", (0.5, 0.47, 1.35), (0.5, 0.45, 1.5))],
        "items": [
            L("NARRATOR", "Lorraine. Who dresses you?"),
            P(0.75),
            L("LORRAINE", "That's a very personal question, detective."),
        ],
        "post": 0.4,
    },
    {
        "id": "basin", "kind": "still", "note": "Mr. Basin objects. There is still no judge.",
        "views": [V("basin_counsel", (0.5, 0.55, 1.05), (0.5, 0.58, 1.25)),
                  V("porch", (0.6, 0.64, 1.05), (0.63, 0.62, 1.32))],
        "items": [
            L("MR. BASIN", "Objection. Relevance."),
            P(0.5),
            L("NARRATOR", "There is still no judge."),
            P(0.4),
            L("MR. BASIN", "There is still an objection."),
        ],
        "post": 0.35,
        "lower_third": ("MR. BASIN", "Birdbath · Attorney for the goose", "Retained by: nobody"),
    },
    {
        "id": "board", "kind": "board", "card": "WHO DRESSES THE GOOSE?",
        "note": "EVIDENCE BOARD, updated: Garrison (AWAY), Lorraine (BACK), SATURDAY.",
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.53, 1.18)),   # ends framed low: the index card stays above every app's description
        "polaroids": BOARD_POLAROIDS,
        "items": [
            L("NARRATOR", "Somebody moves the ornaments."),
            P(0.4),
            L("NARRATOR", "Somebody dresses the goose."),
            P(0.5),
            L("NARRATOR", "Somebody comes on Saturdays."),
        ],
        "post": 0.6, "sfx": ["sting_soft"],
    },
    # --- new cliffhanger: frame 436, Lorraine is back on the step (Garrison still turned, Ray still lit)
    {
        "id": "doorbell", "kind": "doorbell",
        "note": ("DOORBELL CAM, later that minute. The camera drifts toward the porch step. Jump cut to frame "
                 "436; on 'Frame 436' the frames flicker. In 436 Lorraine is back on the step. Pauses on "
                 "'SHE CAME BACK.'"),
        "frame_a": "yard_turned", "frame_b": "yard_back",
        "clock_start": "03:12:25", "jump_after": 4, "frames": (435, 436),
        "lit": [RAY_LIGHT],
        "kb": ((0.5, 0.5, 1.0), (0.70, 0.32, 1.9)),   # ends on the porch step, above the call to action
        "cta": ("SHE CAME", "BACK."), "cta_sub": "Comment the frame ↓",
        "items": [
            L("NARRATOR", "Lorraine left the step at 3:12 and 16.",
              "Lorraine left the step at three twelve and sixteen."),
            P(0.45),
            L("NARRATOR", "A fitting takes longer than that."),
            P(0.5),
            L("NARRATOR", "Frame 436.", "Frame four thirty-six."),
        ],
        "post": 3.8, "sfx": ["crickets"],
    },
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"],
     "note": "END CARD: title, next episode, 'Follow the case.', AI disclaimer."},
]
