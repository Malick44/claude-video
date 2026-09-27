"""NOBODY MOVES, Confessional: "Ray". Posted after Episode 4.

Ray the solar frog, lit and cheerful, would like to report a hat. Garrison's hat. At sunset the sun
goes down behind Garrison's flower bed, and the gnome's long evening shadow, pointed hat and all,
stretches forward to the front edge of the lawn: onto Ray's solar panel. Garrison has worn that hat
since 1994. "Thirty-one years, apparently!" That "apparently" is the tell: Ray is repeating what he
was just told. The punchline comes from his one mechanism: he only remembers back to his last full
charge, so of thirty-one years of sunsets he remembers exactly one. Today's. Worst one of his life.
The punch shot's name card ("Memory: since last charge") arrives with that last line, so a cold
viewer gets the rule without it being telegraphed. (Canon holds: the shade only falls at sunset,
after the afternoon's full charge, so Ray still lights up, and today's sunset is inside his memory.)

No clue, no doorbell (a Confessional plants nothing). Library stills only: ray_lit (ray_night, then
ray, as fallbacks), garrison (a longlens crop of yard_before as its fallback), and aerial/porch
behind the title card. In garrison the sun sets low in the upper left, over the rooftops
behind the gnome, so he stands backlit; it is not lined up behind the hat, and the hat shot's push
already keeps both the sun and the hat in frame.
"""

TITLE = "NOBODY MOVES"
EPISODE = "CONFESSIONAL: RAY"
NEXT_UP = "EPISODE 1 IS PINNED"

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731


# Ray at night, lit: the generated still first, then the derived relight, then Ray by day.
HOOK_VIEWS = [V("ray_lit", (0.33, 0.62, 1.75), (0.33, 0.61, 1.95)),
              V("ray_night", (0.33, 0.62, 1.75), (0.33, 0.61, 1.95)),
              V("ray", (0.33, 0.62, 1.75), (0.33, 0.61, 1.95))]
PUNCH_VIEWS = [V("ray_lit", (0.33, 0.60, 2.1), (0.33, 0.59, 2.45)),     # tighter: the panel and the grin
               V("ray_night", (0.33, 0.60, 2.1), (0.33, 0.59, 2.45)),
               V("ray", (0.33, 0.60, 2.1), (0.33, 0.59, 2.45))]
# Garrison at sunset, backlit: the sun sits low in the upper left, over the rooftops behind him (not
# behind the hat). This push keeps both the sun and the hat in frame; don't reframe to line them up.
HAT_VIEWS = [V("garrison", (0.47, 0.515, 1.1), (0.44, 0.45, 1.3)),
             V("yard_before", (0.165, 0.55, 3.2), (0.165, 0.545, 3.6), "longlens")]


SHOTS = [
    # --- hook: a glowing frog files a complaint against headwear
    {
        "id": "hook", "kind": "still", "note": "CLOSE-UP: Ray at night, lit up, cheerful, filing a complaint.",
        "views": HOOK_VIEWS,
        "items": [
            L("RAY", "I'd like to report a hat."),
            P(0.45),
            L("RAY", "It steals my sun."),
        ],
        "post": 0.3,
        "lower_third": ("RAY", "Solar frog · Edge of the lawn", "Confessional"),
    },
    {
        "id": "title", "kind": "title", "note": "Title card over a piano sting.",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 2.6, "sfx": ["sting"],
    },
    # --- the accused, and the tell: Ray only knows "thirty-one years" because he was just told
    {
        "id": "hat", "kind": "still",
        "note": ("Garrison at sunset, backlit: the sun sits low in the upper left, over the rooftops behind him. "
                 "The camera pushes in toward the hat, keeping the sun and the hat in frame the whole time."),
        "views": HAT_VIEWS,
        "items": [
            L("NARRATOR", "Garrison's hat."),                      # two lines, so neither caption wraps:
            P(0.25),                                                # as one, it read "...Since" / "1994."
            L("NARRATOR", "Since 1994.", "Since nineteen ninety-four."),
            P(0.45),
            L("RAY", "31 years, apparently!", "Thirty-one years, apparently!"),
        ],
        "post": 0.35,
        "lower_third": ("GARRISON", "Garden gnome · Flower bed, No. 7", "Accused of: throwing shade"),
    },
    # --- punchline: of thirty-one years of sunsets, Ray remembers the one since his last full charge.
    #     Music out and no sfx, so the beat before "Just today's." is truly silent. The name card
    #     states the rule as the last line lands, not before; "post" 0.8 holds it long enough to read.
    {
        "id": "punch", "kind": "still", "note": "Ray, tighter on the panel and the face, beaming. No score under this one.",
        "views": PUNCH_VIEWS,
        "items": [
            L("NARRATOR", "Ray, how many sunsets do you remember?"),
            P(0.9),
            L("RAY", "Just today's."),
            P(0.4),
            L("RAY", "Worst one of my life!"),
        ],
        "post": 0.8, "music": "out", "climax": True,
        "lower_third": ("RAY", "Solar frog · Edge of the lawn", "Memory: since last charge"),
        "lower_third_at": "last",
    },
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"],
     "note": "END CARD: 'EPISODE 1 IS PINNED', 'Follow the case.', AI disclaimer."},
]
