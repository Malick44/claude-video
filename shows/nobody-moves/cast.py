"""The show's voice cast, shared by every episode so each character sounds the same all series.

Each voice is a Kokoro TTS preset from assets/models/voices.bin (the model files are
checksum-pinned in setup.sh), plus post-processing in pipeline/build_audio.py:
  speed    Kokoro speaking rate (1.0 = the preset's default)
  pitch    rubberband pitch shift that keeps the tempo (0.86 is about 2.6 semitones down)
  altered  documentary "voice altered" chain: band-limit, light bit-crush, vibrato

Kokoro is deterministic: the same line + the same settings + the same model files give the
same audio. Keep these entries stable; changing one re-voices that character in every
episode. An episode can add one-off speakers by defining its own CAST, which is merged
over this one.
"""

CAST = {
    "NARRATOR": {"voice": "bm_george", "speed": 1.02, "pitch": 1.0},
    "GARRISON": {"voice": "am_fenrir", "speed": 1.0, "pitch": 0.86},
    "LORRAINE": {"voice": "af_bella", "speed": 1.05, "pitch": 1.0},
    "CHIME": {"voice": "af_nicole", "speed": 1.05, "pitch": 0.72, "altered": True},
    # Not cast yet - uncomment when they first speak (any of the 54 Kokoro presets works):
    # "RAY": {"voice": "am_puck", "speed": 1.1, "pitch": 1.08},       # solar frog, perky once charged
    # "MR. BASIN": {"voice": "bm_lewis", "speed": 0.95, "pitch": 0.92},  # birdbath, and his own lawyer
}
