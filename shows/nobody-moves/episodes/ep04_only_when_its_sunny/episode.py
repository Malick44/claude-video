"""NOBODY MOVES, Episode 4: "Only When It's Sunny".

Pays off Ep. 3's hidden clue (frame 428: the porch step is empty, Lorraine left), then turns to
the one witness who was awake at 03:12 and facing the lawn: Ray the solar frog, who can only talk
after a full day of sun. Day ten, day eleven: cloudy. Mr. Basin appoints himself Ray's counsel.
Day twelve, the sun comes out, Ray lights up, and: "I don't remember." He only remembers back to
his last full charge, which was this afternoon.
New clue: in frame 431 Garrison has turned around, away from Deb. "I was facing the other way."

Ray's night still (library key ray_night) is derived from ray by make_stills.py until a generated
ray_lit exists.
"""

TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 4: ONLY WHEN IT'S SUNNY"
NEXT_UP = "NEXT: EPISODE 5 — SATURDAY"
ANSWER = ("In frame 431 (03:12:21) Garrison has turned around: mirrored, he now faces away from Deb. "
          "He faces her in frame 430 a second earlier (and in every frame before). Five seconds after "
          "Lorraine left the step, the gnome who 'was facing the other way' turned to face the other way. "
          "Pays off in Episode 5, 'Saturday'.")

_STYLE = ("Photorealistic, vertical 9:16. The same suburban house: grey vinyl siding, white porch railing "
          "and posts, black front door, brass lantern sconce, silver tubular wind chime, hostas and an "
          "echinacea flower bed. Dusk, blue hour or night. Shallow depth of field, muted teal-and-amber grade, "
          "fine film grain. No people, no text.")

# New stills this episode would like (all optional: every shot falls back to the series library).
# Both go in the series library, shows/nobody-moves/stills/, since later episodes replay Ray.
STILLS = {
    "ray_lit": ("The exact same shot as the ray still: the same small green resin frog statue with a round solar "
                "panel on its back, same pose and low-angle framing at the front edge of the lawn by the sidewalk, "
                "but at night. His solar light is on: the frog glows softly from inside, the panel shines, and the "
                "grass around him is lit a faint green. The porch lantern glows in the background. (Best made by "
                "editing ray and changing only the time and the light.) " + _STYLE),
    "ray_sun": ("The exact same shot as the ray still, but the clouds have finally broken: warm golden-hour sun "
                "just before sunset, long soft shadows across the lawn, a clear sky, the solar panel on the "
                "frog's back gleaming with a bright reflection. Hopeful, the first sun in twelve days. " + _STYLE),
}

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731

RAY_LIGHT = (0.183, 0.768, 0.02)             # Ray's solar light in yard_after / yard_gone (lit from frame 423 on)
GARRISON_BOX = (0.112, 0.486, 0.215, 0.612)  # Garrison in yard_gone: mirrored in frame 431, he faces away from Deb
RAY_DAY_VIEWS = [V("ray", (0.42, 0.66, 1.4), (0.40, 0.665, 1.55)),          # Ray above the caption band
                 V("yard_after", (0.19, 0.775, 4.5), (0.19, 0.778, 5.0), "longlens")]
RAY_NIGHT_VIEWS = [V("ray_lit", (0.42, 0.66, 1.4), (0.40, 0.665, 1.55)),
                   V("ray_night", (0.42, 0.66, 1.4), (0.40, 0.665, 1.55)),
                   V("ray", (0.42, 0.66, 1.4), (0.40, 0.665, 1.55))]
BASIN_VIEWS = [V("basin_counsel", (0.5, 0.55, 1.05), (0.5, 0.58, 1.25)),
               V("porch", (0.6, 0.64, 1.05), (0.63, 0.62, 1.32))]
BOARD_POLAROIDS = [
    ("yard_before", (0.478, 0.380, 0.829), "DEB (MOVED)", 0.50, 0.40, 620, -2.5, None),
    ("garrison", (0.228, 0.335, 0.717), "GARRISON", 0.24, 0.24, 420, 4, None),
    ("yard_gone", (0.680, 0.200, 0.808), "LORRAINE (LEFT)", 0.77, 0.23, 420, -5, None),
    ("porch", (0.234, 0.466, 0.978), "MR. BASIN, ESQ.", 0.29, 0.58, 420, -3, None),
    ("yard_after", (0.130, 0.745, 0.250), "RAY (FORGOT)", 0.72, 0.58, 420, 5, None),
]

