#!/usr/bin/env python3
"""Render a NOBODY MOVES reenactment in Blender, timed to the episode's own narration take.

A reenactment shot with a "blender" dict is rendered here and filed like any other clip, through
pipeline/clips.py's add(): episodes/<ep>/clips/<clip>.mp4 (the mezzanine render.py plays), its clips.json
entry, and a <clip>.blender.json sidecar with the full provenance. render.py needs no change. The guide is
docs/BLENDER_REENACTMENTS.md. The move lands on a word read from build/timeline.json; the subject is rigid by
construction (only its root is keyed; its yaw lives on a static parent); the camera is locked; no human can
appear (the only assets are the cast's models in models/ and procedural set pieces). The label stays
"REENACTMENT · AI" like every reenactment (decision D4), and a clip made with a PROXY can't be delivered.

  python pipeline/blender_reenact.py <episode_dir> --preview [--shot ID] [--frames every:N | a-b | a,b,c]
  python pipeline/blender_reenact.py <episode_dir> --build [--quality draft|final]    # make_episode.sh's pass
  python pipeline/blender_reenact.py <episode_dir> --quality draft|final [--force]
  python pipeline/blender_reenact.py <episode_dir> --still K[,K] [--quality Q] | --keyframe | --dry-run
         common: [--shot ID] [--scale PCT] [--engine auto|eevee|cycles] [--device auto|cpu|gpu] [--samples N]
                 [--require-models] [--save-blend] [--no-mux] [--yes] [--blender PATH] [--reprobe]
  python pipeline/blender_reenact.py <episode_dir> --has-shots     # prints yes if any shot has "blender", else no
  python pipeline/blender_reenact.py --showcase <model> [--mode sheet|turntable|pushin] [--preview] [--out-dir D]
  python pipeline/blender_reenact.py model add <name> <file.glb> --source "..." (--ai|--no-ai)
         [--height-m H] [--forward +z] [--yaw D] [--no-restyle] [--out-dir D]
  python pipeline/blender_reenact.py model list
  python pipeline/blender_reenact.py --selftest [--allow-skip]
  blender -b --factory-startup --python-exit-code 1 -P pipeline/blender_reenact.py -- <episode_dir> [flags]

Modes. --preview renders every 6th frame plus the beat frames (unless --frames says otherwise) and never writes
clips/: build/blender/<clip>/preview.mp4 (each rendered frame held, so the timing reads true; the shot's slice of
build/soundtrack.wav muxed in when it exists), sheet.png (the beat frames, captioned, tag zone and button column
outlined) and contact.png (every rendered frame). --build files the clip at $NM_RX_QUALITY (default draft) unless a
filed clip of the same content at that quality or better is already there ("up to date"). --quality draft|final
files it too. --still renders single frames to look at, never filed. With no mode the run only prints its plan.

Exit codes: 0 ok, 1 an error in the episode or the render, 2 no usable Blender/engine/device/ffmpeg, 3 the estimate
is over 30 min without --yes. make_episode.sh treats 2 and 3 as a warning (the fallback still plays) unless NM_FINAL=1.
--has-shots prints "yes" when a shot has a "blender" dict, else "no" (exit 0 either way, so make_episode.sh can tell
"no Blender shots" from a broken episode.py).

The driver imports no bpy; the worker (rx3d/worker.py) always runs in its own Blender process.
"""
import argparse
import datetime
import glob
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zlib

PIPE = os.path.dirname(os.path.abspath(__file__))
SHOW = os.path.dirname(PIPE)
if PIPE not in sys.path:
    sys.path.insert(0, PIPE)

from common import CLIP_FPS, CLIP_KINDS, load_episode as _load_episode   # noqa: E402
from common import file_sha1 as _file_sha1   # noqa: E402

FPS, W, H = CLIP_FPS, 1080, 1920
# 3D models of the cast (models/README.md). Not assets/models, which holds the Kokoro voice model.
MODELS_DIR = os.environ.get("NM_MODELS_DIR") or os.path.join(SHOW, "models")   # override: tests
ASSETS = os.path.join(SHOW, "assets")                                         # machine caches (git-ignored)
STILL_BOXES = os.path.join(SHOW, "stills", "subject_boxes.json")
CAST = ("garrison", "lorraine", "deb", "basin", "ray", "chime", "dale")
# SERIES.md: Ray 6 in, Garrison 16, Lorraine 20, Mr. Basin 28, Deb 34 (to the top of her head), the chime 36;
# Dale, the inflatable snowman, 8 ft when he is up.
HEIGHTS = {"ray": 0.152, "garrison": 0.406, "lorraine": 0.508, "basin": 0.711, "deb": 0.864, "chime": 0.914,
           "dale": 2.438}
PROXIES = ("garrison", "lorraine", "deb", "basin")
OUTFITS = (None, "bumblebee", "easter", "gingham")
LABEL_AI = CLIP_KINDS["reenactment"]["label"]   # "REENACTMENT · AI" on every reenactment, Blender or not (D4)
BEAT_KEYS = ("move", "tip", "land", "flare")
BLENDER_KEYS = {"template", "subject", "props", "camera", "seed", "options"} | \
    {f"{b}_{s}" for b in BEAT_KEYS for s in ("on", "at")}
