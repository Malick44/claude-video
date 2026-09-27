"""NOBODY MOVES, Confessional: "Lorraine". A 15-25 s short, posted after Episode 5.

Lorraine's one grudge: everyone says she's changed. She hasn't changed, hon. She's BEEN changed,
twelve outfits since March, and nobody asks the goose first. Her own mechanism (the outfit changes
between cuts, and she doesn't pick it) keeps happening all through her own Confessional:
bumblebee, Easter dress, gingham. Every outfit shot shares one camera move (MOVE), so each cut is
a jump cut where only the outfit changes. The last cut leaves her in nothing at all, the lower
third says so, and she renames it the way she did in Ep. 3 ("I was between outfits, hon"), except
that cornered, "hon" has become "detective".

Every still is in the series library: lorraine_bee, lorraine_easter, lorraine_fitting and the bare
lorraine share one framing. The fallbacks only matter if a still goes missing. With any one of them
gone, no cut goes straight from an outfit to the same outfit: the hook falls back to the gingham,
'changed' and 'asks' to the bumblebee. (Without the Easter dress, 'changed' repeats the hook's
bumblebee, with the title card between them.) The last resort for every outfit shot is Ep. 3's
long-lens stakeout crop, never the bare lorraine close-up, which is saved for the punchline. The
punchline falls back to Exhibit A's long lens (canon: nothing on). No clue, no recap, no new stills.
"""

TITLE = "NOBODY MOVES"
EPISODE = "CONFESSIONAL: LORRAINE"
NEXT_UP = "EPISODE 1 IS PINNED"

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731
# looks: None, "longlens" (soft stakeout crop), "anon" (blurred + cold, anonymous source)

LT = "Porch goose · Front steps, No. 7"
# One camera move for every outfit shot. It is slow and short, so the restart at each cut is small and
# only the outfit seems to change. The punchline starts where MOVE ends, then pushes in.
MOVE = ((0.5, 0.47, 1.25), (0.5, 0.46, 1.32))
STAKEOUT = V("yard_before", (0.744, 0.245, 3.0), (0.744, 0.25, 3.35), "longlens")   # Ep. 3's last resort

SHOTS = [
    # --- hook: the bumblebee, and the grudge inside two seconds
    {
        "id": "hook", "kind": "still",
        "note": "CLOSE-UP: Lorraine in the bumblebee, antennae in frame. Warm, a little wounded.",
        "views": [V("lorraine_bee", *MOVE), V("lorraine_fitting", *MOVE), STAKEOUT],
        "items": [
            L("LORRAINE", "Everyone says I've changed, hon."),
            P(0.4),
            L("LORRAINE", "Garrison, mostly."),
        ],
        "post": 0.3,
        "lower_third": ("LORRAINE", LT, "Confessional"),
    },
    {
        "id": "title", "kind": "title", "note": "Title card over a piano sting: CONFESSIONAL: LORRAINE.",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 2.6, "sfx": ["sting"],
    },
    # --- same framing as the hook, and now she's in the Easter dress. Nobody mentions it.
    {
        "id": "changed", "kind": "still",
        "note": "Jump cut, same framing as the hook: now the Easter dress and bonnet. Nobody mentions it.",
        "views": [V("lorraine_easter", *MOVE), V("lorraine_bee", *MOVE), STAKEOUT],
        "items": [
            L("LORRAINE", "I haven't changed."),
            P(0.45),
            L("LORRAINE", "I've been changed."),
        ],
        "post": 0.35,
    },
    # --- escalation: another jump cut, another outfit, same grudge
    {
        "id": "asks", "kind": "still",
        "note": "Jump cut, same framing again: now the gingham from the fitting. Still nobody mentions it.",
        "views": [V("lorraine_fitting", *MOVE), V("lorraine_bee", *MOVE), STAKEOUT],
        "items": [
            L("LORRAINE", "Twelve outfits since March, hon."),
            P(0.45),
            L("LORRAINE", "Nobody asks the goose first."),
        ],
        "post": 0.35,
    },
    # --- punchline: the last cut leaves her in nothing. Silence, the lower third, then her Ep. 3
    #     euphemism, with "hon" turned to "detective". A slow push-in ends on her face.
    {
        "id": "between", "kind": "still",
        "note": ("Jump cut, same framing: Lorraine in nothing at all. The score drops out. For the first "
                 "time the camera reacts: a slow push-in that ends on her face, above the captions."),
        "views": [V("lorraine", MOVE[1], (0.46, 0.42, 1.55)),
                  V("yard_after", (0.75, 0.26, 2.8), (0.745, 0.245, 3.3), "longlens")],
        "items": [
            # The name card fades in at 0.35 s and is fully up by 0.65 s. At 1.2 s, muted viewers get about
            # half a second to read "Now wearing: nothing" before the punchline's caption. With 0.8 s the
            # caption came up almost at once, directly above the card, so the punchline got read first.
            P(1.2),
            L("LORRAINE", "Between outfits, detective."),
        ],
        "post": 0.6,
        "lower_third": ("LORRAINE", LT, "Now wearing: nothing"),
        "music": "out", "climax": True,
    },
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"],
     "note": "END CARD: NOBODY MOVES, 'EPISODE 1 IS PINNED', 'Follow the case.', AI disclaimer."},
]
