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

Other voice sources:
  ElevenLabs   {"provider": "elevenlabs", "voice_id": "<id from your ElevenLabs voice library>",
                "model": "eleven_multilingual_v2", "seed": 7,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}
               Needs ELEVENLABS_API_KEY. "seed" keeps retakes close; pitch/altered still apply.
  Your voice   drop <shot>_<n>.m4a (or .wav/.mp3) into an episode's recordings/ folder; SCRIPT.md
               lists the name for every line. A recording replaces that line's TTS. Add
               "fx_on_recordings": True to a character to also run its pitch/altered chain on
               your takes (e.g. to disguise your own voice as the anonymous source).
"""

CAST = {
    "NARRATOR": {"voice": "bm_george", "speed": 1.02, "pitch": 1.0},
    "GARRISON": {"voice": "am_fenrir", "speed": 1.0, "pitch": 0.86},
    "LORRAINE": {"voice": "af_bella", "speed": 1.05, "pitch": 1.0},
    "CHIME": {"voice": "af_nicole", "speed": 1.05, "pitch": 0.72, "altered": True},
    "MR. BASIN": {"voice": "bm_lewis", "speed": 0.95, "pitch": 0.92},  # birdbath, and his own lawyer (from Ep. 2)
    "RAY": {"voice": "am_puck", "speed": 1.1, "pitch": 1.08},        # solar frog, perky once charged (from Ep. 4)
    # New speakers: English presets only (af_/am_/bf_/bm_). build_audio.py phonemizes "a..." voices
    # as US English and every other voice as British.
}
