"""NOBODY MOVES, Episode 2: "I Was Right Here".

Pays off Ep. 1's hidden clue (frame 418: Lorraine turned around), introduces Mr. Basin as his
own lawyer, and plants the next clue: Ray the solar frog is lit up in frame 423.
"""

TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 2: I WAS RIGHT HERE"
NEXT_UP = "NEXT: EPISODE 3 — THE GOOSE"
ANSWER = ("In frame 423 (03:12:08) Ray, the solar frog at the front edge of the lawn, is glowing. "
          "His light only comes on after a full day of sun, so Ray was charged, awake and watching "
          "at 3:12 AM. Pays off in Episode 4, 'Only When It's Sunny'.")

_STYLE = ("Photorealistic, vertical 9:16. The same suburban house: grey vinyl siding, white porch railing "
          "and posts, black front door, brass lantern sconce, silver tubular wind chime, hostas and an "
          "echinacea flower bed. Dusk, blue hour or night. Shallow depth of field, muted teal-and-amber grade, "
          "fine film grain. No people, no text.")

# New stills this episode would like (all optional: every shot falls back to the series library).
# lorraine + chime are recurring -> put them in shows/nobody-moves/stills/; basin_counsel -> this episode's stills/.
STILLS = {
    "lorraine": ("Close-up portrait of a white ceramic goose statue sitting on the concrete front step of the "
                 "porch, 3/4 view with its beak pointing to frame-left, calm and dignified, framed like the "
                 "subject of a true-crime documentary interview, 85mm lens, warm key light from the lantern. " + _STYLE),
    "chime": ("The silver tubular wind chime hanging beside the black front door at night, backlit by the porch "
              "light so it reads as a dark silhouette with a thin golden rim light, blue night tones, light haze, "
              "the secretive mood of an anonymous-source interview. " + _STYLE),
    "basin_counsel": ("Low-angle documentary portrait of the weathered white concrete birdbath by the hostas at "
                      "dusk, with a tiny brown leather briefcase leaning against its pedestal, as if it has "
                      "retained counsel. Deadpan, dignified, shallow depth of field. " + _STYLE),
}

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731

LORRAINE_VIEWS = [V("lorraine", (0.5, 0.5, 1.05), (0.5, 0.47, 1.22)),
                  V("yard_before", (0.744, 0.245, 3.0), (0.744, 0.25, 3.35), "longlens")]
BASIN_VIEWS = [V("basin_counsel", (0.5, 0.55, 1.05), (0.5, 0.58, 1.25)),
               V("porch", (0.6, 0.64, 1.05), (0.63, 0.62, 1.32))]
CHIME_VIEWS = [V("chime", (0.5, 0.45, 1.1), (0.5, 0.42, 1.3), "anon"),
               V("porch", (0.86, 0.13, 3.0), (0.86, 0.12, 3.35), "anon")]
BOARD_POLAROIDS = [
    ("yard_before", (0.478, 0.380, 0.829), "DEB (MOVED)", 0.50, 0.40, 620, -2.5, None),
    ("garrison", (0.228, 0.335, 0.717), "GARRISON", 0.24, 0.24, 420, 4, None),
    ("yard_before", (0.680, 0.200, 0.808), "LORRAINE (TURNED)", 0.77, 0.23, 420, -5, None),
    ("porch", (0.234, 0.466, 0.978), "MR. BASIN, ESQ.", 0.23, 0.58, 420, -3, None),
    ("porch", (0.696, 0.015, 1.0), "ANON.", 0.78, 0.58, 420, 5, "anon"),
]

