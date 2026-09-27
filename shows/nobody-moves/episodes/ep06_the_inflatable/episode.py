"""NOBODY MOVES, Episode 6: "The Inflatable".

Pays off Ep. 5's hidden clue early (frame 436: Lorraine is back on the porch step after thirteen
seconds). "They had my size, hon." Then a new witness: Dale, the inflatable snowman in the side
yard that nobody took down after Christmas. It's June. His alibi is airtight: he's on a timer, up
at 5 PM, flat at 11, so at 3:12 AM he was flat. Then the timer turns up, and one extra pin is
pushed in: 3:00 to 3:15 AM. At 3:12 he was eight feet tall. He didn't set it ("I don't have
hands"), and timers don't set themselves: somebody was in this yard.
New clue: in frame 530 (03:15:00), the moment the timer clicks off, the window beside the porch
of No. 7 lights up. Somebody inside is awake.

Every doorbell frame is a library still (yard_turned, yard_back) plus render-time lights, so this
episode needs no make_stills.py.
"""

TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 6: THE INFLATABLE"
NEXT_UP = "NEXT: EPISODE 7 — THE FINALE"
ANSWER = ("In frame 530 (03:15:00), the window beside the porch of No. 7 is lit. It's dark in frame 529, "
          "a second and a half earlier, and in every frame of the night before it. It lights the moment the "
          "snowman's timer clicks off: somebody inside No. 7 is awake. Pays off in Episode 7.")

_STYLE = ("Photorealistic, vertical 9:16. The same suburban house: grey vinyl siding, white porch railing "
          "and posts, black front door, brass lantern sconce, silver tubular wind chime, hostas and an "
          "echinacea flower bed. Dusk, blue hour or night. Shallow depth of field, muted teal-and-amber grade, "
          "fine film grain. No people, no text.")

# New stills this episode would like. Every shot falls back to the series library, so it builds
# before these exist; the snowman's fallback is the bare lawn he'd be lying on.
STILLS = {
    "snowman_flat": ("Close-up, low to the ground, of a large deflated Christmas inflatable snowman lying in a "
                     "collapsed heap on green summer grass in the side yard of the same house, at dusk. The "
                     "white nylon is crumpled and sagging, his black top hat folded over, his carrot nose "
                     "drooping, a red scarf in the folds, one stitched smiling face still readable in the "
                     "wrinkles. A small electric blower sits at his base, and a green outdoor extension cord "
                     "runs off out of frame toward the house. Summer flowers and hostas around him make it "
                     "obviously June. Deadpan, like a witness photo. " + _STYLE),
    # Straight-on and dial-filling, or the lone pin doesn't read (a scenic version hid it at the frame edge)
    "timer": ("Night-time evidence photograph, hard on-camera flash, pitch-dark background. Extreme macro "
              "close-up, shot straight on: the round dial of a grey plastic mechanical 24-hour outdoor plug-in "
              "timer fills the centre of the vertical frame, mounted in a weatherproof outlet on grey vinyl "
              "siding. Around the rim of the dial is a ring of small grey plastic tabs. A long continuous arc of "
              "tabs on one side is pushed down. On the opposite side, clearly isolated, exactly ONE single tab "
              "is pushed down, alone, with un-pushed tabs on both sides of it. A green extension cord plug hangs "
              "below. Muted teal-and-amber grade, fine film grain. Photorealistic, vertical 9:16. No readable "
              "numbers, no words, no text, no people."),
}

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731

RAY_LIGHT = (0.183, 0.768, 0.02)   # Ray's solar light, on since frame 423
WINDOW = (0.670, 0.095, 0.02)     # the window between the porch post and the lantern, No. 7
DALE_VIEWS = [V("snowman_flat", (0.45, 0.72, 1.8), (0.44, 0.72, 2.05)),
              V("holes", (0.45, 0.55, 1.4), (0.44, 0.54, 1.58))]
TIMER_VIEWS = [V("timer", (0.49, 0.36, 1.25), (0.49, 0.38, 1.45)),
               V("porch", (0.62, 0.30, 1.8), (0.62, 0.31, 2.1))]
