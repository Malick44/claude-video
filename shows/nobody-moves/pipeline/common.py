"""Shared paths and episode loading for the NOBODY MOVES pipeline."""
import importlib.util
import os
import sys

SHOW_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SHOW_DIR, "assets")  # downloaded by setup.sh, not committed
MODELS = os.path.join(ASSETS, "models")
FONTS = os.path.join(ASSETS, "fonts")


def _import(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_episode(ep_dir):
    """Import <ep_dir>/episode.py and attach the episode's directories to it."""
    ep_dir = os.path.abspath(ep_dir)
    path = os.path.join(ep_dir, "episode.py")
    if not os.path.exists(path):
        sys.exit(f"no episode.py in {ep_dir}")
    ep = _import("episode", path)
    # series voices from cast.py; an episode's own CAST only adds or overrides speakers
    series_cast = _import("cast", os.path.join(SHOW_DIR, "cast.py")).CAST
    ep.CAST = {**series_cast, **getattr(ep, "CAST", {})}
    # music/sfx sources from soundtrack.py; an episode's own SOUNDS overrides names
    ep.SOUNDS = {**load_sound_sources(), **getattr(ep, "SOUNDS", {})}
    ep.DIR = ep_dir
    ep.SLUG = os.path.basename(ep_dir.rstrip("/"))
    ep.BUILD = os.path.join(ep_dir, "build")
    ep.STILLS_DIR = os.path.join(ep_dir, "stills")
    os.makedirs(ep.BUILD, exist_ok=True)
    return ep


def load_sound_sources():
    """The show-wide SOUNDS mapping from soundtrack.py (name -> stock source)."""
    return _import("soundtrack", os.path.join(SHOW_DIR, "soundtrack.py")).SOUNDS


# Seconds from the doorbell flicker to the call-to-action reveal (the renderer shows the text,
# the mix lands the hit there).
CTA_DELAY = 1.9


def doorbell_clock(shot):
    """(clock seconds at shot start, seconds until the jump to frame B) for a doorbell shot.

    clock_start is either an int of seconds past 03:11:00 (ep01 style; the jump happens at
    03:12:00) or an "HH:MM:SS" string with an explicit jump_after (default 4 s).
    """
    cs = shot["clock_start"]
    if isinstance(cs, int):
        return 3 * 3600 + 11 * 60 + cs, shot.get("jump_after", 60 - cs)
    h, m, sec = (int(x) for x in cs.split(":"))
    return h * 3600 + m * 60 + sec, shot.get("jump_after", 4)


def fmt_clock(seconds):
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"
