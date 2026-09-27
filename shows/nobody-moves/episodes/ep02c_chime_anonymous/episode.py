"""NOBODY MOVES, Confessional: "The Wind Chime".

A 15-25 s short, posted after Episode 2. The anonymous source's grudge is against the
investigation: it was promised nobody would know it was the chime. The lower third says the
rule up front ("Voice altered · Wind permitting"), and the title card names it right away, over
the chime unblurred; the chime never notices. Its complaint is the sound: they altered its
voice, then added wind chimes. To save its cover, it goes on the record ("I am not a wind—")
and the wind stops, mid-word. Only the narrator is left: "The wind stopped." "The source
remains anonymous."

No clue, no doorbell, no recap. The case doesn't move: the chime still hasn't finished its
sentence from Episode 2, and doesn't start it here. Every still is from the series library.
"""

TITLE = "NOBODY MOVES"
EPISODE = "CONFESSIONAL: THE WIND CHIME"   # the title card blows its cover; that's part of the joke
NEXT_UP = "EPISODE 1 IS PINNED"

L = lambda who, text, say=None: ("line", who, text, say or text)  # noqa: E731
P = lambda s: ("pause", s)  # noqa: E731
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}  # noqa: E731
# looks: None, "longlens" (soft stakeout crop), "anon" (blurred + cold, anonymous source)

SHOTS = [
    # --- hook: the grudge's setup over the blurred source, wind and chimes underneath. The lower
    #     third plants the rule in the first second, so the cut-off later reads as the wind failing it
    {
        "id": "hook", "kind": "still",
        "note": "ANONYMOUS SOURCE, close on the tubes: blurred and cold. Wind and chimes underneath.",
        "views": [V("chime", (0.61, 0.38, 1.35), (0.63, 0.35, 1.55), "anon"),
                  V("porch", (0.86, 0.13, 3.0), (0.86, 0.12, 3.35), "anon")],
        "items": [
            L("CHIME", "They said nobody would know it was me."),
        ],
        "post": 0.35, "sfx": ["wind", "chimes"],
        "lower_third": ("ANONYMOUS SOURCE", "Voice altered · Wind permitting", "Confessional"),
    },
    # --- the answer to the hook, and nobody says it out loud: the card names the source, over the
    #     chime with no blur, punched in so the clear tubes fill the card behind the text
    {
        "id": "title", "kind": "title",
        "note": "Title card over a piano sting, over the chime UNBLURRED: 'CONFESSIONAL: THE WIND CHIME'.",
        "views": [V("chime", (0.60, 0.40, 1.3), (0.61, 0.38, 1.4)),
                  V("porch", (0.74, 0.20, 1.5), (0.76, 0.18, 1.7)),
                  V("aerial", (0.5, 0.45, 1.25), (0.5, 0.5, 1.12))],
        "items": [], "min": 2.6, "sfx": ["sting"],
    },
    # --- the grudge, escalating: the show's precaution, then the sound design that undid it
    {
        "id": "grudge", "kind": "still", "note": "INTERVIEW: the source, wider. Still blurred, still windy.",
        "views": [V("chime", (0.56, 0.44, 1.12), (0.60, 0.42, 1.3), "anon"),
                  V("porch", (0.86, 0.13, 2.6), (0.86, 0.12, 2.9), "anon")],
        "items": [
            L("CHIME", "They altered my voice."),
            P(0.55),
            L("CHIME", "Then they added wind chimes."),
        ],
        "post": 0.4, "sfx": ["wind", "chimes"],
    },
    # --- it goes on the record to save its cover, and its own mechanism cuts it off mid-word.
    #     build_audio places a voice clip whole, so the cut has to be in the spoken text: "windch"
    #     is Kokoro's /wˈɪndtʃ/, "wind" plus the onset of "chime", and the clip stops on it. No
    #     comma in the spoken text, so the line runs straight into the cut
    {
        "id": "deny", "kind": "still",
        "note": "Punch in on the tubes. Hard cut mid-word: the voice stops on the 'ch' of 'chime'.",
        "views": [V("chime", (0.63, 0.35, 1.7), (0.63, 0.33, 1.95), "anon"),
                  V("porch", (0.86, 0.11, 3.4), (0.86, 0.10, 3.7), "anon")],
        "items": [
            L("CHIME", "For the record, I am not a wind—", "For the record I am not a windch"),
        ],
        "post": 0.05, "sfx": ["wind", "chimes"],
    },
    # --- punchline in real silence: same framing, no wind, no chimes, no score. The narrator gets
    #     the last word, and the investigation keeps its promise, on paper
    {
        "id": "calm", "kind": "still",
        "note": "Same shot. The wind and chimes cut out, and the score with them. The tubes hang dead still.",
        "views": [V("chime", (0.63, 0.33, 1.95), (0.63, 0.33, 1.98), "anon"),
                  V("porch", (0.86, 0.10, 3.7), (0.86, 0.10, 3.75), "anon")],
        "items": [
            P(0.8),
            L("NARRATOR", "The wind stopped."),
            P(0.6),
            L("NARRATOR", "The source remains anonymous."),
        ],
        "post": 0.4, "music": "out", "climax": True,
    },
    {"id": "end", "kind": "end", "items": [], "min": 3.6, "sfx": ["sting_end"],
     "note": "END CARD: title, 'EPISODE 1 IS PINNED', 'Follow the case.', AI disclaimer."},
]
