"""<SHOW TITLE>, Episode 1: "<Title>" - the pilot, as data.

Copy to shows/<slug>/episodes/ep01_<episode_title>/episode.py: the episode's title in lowercase with
underscores (NOBODY MOVES: ep01_three_feet), not the show slug. The folder name becomes the output
names, build/<folder>.mp4 and build/<folder>_tiktok.mp4.

This skeleton uses only the show-neutral shot kinds (still, title, qcard, end) and defines its
placeholder speaker WITNESS below, so it builds on a fresh scaffold from new_show.sh (which also
applies the string_pad fix and the "climax" flag). For show-specific kinds (NOBODY MOVES has
evidence, board and doorbell), see shows/nobody-moves/episodes/ep01_three_feet/episode.py and
your show's pipeline/render.py.

pipeline/build_audio.py turns this file into voice clips, a timeline and the mix, and
pipeline/render.py turns the same timeline into 1080x1920 frames. Change a line here and both
follow. Positions are fractions of the source still ((0.5, 0.5) is the center); zoom 1.0 shows
the whole still. "note" is the stage direction printed in SCRIPT.md.
"""

TITLE = "SHOW TITLE"
EPISODE = "EPISODE 1: PILOT TITLE"
NEXT_UP = "NEXT: EPISODE 2 — NEXT TITLE"
# The answer to the closing comment-bait. SCRIPT.md prints it; the video never shows it.
ANSWER = "In the last frame, <what changed>. Pays off in Episode 2."

# Stills this episode wants: key -> the full prompt the user generates, ending with the SERIES.md
# style block. Save as stills/<key>.webp|png|jpg (series library) or episodes/<ep>/stills/ (this
# episode only). Most important first; mark the ones a fallback view already covers as OPTIONAL.
STILLS = {
    "hero": "Extreme close-up of <main character> ... <style block>",
    "set_wide": "OPTIONAL. Wide establishing shot of <the set> ... <style block>",
}

# Speakers come from the show's cast.py; an episode's CAST only adds one-off voices. WITNESS is a
# placeholder so this builds before cast.py is rewritten: replace it with your characters' cast.py
# names, then delete this line (or keep it for a true one-off, like a mailman).
CAST = {"WITNESS": {"voice": "am_michael", "speed": 1.0, "pitch": 0.92}}

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731
# V(still, (cx, cy, zoom) at start, (cx, cy, zoom) at end, look). "views" lists them best first;
# a shot uses the first whose still exists, so put the ideal still first and a crop of one you
# already have last. Looks: None, "longlens" (soft stakeout crop), "anon" (blurred and cold).

SHOTS = [
    # HOOK, 0 to about 5 s: a character's first line lands within 2 s, over a tight close-up.
    # Never open on the title card.
    {
        "id": "hook", "kind": "still", "note": "EXTREME CLOSE-UP: <character>, slow push-in.",
        "views": [V("hero", (0.5, 0.45, 2.3), (0.5, 0.45, 2.7))],
        "items": [
            L("WITNESS", "A deadpan setup line."),
            P(0.45),                                  # the pause is the joke's timing
            L("WITNESS", "Punchline last."),
        ],
        "post": 0.35,
        "lower_third": ("NAME", "What they are · where they stand", "One absurd credential"),
    },
    # TITLE, at about 5 s and about 3 s long. The "sting" sfx starts the score; a riser lands
    # on it automatically.
    {
        "id": "title", "kind": "title", "note": "Title card over a sting.",
        "views": [V("set_wide", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("hero", (0.5, 0.4, 1.3), (0.5, 0.42, 1.12))],   # fallback crop
        "items": [], "min": 3.2, "sfx": ["sting"],
    },
    # SETUP: the narrator states tiny stakes with total seriousness.
    {
        "id": "setup", "kind": "still", "note": "The whole set, everything in its place.",
        "views": [V("set_wide", (0.5, 0.42, 1.0), (0.46, 0.5, 1.2)),
                  V("hero", (0.5, 0.5, 1.0), (0.5, 0.5, 1.15))],
        "items": [
            L("NARRATOR", "The place. A number. An absurd statistic."),
            P(0.3),
            # third argument = what the voice says, when the caption text would be misread
            L("NARRATOR", "Nothing here has changed since 1994.",
              "Nothing here has changed since nineteen ninety-four."),
        ],
        "post": 0.3,
    },
    # QUESTION CARD: the question types out; the whoosh, typing and bell are automatic.
    {"id": "q1", "kind": "qcard", "note": "BLACK CARD. The question types out.",
     "text": "Where were you on the night of the 13th?", "items": [], "min": 2.4},
    # ANSWER: the character's one mechanism, escalated.
    {
        "id": "answer", "kind": "still", "note": "<character>, long-lens crop.",
        "views": [V("hero", (0.5, 0.45, 1.6), (0.5, 0.45, 1.8), "longlens")],
        "items": [
            L("WITNESS", "An evasive answer."),
            P(0.5),
            L("WITNESS", "Next question."),
        ],
        "post": 0.6,
        "music": "out",   # cut the score for this shot; once or twice an episode, before a punchline
    },
    # CLIFFHANGER: the comment-bait beat. Plant one fair clue: visible at phone size on a rewatch,
    # not obvious on first view. "sting_soft" swells under this shot's last line.
    {
        "id": "cliff", "kind": "still", "note": "The last frame. One thing has changed.",
        "views": [V("set_wide", (0.5, 0.5, 1.1), (0.5, 0.5, 1.25)),
                  V("hero", (0.5, 0.5, 1.2), (0.5, 0.5, 1.35))],
        "items": [
            L("NARRATOR", "Something in this frame is different."),
            P(0.3),
            L("NARRATOR", "Comment what changed."),
        ],
        "post": 0.8, "sfx": ["sting_soft"],
        # The score's build peaks here. new_show.sh patched build_audio.py's climax line to honor
        # this flag; without it (and with no doorbell shot) the build peaks on the end card.
        "climax": True,
    },
    # END CARD: TITLE, NEXT_UP and the AI disclaimer (its text lives in the show's render.py).
    {"id": "end", "kind": "end", "note": "END CARD.", "items": [], "min": 3.6, "sfx": ["sting_end"]},
]
