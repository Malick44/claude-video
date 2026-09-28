"""NOBODY MOVES, Episode 7: "The Finale".

Pays off Ep. 6's hidden clue early (frame 530: the window beside the porch lit up at 3:15, so
somebody inside No. 7 was awake). Then the twist, provable from Ep. 1's own EXHIBIT B: the two
drag tracks don't lead from the holes, they lead to them. The Mower dragged Deb three feet right
on Saturday morning; the holes were one day old. At 3:12 AM on the 14th, nobody moved Deb:
somebody put her back, where she'd stood since 1994, by the light of an inflatable snowman on a
timer. Lorraine got her fitting (thirteen seconds), Garrison was put back facing the street, the
light went off outside and on inside. The wind chime finally finishes its Ep. 2 sentence, and Deb
speaks for the first time.
New clue: one week later, Saturday night, frame 418 again at 3:12 AM. Deb is facing the other
way. It's happening again.
"""

TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 7: THE FINALE"
NEXT_UP = "NEXT: SEASON 2"
ANSWER = ("One week later, 06/21 at 03:12:00, frame 418 again: Deb is facing the other way. In frame 417 "
          "a second earlier she faces left, as she has all series. Everything else is as it was left at "
          "3:15 on the 14th. Somebody is in the yard again, on a Saturday night. Pays off in Season 2.")

_STYLE = ("Photorealistic, vertical 9:16. The same suburban house: grey vinyl siding, white porch railing "
          "and posts, black front door, brass lantern sconce, silver tubular wind chime, hostas and an "
          "echinacea flower bed. Dusk, blue hour or night. Shallow depth of field, muted teal-and-amber grade, "
          "fine film grain. No people, no text.")

# Optional: Deb has only ever been seen from the doorbell cam. Her first close-up would land her
# first line; until then the shot uses a long-lens crop of her in the night yard.
STILLS = {
    "deb": ("Interview close-up of a classic pink plastic lawn flamingo standing on two thin metal legs in a "
            "dark front lawn at night, head in profile facing left, lit softly from the porch lantern, "
            "dignified, like a witness finally ready to talk. The house's grey siding and white porch rail "
            "soft in the background. " + _STYLE),
}

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731

RAY_LIGHT = (0.183, 0.768, 0.02)             # Ray's solar light, on since frame 423 on the 14th
WINDOW = (0.670, 0.095, 0.02)                # the window beside the porch, lit from frame 530
DEB_BOX = (0.262, 0.44, 0.478, 0.612)        # Deb in yard_back: mirrored, she faces the other way
DEB_VIEWS = [V("deb", (0.48, 0.52, 1.1), (0.46, 0.50, 1.28)),
             V("yard_after", (0.37, 0.52, 3.2), (0.37, 0.515, 3.6), "longlens")]
BOARD_POLAROIDS = [
    ("yard_before", (0.478, 0.380, 0.829), "DEB (PUT BACK)", 0.50, 0.40, 620, -2.5, None),
    ("holes", (0.100, 0.300, 0.900), "SAT 9 AM", 0.24, 0.24, 420, 4, None),
    ("snowman_flat", (0.100, 0.470, 0.800), "THE LIGHTING", 0.77, 0.23, 420, -5, None),
    ("timer", (0.120, 0.092, 0.860), "3:00–3:15", 0.29, 0.58, 420, -3, None),
    ("yard_back", (0.540, 0.000, 0.800), "3:15 (INSIDE)", 0.72, 0.58, 420, 5, None),
]

