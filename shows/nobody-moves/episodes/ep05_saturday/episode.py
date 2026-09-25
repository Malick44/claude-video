"""NOBODY MOVES, Episode 5: "Saturday".

Pays off Ep. 4's hidden clue (frame 431: Garrison turned his back on Deb): "A gentleman turns
around, kid." From what? "The fitting." Lorraine was at a fitting at 3:12 AM, to look nice for
Saturday, the street's most feared day: the Mower, shown only as a shadow, picks everyone up and
puts them back. Never three feet off.
New clue: two minutes before Deb moved, in frame 343 (03:10:00), a long shadow reaches across the
lawn from something off-frame. Pays off in Ep. 6, "The Inflatable".

The clue frame (library still yard_shadow) and the Mower stand-in (mower_shadow, this episode's
stills/) are derived by make_stills.py.
"""

TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 5: SATURDAY"
NEXT_UP = "NEXT: EPISODE 6 — THE INFLATABLE"
ANSWER = ("In frame 343 (03:10:00) a long, rounded shadow reaches across the lawn from the left edge: "
          "something off-frame stood up under the street light two minutes before Deb moved. It is not in "
          "frame 342 a second earlier, and it is gone by frame 417 (03:11:59). Pays off in Episode 6, "
          "'The Inflatable': its timer is set for 3:10 AM.")

_STYLE = ("Photorealistic, vertical 9:16. The same suburban house: grey vinyl siding, white porch railing "
          "and posts, black front door, brass lantern sconce, silver tubular wind chime, hostas and an "
          "echinacea flower bed. Dusk, blue hour or night. Shallow depth of field, muted teal-and-amber grade, "
          "fine film grain. No people, no text.")

# New stills this episode would like (all optional: every shot falls back to the library or a derived still).
STILLS = {
    "lorraine_fitting": ("The exact same shot as the lorraine still: the same white ceramic goose on the porch step, "
                         "same pose, framing and lantern light, but mid-fitting: a half-finished outfit of pale "
                         "tailor's muslin pinned around her, a yellow tape measure draped over her neck, a few "
                         "pins and chalk marks. (Best made by editing lorraine and changing only the outfit.) "
                         + _STYLE),
    "mower": ("Morning, low golden sun behind the house. The front lawn at grass level: the long, dark shadow of a "
              "push lawn mower and the one pushing it stretches across the freshly striped grass toward the "
              "camera. The mower itself is out of frame; only its shadow is seen. Ominous, framed like a "
              "horror film. " + _STYLE),
}

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731

RAY_LIGHT = (0.183, 0.768, 0.02)             # Ray's solar light in yard_after / yard_gone (lit from frame 423 on)
GARRISON_BOX = (0.112, 0.486, 0.215, 0.612)  # Garrison in yard_gone: mirrored in frame 431
LORRAINE_VIEWS = [V("lorraine_fitting", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22)),
                  V("lorraine", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22)),
                  V("yard_before", (0.744, 0.245, 3.0), (0.744, 0.25, 3.35), "longlens")]
BASIN_VIEWS = [V("basin_counsel", (0.5, 0.55, 1.05), (0.5, 0.58, 1.25)),
               V("porch", (0.6, 0.64, 1.05), (0.63, 0.62, 1.32))]
BOARD_POLAROIDS = [
    ("yard_before", (0.478, 0.380, 0.829), "DEB (MOVED)", 0.50, 0.40, 620, -2.5, None),
    ("garrison", (0.228, 0.335, 0.717), "GARRISON (TURNED)", 0.24, 0.24, 420, 4, None),
    ("yard_gone", (0.680, 0.200, 0.808), "LORRAINE (FITTING)", 0.77, 0.23, 420, -5, None),
    ("porch", (0.234, 0.466, 0.978), "MR. BASIN, ESQ.", 0.29, 0.58, 420, -3, None),
    ("yard_after", (0.130, 0.745, 0.250), "RAY (FORGOT)", 0.72, 0.58, 420, 5, None),
]

