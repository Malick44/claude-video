"""Where each of the show's named sounds comes from.

Every sound is synthesized by default (pipeline/sounds.py). Point a name at a stock asset
here to replace it in every episode; an episode can override names with its own SOUNDS dict.

Names: theme, sting, sting_end, sting_soft, shutter, typewriter (one key, played per letter),
ding, wind, chimes, crickets, glitch, jump. theme/wind/chimes/crickets are looped or trimmed
to fit; the rest play once.

Sources (all also take "gain_db" to trim the level):
  {"file": "stock/audio/my_sting.wav"}          a local file, any format (relative to the episode
                                                folder or this folder); add "credit": "..." for
                                                anything that needs attribution
  {"url": "https://example.com/sting.mp3"}      downloaded once into stock/
  {"freesound": 123456}                         a Freesound sound by id (FREESOUND_API_KEY)
  {"freesound_search": "night crickets", "max_seconds": 60}
                                                best-rated CC0/CC-BY match, pinned on first use
  {"elevenlabs_sfx": "old camera shutter with flash whine", "seconds": 1.5}
                                                generated once by ElevenLabs (ELEVENLABS_API_KEY)

Fetched files are saved in stock/ and pinned in stock/sources.lock.json, so the same file is
reused in every episode. Credits land in stock/CREDITS.md and each episode's SCRIPT.md.
"""

SOUNDS = {
    # "sting": {"file": "stock/audio/my_sting.wav"},
    # "crickets": {"freesound_search": "crickets night ambience", "max_seconds": 60},
    # "shutter": {"elevenlabs_sfx": "vintage camera shutter click with flash charge whine", "seconds": 1.5},
}
