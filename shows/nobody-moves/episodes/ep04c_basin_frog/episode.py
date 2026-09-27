"""NOBODY MOVES, Confessional: "Mr. Basin". Post after Episode 4.

One ornament, one grudge. Mr. Basin, the birdbath, appointed himself the frog's counsel in Ep. 4
("Until the frog has counsel, the frog has no comment."). His grudge is against Ray: the frog
talked, without his attorney present. Eleven days of no comment, which Mr. Basin calls flawless,
and the narrator corrects in three words, the way Ep. 4's "The frog has no power." did: it was
cloudy. Then on day twelve Ray, lit, said "Hi" to the narrator (Ep. 4's testimony, that night).
The punchline turns Mr. Basin's own mechanism on him: "He represented himself." ... "Amateur."
The name card lands on the last word: Attorney for Mr. Basin. Record: 0–0.

Two grudge shots, both on Ray, in Ep. 4's order: ray (grey day: the boast and the correction),
then ray_lit (day twelve, that night, when he said "Hi!"). Ray sits in the same spot in all four
Ray stills (checked with pipeline/grid.py: eye at about 0.42, 0.52; body x 0.07-0.49,
y 0.49-0.70), so the cut is a punch-in on the same frog: he doesn't move, the light does.

No clue, no doorbell, no new stills. The score builds to the punchline and cuts out for it; the
end card's sting closes the short. Ray's real Ep. 4 answer ("I don't remember.") is left for
another Confessional; here it would split the one grudge.
"""

TITLE = "NOBODY MOVES"
EPISODE = "CONFESSIONAL: MR. BASIN"
NEXT_UP = "EPISODE 1 IS PINNED"

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731

SHOTS = [
    # --- hook: the frog's attorney, with grave news about his client
    {
        "id": "hook", "kind": "still", "note": "EXTREME CLOSE-UP: Mr. Basin's bowl. Grave.",
        "views": [V("basin_counsel", (0.62, 0.47, 1.5), (0.63, 0.46, 1.68)),
                  V("porch", (0.62, 0.62, 1.32), (0.64, 0.6, 1.6))],
        "items": [
            L("MR. BASIN", "The frog talked."),
            P(0.5),
            L("MR. BASIN", "Without his attorney present."),
        ],
        "post": 0.3,
        "lower_third": ("MR. BASIN", "Birdbath · Attorney for the frog", "Confessional"),
    },
    {
        "id": "title", "kind": "title", "note": "Title card over a piano sting.",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 2.6, "sfx": ["sting"],
    },
    # --- the grudge, part one: eleven days of no comment, he takes the credit, the narrator corrects
    #     him over his client under grey skies. ("Eleven days." and "No comment." stay two lines: as
    #     one caption it wraps "Eleven days. No / comment.")
    {
        "id": "silent", "kind": "still",
        "note": "Ray, unlit, grey day. Mr. Basin, proud, over his client; then the narrator, flat.",
        "views": [V("ray", (0.42, 0.645, 1.35), (0.41, 0.655, 1.45)),
                  V("yard_after", (0.19, 0.775, 4.5), (0.19, 0.778, 5.0), "longlens")],
        "items": [
            L("MR. BASIN", "Eleven days."),
            P(0.15),
            L("MR. BASIN", "No comment."),
            P(0.4),
            L("MR. BASIN", "Flawless."),
            P(0.5),
            L("NARRATOR", "It was cloudy."),
        ],
        "post": 0.3,
    },
    # --- the offense: day twelve, that night, lit, as in Ep. 4's testimony. Punch in on the frog.
    {
        "id": "hi", "kind": "still", "note": "NIGHT, day twelve. Ray, lit and beaming. Read out like evidence.",
        "views": [V("ray_lit", (0.36, 0.64, 1.75), (0.36, 0.63, 1.95)),         # placed with grid.py
                  V("ray_night", (0.36, 0.64, 1.75), (0.36, 0.63, 1.95)),       # Ray is in the same spot
                  V("ray", (0.36, 0.64, 1.75), (0.36, 0.63, 1.95))],
        "items": [
            L("MR. BASIN", "Day twelve, he said \"Hi.\"", "Day twelve, he said hi."),
            P(0.4),
            L("MR. BASIN", "To the narrator."),
        ],
        "post": 0.35,
    },
    # --- punchline in silence: the score cuts, and the name card lands on the last word
    {
        "id": "punch", "kind": "still", "note": "Mr. Basin, tighter. No score. The name card lands on 'Amateur.'",
        "views": [V("basin_counsel", (0.64, 0.44, 1.75), (0.65, 0.43, 1.95)),
                  V("porch", (0.64, 0.6, 1.6), (0.65, 0.59, 1.85))],
        "items": [
            L("MR. BASIN", "He represented himself."),
            P(0.8),
            L("MR. BASIN", "Amateur."),
        ],
        "post": 1.4, "music": "out", "climax": True,   # the longer hold lets the card read in silence
        "lower_third": ("MR. BASIN", "Birdbath · Attorney for Mr. Basin", "Record: 0–0"),
        "lower_third_at": "last",
    },
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"],
     "note": "END CARD: title, 'EPISODE 1 IS PINNED', 'Follow the case.', AI disclaimer."},
]
