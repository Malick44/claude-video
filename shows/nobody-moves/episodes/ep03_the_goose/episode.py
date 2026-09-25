"""NOBODY MOVES, Episode 3: "The Goose".

Pays off Ep. 2's hidden clue (frame 423: Ray the solar frog was lit, so he was awake), then
turns on Lorraine: she swears she wore the bumblebee that night, is in an Easter dress after
the next cut, and Exhibit A shows her wearing nothing at all. "I don't pick them, detective."
New clue: in frame 428 the porch step is empty. Lorraine is gone.

The clue frame (library still yard_gone) is derived from yard_after by make_stills.py.
"""

TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 3: THE GOOSE"
NEXT_UP = "NEXT: EPISODE 4 — ONLY WHEN IT'S SUNNY"
ANSWER = ("In frame 428 (03:12:16) the porch step is empty: Lorraine is gone. She is there in frame 427 "
          "a second earlier (and in frame 423). The goose who 'doesn't go anywhere' left the porch 16 "
          "seconds after Deb moved. Pays off in Episode 5, 'Saturday'.")

_STYLE = ("Photorealistic, vertical 9:16. The same suburban house: grey vinyl siding, white porch railing "
          "and posts, black front door, brass lantern sconce, silver tubular wind chime, hostas and an "
          "echinacea flower bed. Dusk, blue hour or night. Shallow depth of field, muted teal-and-amber grade, "
          "fine film grain. No people, no text.")

# New stills this episode would like (all optional: every shot falls back to the series library).
# All three are in the series library, shows/nobody-moves/stills/: the outfits are a running gag
# (Ep. 5's "fitting") and Ray testifies in Ep. 4.
STILLS = {
    "lorraine_bee": ("Close-up portrait of a white ceramic goose statue sitting on the concrete front step of the "
                     "porch, wearing a homemade bumblebee costume: a snug yellow-and-black striped knit sweater, "
                     "small sheer wings, and a headband with two bobbling antennae. 3/4 view with its beak "
                     "pointing to frame-left, calm and dignified, framed like the subject of a true-crime "
                     "documentary interview, 85mm lens, warm key light from the lantern. " + _STYLE),
    "lorraine_easter": ("The exact same shot as lorraine_bee: same goose, same pose, framing and lantern light, "
                        "but now wearing a pastel-yellow Easter dress with a white lace collar and a small straw "
                        "bonnet tied with a lavender ribbon. (Best made by editing lorraine_bee and changing only "
                        "the outfit.) " + _STYLE),
    "ray": ("Low-angle documentary portrait of a small green resin frog statue with a round solar panel on its "
            "back, sitting in the grass at the front edge of the lawn by the sidewalk, under a heavy grey "
            "overcast sky at dusk, flat light, the solar panel dull, patient and slightly forlorn. " + _STYLE),
}

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731

LORRAINE_BEE_VIEWS = [V("lorraine_bee", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22)),
                      V("lorraine", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22)),
                      V("yard_before", (0.744, 0.245, 3.0), (0.744, 0.25, 3.35), "longlens")]
LORRAINE_EASTER_VIEWS = [V("lorraine_easter", (0.5, 0.48, 1.1), (0.5, 0.46, 1.25)),
                         V("lorraine", (0.5, 0.48, 1.12), (0.5, 0.47, 1.3)),
                         V("yard_before", (0.744, 0.25, 3.4), (0.744, 0.252, 3.7), "longlens")]
BASIN_VIEWS = [V("basin_counsel", (0.5, 0.55, 1.05), (0.5, 0.58, 1.25)),
               V("porch", (0.6, 0.64, 1.05), (0.63, 0.62, 1.32))]
RAY_LIGHT = (0.183, 0.768, 0.02)   # Ray's solar light in yard_after (lit from frame 423 on)
BOARD_POLAROIDS = [
    ("yard_before", (0.478, 0.380, 0.829), "DEB (MOVED)", 0.50, 0.40, 620, -2.5, None),
    ("garrison", (0.228, 0.335, 0.717), "GARRISON", 0.24, 0.24, 420, 4, None),
    ("yard_before", (0.680, 0.200, 0.808), "LORRAINE (NO BEE)", 0.77, 0.23, 420, -5, None),
    ("porch", (0.234, 0.466, 0.978), "MR. BASIN, ESQ.", 0.29, 0.58, 420, -3, None),
    ("yard_after", (0.130, 0.745, 0.250), "RAY (AWAKE)", 0.72, 0.58, 420, 5, None),
]

