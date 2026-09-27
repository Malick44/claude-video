"""NOBODY MOVES, Confessional: Garrison ("Nosy"). Post after Episode 5.

Garrison's grudge is against the investigation's star witness: the doorbell camera across the street
at No. 5. It's nosy. Then he lists its specs, far too precisely for a gnome who never looks at
anything: a picture every 1.6 seconds, night vision, motion detection, "on a lawn where nobody moves."
The interviewer asks how he knows all that. The score cuts, and he gives the only answer he has ever
given: "...I was facing the other way." His own name card answers for him: "Facing: the doorbell."
(The label runs "Facing: the other way" in Eps. 2 and 4, then "Facing: the street" in Ep. 5.)

No clue and no doorbell shot. The middle shot is No. 5's own view, long lens, of yard_turned (frames
431 on, already revealed in Ep. 5): the frame that caught him turned toward the street, which is
toward the camera. It opens tight on Deb and the gnome together, then drifts past Deb and creeps in
until he sits alone in Draft 0's stakeout framing, while he complains about being watched. It never
opens wide. The porch step (x about 0.74) stays out of frame (the move never passes x 0.46), and
so does Ray. yard_turned carries no light for Ray (doorbell shots add it with "lit"), and an unlit
frog in a frame-431 picture would read as a new clue. The move's lowest edge is y 0.742, and Ray's
top is at about 0.754. Starting at zoom 2.6 rather than 1.8 also keeps the gnome's face above the
caption band (y 0.547) through the first, two-line caption. Library stills only.

Continuity, for SERIES.md when this ships (a running gag, not a clue):
| 5c | Confessional "Nosy": Garrison knows the No. 5 doorbell's specs by heart (a picture every 1.6
seconds, night vision, motion detection) and still says he "was facing the other way." His name card
reads "Facing: the doorbell", and in frames 431 on he faces the camera. | running gag. The "Facing:"
line so far: "the other way" (Eps. 2, 4), "the street" (Ep. 5), "the doorbell" (5c). Never write it
as Garrison turning himself: the open Mower thread says a person handles this yard. |
"""

TITLE = "NOBODY MOVES"
EPISODE = "CONFESSIONAL: GARRISON"
NEXT_UP = "EPISODE 1 IS PINNED"

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731

LOWER = "Garden gnome · Flower bed, No. 7"
# The specs creep: from Deb and Garrison together to the gnome alone, in the stakeout framing Draft 0
# used for him. Ray and the porch step stay out of frame for the whole move, and the gnome's face
# stays above the captions.
SPECS_CREEP = (0.26, 0.55, 2.6), (0.165, 0.585, 3.2)

SHOTS = [
    # --- hook: a gnome with a grudge against a doorbell, inside two seconds
    {
        "id": "hook", "kind": "still", "note": "EXTREME CLOSE-UP: Garrison, gruff, straight down the lens.",
        "views": [V("garrison", (0.50, 0.52, 1.25), (0.50, 0.51, 1.42)),
                  V("yard_before", (0.17, 0.575, 3.0), (0.17, 0.57, 3.3), "longlens")],
        "items": [
            L("GARRISON", "That doorbell across the street?"),
            P(0.25),
            L("GARRISON", "Nosy."),
        ],
        "post": 0.45,
        "lower_third": ("GARRISON", LOWER, "Confessional"),
    },
    {
        "id": "title", "kind": "title", "note": "Title card over a piano sting.",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 2.6, "sfx": ["sting"],
    },
    # --- escalation: No. 5's own picture of him (frame 431 on, turned toward the street), creeping in
    #     while he lists its specs. He knows them far too well. The last line's the laugh, then the
    #     interviewer's question.
    {
        "id": "specs", "kind": "still",
        "note": ("No. 5's view, long lens, frame 431 on: the camera creeps past Deb and settles on the gnome "
                 "in the flower bed, who is facing it."),
        # Fallback: yard_gone, the frame yard_turned was derived from (identical but for Garrison's box),
        # so the creep frames it the same, with Deb in shot. On yard_before (frame 417) Deb is out of it.
        "views": [V("yard_turned", *SPECS_CREEP, "longlens"),
                  V("yard_gone", *SPECS_CREEP, "longlens")],
        "items": [
            L("GARRISON", "Takes my picture every 1.6 seconds.", "Takes my picture every one point six seconds."),
            P(0.3),
            L("GARRISON", "Night vision."),
            P(0.2),
            L("GARRISON", "Motion detection."),
            P(0.55),
            L("GARRISON", "On a lawn where nobody moves."),
            P(0.5),
            L("NARRATOR", "How do you know all that?"),
        ],
        "post": 0.25,
    },
    # --- punchline: hard cut to the tight close-up, the score cuts out, and his own name card
    #     answers for him. The score builds to this cut ("climax"), so the drop is the joke's timing.
    {
        "id": "punch", "kind": "still",
        "note": "TIGHT CLOSE-UP: Garrison. No score. A long look, then the alibi. The name card lands with it.",
        "views": [V("garrison", (0.49, 0.53, 1.55), (0.49, 0.52, 1.75)),
                  V("yard_before", (0.17, 0.57, 3.4), (0.17, 0.565, 3.7), "longlens")],
        "items": [
            P(0.7),
            L("GARRISON", "...I was facing the other way.", "I was facing the other way."),
        ],
        "post": 1.5, "music": "out", "climax": True,
        "lower_third": ("GARRISON", LOWER, "Facing: the doorbell"),
        "lower_third_at": "last",
    },
    # --- END CARD: EPISODE 1 IS PINNED, 'Follow the case.', AI disclaimer (the Confessional spec, verbatim)
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"]},
]