SHOTS = [
    # --- cold open: the same alibi, four times, fast
    {
        "id": "hook", "kind": "still", "note": "EXTREME CLOSE-UP: Garrison. Cold open, four quick cuts.",
        "views": [V("garrison", (0.47, 0.52, 2.5), (0.47, 0.51, 2.75))],
        "items": [L("GARRISON", "I was right here.")], "post": 0.2,
    },
    {
        "id": "hook2", "kind": "still", "note": "Lorraine on the porch.",
        "views": LORRAINE_VIEWS, "items": [L("LORRAINE", "I was right here, hon.")], "post": 0.2,
    },
    {
        "id": "hook3", "kind": "still", "note": "Mr. Basin.",
        "views": BASIN_VIEWS, "items": [L("MR. BASIN", "My client was right here.")], "post": 0.2,
    },
    {
        "id": "hook4", "kind": "still", "note": "The wind chime, disguised.",
        "views": CHIME_VIEWS, "items": [L("CHIME", "I was right here.")], "post": 0.35, "sfx": ["wind", "chimes"],
    },
    {
        "id": "title", "kind": "title", "note": "Title card over a piano sting.",
        "views": [V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12)),
                  V("porch", (0.42, 0.32, 1.3), (0.42, 0.36, 1.12))],
        "items": [], "min": 3.2, "sfx": ["sting"],
    },
    {
        "id": "alibi", "kind": "still", "note": "Night: the whole yard, every ornament in its place.",
        "views": [V("yard_before", (0.5, 0.42, 1.0), (0.46, 0.5, 1.2))],
        "items": [
            L("NARRATOR", "Every witness on Birchwood Court has the same alibi."),
            P(0.3),
            L("NARRATOR", "It is airtight."),
            P(0.3),
            L("NARRATOR", "It is also the only alibi available to a lawn ornament."),
        ],
        "post": 0.3,
    },
    # --- pay off Ep. 1: replay frames 417/418 and push in on the porch
    {
        "id": "replay", "kind": "doorbell",
        "note": ("DOORBELL CAM REPLAY: frames 417 to 418 again, the camera pushing in on the porch. "
                 "Frame 418: Lorraine faces the other way. Pauses on 'SHE TURNED AROUND.'"),
        "frame_a": "yard_before", "frame_b": "yard_after",
        "clock_start": 56, "frames": (417, 418),
        "alter_box": (0.7163, 0.2129, 0.7800, 0.2787),
        "kb": ((0.5, 0.5, 1.0), (0.744, 0.27, 2.4)),
        "cta": ("SHE TURNED", "AROUND."), "cta_sub": "You found it. Frame 418.",
        "items": [
            L("NARRATOR", "Last week, you found something we missed."),
            P(0.4),
            L("NARRATOR", "Frame 418. The porch.", "Frame four eighteen. The porch."),
        ],
        "post": 3.0, "sfx": ["crickets"],
    },
    {"id": "q1", "kind": "qcard", "text": "Lorraine. You told us you couldn't move.", "items": [], "min": 2.6,
     "note": "BLACK CARD."},
    {
        "id": "lorraine", "kind": "still", "note": "INTERVIEW: Lorraine, unbothered.",
        "views": LORRAINE_VIEWS,
        "items": [
            L("LORRAINE", "I said I don't go anywhere, hon."),
            P(0.35),
            L("LORRAINE", "Turning around isn't going anywhere."),
            P(0.55),
            L("LORRAINE", "It's rotating."),
            P(0.7),
            L("LORRAINE", "Next question."),
        ],
        "post": 0.35,
        "lower_third": ("LORRAINE", "Porch goose · Front steps, No. 7", "Now facing: disputed"),
    },
    {"id": "q2", "kind": "qcard", "text": "Mr. Basin. You stand six feet from where Deb stood.", "items": [],
     "min": 2.8, "note": "BLACK CARD."},
    {
        "id": "basin", "kind": "still", "note": "INTERVIEW: Mr. Basin, through counsel.",
        "views": BASIN_VIEWS,
        "items": [L("MR. BASIN", "My client has no comment at this time.")],
        "post": 0.4,
        "lower_third": ("MR. BASIN", "Birdbath · Six feet from Deb", "Attorney for Mr. Basin"),
    },
    {"id": "q3", "kind": "qcard", "text": "Who is your client?", "items": [], "min": 1.8, "note": "BLACK CARD."},
    {
        "id": "basin2", "kind": "still", "note": "Mr. Basin, tighter. A long pause before he answers.",
        "views": [V("basin_counsel", (0.5, 0.55, 1.25), (0.5, 0.56, 1.45)),
                  V("porch", (0.62, 0.62, 1.32), (0.64, 0.6, 1.6))],
        "items": [
            P(0.7),
            L("MR. BASIN", "Mr. Basin.", "Mister Basin."),
            P(0.8),
            L("NARRATOR", "Mr. Basin is representing himself.", "Mister Basin is representing himself."),
            P(0.4),
            L("NARRATOR", "He has never lost a case."),
            P(0.5),
            L("NARRATOR", "He has never had a case."),
        ],
        "post": 0.4,
    },
    {
        "id": "garrison", "kind": "still", "note": "INTERVIEW: Garrison, defensive.",
        "views": [V("garrison", (0.5, 0.56, 1.0), (0.49, 0.53, 1.18))],
        "items": [
            L("GARRISON", "Kid, I told you. I was facing the other way."),
            P(0.5),
            L("NARRATOR", "Garrison has faced the same direction for thirty-one years."),
            P(0.4),
            L("NARRATOR", "He would like that on the record."),
        ],
        "post": 0.35,
        "lower_third": ("GARRISON", "Garden gnome · Flower bed, No. 7", "Facing: the other way"),
        "lower_third_at": "last",
    },
    # --- the anonymous source almost talks; then the wind stops (same image, no wind/chimes)
    {
        "id": "chime", "kind": "still", "note": "ANONYMOUS SOURCE, mid-sentence. Hard cut.",
        "views": CHIME_VIEWS,
        "items": [
            L("CHIME", "Look. I'll tell you exactly what I saw."),
            P(0.4),
            L("CHIME", "At 3:12, the flamingo was—", "At three twelve, the flamingo was"),
        ],
        "post": 0.05, "sfx": ["wind", "chimes"],
        "lower_third": ("ANONYMOUS SOURCE", "Voice altered", "Identity protected"),
    },
    {
        "id": "calm", "kind": "still", "note": "Same shot. The wind and chimes cut out. Silence.",
        "views": [V("chime", (0.5, 0.42, 1.3), (0.5, 0.42, 1.32), "anon"),
                  V("porch", (0.86, 0.12, 3.35), (0.86, 0.12, 3.4), "anon")],
        "items": [P(1.2), L("NARRATOR", "The wind stopped.")],
        "post": 0.9,
    },
    {
        "id": "board", "kind": "board", "card": "WHAT ELSE CAN MOVE?",
        "note": "EVIDENCE BOARD, updated: Lorraine (TURNED), Mr. Basin, Esq.",
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.48, 1.18)),
        "polaroids": BOARD_POLAROIDS,
        "items": [
            L("NARRATOR", "If a concrete goose can turn around..."),
            P(0.45),
            L("NARRATOR", "what else on Birchwood Court can?"),
        ],
        "post": 0.6, "sfx": ["sting_soft"],
    },
    # --- new cliffhanger: frame 423, Ray the solar frog is lit
    {
        "id": "doorbell", "kind": "doorbell",
        "note": ("DOORBELL CAM, a few seconds later. On 'Frame 423' the frames flicker; in 423 something at "
                 "the edge of the lawn is glowing. Pauses on 'SOMEONE ELSE WAS AWAKE.'"),
        "frame_a": "yard_after", "frame_b": "yard_after",
        "clock_start": "03:12:03", "jump_after": 5, "frames": (422, 423),
        "alter_glow": (0.183, 0.768, 0.02),
        "kb": ((0.5, 0.5, 1.0), (0.5, 0.52, 1.04)),
        "cta": ("SOMEONE ELSE", "WAS AWAKE."), "cta_sub": "Comment who ↓",
        "items": [
            L("NARRATOR", "One witness hasn't said a word."),
            P(0.5),
            L("NARRATOR", "Frame 423.", "Frame four twenty-three."),
        ],
        "post": 3.8, "sfx": ["crickets"],
    },
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"],
     "note": "END CARD: title, next episode, 'Follow the case.', AI disclaimer."},
]