START_BEATS = ("move", "move2", "move3", "tip")     # the beat frame is the last still frame; motion shows after it
EVENT_BEATS = ("land", "flare")                     # the beat happens on its frame
QUALITY = {   # scale %, samples (cycles/eevee), denoise, haze, bounces; "filed": writes clips/
    "preview": {"scale": 25, "cycles": 12, "eevee": 16, "denoise": True, "haze": "mist", "bounces": 6, "filed": False},
    "draft": {"scale": 50, "cycles": 24, "eevee": 32, "denoise": True, "haze": "mist", "bounces": 6, "filed": True},
    "final": {"scale": 100, "cycles": 128, "eevee": 64, "denoise": True, "haze": "volume", "bounces": 8, "filed": True},
    "selftest": {"scale": 10, "cycles": 4, "eevee": 8, "denoise": False, "haze": "off", "bounces": 4, "filed": False},
}
QRANK = {"selftest": -1, "preview": 0, "draft": 1, "final": 2}
# Only the code that shapes the picture is in the content key; editing a test, a log line or this driver's CLI
# does not re-render a final. ENCODER_VERSION stands for how a filed clip is encoded: clips.add()'s mezzanine
# (x264 CRF 17, preset slow, yuv420p, 30 fps) from a lossless PNG intermediate (lossless()).
PICTURE_MODULES = ("worker.py", "templates.py", "look.py", "proxies.py", "geo.py")
ENCODER_VERSION = "clips.add-x264-crf17-slow-yuv420p-from-png-v2"
# Cost model, seconds per frame = overhead + k * samples * megapixels (* 2.5 with volume haze). Measured here
# (4 cores, Cycles CPU, these sets): preview 270x480 at 12 spp, heist ~6 s, action ~5 s a frame.
COST = {("cycles", "cpu"): (2.5, 5.0), ("cycles", "gpu"): (1.0, 0.25), ("eevee", "gpu"): (0.6, 0.05)}
TAG_X, TAG_Y0, TAG_Y1, TAG_MARGIN, BUTTONS_X = 64, 190, 320, 20, 930
CAP_BAND = (80, 1052, 920, 1250)       # render.py: CAP_Y 1052, two 82 px lines + 34, x 500 +- 420
CUTBACK_DX, CUTBACK_DH = 0.06, 0.12    # cut-back match: x-centre within 0.06 of the frame, height within 12%
VALID_SCALES = [s for s in range(5, 101) if (W * s // 100) % 2 == 0 and (H * s // 100) % 2 == 0]
GPU_ORDER = ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI")
SOFTWARE_GL = ("llvmpipe", "softpipe", "swiftshader", "microsoft basic render", "swrast")
INSTALL_HINT = ("Blender's Python module (bpy) was not found. Install one: (1) pip, Python 3.11 only: "
                "./setup.sh --blender (python3.11 -m venv .venv-bpy && .venv-bpy/bin/pip install bpy==5.0.1); "
                "(2) the Blender app 5.0+ from blender.org, then export NM_BLENDER=/path/to/blender (macOS: "
                "/Applications/Blender.app/Contents/MacOS/Blender). Or run inside Blender: blender -b "
                "--factory-startup --python-exit-code 1 -P pipeline/blender_reenact.py -- <episode>")

from rx3d import templates as T   # noqa: E402  (bpy-free: registry, presets, camera solver)


class Fail(Exception):
    def __init__(self, msg, code=1):
        super().__init__(msg)
        self.code = code


def log(*a):
    print(*a, flush=True)


def run(cmd, **kw):
    """subprocess.run, decoding as UTF-8 (Blender prints UTF-8; the Windows locale codec would choke on it)."""
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def write_json(path, obj, **kw):
    """Write JSON atomically (temp file + os.replace): an interrupted run never leaves half a file."""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, **kw)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


# ---------------------------------------------------------------- episode, timeline, tag width
def load_episode(ep_dir):
    """common.load_episode, the loader every pipeline step uses."""
    if not os.path.exists(os.path.join(os.path.abspath(ep_dir), "episode.py")):
        raise Fail(f"no episode.py in {os.path.abspath(ep_dir)}")
    return _load_episode(ep_dir)


def load_timeline(ep):
    path = os.path.join(ep.BUILD, "timeline.json")
    if not os.path.exists(path):
        return None, None
    with open(path, "rb") as f:
        raw = f.read()
    return json.loads(raw), hashlib.sha1(raw).hexdigest()[:12]


def rx_tag_width(label, stamp):
    """render.py's tag width (common.rx_tag_width, the same measurement validate() and render.py use). Without
    PIL or the fonts (a Python inside Blender), measured metrics: PlexMono is monospaced at 18 px, and Oswald Bold
    46 averages 21.1 px a character on the label. The tag zone is in the content key, so file finals from the
    show's .venv (make_episode.sh does)."""
    try:
        from common import rx_tag_width as _w
        return _w(label, stamp)
    except Exception:
        return max(len(label) * 21.1 + 44, len(stamp or "") * 18 + 8)


def tag_zone(shot):
    """The AI tag's box plus a 20 px margin, in 1080x1920 px: nothing the viewer must see goes in here."""
    tw = rx_tag_width(shot.get("label", LABEL_AI), shot.get("stamp", ""))
    return [TAG_X - TAG_MARGIN, TAG_Y0 - TAG_MARGIN, round(TAG_X + tw + TAG_MARGIN, 1), TAG_Y1 + TAG_MARGIN]


# ---------------------------------------------------------------- words and beats
def norm_word(w):
    """Lowercase, strip surrounding punctuation and ellipses, keep inner apostrophes: 'dared.' -> 'dared'."""
    return re.sub(r"^[\W_]+|[\W_]+$", "", w.lower().replace("\u2019", "'"))


def parse_beat(spec, default_edge):
    if spec is None:
        return None
    if isinstance(spec, str):
        m = re.match(r"^(.*?)(?:#(\d+))?$", spec.strip())
        return {"word": norm_word(m.group(1)), "raw": spec, "nth": int(m.group(2) or 1), "edge": default_edge,
                "offset": 0.0}
    if isinstance(spec, dict):
        bad = set(spec) - {"word", "nth", "edge", "offset"}
        if bad or "word" not in spec:
            raise Fail(f"beat {spec!r}: keys are word, nth, edge, offset")
        if spec.get("edge", default_edge) not in ("start", "end"):
            raise Fail(f"beat {spec!r}: edge is 'start' or 'end'")
        return {"word": norm_word(spec["word"]), "raw": spec["word"], "nth": int(spec.get("nth", 1)),
                "edge": spec.get("edge", default_edge), "offset": float(spec.get("offset", 0.0))}
    raise Fail(f"beat {spec!r}: a word ('Then', 'goose#2') or a dict")


def shot_lines(shot):
    return [it[2] for it in shot.get("items", []) if it[0] == "line"]


def shot_words(tl, sid):
    out = []
    for c in tl.get("captions", []):
        if c.get("shot") == sid:
            for w, a, b in c.get("words", []):
                out.append((norm_word(w), w, float(a), float(b)))
    return out


def timeline_shot(tl, sid):
    return next((s for s in tl.get("shots", []) if s.get("id") == sid), None) if tl else None


def stale_reason(tl, shot):
    ts = timeline_shot(tl, shot["id"])
    if ts is None:
        return f"shot {shot['id']} is not in timeline.json"
    caps = [c["text"] for c in tl.get("captions", []) if c.get("shot") == shot["id"]]
    if caps != shot_lines(shot):
        return f"{shot['id']}'s lines changed since timeline.json was built"
    if shot.get("dur") is not None and abs((ts["end"] - ts["start"]) - shot["dur"]) > 1.0 / FPS + 1e-6:
        return f"{shot['id']} is {ts['end'] - ts['start']:.3f} s in timeline.json but dur is {shot['dur']}"
    return None


def resolve_beat(tl, shot, spec, at, name):
    """Shot-local seconds for a beat, where they came from ('timeline', '<name>_at' or None), the parsed spec,
    notes, and the matched word's shot-local [start, end] (None without the timeline)."""
    notes = []
    b = parse_beat(spec, "end" if name == "land" else "start")
    if tl is not None and b is not None:
        why = stale_reason(tl, shot)
        if why is None:
            ts = timeline_shot(tl, shot["id"])
            hits = [w for w in shot_words(tl, shot["id"]) if w[0] == b["word"]]
            if len(hits) >= b["nth"]:
                w = hits[b["nth"] - 1]
                t = (w[2] if b["edge"] == "start" else w[3]) + b["offset"] - ts["start"]
                if at is not None and abs(t - at) > 0.4:
                    notes.append(f"WARN {shot['id']} {name}: '{b['raw']}' is at {t:.2f} s but {name}_at says {at:.2f} s "
                                 f"(drift {t - at:+.2f} s: the take changed since {name}_at was written); the word wins")
                src = "synthetic" if tl.get("synthetic") else "timeline"
                return t, src, b, notes, [round(w[2] - ts["start"], 4), round(w[3] - ts["start"], 4)]
            words = " ".join(f"{w[1]}({w[2] - ts['start']:.2f})" for w in shot_words(tl, shot["id"]))
            msg = f"{name}_on '{b['raw']}'" + (f" #{b['nth']}" if b["nth"] > 1 else "") + f" not in {shot['id']}: {words}"
        else:
            msg = f"{why}; run build_audio.py first"
        if at is None:
            raise Fail(msg)
        notes.append(f"WARN {msg}; using {name}_at {at:.2f} s")
        return float(at), f"{name}_at", b, notes, None
    if at is not None:
        return float(at), f"{name}_at", b, notes, None
    return None, None, b, notes, None


def frames_for(shot):
    """Clip frames: ceil((in + dur) * 30) + 1, and the last frame render.py shows."""
    n = math.ceil((shot.get("in", 0.0) + shot["dur"]) * FPS - 1e-9)
    return n + 1, n - 1


def beat_frame(shot, t_shot, S=0.0, kind="event"):
    """The clip frame of a beat on render.py's grid. render.py shows clip frame floor(30*in + fi - 30*S + 1e-6) on
    global frame fi (S = the shot's start). The first global frame at or after the word (absolute w = S + t) is
    f_w = ceil(30*w - 1e-6); it shows clip frame k. An event beat (land, flare) is k; a start beat (move, tip) is
    k - 1, the last still frame, so k, the first moving frame, is on screen from the word's first frame."""
    w = S + t_shot
    f_w = math.ceil(FPS * w - 1e-6)
    k = math.floor(FPS * shot.get("in", 0.0) + f_w - FPS * S + 1e-6)
    return k - 1 if kind == "start" else k


# ---------------------------------------------------------------- models
_SHA1_MEMO = {}


def load_models(models_dir=None):
    path = os.path.join(models_dir or MODELS_DIR, "models.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def file_sha1(path):
    """common.file_sha1, memoized on (path, mtime, size): a GLB is hashed once per run."""
    st = os.stat(path)
    key = (os.path.abspath(path), st.st_mtime_ns, st.st_size)
    if key not in _SHA1_MEMO:
        _SHA1_MEMO[key] = _file_sha1(path)
    return _SHA1_MEMO[key]


def resolve_model(name, require, notes, outfit=None, models=None, models_dir=None):
    """The resolved asset: a GLB entry (with its MEASURED sha1, and every field that changes the picture) or a proxy.
    A GLB whose bytes differ from the registry fails: the normalization fields were checked against other bytes."""
    models_dir = models_dir or MODELS_DIR
    models = load_models(models_dir) if models is None else models
    key = f"{name}_{outfit}" if outfit else name
    for k in ([key, name] if outfit else [name]):
        if k in models:
            e = models[k]
            path = os.path.join(models_dir, e["file"])
            if not os.path.exists(path):
                raise Fail(f"{k}: models.json names {e['file']} but it is missing; file it with: blender_reenact.py model add")
            sha = file_sha1(path)
            if e.get("sha1") and e["sha1"] != sha:
                raise Fail(f"{k}: models/{e['file']} changed since it was filed (sha1 {sha[:12]}, models.json says "
                           f"{e['sha1'][:12]}): rerun model add {k} <file> so its height, front and import are checked")
            if outfit and k == name:
                notes.append(f"WARN {name}: no models/{key}.glb; the plain model gets the proxy outfit band")
            return {"name": k, "kind": "glb", "path": path, "file": f"models/{e['file']}", "sha1": sha,
                    "height_m": e.get("height_m", HEIGHTS.get(name)), "forward": e.get("forward", "+z"),
                    "yaw_offset_deg": e.get("yaw_offset_deg", 0), "restyle": e.get("restyle", True),
                    "anchors": e.get("anchors", {}), "ai_generated": bool(e.get("ai_generated", True)),
                    "outfit": outfit}
    if name not in PROXIES:
        raise Fail(f"{name}: no models/{name}.glb and no proxy for it (proxies: {', '.join(PROXIES)})")
    if require:
        raise Fail(f"{name}: no models/{name}.glb (--require-models); file one with: blender_reenact.py model add")
    notes.append(f"WARN {name}: no models/{key}.glb, rendering PROXY (not deliverable)")
    return {"name": name, "kind": "proxy", "proxy": name, "outfit": outfit, "height_m": HEIGHTS[name],
            "ai_generated": False}


def asset_identity(m):
    """What an asset IS, for the content key and the sidecar: swapping the figure, its bytes or any field that
    changes how it is normalized changes the key."""
    if m["kind"] == "glb":
        return {k: m.get(k) for k in ("name", "kind", "sha1", "height_m", "forward", "yaw_offset_deg", "restyle",
                                      "anchors", "outfit")}
    return {"kind": "proxy", "proxy": m.get("proxy", m["name"]), "outfit": m.get("outfit"),
            "height_m": m.get("height_m")}


# ---------------------------------------------------------------- validation (docs/BLENDER_REENACTMENTS.md §2)
def _listify(x):
    return x if isinstance(x, (list, tuple)) else [x]


def validate_shot(ep, shot):
    """(errors, warnings) for a reenactment shot's blender fields, before any timing is resolved."""
    errs, warns = [], []
    sid = shot.get("id", "?")
    bl = shot.get("blender")
    if not isinstance(bl, dict):
        return [f"{sid}: blender must be a dict"], warns
    if shot.get("kind") != "reenactment":
        errs.append(f"{sid}: a blender dict belongs on a kind 'reenactment' shot")
    bad = set(bl) - BLENDER_KEYS
    if bad:
        errs.append(f"{sid}: unknown blender key(s) {sorted(bad)} (known: {sorted(BLENDER_KEYS)})")
    if shot.get("dur") is None:
        errs.append(f"{sid}: dur is required on a Blender reenactment (the shot length can't depend on a clip "
                    f"timed from the shot itself)")
    if shot.get("speed", 1.0) != 1.0:
        errs.append(f"{sid}: speed must be 1.0 on a Blender clip (got {shot.get('speed')!r}); author slow motion "
                    f"in the scene (options.slowmo)")
    if "out" in shot:
        errs.append(f"{sid}: out must be absent on a Blender clip (dur cuts it)")
    if shot.get("in", 0.0) != 0.0:
        warns.append(f"WARN {sid}: in={shot['in']} renders and wastes the first {shot['in']} s; `in` is a trim knob "
                     f"for generated takes, use 0")
    if not shot.get("clip"):
        errs.append(f"{sid}: no clip key")
    elif shot["clip"] in (getattr(ep, "CLIPS", {}) or {}):
        errs.append(f"{sid}: clip {shot['clip']!r} is an AI clip's key (CLIPS): a Blender render never takes the AI "
                    f"clip's slot; give it its own key, such as {shot['clip']}_bl")
    elif not shot["clip"].endswith("_bl"):
        warns.append(f"WARN {sid}: clip {shot['clip']!r}: end a Blender clip's key with _bl (rx_<theory>_bl), so it "
                     f"never collides with an AI clip and .gitignore keeps its drafts out of git")
    name = bl.get("template")
    tpl = T.TEMPLATES.get(name)
    if tpl is None or name.startswith("_"):
        errs.append(f"{sid}: unknown template {name!r} (heist, action)")
        return errs, warns
    if tpl["cli_only"]:
        errs.append(f"{sid}: template {name!r} is CLI only (blender_reenact.py --showcase)")
        return errs, warns
    subj = bl.get("subject", tpl["subject"])
    if subj not in CAST:
        errs.append(f"{sid}: subject {subj!r} is not in the cast ({', '.join(CAST)})")
    if subj == "deb" and name in ("heist", "action"):
        errs.append(f"{sid}: deb can't be the subject of {name}: canon never shows how Deb was moved")
    for p in bl.get("props", tpl["props"]):
        if p not in CAST:
            errs.append(f"{sid}: prop {p!r} is not in the cast")
    known = set(tpl["beats"]) | set(tpl["optional_beats"])
    for b in BEAT_KEYS:
        if (f"{b}_on" in bl or f"{b}_at" in bl) and b not in known:
            errs.append(f"{sid}: {name} has no {b} beat ({b}_on/{b}_at; its beats: {', '.join(sorted(known))})")
    for k in ("move_on", "move_at"):
        if isinstance(bl.get(k), (list, tuple)):
            if not tpl["multi_move"]:
                errs.append(f"{sid}: {k} is a list, but {name} has one move")
            elif not 1 <= len(bl[k]) <= 3:
                errs.append(f"{sid}: {k} lists 1-3 words (one rock each)")
    opts = bl.get("options", {}) or {}
    bad = set(opts) - set(tpl["options"])
    if bad:
        errs.append(f"{sid}: unknown option(s) {sorted(bad)} for {name} (known: {sorted(tpl['options'])})")
    o = {**tpl["options"], **opts}
    if name == "heist" and o.get("path") not in ("left", "right"):
        errs.append(f"{sid}: options.path is 'left' or 'right'")
    if name == "heist" and o.get("toward", 0) > 0.35:
        warns.append(f"WARN {sid}: toward {o['toward']} > 0.35: across the frame, never along the lens axis "
                     f"(a rigid figure coming at the lens reads as a zoom)")
    if name == "action":
        if o.get("outfit") not in OUTFITS:
            errs.append(f"{sid}: outfit {o.get('outfit')!r} isn't designed (None, bumblebee, easter, gingham); "
                        f"design it in SERIES.md first")
        if not o.get("allow_facing") and not 15.0 <= float(o.get("facing_deg", 35)) <= 60.0:
            errs.append(f"{sid}: facing_deg {o.get('facing_deg')} shows Lorraine's front or back (15-60 allowed; "
                        f"frame 418's secret). Override with allow_facing only after Episode 2's payoff")
    cam = bl.get("camera", tpl["camera"])
    if isinstance(cam, str):
        if cam not in T.CAMERAS:
            errs.append(f"{sid}: unknown camera preset {cam!r} ({', '.join(T.CAMERAS)})")
    elif isinstance(cam, dict):
        bad = set(cam) - T.CAMERA_KEYS
        if bad:
            errs.append(f"{sid}: unknown camera key(s) {sorted(bad)}")
        if cam.get("preset", tpl["camera"]) not in T.CAMERAS:
            errs.append(f"{sid}: unknown camera preset {cam.get('preset')!r}")
        if float(cam.get("height", 0) or 0) > 1.2:
            warns.append(f"WARN {sid}: camera height {cam['height']} m > 1.2: not from the doorbell's angle")
        if cam.get("anchor") not in (None, "start"):
            errs.append(f"{sid}: camera anchor is 'start' or None")
    else:
        errs.append(f"{sid}: camera is a preset name or a dict")
    label = shot.get("label", LABEL_AI)
    if label != LABEL_AI:
        errs.append(f"{sid}: label must be {LABEL_AI!r}, Blender clip or not (D4); the theory goes in the stamp")
    if TAG_X + rx_tag_width(label, shot.get("stamp", "")) > BUTTONS_X:
        errs.append(f"{sid}: the tag ends past x {BUTTONS_X}: shorten the label or the stamp")
    return errs, warns


def check_beats(shot, tpl, beats, last_word_end, quality):
    errs, warns = [], []
    sid, dur = shot["id"], shot["dur"]
    relax = os.environ.get("NM_RX_SELFTEST") == "1"
    for name, b in beats.items():
        if b is None:
            continue
        if not relax and not 0.3 <= b["t_shot"] <= dur - 0.2:
            errs.append(f"{sid}: {name} at {b['t_shot']:.2f} s is outside [0.3, dur - 0.2 = {dur - 0.2:.2f}]")
        if b["source"] == "default":
            (errs if quality == "final" else warns).append(
                f"{'' if quality == 'final' else 'WARN '}{sid}: {name} timing is a guess (no timeline, no {name}_at)"
                + ("; a published clip is timed to its take" if quality == "final" else ""))
    order = [n for n in ("move", "move2", "move3", "tip", "land") if beats.get(n)]
    for a, b in zip(order, order[1:]):
        if beats[b]["t_shot"] <= beats[a]["t_shot"]:
            errs.append(f"{sid}: {b} ({beats[b]['t_shot']:.2f} s) comes before {a} ({beats[a]['t_shot']:.2f} s)")
    mv, ld = beats.get("move"), beats.get("land")
    if mv and mv["t_shot"] < 1.0 and not relax:
        warns.append(f"WARN {sid}: the move starts {mv['t_shot']:.2f} s in; stillness first (1.0 s or more)")
    if tpl["name"] == "heist" and mv:
        if dur - mv["t_shot"] < 0.5:
            warns.append(f"WARN {sid}: the cut comes {dur - mv['t_shot']:.2f} s after the glide starts (want 0.5+)")
        if last_word_end is not None and dur - last_word_end < 0.5:
            warns.append(f"WARN {sid}: the cut comes {dur - last_word_end:.2f} s after the last word (want 0.5+)")
    if tpl["name"] == "action" and ld and not 0.3 <= dur - ld["t_shot"] <= 1.0:
        warns.append(f"WARN {sid}: the cut comes {dur - ld['t_shot']:.2f} s after the landing (want 0.3-1.0)")
    return errs, warns


# ---------------------------------------------------------------- Blender discovery and probe
def _kind(path):
    return "python" if os.path.basename(path).lower().startswith("python") else "blender"


def _executable(p):
    return bool(p) and os.path.isfile(p) and os.access(p, os.X_OK)


def find_blender(explicit=None):
    """(kind, path): kind 'python' (an interpreter with bpy) or 'blender' (the app binary). None if none.
    Order: --blender, $NM_BLENDER (either one, if set, must be an executable: no silent fall-through to another
    Blender), <show>/.venv-bpy, this interpreter (or, inside the Blender app, the app binary), `blender` on PATH,
    the platform default. NM_BLENDER_DISCOVER=0 turns the auto-discovery off (tests)."""
    for src, p in (("--blender", explicit), ("$NM_BLENDER", os.environ.get("NM_BLENDER"))):
        if p:
            if _executable(p):
                return _kind(p), p
            raise Fail(f"{src} {p}: not an executable (expected a blender binary or a python with bpy)", 2)
    if os.environ.get("NM_BLENDER_DISCOVER") == "0":
        return None
    cands = [("python", os.path.join(SHOW, ".venv-bpy", "bin", "python")),
             ("python", os.path.join(SHOW, ".venv-bpy", "Scripts", "python.exe"))]
    if "bpy" in sys.modules or importlib.util.find_spec("bpy") is not None:
        try:
            import bpy
            app = getattr(bpy.app, "binary_path", "") or ""
        except Exception:
            app = ""
        cands.append(("blender", app) if app and _kind(app) == "blender" else ("python", sys.executable))
    w = shutil.which("blender")
    if w:
        cands.append(("blender", w))
    cands += [("blender", "/Applications/Blender.app/Contents/MacOS/Blender"),
              ("blender", r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe")]
    for kind, c in cands:
        if _executable(c):
            return kind, c
    return None


def worker_cmd(bl, args):
    kind, path = bl
    script = os.path.abspath(__file__)
    if kind == "python":
        return [path, script] + args
    return [path, "-b", "--factory-startup", "--python-exit-code", "1", "-P", script, "--"] + args


def _stamp(path):
    st = os.stat(path)
    return f"{os.path.realpath(path)}:{st.st_mtime_ns}:{st.st_size}"


def probe_key(bl):
    """What identifies the Blender a path runs. For the pip route the interpreter is a symlink to the system
    python, whose mtime never changes when bpy is upgraded, so the key is bpy's own module file."""
    kind, path = bl
    if kind == "python":
        r = run([path, "-c", "import importlib.util as u; s = u.find_spec('bpy'); print(s.origin if s else '')"],
                timeout=60)
        origin = (r.stdout or "").strip().splitlines()[-1:] or [""]
        if origin[0] and os.path.exists(origin[0]):
            return "bpy:" + _stamp(origin[0])
    return "bin:" + _stamp(path)


def _probe_cache():
    p = os.path.join(ASSETS, "blender_probe.json")
    try:
        with open(p, encoding="utf-8") as f:
            c = json.load(f)
        return p, (c if "entries" in c else {"entries": {}})
    except Exception:
        return p, {"entries": {}}


def forget_probe(bl):
    p, cache = _probe_cache()
    if cache["entries"].pop(bl[1], None) is not None:
        write_json(p, cache, indent=1, sort_keys=True)


def probe_blender(bl, reprobe=False):
    """Version, build hash, Cycles GPU devices, and whether Eevee works (a 16x16 render in its own process,
    because a missing EGL aborts the whole process; a software rasterizer counts as no GPU). Cached in
    assets/blender_probe.json, one entry per Blender path, keyed by what that path runs (probe_key)."""
    p, cache = _probe_cache()
    key = probe_key(bl)
    ent = cache["entries"].get(bl[1])
    if ent and ent.get("key") == key and not reprobe:
        return ent["info"]
    r = run(worker_cmd(bl, ["--worker-probe"]), timeout=300)
    line = next((ln for ln in r.stdout.splitlines() if ln.startswith("RXPROBE ")), None)
    if not line:
        raise Fail(f"Blender probe failed ({bl[1]}):\n" + "\n".join((r.stdout + r.stderr).splitlines()[-20:]), 2)
    info = json.loads(line[8:])
    with tempfile.TemporaryDirectory() as td:
        r2 = run(worker_cmd(bl, ["--worker-eevee-probe", os.path.join(td, "e.png")]), timeout=300)
        ln = next((x for x in r2.stdout.splitlines() if x.startswith("RXEEVEE ok")), None)
        info["eevee"] = r2.returncode == 0 and ln is not None
        if info["eevee"]:
            ev = json.loads(ln[len("RXEEVEE ok"):].strip() or "{}")
            info["eevee_gl"] = ev
            gl = f"{ev.get('renderer') or ''} {ev.get('vendor') or ''}".lower()
            soft = next((s for s in SOFTWARE_GL if s in gl), None)
            if not soft and ev.get("env"):
                soft = "software GL forced by " + ", ".join(f"{k}={v}" for k, v in ev["env"].items())
            if not soft and not ev.get("renderer") and ev.get("second_render_s", 0) > 2.5:
                soft = f"a 64x64 Eevee frame took {ev['second_render_s']} s"
            if soft:
                info["eevee"] = False
                info["eevee_error"] = f"Eevee runs on a software rasterizer here ({soft}): treated as no GPU"
        else:
            info["eevee_error"] = "\n".join((r2.stdout + r2.stderr).splitlines()[-3:])
    cache["entries"][bl[1]] = {"key": key, "info": info}
    write_json(p, cache, indent=1, sort_keys=True)
    return info


def check_version(info):
    v = info.get("version_tuple", [0, 0, 0])
    if tuple(v[:2]) < (5, 0):
        raise Fail(f"needs Blender 5.0+ (found {info.get('version')})", 2)


def resolve_engine(args, info, quality):
    engine, device, notes = args.engine, args.device, []
    gpus = info.get("gpu", {})
    if engine == "eevee" and device == "cpu":
        raise Fail("--engine eevee runs on the GPU only; for a CPU render use --engine cycles --device cpu", 2)
    if engine == "auto":
        engine = "eevee" if info.get("eevee") and device != "cpu" else "cycles"
        if engine == "cycles" and device != "cpu":
            notes.append("note: Eevee unavailable here (" + (info.get("eevee_error") or "no GPU/EGL").split("\n")[0][:120]
                         + "): using Cycles")
    if engine == "eevee":
        if not info.get("eevee"):
            raise Fail("Eevee needs a GPU (EGL/OpenGL); this machine has none. Use --engine cycles [--device cpu].", 2)
        device = "gpu"
    elif device == "auto":
        device = "gpu" if gpus else "cpu"
    elif device == "gpu" and not gpus:
        raise Fail("--device gpu: no Cycles GPU device found (looked for OptiX, CUDA, HIP, Metal, oneAPI)", 2)
    gpu_type = next((t for t in GPU_ORDER if t in gpus), None) if (device == "gpu" and engine == "cycles") else None
    return engine, device, gpu_type, notes


# ---------------------------------------------------------------- keys
def picture_sha1():
    """The code that shapes the picture (the worker, templates, look, proxies, geo) plus the encoder settings."""
    h = hashlib.sha1(ENCODER_VERSION.encode())
    for name in PICTURE_MODULES:
        with open(os.path.join(PIPE, "rx3d", name), "rb") as f:
            h.update(name.encode() + b"\0" + f.read())
    return h.hexdigest()


def script_sha1():
    """Every file of the tool (recorded in the sidecar; not in any key)."""
    h = hashlib.sha1()
    for p in [os.path.abspath(__file__)] + sorted(glob.glob(os.path.join(PIPE, "rx3d", "*.py"))):
        with open(p, "rb") as f:
            h.update(os.path.basename(p).encode() + b"\0" + f.read())
    return h.hexdigest()


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def content_key_of(job):
    """What the clip shows: template, assets, beat frames, dur/in, fps, camera, options, seed, the tag zone the set
    is staged around, and the picture code. Independent of the engine, device, samples and Blender version, so a
    final rendered on a GPU and committed counts as up to date on any machine."""
    keyed = {"template": job["template"], "template_version": job["template_version"],
             "subject": asset_identity(job["subject"]), "props": [asset_identity(p) for p in job["props"]],
             "beats": {k: (v["frame"] if v else None) for k, v in sorted(job["beats"].items())},
             "dur": job["dur"], "in": job["in"], "fps": job["fps"], "camera": job["camera"],
             "options": job["options"], "seed": job["seed"], "zones": job.get("zones"), "code": picture_sha1()}
    return hashlib.sha256(canon(keyed).encode()).hexdigest()


def render_key_of(render, blender_version):
    keyed = {k: render.get(k) for k in ("quality", "engine", "device", "samples", "scale", "denoise", "haze",
                                         "bounces", "glare")}
    keyed["blender"] = blender_version
    return hashlib.sha256(canon(keyed).encode()).hexdigest()


def cache_key_of(job, blender_version):
    """content x render: names the frame folder, so a preview, a draft and a final never mix."""
    ck, rk = content_key_of(job), render_key_of(job["render"], blender_version)
    job["content_key"], job["render_key"] = ck, rk
    return hashlib.sha256((ck + rk).encode()).hexdigest()


def up_to_date(sidecar, mp4_path, content_key, quality):
    """A filed clip is current when its bytes match the sidecar, it shows the same content, and it was rendered
    at the requested quality or better (final > draft > preview)."""
    if not sidecar or not os.path.exists(mp4_path):
        return False, "no filed clip"
    if sidecar.get("mp4_sha1") != file_sha1(mp4_path):
        return False, "the MP4 differs from its sidecar"
    if sidecar.get("content_key") != content_key:
        return False, "the content changed (timing, models, options or picture code)"
    if QRANK.get(sidecar.get("quality"), -1) < QRANK[quality]:
        return False, f"filed at {sidecar.get('quality')}, {quality} asked"
    return True, f"filed at {sidecar.get('quality')}"


# ---------------------------------------------------------------- cut-back match (docs/BLENDER_REENACTMENTS.md §6)
def load_still_boxes():
    try:
        with open(STILL_BOXES, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def kb_box(box, still_size, kb_start):
    """Map a still's subject box (fractions of the still) through a view's starting kb (cx, cy, zoom) to fractions
    of the 1080x1920 frame, exactly as render.py's kb_view crops it (clamped to the still)."""
    sw, sh = still_size
    cx, cy, z = kb_start
    base_w = min(sw, sh * W / H)
    base_h = base_w * H / W
    cw, ch = base_w / z, base_h / z
    x0 = min(max(cx * sw - cw / 2, 0), sw - cw)
    y0 = min(max(cy * sh - ch / 2, 0), sh - ch)
    return [(box[0] * sw - x0) / cw, (box[1] * sh - y0) / ch, (box[2] * sw - x0) / cw, (box[3] * sh - y0) / ch]


def suggest_kb(box, still_size, rx):
    """The (cx, cy, zoom) that puts a still's subject box where, and as big as, the reenactment's first frame shows
    it (`rx`, fractions of the frame): kb_box's inverse, the zoom kept at 1.0 or more (render.py can't zoom out
    past the still) and the crop kept inside the still."""
    sw, sh = still_size
    base_w = min(sw, sh * W / H)
    base_h = base_w * H / W
    z = max(1.0, (rx[3] - rx[1]) * base_h / max(1e-6, (box[3] - box[1]) * sh))
    cw, ch = base_w / z, base_h / z
    x0 = min(max((box[0] + box[2]) / 2 * sw - (rx[0] + rx[2]) / 2 * cw, 0), sw - cw)
    y0 = min(max((box[1] + box[3]) / 2 * sh - (rx[1] + rx[3]) / 2 * ch, 0), sh - ch)
    return [round((x0 + cw / 2) / sw, 2), round((y0 + ch / 2) / sh, 2), round(z, 2)]


def cutback_check(ep, shot, motion):
    """Compare the reenactment's FIRST frame with the still the hard cut lands on: the real ornament must be where
    and as big as the reenactment showed it at the start, or the cut reads as a punch-in, not 'it never moved'."""
    shots = list(ep.SHOTS)
    i = next((n for n, s in enumerate(shots) if s is shot or s.get("id") == shot["id"]), None)
    nxt = shots[i + 1] if i is not None and i + 1 < len(shots) else None
    boxes = load_still_boxes()
    derived = getattr(ep, "DERIVED_STILLS", {}) or {}
    s0 = (motion["screen"].get("subject") or [None])[0]
    if not nxt or not s0:
        return None, []
    for v in nxt.get("views", []) or []:
        img = v.get("img")
        src = img if img in boxes else (derived.get(img, {}).get("from") if isinstance(derived.get(img), dict) else None)
        if src not in boxes:
            continue
        b = kb_box(boxes[src]["box"], boxes[src]["size"], v["kb"][0])
        rx = [s0[0] / W, s0[1] / H, s0[2] / W, s0[3] / H]
        dcx = (rx[0] + rx[2]) / 2 - (b[0] + b[2]) / 2
        dh = (rx[3] - rx[1]) / max(1e-6, b[3] - b[1]) - 1
        res = {"next_shot": nxt["id"], "still": img, "still_box": [round(x, 3) for x in b],
               "rx_frame0_box": [round(x, 3) for x in rx], "dcx": round(dcx, 3), "dh": round(dh, 3),
               "ok": abs(dcx) <= CUTBACK_DX and abs(dh) <= CUTBACK_DH,
               "suggested_kb": suggest_kb(boxes[src]["box"], boxes[src]["size"], rx)}
        warns = []
        if not res["ok"]:
            k = res["suggested_kb"]
            warns.append(f"WARN {shot['id']}: the cut-back to {nxt['id']} ({img}) doesn't match the reenactment's first "
                         f"frame: x-centre off by {dcx:+.3f} (max {CUTBACK_DX}), height off by {dh:+.0%} (max "
                         f"{CUTBACK_DH:.0%}). Give {nxt['id']}'s views a kb of about ({k[0]:.2f}, {k[1]:.2f}, {k[2]:.2f}), "
                         f"or move the camera's start_cx/fill")
        return res, warns
    return None, [f"note {shot['id']}: no subject box for {nxt['id']}'s still in stills/subject_boxes.json: "
                  f"cut-back match not checked"]


# ---------------------------------------------------------------- jobs
def resolve_shot(ep, shot, args, tl, tl_sha1, quality, render, blender_version, filed=False):
    """Validate, resolve timing, models, camera and options into a job. Returns (job, notes)."""
    errs, notes = validate_shot(ep, shot)
    if errs:
        raise Fail("\n".join(errs))
    bl = shot["blender"]
    tpl = T.TEMPLATES[bl["template"]]
    opts = {**tpl["options"], **(bl.get("options") or {})}
    cam = bl.get("camera", tpl["camera"])
    cam = dict(T.CAMERAS[cam]) if isinstance(cam, str) else {**T.CAMERAS[cam.get("preset", tpl["camera"])], **cam}
    preset = cam.pop("preset", None) or (bl.get("camera") if isinstance(bl.get("camera"), str) else tpl["camera"])
    for k in ("fill", "top_at", "fstop", "start_cx", "start_cy"):
        if k in opts and (not isinstance(bl.get("camera"), dict) or k not in bl["camera"]):
            cam[k] = opts[k]
    cam["preset"] = preset
    beats, sources = {}, {}
    last_word_end = None
    ts = timeline_shot(tl, shot["id"])
    S = float(ts["start"]) if ts else 0.0
    if tl is not None and ts and not stale_reason(tl, shot):
        ws = shot_words(tl, shot["id"])
        if ws:
            last_word_end = ws[-1][3] - ts["start"]
    specs = []
    for name in tpl["beats"] + tpl["optional_beats"]:
        on, at = bl.get(f"{name}_on"), bl.get(f"{name}_at")
        if name == "move" and (isinstance(on, (list, tuple)) or isinstance(at, (list, tuple))):
            ons, ats = _listify(on) if on is not None else [], _listify(at) if at is not None else []
            for i in range(max(len(ons), len(ats))):
                specs.append(("move" if i == 0 else f"move{i + 1}", ons[i] if i < len(ons) else None,
                              ats[i] if i < len(ats) else None, True))
        else:
            specs.append((name, on, at, name in tpl["beats"]))
    for name, on, at, required in specs:
        if not required and on is None and at is None:
            continue
        t, src, b, n, wt = resolve_beat(tl, shot, on, at, name.rstrip("23") if name.startswith("move") else name)
        notes += n
        if t is None:
            if not required:
                continue
            t = 0.55 * shot["dur"] if name == "move" else shot["dur"] - 0.45
            if tpl["name"] == "action" and name == "move":
                t = max(0.3, shot["dur"] - 0.45 - 1.6)
            src = "default"
        kind = "start" if name in START_BEATS else "event"
        beats[name] = {"word": b["raw"] if b else None, "t_shot": round(t, 4), "frame": beat_frame(shot, t, S, kind),
                       "kind": kind, "source": src, "word_t": wt}
        sources[name] = src
    e2, w2 = check_beats(shot, tpl, beats, last_word_end, quality)
    notes += w2
    if e2:
        raise Fail("\n".join(e2))
    if tl is not None and tl.get("synthetic"):
        if filed and quality == "final":
            raise Fail(f"{shot['id']}: build/timeline.json is synthetic (estimated word times): a published clip is "
                       f"timed to its voiced take: run build_audio.py")
        notes.append(f"WARN {shot['id']}: timeline.json is synthetic (estimated word times); fine for a preview or a "
                     f"draft, never for a final")
    subj_name = bl.get("subject", tpl["subject"])
    subject = resolve_model(subj_name, args.require_models, notes,
                            outfit=opts.get("outfit") if subj_name == "lorraine" else None)
    props = [resolve_model(p, args.require_models, notes) for p in bl.get("props", tpl["props"])]
    nframes, last_shown = frames_for(shot)
    seed = int(bl.get("seed", zlib.crc32(shot["clip"].encode()) % 100000))
    # provenance for clips.json and the sidecar; the on-screen label is REENACTMENT · AI either way (D4)
    ai = subject.get("ai_generated", False) or any(p.get("ai_generated", False) for p in props)
    proxy = subject["kind"] == "proxy" or any(p["kind"] == "proxy" for p in props)
    job = {"template": tpl["name"], "template_version": tpl["version"], "episode": ep.SLUG, "shot": shot["id"],
           "clip": shot["clip"], "fps": FPS, "in": float(shot.get("in", 0.0)), "dur": float(shot["dur"]),
           "frames": nframes, "last_shown": last_shown, "seed": seed, "options": opts, "camera": cam,
           "subject": subject, "props": props, "beats": beats, "render": render, "zones": {"tag": tag_zone(shot)},
           "timing": {"source": sources, "timeline_sha1": tl_sha1, "shot_start": S,
                      "synthetic": bool(tl and tl.get("synthetic"))},
           "ai_generated": ai, "proxy": proxy}
    job["cache_key"] = cache_key_of(job, blender_version)
    return job, notes


def render_settings(quality, engine, device, gpu_type, samples=None, scale=None, threads=None):
    q = QUALITY[quality]
    scale = int(scale or q["scale"])
    check_scale(scale)
    return {"quality": quality, "engine": engine, "device": device, "gpu_type": gpu_type,
            "samples": int(samples or (q["eevee"] if engine == "eevee" else q["cycles"])),
            "scale": scale, "denoise": q["denoise"], "haze": q["haze"], "bounces": q["bounces"],
            "glare": True, "threads": threads or os.cpu_count(), "exposure": 0.0,
            "denoiser": "optix" if gpu_type == "OPTIX" else "oidn"}


def check_scale(scale):
    if scale not in VALID_SCALES:
        w, h = W * scale // 100, H * scale // 100
        near = sorted(VALID_SCALES, key=lambda s: abs(s - scale))[:4]
        raise Fail(f"--scale {scale} gives {w}x{h}; yuv420p needs even sizes: use {', '.join(map(str, sorted(near)))} "
                   f"(or 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 100)")


def estimate(render, n):
    o, k = COST.get((render["engine"], render["device"]), (2.5, 5.0))
    mp = (W * render["scale"] / 100) * (H * render["scale"] / 100) / 1e6
    per = o + k * render["samples"] * mp * (2.5 if render["haze"] == "volume" else 1.0)
    return per, per * n


FRAMES_FORMS = "accepted: every:N (N >= 1), a-b, or a,b,c (clip frames, 0-based)"


def parse_frames(spec, nframes, key_frames=()):
    try:
        if not spec or spec == "every:1":
            ks = list(range(nframes))
        elif spec.startswith("every:"):
            n = int(spec[6:])
            if n < 1:
                raise ValueError
            ks = list(range(0, nframes, n))
        elif "-" in spec:
            a, b = spec.split("-")
            ks = list(range(int(a), min(int(b), nframes - 1) + 1))
        else:
            ks = [int(x) for x in spec.split(",")]
    except ValueError:
        raise Fail(f"--frames {spec!r}: {FRAMES_FORMS}")
    for k in ks:
        if not 0 <= k < nframes:
            raise Fail(f"frame {k} is outside the clip (0-{nframes - 1})")
    if not ks:
        raise Fail(f"--frames {spec!r} selects no frame; {FRAMES_FORMS}")
    return sorted(set(ks) | {k for k in key_frames if k is not None and 0 <= k < nframes})


def _job_results(job_path):
    try:
        with open(job_path, encoding="utf-8") as f:
            spec = json.load(f)
    except Exception:
        return []
    out = []
    for j in spec.get("jobs", [spec]):
        rp = j.get("result_path")
        if rp and os.path.exists(rp):
            try:
                with open(rp, encoding="utf-8") as f:
                    out.append(json.load(f))
            except Exception:
                pass
    return out


def run_worker(bl, job_path, log_path, quiet=False, timeout=None):
    """Run the worker in its own Blender process. A failed job leads the error with its own errors (STAGING,
    the importer's message) from result.json, then the log tail. `timeout` (s) kills a stuck worker (a hung GPU
    driver or Eevee context would otherwise hang make_episode for ever)."""
    t0 = time.time()
    killed = []
    with open(log_path, "w", encoding="utf-8") as lf:
        p = subprocess.Popen(worker_cmd(bl, ["--worker", job_path]), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace")
        timer = None
        if timeout:
            def kill():
                killed.append(True)
                p.kill()
            timer = threading.Timer(timeout, kill)
            timer.daemon = True
            timer.start()
        try:
            for line in p.stdout:
                lf.write(line)
                if line.startswith("RX ") and not quiet:
                    log("  " + line.rstrip())
            p.wait()
        finally:
            if timer:
                timer.cancel()
    if killed or p.returncode != 0:
        with open(log_path, encoding="utf-8", errors="replace") as f:
            tail = "".join(f.readlines()[-40:])
        errs = [e for r in _job_results(job_path) for e in r.get("errors", [])]
        head = ("; ".join(errs) + "\n") if errs else ""
        why = f"ran over {timeout:.0f} s and was killed" if killed else f"failed (exit {p.returncode})"
        raise Fail(f"{head}the Blender worker {why}; {log_path}:\n{tail}")
    return time.time() - t0


# ---------------------------------------------------------------- encoding
def find_ffmpeg():
    if os.environ.get("NM_FFMPEG"):
        return os.environ["NM_FFMPEG"]
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    w = shutil.which("ffmpeg")
    if not w:
        raise Fail("pip install imageio-ffmpeg (in the show's .venv) or put ffmpeg on PATH / set NM_FFMPEG", 2)
    return w


def ffmpeg_version():
    try:
        return (run([find_ffmpeg(), "-version"]).stdout.splitlines() or [""])[0].strip()
    except Exception:
        return None


def _link(src, dst):
    """A numbered name for a frame: a symlink, else a hard link, else a copy (Windows without Developer Mode)."""
    for fn in (os.symlink, os.link, shutil.copyfile):
        try:
            fn(src, dst)
            return
        except (OSError, NotImplementedError):
            continue
    raise Fail(f"can't stage {src} for ffmpeg")


def encode(frames_dir, names, out, audio=None, a_start=0.0, a_dur=None):
    """A preview MP4 (never filed: a filed clip goes through clips.add()): H.264 yuv420p, CRF 17, 30 fps, BT.709,
    +faststart, bitexact. `names[i]` is the PNG shown on output frame i (a held frame repeats its name)."""
    ff = find_ffmpeg()
    with tempfile.TemporaryDirectory() as td:
        for i, n in enumerate(names):
            _link(os.path.join(os.path.abspath(frames_dir), n), os.path.join(td, f"{i:05d}.png"))
        cmd = [ff, "-y", "-v", "error", "-framerate", str(FPS), "-start_number", "0", "-i", os.path.join(td, "%05d.png")]
        if audio:
            cmd += ["-ss", f"{a_start:.3f}", "-t", f"{a_dur:.3f}", "-i", audio]
        cmd += ["-map", "0:v"] + (["-map", "1:a", "-c:a", "aac", "-b:a", "160k", "-shortest"] if audio else ["-an"])
        cmd += ["-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "medium",
                "-crf", "17", "-r", str(FPS), "-x264-params", "threads=4", "-color_primaries", "bt709",
                "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", "-fflags", "+bitexact",
                "-flags:v", "+bitexact", "-map_metadata", "-1", "-f", "mp4", out]
        r = run(cmd)
        if r.returncode:
            raise Fail(f"ffmpeg failed: {r.stderr[-800:]}")


def lossless(frames_dir, n, out):
    """Frames 0000.png .. n-1 as a lossless RGB video (PNG in Matroska, 30 fps): what clips.add() files from."""
    r = run([find_ffmpeg(), "-y", "-v", "error", "-framerate", str(FPS), "-start_number", "0",
             "-i", os.path.join(os.path.abspath(frames_dir), "%04d.png"), "-frames:v", str(n), "-c:v", "png",
             "-fflags", "+bitexact", "-flags:v", "+bitexact", "-map_metadata", "-1", out])
    if r.returncode or not os.path.exists(out):
        raise Fail(f"ffmpeg failed on the frames: {r.stderr[-800:]}")


def probe_mp4(path):
    """fps, pixel format, size, audio streams and duration from `ffmpeg -i` (there is no ffprobe dependency)."""
    r = run([find_ffmpeg(), "-hide_banner", "-i", path])
    s = r.stderr
    v = re.search(r"Video: (\w+).*?, (\w+)(?:\([^)]*\))?, (\d+)x(\d+).*?, ([\d.]+) fps", s)
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", s)
    return {"codec": v.group(1) if v else None, "pix_fmt": v.group(2) if v else None,
            "w": int(v.group(3)) if v else None, "h": int(v.group(4)) if v else None,
            "fps": float(v.group(5)) if v else None, "audio": "Audio:" in s,
            "seconds": (int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3))) if d else None}


# ---------------------------------------------------------------- screen geometry
def poly_area(poly):
    n = len(poly)
    return abs(sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))) / 2 \
        if n >= 3 else 0.0


def clip_poly_rect(poly, rect):
    """Sutherland-Hodgman: a convex polygon clipped to the rectangle [x0, y0, x1, y1]."""
    x0, y0, x1, y1 = rect
    edges = ((lambda p: p[0] >= x0, lambda a, b: _ix(a, b, 0, x0)), (lambda p: p[0] <= x1, lambda a, b: _ix(a, b, 0, x1)),
             (lambda p: p[1] >= y0, lambda a, b: _ix(a, b, 1, y0)), (lambda p: p[1] <= y1, lambda a, b: _ix(a, b, 1, y1)))
    out = [tuple(p) for p in poly]
    for inside, cut in edges:
        if not out:
            break
        src, out = out, []
        for i, cur in enumerate(src):
            prev = src[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cut(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cut(prev, cur))
    return out


def _ix(a, b, axis, v):
    t = (v - a[axis]) / ((b[axis] - a[axis]) or 1e-12)
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


def hull_in_rect(hull, rect):
    """Area (px^2) of a screen hull inside a rectangle; a thin beam hull still counts (> 0.5 px^2)."""
    if not hull:
        return 0.0
    if len(hull) < 3:
        return 1.0 if any(rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3] for x, y in hull) else 0.0
    return poly_area(clip_poly_rect(hull, rect))


# ---------------------------------------------------------------- checks on motion.json
def screen_checks(job, motion, shot, ep=None, facts=None):
    """docs/BLENDER_REENACTMENTS.md §6, in 1080x1920 px. Returns (checks, warnings). Cheap: an up-to-date run re-runs it on the
    cached motion.json."""
    checks, warns = {}, []
    sid = shot["id"]
    zone = tag_zone(shot)
    boxes = [b for b in motion["screen"].get("subject", []) if b]
    last = job["last_shown"]
    shown = boxes[: last + 1]

    def overlap(a, b):
        return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    # the top left stays clear: every tracked thing the template names (subject, beams, the fireball), by its hull
    hulls = motion.get("hull", {})
    clear = {}
    for tr in motion.get("keep_clear", ["subject"]):
        hs = hulls.get(tr, [])[: last + 1]
        hit = [k for k, h in enumerate(hs) if h and hull_in_rect(h, zone) > 0.5]
        clear[tr] = not hit
        if hit:
            warns.append(f"WARN {sid}: {tr} enters the AI tag zone {[round(z) for z in zone]} on frames {hit[0]}-{hit[-1]}: "
                         f"keep the top left clear")
    checks["tag_zone_clear"] = all(clear.values()) if clear else True
    checks["tag_zone"] = {k: v for k, v in sorted(clear.items())}
    cx = [(b[0] + b[2]) / 2 for b in shown]
    cy = [(b[1] + b[3]) / 2 for b in shown]
    checks["button_column"] = max(cx) <= BUTTONS_X
    if not checks["button_column"]:
        warns.append(f"WARN {sid}: the subject's centre reaches x {max(cx):.0f} (> {BUTTONS_X}, TikTok's buttons)")
    checks["edges"] = min(cx) >= 0.1 * W and max(cx) <= 0.9 * W and min(cy) >= 0.1 * H and max(cy) <= 0.9 * H
    if not checks["edges"]:
        warns.append(f"WARN {sid}: the subject's centre leaves the inner 80% of the frame "
                     f"(x {min(cx):.0f}-{max(cx):.0f}, y {min(cy):.0f}-{max(cy):.0f})")
    caps = max(overlap(b, CAP_BAND) / max(1.0, (b[2] - b[0]) * (b[3] - b[1])) for b in shown)
    checks["captions_overlap"] = round(caps, 3)
    if caps > 0.3:
        warns.append(f"WARN {sid}: {caps:.0%} of the subject's box sits in the caption band (keep it under 30%)")
    checks["camera_static"] = all(m == motion["camera"][0] for m in motion["camera"])
    props = [p["name"] for p in job["props"]]
    checks["props_static"] = all(all(m == motion["objects"][p][0] for m in motion["objects"][p]) for p in props
                                 if p in motion["objects"])
    hd = next(iter(motion["heading_deg"].values()), [0])
    checks["yaw_constant"] = all(abs(h - hd[0]) < 1e-3 for h in hd)
    mv = job["beats"].get("move")
    name = job["subject"]["name"]
    subj = motion["objects"].get(name) or motion["objects"].get(name.split("_")[0])
    if mv and subj:
        checks["still_until_move"] = all(m == subj[0] for m in subj[: mv["frame"] + 1])
        checks["moves_after"] = subj[min(mv["frame"] + 2, len(subj) - 1)] != subj[0]
    if motion.get("facing"):
        f = next(iter(motion["facing"].values()))
        angs = [a for a, _ in f]
        checks["facing_deg"] = [round(min(angs), 2), round(max(angs), 2)]
        checks["beak_left"] = all(s < 0 for _, s in f)
        if not 15 <= min(angs) or max(angs) > 60:
            warns.append(f"WARN {sid}: her front is {min(angs):.1f}-{max(angs):.1f} deg to the image plane (15-60)")
    # an effect big enough to read on a phone (the fireball: 6% of the frame by the land beat)
    for tr, rule in sorted((motion.get("coverage_rules") or {}).items()):
        hs = hulls.get(tr, [])
        k = rule.get("by_frame") or last
        h_ = hs[min(k, len(hs) - 1)] if hs else None
        frac = poly_area(clip_poly_rect(h_, (0, 0, W, H))) / (W * H) if h_ and len(h_) >= 3 else 0.0
        checks[f"{tr}_coverage"] = round(frac, 4)
        if frac < rule["min_frac"]:
            warns.append(f"WARN {sid}: the {tr} covers {frac:.1%} of the frame on frame {k} (want "
                         f"{rule['min_frac']:.0%}+): on a phone it won't read")
    # a prop is only readable with its head in frame
    for pname, anchors in sorted((motion.get("prop_anchors") or {}).items()):
        if "head" in anchors:
            x, y, d = anchors["head"]
            inside = d > 0 and 0 <= x <= W and 0 <= y <= H
            checks[f"{pname}_head_in_frame"] = inside
            if not inside:
                warns.append(f"WARN {sid}: {pname}'s head is off the frame (at {x:.0f}, {y:.0f} px): only an "
                             f"unreadable body shows. Reframe, or drop the prop and keep its point of view")
    fv = motion.get("feet_visibility")
    if fv:
        checks["feet_hidden_by_fx"] = fv["fx"]
        if fv["fx"] > 0.5:
            warns.append(f"WARN {sid}: {fv['fx']:.0%} of {name}'s feet are hidden by effects (dust ...) on the last "
                         f"frame, the one the cut leaves in memory")
    bc = [c for c in motion.get("beam_clearance_m", [])[: last + 1] if c is not None]
    if bc:
        checks["beam_clearance_in"] = [round(min(bc) / 0.0254, 3), round(bc[0] / 0.0254, 3), round(bc[-1] / 0.0254, 3)]
    facts = facts if facts is not None else motion.get("facts", {})
    if "min_step_clearance_m" in facts and facts["min_step_clearance_m"] < -0.005:
        warns.append(f"WARN {sid}: the fall sinks {-facts['min_step_clearance_m'] * 1000:.0f} mm into a step")
    # timing: the drop starts on its word and lands after it
    ph = facts.get("phases")
    if ph and isinstance(ph, dict):
        trig = job["beats"].get("tip") or job["beats"].get("land")
        ld = job["beats"].get("land")
        if trig and trig.get("word_t"):
            onset = trig["word_t"][0]
            d_tip, d_fall = ph["t_tip"] - onset, ph["t_fall"] - onset
            checks["drop_on_word_s"] = round(min(d_tip, d_fall, key=abs), 3)
            if min(abs(d_tip), abs(d_fall)) > 0.1:
                warns.append(f"WARN {sid}: the tip ({ph['t_tip']:.2f} s) and the fall ({ph['t_fall']:.2f} s) miss "
                             f"'{trig['word']}' ({onset:.2f} s) by more than 0.1 s: the punch word must trigger the drop")
        if ld and ld.get("word_t"):
            after = ph["t_land"] - ld["word_t"][1]
            checks["land_after_word_s"] = round(after, 3)
            if after < 0.25:
                warns.append(f"WARN {sid}: she lands {after:.2f} s after '{ld['word']}' ends (want 0.25 s+: the thud "
                             f"lands in the silence after the word)")
    if "cast_count" in motion:
        checks["cast_count"] = motion["cast_count"]
    if ep is not None:
        cb, w = cutback_check(ep, shot, motion)
        if cb:
            checks["cutback"] = cb
        warns += w
    return checks, warns


# ---------------------------------------------------------------- preview sheets (PIL; skipped without it)
def _font(size):
    from PIL import ImageFont
    for p in (os.path.join(ASSETS, "fonts", "PlexMono.ttf"), "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _overlay_zones(d, x0, y0, s, zone):
    d.rectangle((x0 + (zone[0] + TAG_MARGIN) * s, y0 + (zone[1] + TAG_MARGIN) * s, x0 + (zone[2] - TAG_MARGIN) * s,
                 y0 + (zone[3] - TAG_MARGIN) * s), outline=(255, 60, 60))
    d.line((x0 + BUTTONS_X * s, y0, x0 + BUTTONS_X * s, y0 + H * s), fill=(80, 200, 255))


def contact_sheet(frames_dir, ks, job, out, header, beat_frames, cols=6):
    from PIL import Image, ImageDraw
    ims = [Image.open(os.path.join(frames_dir, f"{k:04d}.png")).convert("RGB") for k in ks]
    w, h = ims[0].size
    rows = math.ceil(len(ims) / cols)
    pad, lab, top = 8, 30, 64
    sheet = Image.new("RGB", (cols * (w + pad) + pad, top + rows * (h + lab + pad)), (18, 18, 22))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 10), header, font=_font(18), fill=(240, 240, 240))
    d.text((pad, 36), "red box: AI tag zone · blue line: button column (x 930) · * beat frame", font=_font(13),
           fill=(170, 170, 180))
    s = w / W
    for i, (k, im) in enumerate(zip(ks, ims)):
        r, c = divmod(i, cols)
        x, y = pad + c * (w + pad), top + r * (h + lab + pad)
        sheet.paste(im, (x, y))
        _overlay_zones(d, x, y, s, job["zones"]["tag"])
        beat = [n for n, f in beat_frames.items() if f == k]
        cut = k > job["last_shown"]
        txt = f"f{k:03d} {k / FPS:5.2f}s" + (f" *{beat[0]}" if beat else "") + (" (past cut)" if cut else "")
        d.text((x + 2, y + h + 6), txt, font=_font(14), fill=(255, 210, 60) if beat else (220, 220, 220))
    sheet.save(out)


def key_sheet(frames_dir, items, job, out, header):
    """The design's preview sheet: frame 0, the beats, move + 0.5 s, the last frame; each captioned."""
    from PIL import Image, ImageDraw
    ims = [Image.open(os.path.join(frames_dir, f"{k:04d}.png")).convert("RGB") for k, _ in items]
    w, h = ims[0].size
    pad, lab, top = 10, 46, 40
    sheet = Image.new("RGB", (len(ims) * (w + pad) + pad, top + h + lab), (18, 18, 22))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 10), header, font=_font(18), fill=(255, 120, 120) if "PROXY" in header else (240, 240, 240))
    for i, ((k, cap), im) in enumerate(zip(items, ims)):
        x = pad + i * (w + pad)
        sheet.paste(im, (x, top))
        _overlay_zones(d, x, top, w / W, job["zones"]["tag"])
        d.text((x + 2, top + h + 4), f"f{k:03d} {k / FPS:.2f}s", font=_font(14), fill=(255, 210, 60))
        d.text((x + 2, top + h + 24), cap[:34], font=_font(13), fill=(220, 220, 220))
    sheet.save(out)


