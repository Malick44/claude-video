"""The show's voice cast, shared by every episode so each character sounds the same all series.

Two casts: CAST_KOKORO, the free, offline scratch voices every episode builds on today, and CAST_V4,
the final Eleven v4 voices, designed with ElevenLabs Voice Design (no voice_id yet: each is a
placeholder until its voice is designed). CAST is the decided cast: Kokoro, with the characters in
FINAL_V4 switched to v4 once they win the public voice test. NM_VOICES forces one side for an A/B:
  NM_VOICES=kokoro   every character on Kokoro
  NM_VOICES=v4       every character on v4 (build_audio.py stops, before voicing anything, on a line
                     whose character still has a placeholder voice_id)
Casting, the settings to verify, locking takes and the rollout: docs/AUDIO_ELEVENLABS_V4.md.

Each scratch voice (CAST_KOKORO) is a Kokoro TTS preset from assets/models/voices.bin (the model
files are checksum-pinned in setup.sh), plus post-processing in pipeline/build_audio.py:
  speed    Kokoro speaking rate (1.0 = the preset's default)
  pitch    rubberband pitch shift that keeps the tempo (0.86 is about 2.6 semitones down)
  altered  documentary "voice altered" chain: band-limit, light bit-crush, vibrato

Kokoro is deterministic: the same line + the same settings + the same model files give the
same audio. Keep these entries stable; changing a voice or its speed re-voices that character
in every episode (pitch, altered and fx_on_recordings only re-process the cached clips). An
episode can add one-off speakers by defining its own CAST, which is merged over this one.

Other voice sources:
  ElevenLabs   {"provider": "elevenlabs", "voice_id": "<id from your ElevenLabs voice library>",
                "model": "eleven_multilingual_v2", "seed": 7,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}
               Needs ELEVENLABS_API_KEY. "seed" keeps retakes close; pitch/altered still apply.
               Without "model", eleven_multilingual_v2 is used. "lang": "en-gb" (or "en-us", the
               default) is the accent the word timing assumes for an ElevenLabs voice; it changes no
               cache key.
               Eleven v4: {"provider": "elevenlabs", "voice_id": "<id>", "model": "eleven_v4"}. Not yet
               confirmed for v4: whether it honors "seed" and each voice_settings field, so leave them
               out until a retake test shows they work.
               v4 also takes inline audio tags in a line's spoken text, L()'s third argument:
               L("GARRISON", "I didn't see nothing.", "[too quickly] I didn't see nothing."). Tags like
               [sighs] or [too quickly] steer the delivery and go to ElevenLabs as written; Kokoro
               voices leave them out. The word highlight gives a sound tag ([sighs]) its own time and
               a direction ([too quickly]) none. A caption may show brackets only when L() has separate
               spoken text (build_audio.py stops otherwise). For a pause use punctuation or P(), not
               SSML <break> (reported disabled in v4).
  Your voice   drop <shot>_<n>.m4a (or .wav/.mp3) into an episode's recordings/ folder; SCRIPT.md
               lists the name for every line. A recording replaces that line's TTS. Add
               "fx_on_recordings": True to a character to also run its pitch/altered chain on
               your takes (e.g. to disguise your own voice as the anonymous source).
"""

import os

CAST_KOKORO = {
    "NARRATOR": {"voice": "bm_george", "speed": 1.02, "pitch": 1.0},
    "GARRISON": {"voice": "am_fenrir", "speed": 1.0, "pitch": 0.86},
    "LORRAINE": {"voice": "af_bella", "speed": 1.05, "pitch": 1.0},
    "CHIME": {"voice": "af_nicole", "speed": 1.05, "pitch": 0.72, "altered": True,
              "fx_on_recordings": True},   # a human take keeps the disguise too: it is the joke
    "MR. BASIN": {"voice": "bm_lewis", "speed": 0.95, "pitch": 0.92},  # birdbath, and his own lawyer (from Ep. 2)
    "RAY": {"voice": "am_puck", "speed": 1.1, "pitch": 1.08},        # solar frog, perky once charged (from Ep. 4)
    "DALE": {"voice": "am_michael", "speed": 0.9, "pitch": 0.97},    # inflatable snowman, slow and deflated (from Ep. 6)
    "DEB": {"voice": "bf_isabella", "speed": 0.95, "pitch": 1.0},    # lawn flamingo, first speaks in Ep. 7
    # New speakers: English presets only (af_/am_/bf_/bm_). build_audio.py phonemizes "a..." voices
    # as US English and every other voice as British.
}

# Final voices: ElevenLabs Eleven v4, designed with Voice Design. As a comment beside each voice_id:
# the design date, the full prompt and the preview text (or, for a Library voice, its ID, sharing
# terms and the soundalike check; never for the narrator, who is designed only). seed: added to every
# entry only if the seed check passes, before any take is locked. voice_settings: added per field only
# after it is verified for v4. "lang" is the accent the word timing assumes; it changes no cache key.
# The designed voices drop the Kokoro-era pitch and speed, except the CHIME: its disguise is the joke.
PLACEHOLDER = "<fill after design>"
CAST_V4 = {
    "NARRATOR":  {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-gb"},
    "GARRISON":  {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-us"},
    "LORRAINE":  {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-us"},
    "CHIME":     {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-us",
                  "pitch": 0.72, "altered": True, "fx_on_recordings": True},   # the disguise is the joke: keep it
    "MR. BASIN": {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-gb"},
    "RAY":       {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-us"},
    "DALE":      {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-us"},
    "DEB":       {"provider": "elevenlabs", "model": "eleven_v4", "voice_id": PLACEHOLDER, "lang": "en-gb"},
}
FINAL_V4 = set()   # the series default per character, set after the public voice test

# The approved audio tags per character: house style, kept out of the cast entries so editing it
# changes no cache key. Untagged is the default; a tag goes only on a punchline or button line, at most
# one tagged line per shot and one NARRATOR tag per episode. A new tag joins once it wins a blind pick
# against the untagged take. No laughter, sound-effect, accent, shouting or SSML tags, ever.
TAGS = {
    "NARRATOR": ["[quietly]", "[gravely]"],
    "GARRISON": ["[gruffly]", "[defensively]", "[too quickly]", "[quietly]", "[under his breath]", "[with contempt]",
                 "[flatly]"],
    "LORRAINE": ["[warmly]", "[sweetly]", "[unbothered]", "[coolly]"],
    "CHIME": ["[hushed]", "[nervously]", "[urgently]", "[ominously]"],
    "MR. BASIN": ["[dryly]", "[formally]", "[firmly]", "[clears throat]"],
    "RAY": ["[cheerfully]", "[brightly]", "[excitedly]"],
    "DALE": ["[slowly]", "[deflated]", "[unbothered]", "[exhales]"],
    "DEB": ["[serenely]", "[softly]"],
}

VOICES = os.environ.get("NM_VOICES", "")
if VOICES not in ("", "kokoro", "v4"):
    raise SystemExit(f"NM_VOICES={VOICES!r}: use kokoro (every character on the scratch voices) or v4 (every "
                     "character on Eleven v4), or leave it unset for the decided cast")
CAST = {**CAST_KOKORO, **{k: CAST_V4[k] for k in FINAL_V4}}   # the decided cast, per character
if VOICES == "kokoro":     # force the free scratch cast for every character
    CAST = dict(CAST_KOKORO)
elif VOICES == "v4":       # A/B builds only: every character on v4
    CAST = {**CAST_KOKORO, **CAST_V4}