SHOTS = [
    # --- hook: Garrison, defensive as ever, points at the one witness who wasn't
    {
        "id": "hook", "kind": "still", "note": "EXTREME CLOSE-UP: Garrison.",
        "views": [V("garrison", (0.5, 0.5, 1.2), (0.5, 0.47, 1.36))],
        "items": [
            L("GARRISON", "Everybody on this lawn was facing the other way, kid."),
            P(0.45),
            L("GARRISON", "Except the frog."),
        ],
        "post": 0.3,
        "lower_third": ("GARRISON", "Garden gnome · Flower bed, No. 7", "Facing: the other way"),
    },
    {
        "id": "title", "kind": "title", "note": "Title card over a piano sting.",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 3.2, "sfx": ["sting"],
    },
    # --- pay off Ep. 3: replay frames 427/428 and push in on the empty step
    {
        "id": "replay", "kind": "doorbell",
        "note": ("DOORBELL CAM REPLAY: frames 427 to 428 again, the camera pushing in on the porch step. "
                 "Frame 428: the step is empty. Pauses on 'LORRAINE LEFT.'"),
        "frame_a": "yard_after", "frame_b": "yard_gone",
        "clock_start": "03:12:11", "jump_after": 5, "frames": (427, 428),
        "lit": [RAY_LIGHT],
        "kb": ((0.5, 0.5, 1.0), (0.72, 0.28, 2.2)),
        "cta": ("LORRAINE", "LEFT."), "cta_sub": "You found it. Frame 428.",
        "items": [
            L("NARRATOR", "Last week, you found an empty step."),
            P(0.4),
            L("NARRATOR", "Frame 428.", "Frame four twenty-eight."),
        ],
        "post": 3.6, "sfx": ["crickets"],
    },
    # --- the one witness who was awake
    {
        "id": "ray", "kind": "still", "note": "Ray the solar frog under grey skies. Unlit.",
        "views": RAY_DAY_VIEWS,
        "items": [
            L("NARRATOR", "At 3:12, one witness was awake.", "At three twelve, one witness was awake."),
            P(0.4),
            L("NARRATOR", "Ray has not been charged."),
            P(0.5),
            L("NARRATOR", "With anything."),
        ],
        "post": 0.35,
        "lower_third": ("RAY", "Solar frog · Edge of the lawn", "Battery: 2%"),
    },
    {"id": "q1", "kind": "qcard", "text": "Ray. What did you see at 3:12 AM?", "items": [], "min": 2.6,
     "note": "BLACK CARD."},
    # --- no answer. The score drops out for the wait.
    {
        "id": "wait", "kind": "still", "note": "Ray, tighter. Silence. The days go by.",
        "views": [V("ray", (0.41, 0.64, 1.7), (0.40, 0.64, 1.85)),
                  V("yard_after", (0.19, 0.775, 5.0), (0.19, 0.778, 5.4), "longlens")],
        "items": [
            P(1.3),
            L("NARRATOR", "Day ten. Cloudy."),
            P(0.45),
            L("NARRATOR", "Day eleven. Cloudier."),
        ],
        "post": 0.4, "music": "out",
    },
    {
        "id": "basin", "kind": "still", "note": "Mr. Basin, self-appointed counsel for the frog.",
        "views": BASIN_VIEWS,
        "items": [
            L("MR. BASIN", "Until the frog has counsel, the frog has no comment."),
            P(0.55),
            L("NARRATOR", "The frog has no power."),
        ],
        "post": 0.35,
        "lower_third": ("MR. BASIN", "Birdbath · Attorney for the frog", "Appointed by: himself"),
    },
    # --- day twelve
    {
        "id": "sun", "kind": "still", "note": "The sun, finally.",
        "views": [V("ray_sun", (0.42, 0.62, 1.3), (0.41, 0.63, 1.45)),
                  V("holes", (0.3, 0.3, 1.6), (0.28, 0.28, 1.75))],
        "items": [
            L("NARRATOR", "Day twelve."),
            P(0.4),
            L("NARRATOR", "The sun came out."),
        ],
        "post": 0.5,
    },
    {
        "id": "testimony", "kind": "still", "note": "NIGHT. Ray, lit up and delighted.",
        "views": RAY_NIGHT_VIEWS,
        "items": [
            P(0.3),
            L("RAY", "Hi! Wow. What a day, huh?"),
            P(0.45),
            L("NARRATOR", "Ray. June 14th. 3:12 AM. What did you see?",
              "Ray. June fourteenth. Three twelve AM. What did you see?"),
            P(1.0),
            L("RAY", "I don't remember."),
        ],
        "post": 0.4,
        "lower_third": ("RAY", "Solar frog · Edge of the lawn", "Battery: 100%"),
    },
    {
        "id": "memory", "kind": "still", "note": "Ray, tighter, beaming.",
        "views": [V("ray_lit", (0.41, 0.62, 1.75), (0.40, 0.61, 1.95)),
                  V("ray_night", (0.41, 0.62, 1.75), (0.40, 0.61, 1.95)),
                  V("ray", (0.41, 0.62, 1.75), (0.40, 0.61, 1.95))],
        "items": [
            L("NARRATOR", "Ray only remembers back to his last full charge."),
            P(0.5),
            L("NARRATOR", "That was this afternoon."),
            P(0.4),
            L("RAY", "It was a great afternoon."),
        ],
        "post": 0.35,
    },
    {
        "id": "garrison", "kind": "still", "note": "INTERVIEW: Garrison, bitter.",
        "views": [V("garrison", (0.5, 0.56, 1.0), (0.49, 0.53, 1.18))],
        "items": [
            L("GARRISON", "Twelve days for \"I don't remember.\""),
            P(0.45),
            L("GARRISON", "I've been not remembering for thirty-one years."),
        ],
        "post": 0.35,
        "lower_third": ("GARRISON", "Garden gnome · Flower bed, No. 7", "Memory: selective"),
        "lower_third_at": "last",
    },
    {
        "id": "board", "kind": "board", "card": "WHO ELSE WAS AWAKE?",
        "note": "EVIDENCE BOARD, updated: Lorraine (LEFT), Ray (FORGOT).",
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.53, 1.18)),   # ends framed low: the index card stays above every app's description
        "polaroids": BOARD_POLAROIDS,
        "items": [
            L("NARRATOR", "Our best witness was awake at 3:12.", "Our best witness was awake at three twelve."),
            P(0.4),
            L("NARRATOR", "He remembers nothing."),
            P(0.5),
            L("NARRATOR", "So who else was up?"),
        ],
        "post": 0.6, "sfx": ["sting_soft"],
    },
    # --- new cliffhanger: frame 431, Garrison has turned around (Ray still lit, the step still empty)
    {
        "id": "doorbell", "kind": "doorbell",
        "note": ("DOORBELL CAM, a few seconds later. The camera drifts toward Ray at the edge of the lawn. Jump cut "
                 "to frame 431; on 'Frame 431' the frames flicker. In 431 Garrison has turned around, away from "
                 "Deb. Pauses on 'SOMEONE LOOKED AWAY.'"),
        "frame_a": "yard_gone", "frame_b": "yard_gone",
        "clock_start": "03:12:17", "jump_after": 4, "frames": (430, 431),
        "lit": [RAY_LIGHT],
        "alter_box": GARRISON_BOX,
        "kb": ((0.5, 0.5, 1.0), (0.32, 0.62, 1.3)),   # ends with Garrison above the call to action
        "cta": ("SOMEONE", "LOOKED AWAY."), "cta_sub": "Comment who + the frame ↓",
        "items": [
            L("NARRATOR", "Ray doesn't remember 3:12.", "Ray doesn't remember three twelve."),
            P(0.45),
            L("NARRATOR", "Someone else on this lawn does."),
            P(0.5),
            L("NARRATOR", "Frame 431.", "Frame four thirty-one."),
        ],
        "post": 3.8, "sfx": ["crickets"],
    },
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"],
     "note": "END CARD: title, next episode, 'Follow the case.', AI disclaimer."},
]
