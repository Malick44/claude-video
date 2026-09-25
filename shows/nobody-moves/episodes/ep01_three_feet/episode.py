"""NOBODY MOVES, Episode 1: "Three Feet" - the pilot, as data.

Every shot is a list of items (spoken lines and pauses). pipeline/build_audio.py
turns this into timed voice clips + a mixed soundtrack; pipeline/render.py turns
the same timeline into 1080x1920 frames. Change a line here and both follow.
"note" on a shot is the stage direction printed in SCRIPT.md.
"""

TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 1: THREE FEET"
NEXT_UP = "NEXT: EPISODE 2 \u2014 I WAS RIGHT HERE"
# The hidden clue in the doorbell-cam flicker (kept out of the video; SCRIPT.md only).
ANSWER = ("In frame 418 Lorraine the porch goose has turned to face the other way. Deb's jump is "
          "the obvious change; the goose is the hidden one - the same goose who said "
          "\"Where would I go? I'm concrete.\"")

# Voices come from the shared series cast (../../cast.py). Define CAST here only to add
# a one-off speaker for this episode.

# Stills (stills/<key>.webp|png|jpg). The first five are the user's images;
# the rest are optional upgrades - a shot uses the first view whose still exists.
STILLS = {
    "garrison": "gnome by the flower bed at dusk (user image 3)",
    "porch": "birdbath close-up, porch + wind chime behind (user image 1)",
    "holes": "two holes in a bare patch, drag marks (user image 2)",
    "yard_before": "night yard, Deb in her spot (user image 5)",
    "yard_after": "night yard, Deb three feet left, holes (user image 4)",
    "lorraine": "OPTIONAL goose close-up on the porch step",
    "chime": "OPTIONAL backlit wind chime silhouette",
    "aerial": "OPTIONAL drone shot of the cul-de-sac",
    "cork": "OPTIONAL empty cork board",
}

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731

