"""NOBODY MOVES, Episode N: "Title" - annotated template. Copy to episodes/<epNN_slug>/episode.py.

Every shot is a dict; "items" are spoken lines L(...) and pauses P(...). Positions are
fractions of the source image (0.5, 0.5 = center); zoom 1.0 = whole image.
"""

TITLE = "NOBODY MOVES"
EPISODE = "EPISODE N: TITLE"
NEXT_UP = "NEXT: EPISODE N+1 — NEXT TITLE"
# The hidden clue in the closing doorbell frame. SCRIPT.md shows it; the video never does.
ANSWER = "In frame X, ... (pays off in Episode Y)."

# New stills this episode wants: key -> generation prompt (end with the SERIES.md style block).
# Every shot still lists a fallback view, so the episode builds before these exist.
STILLS = {
    # "basin_counsel": "A weathered white concrete birdbath ... <style block>",
}

# Optional: one-off speakers (series voices live in cast.py) and per-episode sound swaps.
# CAST = {"MAILMAN": {"voice": "am_puck", "speed": 1.0, "pitch": 1.0}}
# SOUNDS = {"crickets": {"freesound_search": "crickets night", "max_seconds": 60}}

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731
# looks: None, "longlens" (soft stakeout crop), "anon" (blurred + cold, anonymous source)

SHOTS = [
    # --- HOOK: a character line over a tight close-up, within the first 2 seconds
    {
        "id": "hook", "kind": "still", "note": "EXTREME CLOSE-UP: ...",
        "views": [V("garrison", (0.47, 0.52, 2.35), (0.47, 0.51, 2.75))],
        "items": [L("GARRISON", "Line.")],
        "post": 0.35,
        "lower_third": ("GARRISON", "Garden gnome · Flower bed, No. 7", "Gag line"),
        # "lower_third_at": "last",   # show the name card on the last line instead of at 0.35 s
    },
    # --- TITLE card over a sting (the score starts here)
    {
        "id": "title", "kind": "title", "note": "Title card over a piano sting.",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)), V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 3.2, "sfx": ["sting"],
    },
    # --- EVIDENCE photo: camera flash, EXHIBIT tag, optional arrow / circles
    {
        "id": "exhibit", "kind": "evidence", "label": "EXHIBIT C", "stamp": "06/14 · 5:41 AM", "note": "...",
        "views": [V("yard_after", (0.53, 0.64, 1.45), (0.52, 0.645, 1.62))],
        "items": [P(0.25), L("NARRATOR", "Line.")],
        "post": 0.5, "sfx": ["shutter"],
        # "annot_arrow": {"from": (x, y), "to": (x, y), "label": "3 FT"},   # draws on the last line
        # "annot_circles": [(x, y, r)],                                     # r = fraction of image width
    },
    # --- QUESTION card: the interviewer types (typewriter + bell automatic)
    {"id": "q1", "kind": "qcard", "text": "Question?", "items": [], "min": 2.0, "note": "BLACK CARD."},
    # --- INTERVIEW: one still, one character; punchline after a pause
    {
        "id": "lorraine", "kind": "still", "note": "...",
        "views": [V("lorraine", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22)),
                  V("yard_before", (0.744, 0.245, 3.0), (0.744, 0.25, 3.35), "longlens")],
        "items": [L("LORRAINE", "Setup."), P(0.5), L("LORRAINE", "Punchline.")],
        "post": 0.35,
        "lower_third": ("LORRAINE", "Porch goose · Front steps, No. 7", "Gag line"),
    },
    # --- ANONYMOUS SOURCE: sfx wind + chimes; drop them in the next shot for "the wind stopped"
    {
        "id": "chime", "kind": "still", "note": "...",
        "views": [V("chime", (0.5, 0.45, 1.1), (0.5, 0.42, 1.3), "anon"),
                  V("porch", (0.86, 0.13, 3.0), (0.86, 0.12, 3.35), "anon")],
        "items": [L("CHIME", "Line.")], "post": 0.5, "sfx": ["wind", "chimes"],
        "lower_third": ("ANONYMOUS SOURCE", "Voice altered", "Identity protected"),
    },
    # --- EVIDENCE BOARD: polaroids + red string; the index card lands on the last line
    {
        "id": "board", "kind": "board", "card": "WHO MOVED DEB?", "note": "...",
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.48, 1.18)),
        # (still, square crop (x0, y0, x1), label, center fx, fy, size, rotation, look) - first is the hub
        "polaroids": [
            ("yard_before", (0.478, 0.380, 0.829), "DEB (MOVED)", 0.50, 0.40, 620, -2.5, None),
            ("garrison", (0.228, 0.335, 0.717), "GARRISON", 0.24, 0.24, 420, 4, None),
            ("yard_before", (0.680, 0.200, 0.808), "LORRAINE", 0.77, 0.23, 420, -5, None),
            ("porch", (0.234, 0.466, 0.978), "MR. BASIN", 0.23, 0.58, 420, -3, None),
            ("porch", (0.696, 0.015, 1.0), "ANON.", 0.78, 0.58, 420, 5, "anon"),
        ],
        "items": [L("NARRATOR", "The question...")], "post": 0.6, "sfx": ["sting_soft"],
    },
    # --- DOORBELL CAM cliffhanger: jump cut A -> B at jump_after, flicker after the last line,
    #     pause on B, then the call to action. Frame B carries the hidden clue.
    {
        "id": "doorbell", "kind": "doorbell", "note": "...",
        "frame_a": "yard_after", "frame_b": "yard_after",
        "clock_start": "03:12:03", "jump_after": 2, "frames": (422, 423),
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.52, 1.04)),
        # "alter_box": (x0, y0, x1, y1),   # mirror this region in frame B (it turned around)
        # "alter_glow": (x, y, r),         # light up this point in frame B (it switched on)
        "cta": ("SOMETHING ELSE IN", "THIS FRAME MOVED."), "cta_sub": "Comment the object + timestamp ↓",
        "items": [L("NARRATOR", "Setup."), P(0.5), L("NARRATOR", "Look closer.")],
        "post": 4.0, "sfx": ["crickets"],
    },
    # --- END card: NEXT_UP + "Follow the case." + AI disclaimer
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"], "note": "END CARD."},
]