BOARD_POLAROIDS = [
    ("yard_before", (0.478, 0.380, 0.829), "DEB (MOVED)", 0.50, 0.40, 620, -2.5, None),
    ("yard_back", (0.680, 0.200, 0.808), "LORRAINE (13 SEC)", 0.77, 0.23, 420, -5, None),
    ("yard_turned", (0.228, 0.335, 0.717), "GARRISON (AWAY)", 0.24, 0.24, 420, 4, None),
    ("snowman_flat", (0.100, 0.470, 0.800), "DALE (UP)", 0.29, 0.58, 420, -3, None),
    ("timer", (0.120, 0.092, 0.860), "3:00–3:15", 0.72, 0.58, 420, 5, None),
]

SHOTS = [
    # --- hook: a Christmas snowman, still here in June
    {
        "id": "hook", "kind": "still", "note": "EXTREME CLOSE-UP: Dale, flat on the grass.",
        "views": DALE_VIEWS,
        "items": [
            L("DALE", "Nobody took me down after Christmas."),
            P(0.6),
            L("DALE", "It's June."),
        ],
        "post": 0.35,
        "lower_third": ("DALE", "Inflatable snowman · Side yard, No. 7", "Up since: December"),
    },
    {
        "id": "title", "kind": "title", "note": "Title card over a piano sting.",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 3.2, "sfx": ["sting"],
    },
    # --- pay off Ep. 5: replay frames 435/436, the goose is back
    {
        "id": "replay", "kind": "doorbell",
        "note": ("DOORBELL CAM REPLAY: frames 435 to 436 again, the camera pushing in on the porch step. "
                 "Frame 436: Lorraine is back. Pauses on 'SHE CAME BACK.'"),
        "frame_a": "yard_turned", "frame_b": "yard_back",
        "clock_start": "03:12:25", "jump_after": 4, "frames": (435, 436),
        "lit": [RAY_LIGHT],
        "kb": ((0.5, 0.5, 1.0), (0.72, 0.30, 2.1)),
        "cta": ("SHE CAME", "BACK."), "cta_sub": "You found it. Frame 436.",
        "items": [
            L("NARRATOR", "Last week, you found a goose."),
            P(0.4),
            L("NARRATOR", "Frame 436.", "Frame four thirty-six."),
        ],
        "post": 3.6, "sfx": ["crickets"],
    },
    {
        "id": "lorraine", "kind": "still", "note": "INTERVIEW: Lorraine, in the fitting outfit.",
        "views": [V("lorraine_fitting", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22)),
                  V("lorraine", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22))],
        "items": [
            L("NARRATOR", "Thirteen seconds is a short fitting."),
            P(0.6),
            L("LORRAINE", "They had my size, hon."),
        ],
        "post": 0.35,
        "lower_third": ("LORRAINE", "Porch goose · Front steps, No. 7", "Fitting: 13 seconds"),
    },
    {"id": "q1", "kind": "qcard", "text": "Dale. Where were you at 3:12 AM?", "items": [], "min": 2.6,
     "note": "BLACK CARD."},
    # --- the snowman's alibi
    {
        "id": "alibi", "kind": "still", "note": "INTERVIEW: Dale, flat and unbothered.",
        "views": [V("snowman_flat", (0.47, 0.71, 1.6), (0.46, 0.71, 1.75)),
                  V("holes", (0.40, 0.52, 1.8), (0.39, 0.51, 2.0))],
        "items": [
            L("DALE", "Flat."),
            P(0.5),
            L("DALE", "I'm on a timer. Up at 5 PM. Flat at 11.",
              "I'm on a timer. Up at five PM. Flat at eleven."),
            P(0.5),
            L("NARRATOR", "An airtight alibi."),
        ],
        "post": 0.3,
    },
    # --- the punchline lands in silence: the score cuts for this shot only
    {
        "id": "airtight", "kind": "still", "note": "Dale, tighter. No score under this one.",
        "views": [V("snowman_flat", (0.42, 0.71, 2.3), (0.41, 0.71, 2.5)),
                  V("holes", (0.38, 0.5, 2.1), (0.37, 0.5, 2.3))],
        "items": [
            P(0.3),
            L("DALE", "Nothing about me is airtight."),
        ],
        "post": 0.6, "music": "out",
    },
    {
        "id": "basin", "kind": "still", "note": "Mr. Basin, uninvited again.",
        "views": [V("basin_counsel", (0.5, 0.55, 1.05), (0.5, 0.58, 1.25)),
                  V("porch", (0.6, 0.64, 1.05), (0.63, 0.62, 1.32))],
        "items": [
            L("MR. BASIN", "My client has no comment."),
            P(0.45),
            L("NARRATOR", "He isn't your client."),
            P(0.4),
            L("MR. BASIN", "Then he has no counsel. And no comment."),
        ],
        "post": 0.35,
        "lower_third": ("MR. BASIN", "Birdbath · Attorney for the snowman", "Retained by: nobody"),
    },
    # --- the timer: one extra pin
    {
        "id": "exhibit", "kind": "evidence", "label": "EXHIBIT C", "stamp": "06/14 · OUTLET, SIDE OF NO. 7",
        "note": "CAMERA FLASH. The snowman's timer. Circle the one lone pin pushed in at 3 AM.",
        "views": TIMER_VIEWS,
        "items": [
            P(0.25),
            L("NARRATOR", "Then we found his timer."),
            P(0.4),
            L("NARRATOR", "5 PM to 11.", "Five PM to eleven."),
            P(0.45),
            L("NARRATOR", "And one more pin."),
        ],
        "annot_circles": [(0.490, 0.491, 0.035)],   # the lone pin
        "post": 0.5, "sfx": ["shutter"],
    },
    {
        "id": "pin", "kind": "still", "note": "The dial, tighter on the lone pin.",
        "views": [V("timer", (0.485, 0.55, 2.2), (0.485, 0.56, 2.5)),
                  V("porch", (0.62, 0.31, 2.3), (0.62, 0.32, 2.6))],
        "items": [
            L("NARRATOR", "3 AM to 3:15.", "Three AM to three fifteen."),
            P(0.5),
            L("NARRATOR", "At 3:12, Dale was eight feet tall.", "At three twelve, Dale was eight feet tall."),
        ],
        "post": 0.4,
    },
    {
        "id": "hands", "kind": "still", "note": "Dale, flat. He didn't set it.",
        "views": [V("snowman_flat", (0.48, 0.70, 1.5), (0.47, 0.71, 1.7)),
                  V("holes", (0.42, 0.53, 1.6), (0.41, 0.52, 1.78))],
        "items": [
            L("DALE", "I didn't set that."),
            P(0.45),
            L("DALE", "I don't have hands."),
            P(0.55),
            L("DALE", "I barely have a shape."),
        ],
        "post": 0.35,
        "lower_third": ("DALE", "Inflatable snowman · Side yard, No. 7", "Hands: none"),
        "lower_third_at": "last",
    },
    {
        "id": "board", "kind": "board", "card": "WHO SET THE TIMER?",
        "note": "EVIDENCE BOARD, updated: Lorraine (13 SEC), Dale (UP), the timer.",
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.53, 1.18)),   # ends framed low: the index card stays above every app's description
        "polaroids": BOARD_POLAROIDS,
        "items": [
            L("NARRATOR", "Snowmen don't push pins."),
            P(0.4),
            L("NARRATOR", "Somebody set this timer."),
            P(0.5),
            L("NARRATOR", "Somebody was in this yard."),
        ],
        "post": 0.6, "sfx": ["sting_soft"],
    },
    # --- new cliffhanger: frame 530, the timer clicks off and the window beside the porch lights up
    {
        "id": "doorbell", "kind": "doorbell",
        "note": ("DOORBELL CAM, two and a half minutes later. The camera drifts toward the porch. Jump cut to "
                 "frame 530; on 'Frame 530' the frames flicker. In 530 the window beside the porch is lit. "
                 "Pauses on 'WHAT CHANGED AT 3:15?'"),
        "frame_a": "yard_back", "frame_b": "yard_back",
        "clock_start": "03:14:56", "jump_after": 4, "frames": (529, 530),
        "lit": [RAY_LIGHT],
        "alter_glow": WINDOW,
        "kb": ((0.5, 0.5, 1.0), (0.64, 0.30, 1.7)),   # ends on the porch and the window, above the call to action
        "cta": ("WHAT CHANGED", "AT 3:15?"), "cta_sub": "Comment the frame ↓",
        "items": [
            L("NARRATOR", "At 3:15, the timer clicked off.", "At three fifteen, the timer clicked off."),
            P(0.45),
            L("NARRATOR", "Dale went flat. The yard went still."),
            P(0.5),
            L("NARRATOR", "Frame 530.", "Frame five thirty."),
        ],
        "post": 3.8, "sfx": ["crickets"],
    },
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"],
     "note": "END CARD: title, next episode, 'Follow the case.', AI disclaimer."},
]
