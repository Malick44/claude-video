"""Shared paths and episode loading for the NOBODY MOVES pipeline."""
import importlib.util
import os
import sys

SHOW_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SHOW_DIR, "assets")  # downloaded by setup.sh, not committed
MODELS = os.path.join(ASSETS, "models")
FONTS = os.path.join(ASSETS, "fonts")


def load_episode(ep_dir):
    """Import <ep_dir>/episode.py and attach the episode's directories to it."""
    ep_dir = os.path.abspath(ep_dir)
    path = os.path.join(ep_dir, "episode.py")
    if not os.path.exists(path):
        sys.exit(f"no episode.py in {ep_dir}")
    spec = importlib.util.spec_from_file_location("episode", path)
    ep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ep)
    ep.DIR = ep_dir
    ep.SLUG = os.path.basename(ep_dir.rstrip("/"))
    ep.BUILD = os.path.join(ep_dir, "build")
    ep.STILLS_DIR = os.path.join(ep_dir, "stills")
    os.makedirs(ep.BUILD, exist_ok=True)
    return ep