SHOTS = [
    # --- hook: Lorraine, in the bumblebee
    {
        "id": "hook", "kind": "still", "note": "EXTREME CLOSE-UP: Lorraine in the bumblebee costume.",
        "views": LORRAINE_BEE_VIEWS,
        "items": [
            L("LORRAINE", "That night? I was wearing the bumblebee, hon."),
            P(0.45),
            L("LORRAINE", "I remember, because it itches."),
        ],
        "post": 0.3,
        "lower_third": ("LORRAINE", "Porch goose · Front steps, No. 7", "Wearing: the bumblebee (she says)"),
    },
    {
        "id": "title", "kind": "title", "note": "Title card over a piano sting.",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 3.2, "sfx": ["sting"],
    },
    # --- pay off Ep. 2: replay frames 422/423 and push in on Ray
    {
        "id": "replay", "kind": "doorbell",
        "note": ("DOORBELL CAM REPLAY: frames 422 to 423 again, the camera pushing in on the edge of the lawn. "
                 "Frame 423: Ray the solar frog is glowing. Pauses on 'RAY WAS AWAKE.'"),
        "frame_a": "yard_after", "frame_b": "yard_after",
        "clock_start": "03:12:04", "jump_after": 4, "frames": (422, 423),
        "alter_glow": RAY_LIGHT,
        "kb": ((0.5, 0.5, 1.0), (0.22, 0.8, 2.6)),
        "cta": ("RAY WAS", "AWAKE."), "cta_sub": "You found him. Frame 423.",
        "items": [
            L("NARRATOR", "Last week, you found a witness nobody interviewed."),
            P(0.4),
            L("NARRATOR", "Frame 423.", "Frame four twenty-three."),
        ],
        "post": 3.6, "sfx": ["crickets"],
    },
    {
        "id": "ray", "kind": "still", "note": "Ray the solar frog under grey skies. Unlit.",
        "views": [V("ray", (0.42, 0.66, 1.4), (0.40, 0.665, 1.55)),   # Ray above the caption band
                  V("yard_after", (0.19, 0.775, 4.5), (0.19, 0.778, 5.0), "longlens")],
        "items": [
            L("NARRATOR", "Ray only lights up after a full day of sun."),
            P(0.35),
            L("NARRATOR", "We asked Ray for comment."),
            P(0.6),
            L("NARRATOR", "It has been cloudy for nine days."),
        ],
        "post": 0.4,
        "lower_third": ("RAY", "Solar frog · Edge of the lawn", "Battery: 4%"),
        "lower_third_at": "last",
    },
    {"id": "q1", "kind": "qcard", "text": "Lorraine. What were you wearing that night?", "items": [], "min": 2.6,
     "note": "BLACK CARD."},
    # --- after the cut she is in an Easter dress; nobody mentions it
    {
        "id": "lorraine", "kind": "still", "note": "INTERVIEW: Lorraine, now in an Easter dress. Nobody mentions it.",
        "views": LORRAINE_EASTER_VIEWS,
        "items": [
            L("LORRAINE", "The bumblebee, hon. Like I said."),
            P(0.45),
            L("LORRAINE", "I always wear the bumblebee in June."),
            P(0.45),
            L("LORRAINE", "It's seasonal."),
        ],
        "post": 0.35,
        "lower_third": ("LORRAINE", "Porch goose · Front steps, No. 7", "Now wearing: Easter"),
    },
    # --- Exhibit A, again: no bumblebee. The score drops out for the reveal.
    {
        "id": "exhibit", "kind": "evidence", "label": "EXHIBIT A", "stamp": "06/14 · 5:41 AM",
        "note": "CAMERA FLASH. Exhibit A again, pushed in on the porch; a yellow circle around Lorraine. Plain white. Silence.",
        "views": [V("yard_after", (0.7, 0.3, 2.0), (0.75, 0.26, 2.8))],
        "items": [
            P(0.25),
            L("NARRATOR", "We went back to Exhibit A."),
            P(0.3),
            P(0.3),
            L("NARRATOR", "Lorraine is not wearing the bumblebee."),
            P(0.7),
            L("NARRATOR", "Lorraine is not wearing anything."),
        ],
        "annot_circles": [(0.75, 0.25, 0.04)],
        "post": 0.5, "sfx": ["shutter"], "music": "out",
    },
    {
        "id": "between", "kind": "still", "note": "Lorraine, unbothered.",
        "views": LORRAINE_EASTER_VIEWS,
        "items": [L("LORRAINE", "I was between outfits, hon."), P(0.45), L("LORRAINE", "It happens.")],
        "post": 0.3,
    },
    {"id": "q2", "kind": "qcard", "text": "Who changes your outfits?", "items": [], "min": 2.2,
     "note": "BLACK CARD."},
    {
        "id": "detective", "kind": "still", "note": "Lorraine, tighter. The warmth is gone.",
        "views": [V("lorraine_easter", (0.5, 0.44, 1.35), (0.5, 0.43, 1.55)),
                  V("lorraine", (0.5, 0.44, 1.35), (0.5, 0.43, 1.55)),
                  V("yard_before", (0.744, 0.243, 3.9), (0.744, 0.243, 4.3), "longlens")],
        "items": [
            P(0.8),
            L("LORRAINE", "I don't pick them, detective."),
            P(0.6),
            L("NARRATOR", "Lorraine has never called us detective before."),
        ],
        "post": 0.4,
    },
    {"id": "q3", "kind": "qcard", "text": "Garrison. Who dresses the goose?", "items": [], "min": 2.3,
     "note": "BLACK CARD."},
    {
        "id": "garrison", "kind": "still", "note": "INTERVIEW: Garrison, bitter.",
        "views": [V("garrison", (0.5, 0.56, 1.0), (0.49, 0.53, 1.18))],
        "items": [
            L("GARRISON", "Eleven outfits since March, kid."),
            P(0.4),
            L("GARRISON", "I've had this hat since 1994.", "I've had this hat since nineteen ninety-four."),
            P(0.55),
            L("NARRATOR", "Garrison was facing the other way for all eleven."),
        ],
        "post": 0.35,
        "lower_third": ("GARRISON", "Garden gnome · Flower bed, No. 7", "Hat: original"),
        "lower_third_at": "last",
    },
    {
        "id": "basin", "kind": "still", "note": "Mr. Basin, through counsel.",
        "views": BASIN_VIEWS,
        "items": [
            L("MR. BASIN", "Objection."),
            P(0.6),
            L("NARRATOR", "There is no judge."),
        ],
        "post": 0.35,
        "lower_third": ("MR. BASIN", "Birdbath · Attorney for Mr. Basin", "Objecting"),
    },
    {
        "id": "board", "kind": "board", "card": "WHO DRESSES THE GOOSE?",
        "note": "EVIDENCE BOARD, updated: Lorraine (NO BEE), Ray (AWAKE).",
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.53, 1.18)),   # ends framed low: the index card stays above every app's description
        "polaroids": BOARD_POLAROIDS,
        "items": [
            L("NARRATOR", "At 3:12 AM, someone moved Deb.", "At three twelve AM, someone moved Deb."),
            P(0.4),
            L("NARRATOR", "And someone keeps changing the goose."),
            P(0.5),
            L("NARRATOR", "What if it's the same someone?"),
        ],
        "post": 0.6, "sfx": ["sting_soft"],
    },
    # --- new cliffhanger: frame 428, the porch step is empty (Ray still lit from 423)
    {
        "id": "doorbell", "kind": "doorbell",
        "note": ("DOORBELL CAM, a few seconds later. Jump cut to frame 428; on 'Frame 428' the frames flicker. "
                 "In 428 the porch step is empty: Lorraine is gone. Pauses on 'SOMEONE WASN'T RIGHT HERE.'"),
        "frame_a": "yard_after", "frame_b": "yard_gone",
        "clock_start": "03:12:11", "jump_after": 5, "frames": (427, 428),
        "lit": [RAY_LIGHT],
        "kb": ((0.5, 0.5, 1.0), (0.46, 0.53, 1.05)),
        "cta": ("SOMEONE WASN'T", "RIGHT HERE."), "cta_sub": "Comment who + the frame ↓",
        "items": [
            L("NARRATOR", "Everyone on Birchwood Court says they were right here."),
            P(0.5),
            L("NARRATOR", "Frame 428.", "Frame four twenty-eight."),
        ],
        "post": 3.8, "sfx": ["crickets"],
    },
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"],
     "note": "END CARD: title, next episode, 'Follow the case.', AI disclaimer."},
]
