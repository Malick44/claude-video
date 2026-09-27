"""NOBODY MOVES, Confessional: "Deb" (posted after Episode 1).

The victim's Confessional. Deb has never spoken and has no voice, so the narrator and the silence
carry it. "Deb has never spoken." "Nobody asked her." So the narrator asks, and reads every silence
as the answer the show wants. "Can we film you?" (crickets) "Great." "Can we replay your worst
second?" (crickets) "Wonderful." "And can we delete Episode 1?" (the score cuts; only the crickets)
"Didn't think so." Then the end card: EPISODE 1 IS PINNED.

No clue, no doorbell, no question cards, and Deb has no lines (and no cast.py entry). Every shot is
a crop of yard_after, where she stands now, three feet left of her holes. "Great." and "Wonderful."
stay single words with full stops, so the narrator reads them flat, like ticking boxes on a form.
Built and checked: 23.07 s, 28 spoken words, mixcheck 5/5 (the music-out shot reads silent), and
no text under the TikTok, Reels or Shorts UI. The "film" shot holds 0.9 s after "Great." so the
"Consent: implied" name card stays up about 1.6 s.
"""

TITLE = "NOBODY MOVES"
EPISODE = "CONFESSIONAL: DEB"
NEXT_UP = "EPISODE 1 IS PINNED"

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731

# Deb in yard_after: beak tip about x 0.265, head (0.29, 0.46), body to (0.45, 0.53), feet at y 0.59;
# her holes at (0.673, 0.604) and (0.717, 0.607). Every crop, along its whole move, keeps Garrison
# (x < 0.212), Ray (x < 0.229, y 0.75 to 0.815) and Lorraine on her step (feet at y 0.28) out of frame,
# so nothing contradicts that night's doorbell table.
# No fallback views: yard_after is a library still, and there is no real alternative. yard_gone is
# identical inside every one of these crops (a duplicate, not a fallback), and yard_before shows Deb
# where she used to stand.
DEB_LT = "Lawn flamingo · Center lawn, No. 7"

SHOTS = [
    # --- hook: her silence, explained for new viewers in the first second
    {
        "id": "hook", "kind": "still", "note": "CLOSE-UP: Deb, perfectly still, slow push-in. No score yet.",
        "views": [V("yard_after", (0.375, 0.50, 3.2), (0.37, 0.495, 3.5))],
        "items": [
            L("NARRATOR", "Deb has never spoken."),
            P(0.4),
            L("NARRATOR", "Nobody asked her."),
        ],
        "post": 0.2,
        "lower_third": ("DEB", DEB_LT, "Confessional"),
    },
    {
        "id": "title", "kind": "title", "note": "Title card over a piano sting.",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 2.6, "sfx": ["sting"],
    },
    # --- so the narrator asks, and takes the silence as a yes
    {
        "id": "film", "kind": "still",
        "note": ("MEDIUM: Deb and a lot of empty lawn. She doesn't answer. Crickets. On 'Great.' her name card "
                 "comes back, now reading 'Consent: implied', and holds a beat."),
        "views": [V("yard_after", (0.49, 0.56, 2.0), (0.475, 0.55, 2.15))],
        "items": [
            L("NARRATOR", "Can we film you?"),
            P(1.0),
            L("NARRATOR", "Great."),
        ],
        "post": 0.9, "sfx": ["crickets"],   # hold "Consent: implied" long enough to read (~1.6 s)
        "lower_third": ("DEB", DEB_LT, "Consent: implied"),
        "lower_third_at": "last",
    },
    {
        "id": "loop", "kind": "still",
        "note": "LONG LENS: the camera pulls back from Deb toward the No. 5 doorbell-cam wide. No answer.",
        "views": [V("yard_after", (0.46, 0.53, 2.3), (0.545, 0.60, 1.7), "longlens")],
        "items": [
            L("NARRATOR", "Can we replay your worst second?"),
            P(0.8),
            L("NARRATOR", "Wonderful."),
        ],
        "post": 0.2, "sfx": ["crickets"],
    },
    # --- the punchline: the score has built to here and cuts; only the crickets answer
    {
        "id": "pinned", "kind": "still",
        "note": "TIGHTEST: Deb fills the frame, staring. The score cuts out. Only crickets.",
        "views": [V("yard_after", (0.335, 0.49, 4.3), (0.33, 0.485, 4.8))],
        "items": [
            L("NARRATOR", "And can we delete Episode 1?", "And can we delete Episode one?"),
            P(1.5),
            L("NARRATOR", "Didn't think so."),
        ],
        "post": 0.45, "sfx": ["crickets"], "music": "out", "climax": True,
    },
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"],
     "note": "END CARD: 'EPISODE 1 IS PINNED', 'Follow the case.', AI disclaimer. It answers for her."},
]