# ---------------------------------------------------------------- filing: sidecar and clips.json
def git_info():
    """The commit, and whether the tool or the models have uncommitted edits (scoped: not the whole repo, and
    called before the new clip is written)."""
    try:
        c = run(["git", "-C", SHOW, "rev-parse", "--short", "HEAD"])
        if c.returncode:
            return None
        d = run(["git", "-C", SHOW, "status", "--porcelain", "--", "pipeline/blender_reenact.py", "pipeline/rx3d",
                 "models"])
        return {"commit": c.stdout.strip(), "dirty": bool(d.stdout.strip())}
    except Exception:
        return None


def cliptools():
    """pipeline/clips.py, imported when filing (it needs numpy; --has-shots and --dry-run don't)."""
    import clips
    return clips


def clip_entry(clips_dir, key):
    """The clip's clips.json entry, read by clips.py's own reader."""
    return cliptools().clip_entry(clips_dir, key)


def describe(job):
    b = job["beats"]
    s = job["subject"]["name"]
    if job["template"] == "heist":
        mv = b["move"]
        w = f" ('{mv['word']}')" if mv.get("word") else ""
        return (f"heist: {s} glides {job['options']['path']} from {mv['t_shot']:.2f} s{w}, "
                f"{job['options']['travel']} frame width by the cut" +
                ("; " + ", ".join(p["name"] for p in job["props"]) + " static" if job["props"] else ""))
    if job["template"] == "action":
        mv, ld = b["move"], b["land"]
        rocks = [b[n]["word"] for n in ("move", "move2", "move3") if b.get(n)]
        tip = f", tips on '{b['tip']['word']}'" if b.get("tip") else ""
        return (f"action: {s} rocks on {', '.join(repr(r) for r in rocks)} from {mv['t_shot']:.2f} s{tip}, drops "
                f"{job['options']['steps_down']} step, lands {ld['t_shot']:.2f} s ('{ld.get('word')}'); fireball, chime")
    return job["template"]


