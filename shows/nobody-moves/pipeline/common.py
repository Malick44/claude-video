"""Shared paths, episode loading and shot-kind constants for the NOBODY MOVES pipeline."""
import functools
import hashlib
import math
import os
import re
import subprocess
import sys
import types

SHOW_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SHOW_DIR, "assets")  # downloaded by setup.sh, not committed
MODELS = os.path.join(ASSETS, "models")
FONTS = os.path.join(ASSETS, "fonts")


def load_source(name, path):
    """Run a Python file as a fresh module, always from its source. importlib's bytecode cache is keyed on
    the file's mtime (to the second) and size, so an episode.py rewritten within a second to text of the
    same length (a "clip" renamed, a number changed) would otherwise run its previous version."""
    mod = types.ModuleType(name)
    mod.__file__ = path
    with open(path, "rb") as f:
        exec(compile(f.read(), path, "exec"), mod.__dict__)
    return mod


def _import(name, path):
    return load_source(name, path)


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
    ep.CLIPS_DIR = os.path.join(ep_dir, "clips")
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


# ---------------------------------------------------------------- shot kinds

KINDS = ("still", "evidence", "title", "qcard", "board", "doorbell", "reenactment", "end")

# Kinds that play a video clip from clips/ instead of a still, with their defaults. A reenactment is the
# narrator's dramatized theory: a generated 3D clip, labelled as AI on every frame, cut hard back to the
# real, unmoved ornament. Its label is fixed: the theory and any escalation go in the stamp.
CLIP_KINDS = {
    "reenactment": {"label": "REENACTMENT · AI", "color": "red", "look": "reenact", "cue": True,
                    "cut_silence": 0.6, "length": (3.0, 6.0)},
}
CLIP_EXTS = ("mp4",)          # clips.py add files every clip as an H.264 MP4 mezzanine
CLIP_FPS = 30                 # the mezzanine's constant frame rate (the render's too)
REENACT_DEFAULT_S = 4.0       # a reenactment's length while its clip is missing and it has no "dur"
DISCLOSURE_IN = 0.65          # end card with a reenactment: the AI disclosure is fully visible from here
DISCLOSURE_MIN_S = 1.8        # ... and must stay fully visible at least this long
RX_TAG_X, RX_TAG_Y, RX_TAG_MAX_X = 64, 190, 930   # the reenactment tag's corner, and where the buttons start


def still_file(ep, key):
    """The file a still key draws from: the episode's own still, else the series library, else (for an
    episode's DERIVED_STILLS entry, which render.py computes in memory) the still it is derived from."""
    for folder in (ep.STILLS_DIR, os.path.join(SHOW_DIR, "stills")):
        for ext in ("png", "jpg", "jpeg", "webp"):
            p = os.path.join(folder, f"{key}.{ext}")
            if os.path.exists(p):
                return p
    spec = getattr(ep, "DERIVED_STILLS", {}).get(key)
    if spec and spec.get("from") and spec["from"] != key:
        return still_file(ep, spec["from"])
    return None


def clip_path(ep_dir, key):
    """episodes/<ep>/clips/<key>.mp4, else the series library's clips/<key>.mp4 (as stills: the episode's
    own clip overrides a library clip with the same key)."""
    for folder in (os.path.join(ep_dir, "clips"), os.path.join(SHOW_DIR, "clips")):
        for ext in CLIP_EXTS:
            p = os.path.join(folder, f"{key}.{ext}")
            if os.path.exists(p):
                return p
    return None


def ffmpeg_exe():
    """imageio-ffmpeg's ffmpeg (the show's .venv). Only a Python without it (Blender's own, running
    blender_reenact.py) falls back to $NM_FFMPEG, then ffmpeg on PATH."""
    try:
        import imageio_ffmpeg
    except ImportError:
        import shutil
        exe = os.environ.get("NM_FFMPEG") or shutil.which("ffmpeg")
        if exe:
            return exe
        raise
    return imageio_ffmpeg.get_ffmpeg_exe()


def clip_info(path):
    """{"seconds", "fps", "w", "h", "frames", "audio", "rotation", "sar"} of a video file, from `ffmpeg -i`
    (there is no ffprobe), or None when it has no video stream. "frames" is counted by a stream copy of
    the video, so "seconds" is the video's own length, not the container's. "w" and "h" are the decoded
    frame's, which ffmpeg turns upright: a 1920x1080 stream with a 90° display rotation is 1080x1920.
    "sar" is that frame's pixel aspect (num, den), (1, 1) when square or unknown; "rotation" is in degrees."""
    head = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    v = re.search(r"Stream #\S+.*?: Video: [^\n]*?\b(\d{2,5})x(\d{2,5})\b([^\n]*)", head)
    if not v:
        return None
    w, h = int(v[1]), int(v[2])
    sar = re.match(r"\s*\[SAR (\d+):(\d+)", v[3])
    sar = (int(sar[1]), int(sar[2])) if sar and int(sar[1]) and int(sar[2]) else (1, 1)
    rot = re.search(r"rotation of (-?[\d.]+) degrees", head) or re.search(r"\n\s*rotate\s*:\s*(-?[\d.]+)", head)
    rotation = float(rot[1]) if rot else 0.0
    if round(abs(rotation)) % 180 == 90:        # the decoder turns it upright: swap the frame and its pixels
        w, h, sar = h, w, (sar[1], sar[0])
    g = math.gcd(*sar)
    sar = (sar[0] // g, sar[1] // g)
    fps = re.search(r"Video: .*?([\d.]+) fps", head) or re.search(r"Video: .*?([\d.]+) tbr", head)
    fps = float(fps.group(1)) if fps else float(CLIP_FPS)
    count = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", path, "-map", "0:v:0", "-c", "copy", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    frames = re.findall(r"frame=\s*(\d+)", count)
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", head)
    seconds = int(frames[-1]) / fps if frames else (int(d[1]) * 3600 + int(d[2]) * 60 + float(d[3]) if d else 0.0)
    return {"seconds": round(seconds, 4), "fps": round(fps, 3), "w": w, "h": h,
            "frames": int(frames[-1]) if frames else int(round(seconds * fps)), "audio": " Audio: " in head,
            "rotation": rotation % 360, "sar": sar}


def fmt_rate(x):
    """A playback rate as the reports print it: 1.0, 0.5, 1.35."""
    text = f"{x:.2f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


def file_sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


@functools.lru_cache(maxsize=None)
def _tag_fonts():
    from PIL import ImageFont
    bold = ImageFont.truetype(os.path.join(FONTS, "Oswald.ttf"), 46)
    bold.set_variation_by_name("Bold")
    return bold, ImageFont.truetype(os.path.join(FONTS, "PlexMono.ttf"), 30)


def rx_tag_width(label, stamp=None):
    """Width in px of the reenactment tag (render.rx_tag): the red label box, or the stamp under it if
    that is wider. The same measurement render.py draws with, so validation and drawing agree."""
    bold, mono = _tag_fonts()
    w = bold.getlength(label) + 44
    if stamp:
        w = max(w, mono.getlength(stamp) + 8)
    return int(math.ceil(w))