# Each view: Ken Burns move (center_x, center_y, zoom) start -> end, as fractions
# of the source image (zoom 1.0 = whole frame), plus an optional grade "look".
SHOTS = [
    {
        "id": "hook", "note": 'EXTREME CLOSE-UP: Garrison the gnome, frozen grin, slow push-in.', "kind": "still",
        "views": [V("garrison", (0.47, 0.52, 2.35), (0.47, 0.51, 2.75))],
        "items": [
            L("GARRISON", "I've been standing in this exact spot for thirty-one years."),
            P(0.45),
            L("GARRISON", "I didn't see nothing."),
        ],
        "post": 0.35,
        "lower_third": ("GARRISON", "Garden gnome · Flower bed, No. 7", "31 years on the lawn"),
    },
    {
        "id": "title", "note": 'Title card over a piano sting.', "kind": "title",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 3.2, "sfx": ["sting"],
    },
    {
        "id": "street", "note": 'Night: the whole yard, every ornament in its place.', "kind": "still",
        "views": [V("yard_before", (0.5, 0.42, 1.0), (0.46, 0.52, 1.22))],
        "items": [
            L("NARRATOR", "Birchwood Court. Eleven houses. Forty-three lawn ornaments."),
            P(0.3),
            L("NARRATOR", "Not one of them has moved since 1994.",
              "Not one of them has moved since nineteen ninety-four."),
        ],
        "post": 0.3,
    },
    {
        "id": "deb", "note": 'CAMERA FLASH. EXHIBIT A: the yard at 5:41 AM. Yellow circles mark the two empty holes; a dashed "3 FT" arrow draws from the holes to where Deb stands now.', "kind": "evidence", "label": "EXHIBIT A", "stamp": "06/14 · 5:41 AM",
        "views": [V("yard_after", (0.53, 0.64, 1.45), (0.52, 0.645, 1.62))],
        "items": [
            P(0.25),
            L("NARRATOR", "Then, on the morning of June 14th, Deb was found...",
              "Then, on the morning of June fourteenth, Deb was found..."),
            P(0.35),
            L("NARRATOR", "three feet to the left."),
        ],
        "post": 0.5, "sfx": ["shutter"],
        # dashed arrow from the holes (where she stood) to where she is now
        "annot_arrow": {"from": (0.695, 0.626), "to": (0.43, 0.626), "label": "3 FT"},
        "annot_circles": [(0.673, 0.604, 0.018), (0.717, 0.607, 0.018)],
        "lower_third": ("DEB", "Lawn flamingo · Center lawn, No. 7", "Condition: unharmed. Position: wrong."),
        "lower_third_at": "last",
    },
    {
        "id": "holes", "note": 'CAMERA FLASH. EXHIBIT B: close-up of the two holes at dawn, circled in yellow.', "kind": "evidence", "label": "EXHIBIT B", "stamp": "06/14 · 6:52 AM",
        "views": [V("holes", (0.66, 0.58, 1.25), (0.665, 0.61, 1.55))],
        "items": [
            P(0.2),
            L("NARRATOR", "These two holes are where she stood for thirty years."),
            P(0.5),
            L("NARRATOR", "They were still warm."),
        ],
        "post": 0.5, "sfx": ["shutter"],
        "annot_circles": [(0.562, 0.619, 0.052), (0.769, 0.619, 0.052)],
    },
    {
        "id": "q1", "note": "BLACK CARD. The interviewer's question types out, with typewriter clicks and a bell.", "kind": "qcard", "text": "Where were you on the night of June 13th?",
        "items": [], "min": 2.4,
    },
    {
        "id": "lorraine", "note": 'Lorraine on the porch steps (a long-lens stakeout crop until a close-up is provided).', "kind": "still",
        "views": [V("lorraine", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22)),
                  V("yard_before", (0.744, 0.245, 3.0), (0.744, 0.25, 3.35), "longlens")],
        "items": [
            L("LORRAINE", "On the porch, hon."),
            P(0.3),
            L("LORRAINE", "Where would I go? I'm concrete."),
            P(0.6),
            L("LORRAINE", "Next question."),
        ],
        "post": 0.35,
        "lower_third": ("LORRAINE", "Porch goose · Front steps, No. 7", "Hasn't left the porch since 1998"),
    },
    {
        "id": "q2", "note": 'BLACK CARD. Typewriter question.', "kind": "qcard", "text": "Did you see anything?",
        "items": [], "min": 1.7,
    },
    {
        "id": "garrison2", "note": 'INTERVIEW: Garrison, wider.', "kind": "still",
        "views": [V("garrison", (0.5, 0.56, 1.0), (0.49, 0.53, 1.18))],
        "items": [
            L("GARRISON", "Kid, I've got a perfect view of that lawn. Twenty-four hours a day."),
            P(0.8),
            L("GARRISON", "...I was facing the other way.", "I was facing the other way."),
        ],
        "post": 0.45,
    },
    {
        "id": "basin", "note": 'The birdbath, in a long, awkward hold.', "kind": "still",
        "views": [V("porch", (0.6, 0.64, 1.05), (0.63, 0.62, 1.32))],
        "items": [
            L("NARRATOR", "Mr. Basin, the birdbath, declined to comment.",
              "Mister Basin, the birdbath, declined to comment."),
        ],
        "post": 0.9,
        "lower_third": ("MR. BASIN", "Birdbath · Six feet from Deb", "Declined to comment"),
    },
    {
        "id": "chime", "note": 'ANONYMOUS SOURCE: the wind chime, blurred and cold-graded to hide its identity. Voice disguised, wind chimes underneath.', "kind": "still",
        "views": [V("chime", (0.545, 0.44, 1.1), (0.6, 0.42, 1.3), "anon"),   # centered on the tubes
                  V("porch", (0.86, 0.13, 3.0), (0.86, 0.12, 3.35), "anon")],
        "items": [
            P(0.4),
            L("CHIME", "Everybody on Birchwood knows something."),
            P(0.35),
            L("CHIME", "They just... stand there.", "They just. Stand there."),
            P(0.7),
            L("CHIME", "Look. I only talk when it's windy."),
            P(0.35),
            L("CHIME", "And that night?"),
            P(0.55),
            L("CHIME", "It was very windy."),
        ],
        "post": 0.5, "sfx": ["wind", "chimes"],
        "lower_third": ("ANONYMOUS SOURCE", "Voice altered", "Identity protected"),
    },
    {
        "id": "board", "note": 'EVIDENCE BOARD: polaroids of every witness joined by red string to Deb. On the last line, an index card reading "WHO MOVED DEB?" appears.', "kind": "board",
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.48, 1.18)),
        # polaroids: (still, crop box as fractions x0,y0,x1,y1, label, center fx, fy, size, rotation, look)
        "polaroids": [
            ("yard_before", (0.478, 0.380, 0.829), "DEB (MOVED)", 0.50, 0.40, 620, -2.5, None),
            ("garrison", (0.228, 0.335, 0.717), "GARRISON", 0.24, 0.24, 420, 4, None),
            ("yard_before", (0.680, 0.200, 0.808), "LORRAINE", 0.77, 0.23, 420, -5, None),
            ("porch", (0.234, 0.466, 0.978), "MR. BASIN", 0.23, 0.58, 420, -3, None),
            ("porch", (0.696, 0.015, 1.0), "ANON.", 0.78, 0.58, 420, 5, "anon"),
        ],
        "items": [
            L("NARRATOR", "Forty-three witnesses. Zero movement."),
            P(0.35),
            L("NARRATOR", "So if nobody moves..."),
            P(0.45),
            L("NARRATOR", "who moved Deb?"),
        ],
        "post": 0.6, "sfx": ["sting_soft"],
    },
    {
        "id": "doorbell", "note": 'DOORBELL CAM, night vision. The clock ticks 03:11:56 to 59. At 03:12:00 Deb has jumped three feet, with nobody seen moving her. On "Look closer," frames 417 and 418 flicker back and forth; in 418 Lorraine the goose has turned around. The footage pauses on "SOMETHING ELSE IN THIS FRAME MOVED. Comment the object + timestamp."', "kind": "doorbell",
        # 03:11:5x shows the yard as it was; at 03:12:00 Deb has jumped three feet.
        "frame_a": "yard_before", "frame_b": "yard_after",
        "clock_start": 56,  # seconds past 03:11 at shot start; B appears at 03:12:00
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.5, 1.06)),
        # the hidden clue: in frame B, Lorraine (porch goose) is mirrored - she turned around
        "alter_box": (0.7163, 0.2129, 0.7800, 0.2787),
        "items": [
            L("NARRATOR", "At 3:12 AM, the doorbell camera at No. 5 captured this.",
              "At three twelve A.M., the doorbell camera at number five captured this."),
            P(0.5),
            L("NARRATOR", "Look closer."),
        ],
        "post": 4.0, "sfx": ["crickets"],
    },
    {
        "id": "end", "note": 'END CARD: title, next episode, "Follow the case." Disclaimer: "Reenactments dramatized with AI. The flamingo is real."', "kind": "end",
        "items": [], "min": 3.6, "sfx": ["sting_end"],
    },
]