SHOTS = [
    # --- hook: the goose has known all along
    {
        "id": "hook", "kind": "still", "note": "EXTREME CLOSE-UP: Lorraine, in the fitting outfit.",
        "views": [V("lorraine_fitting", (0.5, 0.47, 1.3), (0.5, 0.45, 1.48)),
                  V("lorraine", (0.5, 0.47, 1.3), (0.5, 0.45, 1.48))],
        "items": [
            L("LORRAINE", "You want to know who moved Deb, hon?"),
            P(0.6),
            L("LORRAINE", "Nobody moved Deb."),
        ],
        "post": 0.35,
        "lower_third": ("LORRAINE", "Porch goose · Front steps, No. 7", "Knew: the whole time"),
    },
    {
        "id": "title", "kind": "title", "note": "Title card over a piano sting.",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 3.2, "sfx": ["sting"],
    },
    # --- pay off Ep. 6: replay frames 529/530, the window lights up
    {
        "id": "replay", "kind": "doorbell",
        "note": ("DOORBELL CAM REPLAY: frames 529 to 530 again, the camera pushing in on the window beside "
                 "the porch. Frame 530: it's lit. Pauses on 'SOMEBODY WAS AWAKE.'"),
        "frame_a": "yard_back", "frame_b": "yard_back",
        "clock_start": "03:14:56", "jump_after": 4, "frames": (529, 530),
        "lit": [RAY_LIGHT],
        "alter_glow": WINDOW,
        "kb": ((0.5, 0.5, 1.0), (0.66, 0.24, 2.0)),
        "cta": ("SOMEBODY WAS", "AWAKE."), "cta_sub": "You found it. Frame 530.",
        "items": [
            L("NARRATOR", "Last week, you found a window."),
            P(0.4),
            L("NARRATOR", "Frame 530.", "Frame five thirty."),
        ],
        "post": 3.6, "sfx": ["crickets"],
    },
    # --- the twist, from Ep. 1's own evidence: the drag tracks lead TO the holes
    {
        "id": "tracks", "kind": "evidence", "label": "EXHIBIT B", "stamp": "06/14 · 6:52 AM",
        "note": ("CAMERA FLASH. Ep. 1's EXHIBIT B again. A dashed arrow draws along the two drag tracks, "
                 "from the left INTO the holes, labelled 'SAT 9 AM'."),
        "views": [V("holes", (0.42, 0.44, 1.2), (0.45, 0.46, 1.4))],
        "items": [
            P(0.2),
            L("NARRATOR", "Episode 1. Two holes. Two drag tracks."),
            P(0.45),
            L("NARRATOR", "They don't lead from the holes."),
            P(0.4),
            L("NARRATOR", "They lead to them."),
        ],
        "post": 0.5, "sfx": ["shutter"],
        "annot_arrow": {"from": (0.17, 0.38), "to": (0.52, 0.60), "label": "SAT 9 AM"},
    },
    {
        "id": "oneday", "kind": "still", "note": "The holes, tighter. The narrator corrects the record.",
        "views": [V("holes", (0.66, 0.60, 1.6), (0.66, 0.61, 1.85))],
        "items": [
            L("NARRATOR", "Saturday morning, the Mower dragged Deb three feet right."),
            P(0.5),
            L("NARRATOR", "These holes weren't thirty years old."),
            P(0.4),
            L("NARRATOR", "They were one day old."),
        ],
        "post": 0.35,
    },
    {"id": "q1", "kind": "qcard", "text": "So what happened at 3:12 AM?", "items": [], "min": 2.3,
     "note": "BLACK CARD."},
    # --- the reconstruction, one witness at a time
    {
        "id": "dale", "kind": "still", "note": "Dale, flat. Saturday night, 3 AM, he goes up.",
        "views": [V("snowman_flat", (0.47, 0.71, 1.6), (0.46, 0.71, 1.75)),
                  V("holes", (0.40, 0.52, 1.8), (0.39, 0.51, 2.0))],
        "items": [
            L("NARRATOR", "3 AM. The snowman goes up.", "Three AM. The snowman goes up."),
            P(0.45),
            L("DALE", "I'm not a witness."),
            P(0.5),
            L("DALE", "I'm the lighting."),
        ],
        "post": 0.35,
        "lower_third": ("DALE", "Inflatable snowman · Side yard, No. 7", "Role: lighting"),
        "lower_third_at": "last",
    },
    {
        "id": "putback", "kind": "still", "note": "LONG LENS: Deb in the night yard, where she belongs.",
        "views": DEB_VIEWS,
        "items": [
            L("NARRATOR", "3:12. Deb goes back where she's stood since 1994.",
              "Three twelve. Deb goes back where she's stood since nineteen ninety-four."),
        ],
        "post": 0.4,
    },
    {
        "id": "fitting", "kind": "still", "note": "Lorraine, in the fitting outfit.",
        "views": [V("lorraine_fitting", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22)),
                  V("lorraine", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22))],
        "items": [
            L("NARRATOR", "The goose gets her fitting."),
            P(0.45),
            L("LORRAINE", "Thirteen seconds, hon. They know my size."),
        ],
        "post": 0.35,
    },
    {
        "id": "street", "kind": "still", "note": "Garrison, content for once.",
        "views": [V("garrison", (0.5, 0.52, 1.28), (0.5, 0.5, 1.44))],
        "items": [
            L("NARRATOR", "Garrison is put back facing the street."),
            P(0.45),
            L("GARRISON", "The way I like it."),
        ],
        "post": 0.35,
    },
    # --- the anonymous source finally finishes its Ep. 2 sentence
    {
        "id": "chime", "kind": "still", "note": "ANONYMOUS SOURCE. It's windy again.",
        "views": [V("chime", (0.5, 0.45, 1.1), (0.5, 0.42, 1.3), "anon"),
                  V("porch", (0.86, 0.13, 3.0), (0.86, 0.12, 3.35), "anon")],
        "items": [
            L("CHIME", "At 3:12, the flamingo was—", "At three twelve, the flamingo was"),
            P(0.6),
            L("CHIME", "put back."),
        ],
        "post": 0.4, "sfx": ["wind", "chimes"],
        "lower_third": ("ANONYMOUS SOURCE", "Voice altered", "Sentence: finished"),
    },
    {
        "id": "basin", "kind": "still", "note": "Mr. Basin closes the case nobody opened.",
        "views": [V("basin_counsel", (0.5, 0.55, 1.05), (0.5, 0.58, 1.25)),
                  V("porch", (0.6, 0.64, 1.05), (0.63, 0.62, 1.32))],
        "items": [
            L("MR. BASIN", "Case dismissed."),
            P(0.45),
            L("NARRATOR", "There is no judge."),
            P(0.4),
            L("MR. BASIN", "I dismissed it."),
        ],
        "post": 0.35,
        "lower_third": ("MR. BASIN", "Birdbath · Attorney for everyone", "Record: 1–0"),
    },
    # --- Deb speaks for the first time, in silence: the score cuts for this shot only
    {
        "id": "deb", "kind": "still", "note": "Deb. No score under this one. Her first line in seven episodes.",
        "views": DEB_VIEWS,
        "items": [
            L("NARRATOR", "Deb. Anything to add?"),
            P(1.1),
            L("DEB", "It's good to be home."),
        ],
        "post": 0.6, "music": "out",
        "lower_third": ("DEB", "Lawn flamingo · Center lawn, No. 7", "Condition: unharmed. Position: right."),
        "lower_third_at": "last",
    },
    {
        "id": "board", "kind": "board", "card": "NOBODY MOVED DEB.",
        "note": "EVIDENCE BOARD, solved: DEB (PUT BACK), SAT 9 AM, THE LIGHTING, 3:00–3:15, 3:15 (INSIDE).",
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.53, 1.18)),   # ends framed low: the index card stays above every app's description
        "polaroids": BOARD_POLAROIDS,
        "items": [
            L("NARRATOR", "Nobody moved Deb."),
            P(0.45),
            L("NARRATOR", "Somebody puts this yard back."),
            P(0.5),
            L("NARRATOR", "Every Saturday night."),
        ],
        "post": 0.6, "sfx": ["sting_soft"],
    },
    # --- new cliffhanger: one week later, frame 418 again, and Deb has turned around
    {
        "id": "doorbell", "kind": "doorbell",
        "note": ("DOORBELL CAM, one week later: 06/21, Saturday night. Frames 417 to 418 again, at 3:12. "
                 "The camera drifts toward Deb. In 418 she faces the other way. Pauses on 'IT'S SATURDAY "
                 "AGAIN.'"),
        "frame_a": "yard_back", "frame_b": "yard_back", "date": "06/21/2026",
        "clock_start": "03:11:56", "jump_after": 4, "frames": (417, 418),
        "alter_box": DEB_BOX,
        "kb": ((0.5, 0.5, 1.0), (0.40, 0.61, 1.7)),   # ends with Deb high in frame, above the call to action
        "cta": ("IT'S SATURDAY", "AGAIN."), "cta_sub": "Comment what moved ↓",
        "items": [
            L("NARRATOR", "One week later. Saturday night."),
            P(0.45),
            L("NARRATOR", "3:12 AM.", "Three twelve AM."),
            P(0.5),
            L("NARRATOR", "Frame 418.", "Frame four eighteen."),
        ],
        "post": 3.8, "sfx": ["crickets"],
    },
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"],
     "note": "END CARD: title, next up, 'Follow the case.', AI disclaimer."},
]