SHOTS = [
    # --- hook: Garrison, doubling down
    {
        "id": "hook", "kind": "still", "note": "EXTREME CLOSE-UP: Garrison.",
        "views": [V("garrison", (0.5, 0.5, 1.2), (0.5, 0.47, 1.36))],
        "items": [
            L("GARRISON", "I was facing the other way, kid."),
            P(0.45),
            L("GARRISON", "I'm always facing the other way."),
        ],
        "post": 0.3,
        "lower_third": ("GARRISON", "Garden gnome · Flower bed, No. 7", "Facing: under review"),
    },
    {
        "id": "title", "kind": "title", "note": "Title card over a piano sting.",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 3.2, "sfx": ["sting"],
    },
    # --- pay off Ep. 4: replay frames 430/431 and push in on Garrison
    {
        "id": "replay", "kind": "doorbell",
        "note": ("DOORBELL CAM REPLAY: frames 430 to 431 again, the camera pushing in on the flower bed. "
                 "Frame 431: Garrison has turned his back on Deb. Pauses on 'GARRISON TURNED.'"),
        "frame_a": "yard_gone", "frame_b": "yard_gone",
        "clock_start": "03:12:17", "jump_after": 4, "frames": (430, 431),
        "lit": [RAY_LIGHT],
        "alter_box": GARRISON_BOX,
        "kb": ((0.5, 0.5, 1.0), (0.2, 0.6, 2.2)),     # ends with Garrison above the call to action
        "cta": ("GARRISON", "TURNED."), "cta_sub": "You found him. Frame 431.",
        "items": [
            L("NARRATOR", "Last week, you found a gnome who turned his back."),
            P(0.4),
            L("NARRATOR", "Frame 431.", "Frame four thirty-one."),
        ],
        "post": 3.6, "sfx": ["crickets"],
    },
    {
        "id": "gentleman", "kind": "still", "note": "INTERVIEW: Garrison, dignified.",
        "views": [V("garrison", (0.5, 0.56, 1.0), (0.49, 0.53, 1.18))],
        "items": [
            L("GARRISON", "A gentleman turns around, kid."),
            P(0.5),
            L("NARRATOR", "From what?"),
            P(0.6),
            L("GARRISON", "The fitting."),
        ],
        "post": 0.35,
    },
    # --- where Lorraine went at 03:12:16
    {
        "id": "lorraine", "kind": "still", "note": "INTERVIEW: Lorraine, mid-alterations.",
        "views": LORRAINE_VIEWS,
        "items": [
            L("LORRAINE", "I was at a fitting, hon."),
            P(0.45),
            L("LORRAINE", "You have to look nice for Saturday."),
        ],
        "post": 0.3,
        "lower_third": ("LORRAINE", "Porch goose · Front steps, No. 7", "Wearing: alterations"),
    },
    {"id": "q1", "kind": "qcard", "text": "Who does your fittings?", "items": [], "min": 2.2,
     "note": "BLACK CARD."},
    {
        "id": "tailor", "kind": "still", "note": "Lorraine, tighter. Warm, and closed.",
        "views": [V("lorraine_fitting", (0.5, 0.44, 1.35), (0.5, 0.43, 1.55)),
                  V("lorraine", (0.5, 0.44, 1.35), (0.5, 0.43, 1.55)),
                  V("yard_before", (0.744, 0.243, 3.9), (0.744, 0.243, 4.3), "longlens")],
        "items": [
            L("LORRAINE", "A professional, hon."),
            P(0.5),
            L("LORRAINE", "Very discreet."),
        ],
        "post": 0.35,
    },
    {"id": "q2", "kind": "qcard", "text": "What happens on Saturday?", "items": [], "min": 2.2,
     "note": "BLACK CARD."},
    {
        "id": "basin", "kind": "still", "note": "Mr. Basin, through counsel.",
        "views": BASIN_VIEWS,
        "items": [
            L("MR. BASIN", "My client does not discuss Saturday."),
            P(0.5),
            L("NARRATOR", "Every Saturday, Mr. Basin is emptied and scrubbed."),
            P(0.4),
            L("MR. BASIN", "Objection."),
        ],
        "post": 0.35,
        "lower_third": ("MR. BASIN", "Birdbath · Attorney for Mr. Basin", "Scrubbed: weekly"),
    },
    # --- the reenactment. The score drops out: dread.
    {
        "id": "mower", "kind": "still", "note": "RECONSTRUCTION: the lawn at dawn. The Mower, seen only as a shadow. Silence.",
        "views": [V("mower", (0.5, 0.5, 1.05), (0.52, 0.55, 1.22)),
                  V("mower_shadow", (0.5, 0.5, 1.05), (0.52, 0.55, 1.22))],
        "items": [
            P(0.3),
            L("NARRATOR", "What follows is a reenactment."),
            P(0.6),
            L("NARRATOR", "Saturday. 7 AM.", "Saturday. Seven AM."),
            P(0.6),
            L("NARRATOR", "The Mower."),
        ],
        "post": 0.6, "music": "out",
    },
    {
        "id": "saturday", "kind": "still", "note": "The cul-de-sac from above: the Mower's territory.",
        "views": [V("aerial", (0.5, 0.5, 1.15), (0.5, 0.53, 1.32))],
        "items": [
            L("NARRATOR", "Every Saturday, the Mower picks everyone up."),
            P(0.35),
            L("NARRATOR", "And puts them back."),
            P(0.5),
            L("NARRATOR", "Never three feet off."),
        ],
        "post": 0.35,
    },
    {
        "id": "garrison", "kind": "still", "note": "Garrison, haunted.",
        "views": [V("garrison", (0.5, 0.52, 1.25), (0.5, 0.5, 1.4))],
        "items": [
            L("GARRISON", "Thirty-one years of Saturdays, kid."),
            P(0.45),
            L("GARRISON", "I've never once looked."),
        ],
        "post": 0.35,
    },
    {
        "id": "board", "kind": "board", "card": "WHO WAS AT THE FITTING?",
        "note": "EVIDENCE BOARD, updated: Garrison (TURNED), Lorraine (FITTING).",
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.53, 1.18)),   # ends framed low: the index card stays above every app's description
        "polaroids": BOARD_POLAROIDS,
        "items": [
            L("NARRATOR", "Lorraine was at a fitting."),
            P(0.35),
            L("NARRATOR", "Garrison looked away."),
            P(0.5),
            L("NARRATOR", "And somebody moved Deb."),
        ],
        "post": 0.6, "sfx": ["sting_soft"],
    },
    # --- new cliffhanger: two minutes earlier, frame 343, a shadow on the lawn (Ray not lit yet)
    {
        "id": "doorbell", "kind": "doorbell",
        "note": ("DOORBELL CAM, two minutes earlier. Jump cut to frame 343; on 'Frame 343' the frames flicker. "
                 "In 343 a long, rounded shadow reaches across the lawn from the left edge. "
                 "Pauses on 'SOMETHING ELSE WAS UP.'"),
        "frame_a": "yard_before", "frame_b": "yard_shadow",
        "clock_start": "03:09:56", "jump_after": 4, "frames": (342, 343),
        "kb": ((0.5, 0.5, 1.0), (0.45, 0.47, 1.1)),
        "cta": ("SOMETHING ELSE", "WAS UP."), "cta_sub": "Comment what + the frame ↓",
        "items": [
            L("NARRATOR", "Deb was moved at 3:12.", "Deb was moved at three twelve."),
            P(0.45),
            L("NARRATOR", "We went back two minutes."),
            P(0.5),
            L("NARRATOR", "Frame 343.", "Frame three forty-three."),
        ],
        "post": 3.8, "sfx": ["crickets"],
    },
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"],
     "note": "END CARD: title, next episode, 'Follow the case.', AI disclaimer."},
]
