"""NOBODY MOVES, Episode N: "Title" - annotated template. Copy to episodes/<epNN_slug>/episode.py.

Every shot is a dict; "items" are spoken lines L(...) and pauses P(...). Positions are
fractions of the source image (0.5, 0.5 = center); zoom 1.0 = whole image.

The rule (SERIES.md): nobody moves while anyone is watching. Reality (every still, every doorbell
frame) never moves; only the camera does. An ornament moves only in a labelled "reenactment" shot
of the narrator's theory, then hard-cuts back to the real ornament, motionless, denying it.
A main episode runs under 50 s: it opens on the event (no title card), asks an easy comment
question by about 10 s, has at most 2 reenactments (about 20% of the runtime, 3-6 s each), and
hides a bonus change in its last doorbell frame. Hand-written notes go in NOTES.md beside this file
(script_md.py rewrites SCRIPT.md on every build). The worked example is
episodes/ep01r_three_feet_reenacted/.
"""

TITLE = "NOBODY MOVES"
EPISODE = "EPISODE N: TITLE"
CORNER_LABEL = "NOBODY MOVES"   # the series title, small, on every reality shot (none on reenactments or the end card)
NEXT_UP = "NEXT: EPISODE N+1 — NEXT TITLE"
# The hidden clue in the closing doorbell frame. SCRIPT.md shows it; the video never does.
ANSWER = "In frame X, ... (pays off in Episode Y)."

# New stills this episode wants: key -> generation prompt. Reality stills end with the SERIES.md
# "Image style" block; a reenactment keyframe (rx_<name>_key) is built in SERIES.md's keyframe order
# (image map, reference blocks word for word, the first instant of the action, the subject's size,
# "Exactly one ...", a static camera, "Time and state: ..." with no date or clock time, every window
# dark) and ends with SERIES.md's still suffix. Every shot still lists a fallback view, so the episode
# builds before these exist.
STILLS = {
    # "basin_counsel": "A weathered white concrete birdbath ... <style block>",
    # "rx_theory_key": "Image 1: 3D sheet view of Garrison (front). Image 2: photo of Garrison. GARRISON: ... <still suffix>",
}

# Optional: a dark library still lifted for this episode, computed at render time (same pixels and
# framing, so the doorbell frames still match). Target: a mean of about 80/255 per shot.
# DERIVED_STILLS = {"garrison_lift": {"from": "garrison", "gamma": 1.5}}

# Reenactment clips: key -> image-to-video motion prompt. The locked camera first, then how long the
# ornament holds still and its one rigid move (across the frame, along its facing), then background
# motion, then SERIES.md's motion suffix word for word. No person, ever: the build's prompt lint refuses
# one. The hold time comes from the LOCKED narration take: "For the first X seconds" with
# X = pre + the key word's time in the take + in.
CLIPS = {
    # "rx_theory": "Locked-off camera at grass height; the camera never moves. For the first two and a half "
    #              "seconds the garden gnome stands perfectly still. Then he slides sideways ... <motion suffix>",
}
# What the generators get, recorded by pipeline/clips.py add (nothing else reads it). "seconds": 5, or 10
# when in + dur passes 5. Seedance has no negative field: use camera_fixed and append seedance_suffix.
CLIP_SOURCES = {
    # "rx_theory": {"keyframe": "rx_theory_key", "keyframe_refs": ["ref3d_garrison, front view cropped", "garrison, cropped"],
    #               "seconds": 5, "aspect": "9:16", "camera_fixed": True,
    #               "negative": "<SERIES.md shared negative>, <per-clip list>",
    #               "seedance_suffix": "Only the gnome moves, as one rigid piece. No people, no text, no graphics."},
}

# The human fallback: the 3-5 lines a human records if no v4 take lands them in 3 tries (no narrator
# lines), each with one line of direction. script_md.py stars them in SCRIPT.md.
# HUMAN_TAKES = {"deny_2": "GARRISON: gruff, a hair too fast, as if that settles it."}