def load_sidecar(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return None


# ---------------------------------------------------------------- episode run
def shot_dirs(ep, job):
    base = os.path.join(ep.BUILD, "blender", job["clip"])
    rdir = os.path.join(base, job["cache_key"][:12])
    return base, rdir


def mode_of(args):
    if args.keyframe:
        return "keyframe"
    if args.still:
        return "still"
    if args.preview or args.quality == "preview":
        return "preview"
    if args.build or args.quality in ("draft", "final"):
        return "filed"
    return "plan"


def run_shot(ep, shot, args, bl, info, tl, tl_sha1):
    mode = mode_of(args)
    if mode == "keyframe":
        quality = "final"
    elif mode == "preview":
        quality = "preview"
    elif mode == "filed":
        quality = args.quality or os.environ.get("NM_RX_QUALITY") or "draft"
    elif mode == "still":
        quality = args.quality or "final"
    else:
        quality = args.quality or "preview"
    if mode == "filed" and quality not in ("draft", "final"):
        raise Fail(f"--build files a clip at draft or final, not {quality!r} (NM_RX_QUALITY)")
    filed = mode == "filed"
    engine, device, gpu_type, enotes = resolve_engine(args, info, quality)
    scale = args.scale or (100 if mode == "keyframe" else None)
    render = render_settings(quality, engine, device, gpu_type, args.samples, scale)
    job, notes = resolve_shot(ep, shot, args, tl, tl_sha1, quality, render, info["version"], filed=filed)
    for n in enotes + notes:
        log("  " + n)
    base, rdir = shot_dirs(ep, job)
    frames_dir = os.path.join(rdir, "frames")
    beats = {k: v["frame"] for k, v in job["beats"].items() if v}
    mv = beats.get("move")
    keys = [0, job["last_shown"]] + list(beats.values()) + ([min(mv + 15, job["last_shown"])] if mv is not None else [])
    for n, b in job["beats"].items():         # the first moving frame of each start beat, the flare's peak
        if b:
            keys.append(b["frame"] + (1 if b["kind"] == "start" else 2 if n == "flare" else 0))
    if mode == "keyframe":
        ks = [0]
    elif mode == "still":
        ks = parse_frames(args.still, job["frames"])
    elif filed:
        if args.frames and args.frames != "every:1":
            raise Fail("a filed clip needs every frame (--frames is for --preview and --still)")
        ks = list(range(job["frames"]))
    else:
        ks = parse_frames(args.frames or "every:6", job["frames"], keys)
    todo = [k for k in ks if not os.path.exists(os.path.join(frames_dir, f"{k:04d}.png"))]
    per, total = estimate(render, len(todo))
    clip_mp4 = os.path.join(ep.CLIPS_DIR, f"{job['clip']}.mp4")
    sidecar = os.path.join(ep.CLIPS_DIR, f"{job['clip']}.blender.json")
    current, why = (False, "")
    sc_old = load_sidecar(sidecar)
    if filed and not args.force:
        current, why = up_to_date(sc_old, clip_mp4, job["content_key"], quality)
    log(f"{shot['id']} {job['clip']}: {job['template']} v{job['template_version']}, subject "
        f"{job['subject']['name']} ({job['subject']['kind'].upper()})"
        + (f", props {', '.join(p['name'] + ' (' + p['kind'].upper() + ')' for p in job['props'])}" if job['props'] else ""))
    for name, b in job["beats"].items():
        if b:
            log(f"  {name}: {('%r' % b['word']) if b['word'] else '-'} -> {b['t_shot']:.3f} s -> clip frame {b['frame']} "
                f"({b['kind']}; Blender frame {b['frame'] + 1}) [{b['source']}]")
    log(f"  {job['frames']} frames (shows 0-{job['last_shown']}), {quality} {render['scale']}% "
        f"({W * render['scale'] // 100}x{H * render['scale'] // 100}), {engine} {device}"
        f"{' ' + gpu_type if gpu_type else ''} {render['samples']} spp, haze {render['haze']}, seed {job['seed']}, "
        f"content {job['content_key'][:12]}, frames dir {job['cache_key'][:12]}" + (" (up to date)" if current else ""))
    log(f"  to render: {len(todo)} of {len(ks)} frame(s); estimate {per:.1f} s/frame, {total / 60:.1f} min")
    if args.dry_run or mode == "plan":
        log(json.dumps({k: job[k] for k in ("camera", "options", "subject", "props", "zones")}, indent=1, default=str))
        if mode == "plan" and not args.dry_run:
            log("  nothing rendered: pass --preview (look and timing), --build (file the clip at $NM_RX_QUALITY or draft),"
                " --quality draft|final, --still K or --keyframe")
        return None
    if current:
        log(f"{shot['id']} {job['clip']}: up to date ({why})")
        out = {"up_to_date": True, "job": job}
        mp = os.path.join(base, (sc_old.get("cache_key") or "")[:12], "motion.json")
        if os.path.exists(mp):        # cheap: re-run the screen checks on the cached motion, print any new WARN
            with open(mp, encoding="utf-8") as f:
                motion = json.load(f)
            checks, warns = screen_checks(job, motion, shot, ep)
            for w_ in warns:
                log("  " + w_)
            out["checks"], out["warnings"] = checks, warns
        return out
    if filed:
        ent = clip_entry(ep.CLIPS_DIR, job["clip"])
        if ent and not ent.get("sidecar") and not args.force:
            raise Fail(f"clips/{job['clip']}.mp4 was filed by clips.py add from {ent.get('generator') or 'a generator'} "
                       f"(clips.json), not rendered here: use a new key such as {job['clip']}_bl, or --force")
    if total > 30 * 60 and not args.yes:
        raise Fail(f"estimated {total / 60:.0f} min ({per:.0f} s/frame x {len(todo)}): pass --yes to go ahead, or use "
                   f"--preview / --quality draft / --engine eevee on a GPU", 3)
    os.makedirs(rdir, exist_ok=True)
    job.update({"frames_dir": frames_dir, "render_frames": ks, "motion_path": os.path.join(rdir, "motion.json"),
                "result_path": os.path.join(rdir, "result.json"),
                "save_blend": os.path.join(rdir, "scene.blend") if args.save_blend else None})
    job_path = os.path.join(rdir, "job.json")
    write_json(job_path, job, indent=1, sort_keys=True)
    wall = run_worker(bl, job_path, os.path.join(rdir, "worker.log"), timeout=max(120.0, 3 * total + 90))
    with open(job["result_path"], encoding="utf-8") as f:
        res = json.load(f)
    if not res["ok"]:
        raise Fail(f"{shot['id']}: " + "; ".join(res["errors"]))
    wb = res.get("blender") or {}
    if wb.get("version") and wb["version"] != info["version"]:
        forget_probe(bl)
        raise Fail(f"{bl[1]} now runs Blender {wb['version']} ({wb.get('hash')}), but the probe cache said "
                   f"{info['version']}: the cache is refreshed; run again", 2)
    with open(job["motion_path"], encoding="utf-8") as f:
        motion = json.load(f)
    checks, warns = screen_checks(job, motion, shot, ep, res.get("facts"))
    stats = {int(k): v for k, v in (res.get("frame_stats") or {}).items()}
    mid = min(ks, key=lambda k: abs(k - job["last_shown"] / 2))
    st = stats.get(mid, {})
    checks["mean_luma_mid"] = st.get("mean")
    checks["luma_mid"] = {k: st.get(k) for k in ("mean", "std", "subject_mean", "backdrop_mean")}
    if checks["mean_luma_mid"] is not None and checks["mean_luma_mid"] < 60:
        warns.append(f"WARN {shot['id']}: mean luma {checks['mean_luma_mid']} at frame {mid}: too dark for the style "
                     f"(target 100-120)")
    for w_ in warns:
        log("  " + w_)
    times = {int(k): v for k, v in res["render_s"].items()}
    if times:
        log(f"  rendered {len(times)} frame(s): {sum(times.values()) / len(times):.2f} s/frame "
            f"(min {min(times.values()):.2f}, max {max(times.values()):.2f}); worker {wall:.1f} s")
    log(f"  luma at frame {mid}: mean {st.get('mean')}, subject {st.get('subject_mean')}, backdrop {st.get('backdrop_mean')}")
    out = {"job": job, "checks": checks, "warnings": warns, "render_s": times, "worker_s": round(wall, 1),
           "frames": ks, "frames_dir": frames_dir, "facts": res.get("facts", {}), "frame_stats": stats,
           "device": res.get("device"), "blender": wb}
    header = (("PROXY: " + job["subject"]["name"] + " · ") if job["proxy"] else "") + \
        f"{ep.SLUG} {shot['id']} {job['clip']} · {quality} {render['scale']}% {render['engine']} {render['samples']}spp"
    if mode in ("still", "keyframe"):
        for k in ks:
            dst = os.path.join(base, f"still_{quality}_{render['scale']}_{k:04d}.png")
            shutil.copyfile(os.path.join(frames_dir, f"{k:04d}.png"), dst)
            log(f"  still: {dst}")
            out.setdefault("stills", []).append(dst)
        if mode == "keyframe":
            os.makedirs(ep.STILLS_DIR, exist_ok=True)
            dst = os.path.join(ep.STILLS_DIR, f"{job['clip']}_key.png")
            shutil.copyfile(os.path.join(frames_dir, "0000.png"), dst)
            log(f"  keyframe: {dst}")
        return out
    if not filed:   # preview: held-frame MP4 with true timing, the key sheet and the contact sheet
        names = []
        for i in range(job["last_shown"] + 1):
            k = max(x for x in ks if x <= i)
            names.append(f"{k:04d}.png")
        audio = os.path.join(ep.BUILD, "soundtrack.wav")
        ts = timeline_shot(tl, shot["id"]) if tl else None
        mux = (not args.no_mux) and os.path.exists(audio) and ts is not None
        pv = os.path.join(base, "preview.mp4")
        encode(frames_dir, names, pv + ".tmp", audio if mux else None, ts["start"] if mux else 0,
               shot["dur"] if mux else None)
        os.replace(pv + ".tmp", pv)
        log(f"  preview: {pv}" + ("" if mux else " (no build/soundtrack.wav: silent)"))
        out["preview_mp4"] = pv
        try:
            items = [(0, "frame 0 (cut-back match)")]
            labels = {"move": "first move", "move2": "rock 2", "move3": "rock 3", "tip": "tip", "land": "land",
                      "flare": "flare"}
            for n in ("move", "move2", "tip", "land", "flare"):
                b = job["beats"].get(n)
                if b:
                    k = b["frame"] + (1 if b["kind"] == "start" else 2 if n == "flare" else 0)
                    k = min(max(k, 0), job["last_shown"])
                    if k in ks:
                        items.append((k, f"{labels[n]} '{b['word'] or ''}'"))
            if mv is not None and min(mv + 15, job["last_shown"]) in ks:
                items.append((min(mv + 15, job["last_shown"]), "move +0.5 s"))
            items.append((job["last_shown"], "last frame (the cut)"))
            seen, items_u = set(), []
            for k, c in sorted(items):
                if k not in seen:
                    seen.add(k)
                    items_u.append((k, c))
            key_sheet(frames_dir, items_u, job, os.path.join(base, "sheet.png"), header)
            contact_sheet(frames_dir, ks, job, os.path.join(base, "contact.png"),
                          header + f" · every rendered frame ({len(ks)})", beats)
            out["sheet"] = os.path.join(base, "sheet.png")
            out["contact"] = os.path.join(base, "contact.png")
            log(f"  sheets: {out['sheet']}, {out['contact']}")
        except ImportError:
            log("  (no PIL here: no sheet.png / contact.png)")
        return out
    # filed clip: exactly like any other clip, through clips.py add() (the mezzanine, its checks, the clips.json
    # entry). The frames go in as a lossless intermediate, so the only lossy encode is add()'s own. add() swaps the
    # MP4 in only once it checks out; the sidecar follows it (atomically), so an interrupted run leaves either the
    # old pair or a new MP4 whose sha1 no longer matches the old sidecar, which the next --build re-renders.
    git = git_info()
    clips = cliptools()
    inter = os.path.join(rdir, "frames.mkv")
    lossless(frames_dir, job["frames"], inter)

    def asset(m):
        d = asset_identity(m)
        d["ai_generated"] = m.get("ai_generated", False)
        if m["kind"] == "glb":
            d["file"] = m["file"]
        return d
    w_, h_ = W * render["scale"] // 100, H * render["scale"] // 100
    generator = f"Blender {wb.get('version')}, blender_reenact {job['template']} v{job['template_version']}"
    entry_extra = {
        "source": os.path.relpath(frames_dir, ep.DIR) + f" ({job['frames']} PNG frames, lossless intermediate)",
        "references": [m.get("file", f"proxy:{m['name']}") for m in [job["subject"]] + job["props"]],
        "quality": quality, "proxy": job["proxy"], "render": f"{render['engine']} {render['device']}"
        + (f" {render['gpu_type']}" if render.get("gpu_type") else "") + f", {render['samples']} spp",
        "sidecar": os.path.basename(sidecar)}
    try:
        clips.add(ep.DIR, job["clip"], inter, generator, prompt=describe(job), force=True, extra=entry_extra,
                  ai_generated=job["ai_generated"], described=True,
                  low_res_fix="a draft; render the deliverable with --quality final (1080x1920)")
    except SystemExit as e:        # clips.py stops with sys.exit("message")
        raise Fail(f"{shot['id']}: clips.py add refused the render: {e}")
    finally:
        if os.path.exists(inter):
            os.remove(inter)
    mp4_sha1 = file_sha1(clip_mp4)
    side = {"generator": "blender", "blender_version": wb.get("version"), "blender_hash": wb.get("hash"),
            "device_used": res.get("device"), "script_sha1": script_sha1(), "picture_sha1": picture_sha1(),
            "ffmpeg": ffmpeg_version(), "encoder": ENCODER_VERSION, "git": git, "episode": job["episode"],
            "shot": job["shot"], "dur": job["dur"], "in": job["in"], "template": job["template"],
            "template_version": job["template_version"], "seed": job["seed"], "subject": asset(job["subject"]),
            "props": [asset(p) for p in job["props"]], "engine": render["engine"], "device": render["device"],
            "quality": quality, "samples": render["samples"], "render": render, "w": w_, "h": h_, "fps": FPS,
            "frames": job["frames"],
            "timing": {"source": job["timing"]["source"], "timeline_sha1": job["timing"]["timeline_sha1"],
                       "synthetic": job["timing"]["synthetic"], "shot_start": job["timing"]["shot_start"],
                       **{k: v for k, v in job["beats"].items()}, "last_frame": job["last_shown"]},
            "camera": job["camera"], "camera_solved": res.get("facts", {}).get("camera_solved"),
            "options": job["options"], "zones": job["zones"], "checks": checks, "ai_generated": job["ai_generated"],
            "proxy": job["proxy"], "content_key": job["content_key"], "render_key": job["render_key"],
            "cache_key": job["cache_key"], "mp4_sha1": mp4_sha1}
    write_json(sidecar, side, indent=1, sort_keys=True, default=str)
    log(f"  filed: {clip_mp4} (clips.py add: + its clips.json entry; provenance in {os.path.basename(sidecar)})"
        + ("; PROXY: a placeholder, deliver.py refuses it" if job["proxy"] else ""))
    out.update(mp4=clip_mp4, sidecar=sidecar)
    return out


def episode_main(args):
    ep = load_episode(args.episode)
    shots = [s for s in ep.SHOTS if s.get("blender")]
    if args.has_shots:
        print("yes" if shots else "no")
        return 0
    if args.shot:
        sel = [s for s in shots if s["id"] == args.shot]
        if not sel:
            raise Fail(f"no Blender shot {args.shot!r} in {ep.SLUG}; shots with a blender dict: "
                       f"{', '.join(s['id'] for s in shots) or 'none'}")
        shots = sel
    if not shots:
        log(f"{ep.SLUG}: no shot has a blender dict")
        return 0
    errs = []
    for s in shots:
        e, _ = validate_shot(ep, s)
        errs += e
    if errs:
        raise Fail("\n".join(errs))
    bl = find_blender(args.blender)
    if bl is None:
        raise Fail(INSTALL_HINT, 2)
    info = probe_blender(bl, reprobe=args.reprobe)
    check_version(info)
    tl, tl_sha1 = load_timeline(ep)
    if tl is None:
        log(f"note: no {os.path.join(ep.BUILD, 'timeline.json')}: beats come from move_at/land_at")
    results = {}
    for s in shots:
        results[s["id"]] = run_shot(ep, s, args, bl, info, tl, tl_sha1)
    if args.json_out:
        write_json(args.json_out, results, indent=1, default=str)
    return 0


# ---------------------------------------------------------------- showcase and models
def showcase_job(model, mode, render, require=False, out_dir=None, frames=None, models=None, models_dir=None):
    notes = []
    m = resolve_model(model, require, notes, models=models, models_dir=models_dir)
    n = {"sheet": 4, "turntable": 120, "pushin": 60}[mode]
    tpl = T.TEMPLATES["showcase"]
    job = {"template": "showcase", "template_version": tpl["version"], "episode": None, "shot": None,
           "clip": f"showcase_{model}_{mode}", "fps": FPS, "in": 0.0, "dur": n / FPS, "frames": n, "last_shown": n - 1,
           "seed": zlib.crc32(model.encode()) % 100000, "options": {**tpl["options"], "mode": mode},
           "camera": dict(T.CAMERAS["sheet"]), "subject": m, "props": [], "beats": {}, "render": render, "zones": {}}
    job["cache_key"] = cache_key_of(job, "n/a")
    out_dir = out_dir or os.path.join(SHOW, "build", "models", f"{model}_{mode}_{job['cache_key'][:8]}")
    job.update({"frames_dir": os.path.join(out_dir, "frames"), "render_frames": frames if frames is not None else list(range(n)),
                "motion_path": os.path.join(out_dir, "motion.json"), "result_path": os.path.join(out_dir, "result.json")})
    return job, notes, out_dir


def sheet_png(frames_dir, model, out):
    """front, three-quarter, side, back, and the library still (the library wins on identity)."""
    from PIL import Image
    cells = [Image.open(os.path.join(frames_dir, f"{k:04d}.png")).convert("RGB") for k in range(4)]
    still = next((p for p in (os.path.join(SHOW, "stills", f"{model}.{e}") for e in ("webp", "png", "jpg"))
                  if os.path.exists(p)), None)
    if still:
        im = Image.open(still).convert("RGB")
        cells.append(im.resize((int(im.width * cells[0].height / im.height), cells[0].height)))
    w = sum(c.width for c in cells) + 10 * (len(cells) + 1)
    sheet = Image.new("RGB", (w, cells[0].height + 20), (40, 40, 40))
    x = 10
    for c in cells:
        sheet.paste(c, (x, 10))
        x += c.width + 10
    sheet.save(out)
    return bool(still)


def showcase_main(args):
    bl = find_blender(args.blender)
    if bl is None:
        raise Fail(INSTALL_HINT, 2)
    info = probe_blender(bl, reprobe=args.reprobe)
    engine, device, gpu, _ = resolve_engine(args, info, "preview")
    render = render_settings("preview" if args.preview else "draft", engine, device, gpu, args.samples, args.scale)
    job, notes, out_dir = showcase_job(args.showcase, args.mode, render, args.require_models, out_dir=args.out_dir)
    for n in notes:
        log("  " + n)
    os.makedirs(out_dir, exist_ok=True)
    jp = os.path.join(out_dir, "job.json")
    write_json(jp, job, indent=1)
    run_worker(bl, jp, os.path.join(out_dir, "worker.log"), timeout=900)
    with open(job["result_path"], encoding="utf-8") as f:
        res = json.load(f)
    log(f"showcase {args.showcase} {args.mode}: height {res['facts'].get('height_m')} m -> {out_dir}")
    if args.mode == "sheet":
        try:
            p = os.path.join(out_dir, f"{args.showcase}_sheet.png")
            has = sheet_png(job["frames_dir"], args.showcase, p)
            log(f"  sheet: {p} (front, three-quarter, side, back{', library still' if has else ''})")
        except ImportError:
            pass
    return 0


def model_main(argv):
    ap = argparse.ArgumentParser(prog="blender_reenact.py model")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("name")
    a.add_argument("file")
    a.add_argument("--source", required=True)
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument("--ai", action="store_true")
    g.add_argument("--no-ai", action="store_true")
    a.add_argument("--height-m", type=float)
    a.add_argument("--forward", default="+z", choices=("+z", "-z", "+x", "-x"))
    a.add_argument("--yaw", type=float, default=0.0)
    a.add_argument("--no-restyle", action="store_true")
    a.add_argument("--credit")
    a.add_argument("--blender")
    a.add_argument("--out-dir", help="where the check's sheet frames go (default build/models/<name>_sheet_<key>)")
    sub.add_parser("list")
    args = ap.parse_args(argv)
    models = load_models()
    if args.cmd == "list":
        for k, e in sorted(models.items()):
            log(f"{k:20s} {e['file']:24s} {e.get('height_m')} m  {e.get('tris', '?')} tris  "
                f"{'AI' if e.get('ai_generated') else 'hand'}  {e.get('source', '')}")
        if not models:
            log("no models filed: every subject renders as a PROXY")
        return 0
    base = args.name.split("_")[0]
    if base not in CAST or (args.name != base and not (base == "lorraine" and args.name[9:] in OUTFITS)):
        raise Fail(f"{args.name}: model names come from the cast list ({', '.join(CAST)}, lorraine_<outfit>)")
    if not args.file.lower().endswith(".glb") or not os.path.exists(args.file):
        raise Fail(f"{args.file}: a .glb file is required")
    height = args.height_m or HEIGHTS.get(base)
    if not height:
        raise Fail(f"{args.name}: the bible has no height for it: pass --height-m (metres)")
    os.makedirs(MODELS_DIR, exist_ok=True)
    # Check first, file after: the GLB goes into a temporary models folder, is imported and normalized by a worker
    # from there, and only on success replaces models/<name>.glb and its models.json entry. A failed re-add over a
    # good model leaves the good one filed.
    tmp_dir = tempfile.mkdtemp(prefix=".model_add_", dir=MODELS_DIR)
    try:
        tmp_glb = os.path.join(tmp_dir, f"{args.name}.glb")
        shutil.copyfile(args.file, tmp_glb)
        entry = {"file": os.path.basename(tmp_glb), "sha1": file_sha1(tmp_glb), "source": args.source,
                 "ai_generated": bool(args.ai), "credit": args.credit, "height_m": height, "forward": args.forward,
                 "yaw_offset_deg": args.yaw, "restyle": not args.no_restyle, "anchors": {},
                 "added": datetime.date.today().isoformat()}
        bl = find_blender(args.blender)
        if bl is None:
            log("WARN filed without an import check (no Blender here): " + INSTALL_HINT)
            sub_info = {}
        else:
            info = probe_blender(bl)
            engine, device, gpu, _ = resolve_engine(argparse.Namespace(engine="auto", device="auto"), info, "preview")
            check_q = os.environ.get("NM_RX_CHECK_QUALITY", "preview")      # the selftest checks at "selftest"
            render = render_settings(check_q, engine, device, gpu)
            job, _, out_dir = showcase_job(args.name, "sheet", render, out_dir=args.out_dir,
                                           models={args.name: entry}, models_dir=tmp_dir)
            if not args.out_dir:
                out_dir = os.path.join(SHOW, "build", "models", f"{args.name}_sheet_{entry['sha1'][:8]}")
                job.update({"frames_dir": os.path.join(out_dir, "frames"),
                            "motion_path": os.path.join(out_dir, "motion.json"),
                            "result_path": os.path.join(out_dir, "result.json")})
            os.makedirs(out_dir, exist_ok=True)
            jp = os.path.join(out_dir, "job.json")
            write_json(jp, job, indent=1)
            try:
                run_worker(bl, jp, os.path.join(out_dir, "worker.log"), quiet=True, timeout=900)
            except Fail as e:
                raise Fail(f"{args.name}: import check failed, nothing filed: {e}")
            with open(job["result_path"], encoding="utf-8") as f:
                res = json.load(f)
            with open(job["motion_path"], encoding="utf-8") as f:
                sub_info = json.load(f)["subjects"].get(args.name, {})
            sub_info["facts"] = res.get("facts", {})
            sub_info["out_dir"] = out_dir
            entry["tris"] = sub_info.get("tris")
        dst = os.path.join(MODELS_DIR, f"{args.name}.glb")
        entry["file"] = os.path.basename(dst)
        os.replace(tmp_glb, dst)
        models = load_models()
        models[args.name] = entry
        write_json(os.path.join(MODELS_DIR, "models.json"), dict(sorted(models.items())), indent=1)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    if sub_info:
        f = sub_info.get("facts", {})
        log(f"{args.name}: filed {dst}; normalized height {f.get('height_m')} m, footprint {f.get('foot')}, "
            f"{sub_info.get('tris')} tris" + (f", stripped {sub_info.get('stripped')}" if sub_info.get("stripped") else "")
            + f"; sheet frames in {sub_info['out_dir']} (check identity against the library still; never use its back "
              f"view)")
    else:
        log(f"{args.name}: filed {dst} (unchecked)")
    return 0


# ---------------------------------------------------------------- selftest
def selftest(args):
    from rx3d import selftest as st
    return st.run(sys.modules[__name__], args)


# ---------------------------------------------------------------- CLI
def parse(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("episode", nargs="?")
    ap.add_argument("--shot")
    ap.add_argument("--preview", action="store_true", help="look and timing; never files")
    ap.add_argument("--build", action="store_true",
                    help="file the clip at --quality or $NM_RX_QUALITY (default draft), or report it up to date")
    ap.add_argument("--quality", choices=("preview", "draft", "final"))
    ap.add_argument("--frames")
    ap.add_argument("--still", help="render these clip frames (K or K,K) to look at; default quality final; never filed")
    ap.add_argument("--scale", type=int, help="percent of 1080x1920 (overrides the quality's); sizes must be even")
    ap.add_argument("--engine", default="auto", choices=("auto", "eevee", "cycles"))
    ap.add_argument("--device", default="auto", choices=("auto", "cpu", "gpu"))
    ap.add_argument("--samples", type=int)
    ap.add_argument("--keyframe", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", "--rerender", action="store_true", dest="force")
    ap.add_argument("--require-models", action="store_true")
    ap.add_argument("--save-blend", action="store_true")
    ap.add_argument("--no-mux", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--has-shots", action="store_true")
    ap.add_argument("--showcase")
    ap.add_argument("--mode", default="sheet", choices=("sheet", "turntable", "pushin"))
    ap.add_argument("--out-dir")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--allow-skip", action="store_true", help="selftest: pass even when the rendering half can't run")
    ap.add_argument("--blender")
    ap.add_argument("--reprobe", action="store_true", help="probe Blender again (version, GPU devices, Eevee)")
    ap.add_argument("--json-out", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.scale is not None:
        check_scale(args.scale)
    if args.build and args.preview:
        raise Fail("--build files a clip, --preview never does: pick one")
    return args


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--" in argv:                       # blender -b -P blender_reenact.py -- <args>
        argv = argv[argv.index("--") + 1:]
    if argv and argv[0].startswith("--worker"):
        from rx3d import worker
        return worker.main(argv)
    try:
        if argv and argv[0] == "model":
            return model_main(argv[1:])
        args = parse(argv)
        if args.selftest:
            return selftest(args)
        if args.showcase:
            return showcase_main(args)
        if not args.episode:
            raise Fail("usage: blender_reenact.py <episode_dir> [flags] (see --help)")
        return episode_main(args)
    except Fail as e:
        print(f"ERROR {e}" if e.code != 2 else str(e), file=sys.stderr, flush=True)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