# Optional: one-off speakers (series voices live in cast.py; English presets af_/am_/bf_/bm_ only)
# and per-episode sound swaps. A "file" is looked up in this episode's folder, then the show folder.
# Freesound and ElevenLabs sources need hosts that cloud sessions block; ask the user for the file.
# Swapping a sound is nobody-moves-sound-design's recipe (c): it matches the level with gain_db.
# CAST = {"MAILMAN": {"voice": "am_puck", "speed": 1.0, "pitch": 1.0}}
# SOUNDS = {"crickets": {"file": "audio/crickets.wav", "credit": "Title by Author, CC0"}}

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731
# looks: None, "longlens" (soft stakeout crop), "anon" (blurred + cold, anonymous source)
# Audio tags: untagged by default; at most one tagged line per shot, on its punchline or button; at
# most one NARRATOR tag per episode; only from the character's approved list (docs/AUDIO_ELEVENLABS_V4.md);
# ONLY in the spoken text, L()'s third argument, never in the caption. Kokoro leaves them out.

SHOTS = [
    # --- COLD OPEN: the event in the first second, no title card. A doorbell that only jumps: no flicker,
    #     no call to action (those belong to the closing doorbell). Or open on a character line over a
    #     tight close-up (a "still" with a lower_third).
    {
        "id": "cold", "kind": "doorbell", "note": "COLD OPEN, no title card. ...",
        "frame_a": "yard_before", "frame_b": "yard_after",
        # frames, clock and alter_* must match SERIES.md's doorbell table (417 = yard_before; 418 = yard_after +
        # alter_box on Lorraine, the hidden change): every replay of a frame carries its alter_*
        "clock_start": "03:11:59", "jump_after": 1, "frames": (417, 418),   # jump_after: an int
        "flicker": False,
        "alter_box": (0.7163, 0.2129, 0.7800, 0.2787),   # frame 418: Lorraine turned (SERIES.md doorbell table)
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.5, 1.05)),
        "items": [L("NARRATOR", "3:12 AM.", "Three twelve AM."), P(0.1), L("NARRATOR", "Line.")],
        "post": 0.0, "sfx": ["crickets"],
    },
    # --- TITLE card over a sting. NOT in a new main episode (the corner label is the title); a
    #     Confessional may keep one. The score starts at the first "sting" (with none, from the first
    #     frame) and builds to the last shot marked "climax": True, else to the last doorbell.
    # {
    #     "id": "title", "kind": "title", "note": "Title card over a piano sting.",
    #     "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)), V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
    #     "items": [], "min": 3.2, "sfx": ["sting"],
    # },
    # --- EVIDENCE photo: camera flash, EXHIBIT tag, optional arrow / circles
    {
        "id": "exhibit", "kind": "evidence", "label": "EXHIBIT C", "stamp": "06/14 · 5:41 AM", "note": "...",
        "views": [V("yard_after", (0.53, 0.64, 1.45), (0.52, 0.645, 1.62))],
        "items": [P(0.1), L("NARRATOR", "Line.")],
        "post": 0.25, "sfx": ["shutter"],
        # "annot_arrow": {"from": (x, y), "to": (x, y), "label": "3 FT"},   # draws on the last line
        # "annot_circles": [(x, y, r)],                                     # r = fraction of image width
        # "lower_third": ("DEB", "Lawn flamingo · Center lawn, No. 7", "Gag line"), "lower_third_at": "last",
        # "climax": True,   # only when this reveal, not a later doorbell, is the episode's peak (e.g. no
        #                   # doorbell ending). The score builds to the LAST shot marked "climax"; with none,
        #                   # to the last doorbell; with neither, to the end card. Then it holds at full.
    },
    # --- EVIDENCE BOARD with the EASY COMMENT QUESTION, by about 10 s: binary, no lore, one word. The
    #     index card lands on the last line. No sting_soft on the shot before a reenactment (its swell
    #     would peak on the reenactment's first frame), and "post" >= 0.35: reenact_hit's suck-in starts there.
    {
        "id": "lineup", "kind": "board", "card": "COMMENT: GNOME OR GOOSE?", "note": "...",
        "kb": ((0.5, 0.45, 1.0), (0.5, 0.5, 1.1)),   # ends at (0.5, 0.5, 1.1) with the suspects at fy 0.56: the index card
                                                    # and the labels stay clear of every app's UI (re-run safezones.py)
        # (still, square crop (x0, y0, x1), label, center fx, fy, size, rotation, look) - first is the hub
        "polaroids": [
            ("deb", (0.15, 0.28, 0.95), "DEB (MOVED)", 0.50, 0.30, 600, -2.5, None),
            ("garrison", (0.228, 0.335, 0.717), "GNOME", 0.26, 0.56, 440, 4, None),
            ("lorraine", (0.240, 0.310, 0.820), "GOOSE", 0.74, 0.56, 440, -5, None),
        ],
        "items": [L("NARRATOR", "Two suspects."), P(0.15), L("NARRATOR", "Who did it? Gnome, or goose?")],
        "post": 0.35,
    },
    # --- REENACTMENT: the narrator's theory, 3-6 s, at most 2 per main episode, never back to back.
    #     The ornament holds still under the setup and makes ONE rigid move on the key word; the camera
    #     is locked. The label is exactly "REENACTMENT · AI" (the build refuses any other); the theory and
    #     any escalation go in the stamp, with no clock time. No lower_third, "music": "out" or "climax"
    #     here, and never the last shot. dur = pre + the line + >= 0.5 s of action after it, at most 6.0.
    {
        "id": "theory", "kind": "reenactment", "note": "REENACTMENT · AI, THEORY #1. ... Hard cut mid-move.",
        "clip": "rx_theory", "in": 0.25, "speed": 1.0, "dur": 4.0,   # tune "in" so the move lands on its word; never "speed"
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.5, 1.0)),                     # locked: a push-in would read as a zoom on a still
        "label": "REENACTMENT · AI", "stamp": "THEORY #1: THE GNOME",
        "look": "reenact", "cue": True, "cut_silence": 0.6,
        "fallback": [V("rx_theory_key", (0.5, 0.5, 1.0), (0.5, 0.48, 1.3)),   # until the clip exists
                     V("garrison", (0.47, 0.52, 1.6), (0.47, 0.50, 2.3))],
        "pre": 0.35,
        "items": [L("NARRATOR", "Setup, about two seconds. Then the key word.")],   # about 10 words
    },
    # --- THE HARD CUT BACK: the real ornament, back in its spot, same size and angle, in silence. The
    #     denial comes from the character's one mechanism; the motionless hold after it is the laugh.
    {
        "id": "deny", "kind": "still", "music": "out", "pre": 0.45, "note": "HARD CUT: the real ornament, unmoved.",
        "views": [V("garrison", (0.47, 0.49, 1.37), (0.47, 0.49, 1.37))],   # locked, like the reenactment
        "items": [L("GARRISON", "Kid."), P(0.4),
                  L("GARRISON", "I was facing the other way.", "[too quickly] I was facing the other way.")],
        "post": 0.35, "sfx": ["crickets"],
        "lower_third": ("GARRISON", "Garden gnome · Flower bed, No. 7", "Gag line"),
    },
    # --- SILENT REACTION CUTAWAY (optional, about 1.6 s): no line; the name card carries the joke, fully on
    #     from the cut to the cut. The punch alone on the yellow third line, about 15 characters at most.
    {
        "id": "react", "kind": "still", "music": "out", "note": "SILENT CUTAWAY: ...",
        "views": [V("porch", (0.6, 0.64, 1.1), (0.62, 0.63, 1.22))],
        "items": [], "min": 1.6, "sfx": ["crickets"],
        "lower_third": ("MR. BASIN", "Birdbath · Declined to comment", "Facing: up."),
        "lower_third_at": "cut",
    },
    # --- QUESTION card: the interviewer types (typewriter + bell automatic)
    {"id": "q1", "kind": "qcard", "text": "Question?", "items": [], "min": 2.0, "note": "BLACK CARD."},
    # --- INTERVIEW: one still, one character; punchline after a pause
    {
        "id": "lorraine", "kind": "still", "note": "...",
        "views": [V("lorraine", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22)),
                  V("yard_before", (0.744, 0.245, 3.0), (0.744, 0.25, 3.35), "longlens")],
        "items": [L("LORRAINE", "Setup."), P(0.35), L("LORRAINE", "Punchline.")],
        "post": 0.35,
        "lower_third": ("LORRAINE", "Porch goose · Front steps, No. 7", "Gag line"),
        # "lower_third_at": "last",   # show the name card on the last line instead of at 0.35 s
        # "music": "out",   # cut the score bed for this shot. Never on a sting_soft, doorbell or reenactment
        #                   # shot (their swell/riser play on the score bus, so mixcheck fails). The shot's own
        #                   # effects sfx still play: give it none for real silence. Not right after a sting's
        #                   # tail. Every cut-back uses it; otherwise once or twice an episode.
    },
    # --- ANONYMOUS SOURCE: sfx wind + chimes. For "the wind stopped", follow it with another chime
    #     shot with no sfx and "music": "out": that cuts the score bed, and with no sfx on that shot,
    #     only the line is heard
    {
        "id": "chime", "kind": "still", "note": "...",
        "views": [V("chime", (0.5, 0.45, 1.1), (0.5, 0.42, 1.3), "anon"),
                  V("porch", (0.86, 0.13, 3.0), (0.86, 0.12, 3.35), "anon")],
        "items": [L("CHIME", "Line.")], "post": 0.1, "sfx": ["wind", "chimes"],
        "lower_third": ("ANONYMOUS SOURCE", "Voice altered", "Identity protected"),
    },
    # --- DOORBELL CAM cliffhanger: jump cut A -> B at jump_after, flicker after the last line,
    #     pause on B, then the call to action. Frame B carries the hidden bonus. The CTA asks for a
    #     description ("What else changed?"), never a bare object name, which reads as a poll vote.
    {
        "id": "doorbell", "kind": "doorbell", "note": "...",
        # frames, clock and alter_* must match SERIES.md's doorbell table: 422 at 03:12:07, 423 at 03:12:08 with
        # Ray lit. The clock ticks from clock_start, so frame A shows 03:12:03-07 and B lands on 03:12:08 (as Ep. 2).
        "frame_a": "yard_after", "frame_b": "yard_after",
        "clock_start": "03:12:03", "jump_after": 5, "frames": (422, 423),
        "alter_glow": (0.183, 0.768, 0.02),   # frame 423: Ray lit (SERIES.md doorbell table)
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.52, 1.04)),
        # "alter_box": (x0, y0, x1, y1),   # mirror this region in frame B (it turned around)
        # "camera": "NO. 5 · NOT A REENACTMENT",   # the camera label, after an episode's reenactments
        # cta_sub points at the second where frame B first shows: "Rewatch 0:01" only when B replays the cold
        # open's frame (the remake replays 418); a new frame B first shows here, so no rewatch time.
        "cta": ("SOMETHING ELSE IN", "THIS FRAME MOVED."), "cta_sub": "What else changed? ↓",
        "items": [L("NARRATOR", "Setup."), P(0.5), L("NARRATOR", "Look closer.")],
        "post": 4.0, "sfx": ["crickets"],
    },
    # --- BUTTON (optional): end cards draw no captions, so a closing line gets its own still. The best
    #     button objects to the dramatization, not the accusation.
    {
        "id": "button", "kind": "still", "music": "out", "pre": 0.2, "note": "HARD CUT back to the real ornament.",
        "views": [V("garrison", (0.47, 0.49, 1.37), (0.47, 0.49, 1.37))],
        "items": [L("GARRISON", "They made me look short.", "[with contempt] They made me look short.")],
        "post": 0.2, "min": 1.5, "sfx": ["crickets"],
    },
    # --- END card: NEXT_UP + "Follow the case." + the AI disclosure. With a reenactment in the episode the
    #     disclosure reads "Footage, reenactments and voices made with AI." and must stay fully legible
    #     1.8 s: min 2.6 (2.45 at the least). Without one, the published episodes used 3.6.
    {"id": "end", "kind": "end", "items": [], "min": 2.6, "sfx": ["sting_end"], "note": "END CARD."},
]
