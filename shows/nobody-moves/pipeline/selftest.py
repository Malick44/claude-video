"""Offline self-test for stock sources, against a local mock of Freesound, ElevenLabs and Pexels.

  .venv/bin/python pipeline/selftest.py

Builds a throwaway episode that uses every source type (local file, URL, Freesound id and
search, ElevenLabs sound effects and voice, your own recording, a Pexels still) and checks
fetching, lock-file pinning, rebuilds without network, and credits. Also checks audio tags
("[deadpan]"): they reach an Eleven v4 voice as written, Kokoro never gets them, captions never show
them, a sound tag ("[yawns]") keeps its own time in the word timing, and build_audio.check_lines()
stops a bad line before anything is voiced. Then the reenactment shot kind, on a second throwaway
episode (ep98_rx) with generated test clips: filing clips (clips.py add), the timeline, every build
error and warning, frame mapping and the cover crop, the REENACTMENT · AI tag, the hard cut in picture,
captions and sound, the end card's AI disclosure, review.py, SCRIPT.md and the contact sheet; and
cast.py's NM_VOICES switch. Then the voice provenance in timeline.json on a third (ep97_voices): built on
v4 and rendered without NM_VOICES, a locked recordings/<rec>.v4.wav take, NM_VOICES=kokoro skipping it, and
a human take. Then a Blender reenactment on a fourth (ep96_blender): the "blender" fields checked by
build_audio.py, a rendered clip filed through clips.add() and recorded as clip_blender, review.py and
deliver.py on a proxy draft; and blender_reenact.py --selftest --allow-skip, whose rendering half runs only
where Blender is found ($NM_BLENDER, .venv-bpy/, bpy in this Python, blender on PATH) and prints SKIP
otherwise. Touches nothing in the real stock/ folder or episodes/.

  .venv/bin/python pipeline/selftest.py --full    # also renders ep98_rx to MP4 and runs review.py on it
"""
import contextlib
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import types
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SHOW = os.path.dirname(HERE)
PY = sys.executable
HITS = []
SAID = []   # (voice id, request body) for every ElevenLabs text-to-speech call


def tone_samples(freq, seconds, sr=24000):
    t = np.arange(int(seconds * sr)) / sr
    return (0.5 * np.sin(2 * np.pi * freq * t) * np.minimum(1, t / 0.01) * np.exp(-t)).astype(np.float32)


def tone(freq, seconds, sr=24000, then=None):
    """A WAV file of a decaying tone, optionally followed by more samples (`then`)."""
    y = tone_samples(freq, seconds, sr)
    if then is not None:
        y = np.concatenate([y, then.astype(np.float32)])
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((y * 32767).astype("<i2").tobytes())
    return buf.getvalue()


def jpeg():
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (900, 1600), (40, 60, 80)).save(buf, "JPEG")
    return buf.getvalue()


class Mock(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, ctype, code=200):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _sound(self, sid):
        base = f"http://127.0.0.1:{self.server.server_port}"
        return {"id": sid, "name": f"Test sound {sid}", "username": "mock_user",
                "license": "http://creativecommons.org/publicdomain/zero/1.0/",
                "url": f"https://freesound.org/s/{sid}/", "duration": 3.0,
                "previews": {"preview-hq-mp3": f"{base}/files/fs{sid}.mp3"}}

    def do_GET(self):
        HITS.append(("GET", self.path))
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path.startswith("/fs/sounds/"):
            if q.get("token") != ["fs-key"]:
                return self._send({"detail": "bad token"}, "application/json", 401)
            return self._send(self._sound(int(u.path.split("/")[3])), "application/json")
        if u.path == "/fs/search/text/":
            assert "Creative Commons 0" in q["filter"][0] and "duration:[0 TO 30]" in q["filter"][0], q
            return self._send({"results": [self._sound(4242)]}, "application/json")
        if u.path == "/px/search":
            if self.headers.get("Authorization") != "px-key":
                return self._send({"error": "unauthorized"}, "application/json", 401)
            base = f"http://127.0.0.1:{self.server.server_port}"
            return self._send({"photos": [{"alt": "A street", "photographer": "Mock Photographer",
                                           "url": "https://www.pexels.com/photo/1/",
                                           "src": {"large2x": f"{base}/files/photo.jpeg", "original": ""}}]},
                              "application/json")
        if u.path.startswith("/files/") or u.path.startswith("/cdn/"):
            if u.path.endswith(".jpeg"):
                return self._send(jpeg(), "image/jpeg")
            return self._send(tone(880, 2.0), "audio/mpeg")
        self._send(b"not found", "text/plain", 404)

    def do_POST(self):
        HITS.append(("POST", self.path))
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.headers.get("xi-api-key") != "el-key":
            return self._send({"detail": "bad key"}, "application/json", 401)
        if self.path == "/el/sound-generation":
            return self._send(tone(330, body.get("duration_seconds", 2.0)), "audio/mpeg")
        if self.path.startswith("/el/text-to-speech/"):
            voice = urlparse(self.path).path.rsplit("/", 1)[-1]
            if voice not in ("voice123", "voice456"):
                return self._send({"detail": "voice not found"}, "application/json", 404)
            SAID.append((voice, body))
            if voice == "voice123":
                assert body["model_id"] == "eleven_multilingual_v2" and body["seed"] == 7, body
            yawn = None   # a trailing [yawns] comes back as a sound after the words: 0.15 s gap, 0.6 s noise
            if body["text"].rstrip().endswith("[yawns]"):
                yawn = np.concatenate([np.zeros(3600), 0.05 * np.random.default_rng(1).standard_normal(14400)])
            return self._send(tone(220, 0.5 + 0.04 * len(body["text"]), then=yawn), "audio/mpeg")
        self._send(b"not found", "text/plain", 404)


EPISODE = '''
TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 99: SELF TEST"
NEXT_UP = "NEXT: NOTHING"
L = lambda who, text, say=None: ("line", who, text, say or text)
V = lambda img, a, b, look=None: {{"img": img, "kb": (a, b), "look": look}}
CAST = {{"NARRATOR": {{"provider": "elevenlabs", "voice_id": "voice123", "model": "eleven_multilingual_v2", "seed": 7}},
        "DEB": {{"provider": "elevenlabs", "voice_id": "voice456", "model": "eleven_v4"}}}}
SOUNDS = {{
    "sting": {{"file": "local_sting.wav", "credit": "Test sting, recorded by me"}},
    "shutter": {{"freesound": 1234}},
    "crickets": {{"freesound_search": "crickets night", "max_seconds": 30}},
    "theme": {{"elevenlabs_sfx": "ominous solo piano", "seconds": 8}},
    "ding": {{"url": "{base}/cdn/bell.wav", "credit": {{"author": "Bell Maker", "license": "CC0"}}}},
}}
SHOTS = [
    {{"id": "title", "kind": "title", "views": [V("garrison", (0.5, 0.5, 1.0), (0.5, 0.5, 1.1))], "items": [], "min": 2.0, "sfx": ["sting"]}},
    {{"id": "hook", "kind": "evidence", "label": "EXHIBIT A", "stamp": "now",
      "views": [V("garrison", (0.5, 0.5, 1.2), (0.5, 0.5, 1.3))], "sfx": ["shutter", "crickets"],
      "items": [L("NARRATOR", "This is a test."), L("GARRISON", "I didn't see nothing.", "[sighs] I didn't see nothing."),
                L("DEB", "I was asleep at 3:12.", "[deadpan] I was asleep at three twelve. [yawns]")]}},
    {{"id": "q1", "kind": "qcard", "text": "Test?", "items": [], "min": 1.5}},
    {{"id": "end", "kind": "end", "items": [], "min": 2.0, "sfx": ["sting_end"]}},
]
'''


def run(args, env, expect_ok=True):
    r = subprocess.run([PY, *args], cwd=SHOW, env=env, capture_output=True, text=True)
    if expect_ok and r.returncode:
        raise AssertionError(f"{args} failed:\n{r.stdout}\n{r.stderr}")
    if not expect_ok and not r.returncode:
        raise AssertionError(f"{args} should have failed")
    return r


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print("ok  ", msg)


def load_checks():
    """An episode.py rewritten to text of the same length with the same mtime (two edits in one second) must
    load its new text. importlib's bytecode cache matches on mtime and size alone, so it would run the old one.
    The .pyc is written explicitly with py_compile (not left to PYTHONDONTWRITEBYTECODE), and a control loads
    the same v2 text through importlib, which must still get v1: if it does not, this check no longer
    reproduces the bug and fails."""
    import importlib.util
    import py_compile
    import common
    v1, v2 = 'CLIP = "rx_rot_raw"\nSHOTS = []\n', 'CLIP = "rx_sar_raw"\nSHOTS = []\n'
    check(len(v1) == len(v2), "the stale-bytecode check rewrites the episode to text of the same length")
    folder = tempfile.mkdtemp(prefix="nm-selftest-load-")
    try:
        path = os.path.join(folder, "episode.py")
        with open(path, "w") as f:
            f.write(v1)
        stat = os.stat(path)
        py_compile.compile(path, cfile=importlib.util.cache_from_source(path), doraise=True)
        with open(path, "w") as f:
            f.write(v2)
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        spec = importlib.util.spec_from_file_location("episode", path)
        control = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(control)
        if control.CLIP != "rx_rot_raw":
            raise AssertionError(f"load_checks no longer reproduces the stale-bytecode bug: importlib loaded "
                                 f"{control.CLIP!r} from the v2 text, not the cached v1 value 'rx_rot_raw'")
        print("ok   control: importlib runs the stale cached v1 compile of the rewritten v2 text (the bug)")
        check(common.load_episode(folder).CLIP == "rx_sar_raw",
              "an episode.py rewritten within the same second to the same length loads its new text, not a cached compile")
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def placeholder_gate_checks():
    """--require-models (make_episode.sh's NM_FINAL=1 build) refuses a cast model that is not filed, and passes
    once it is. Pure Python: blender_reenact's remote guard is in main(), so nothing renders or probes here."""
    import blender_reenact as bl
    folder = tempfile.mkdtemp(prefix="nm-selftest-models-")
    old_dir = bl.MODELS_DIR
    try:
        bl.MODELS_DIR = folder
        try:
            bl.resolve_model("garrison", True, [])
            refused = None
        except bl.Fail as e:
            refused = str(e)
        check(refused is not None and "--require-models" in refused,
              "resolve_model(require=True) raises Fail for a cast model with no models/<name>.glb")
        path = os.path.join(folder, "garrison.glb")
        with open(path, "wb") as f:
            f.write(b"glTF")
        with open(os.path.join(folder, "models.json"), "w") as f:
            json.dump({"garrison": {"file": "garrison.glb", "sha1": bl.file_sha1(path)}}, f)
        got = bl.resolve_model("garrison", True, [])
        check(got["kind"] == "glb" and got["name"] == "garrison",
              "resolve_model(require=True) passes once models/garrison.glb is filed")
    finally:
        bl.MODELS_DIR = old_dir
        shutil.rmtree(folder, ignore_errors=True)
    lines = open(os.path.join(SHOW, "make_episode.sh")).read().splitlines()
    start = next(i for i, line in enumerate(lines) if "--has-shots" in line and line.lstrip().startswith("if "))
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == "fi")
    branch = lines[start:end]
    check(any('"$FINAL" = 1' in line and "--require-models" in line for line in branch)
          and not any("--require-models" in line for line in lines[:start] + lines[end:]),
          "make_episode.sh passes --require-models only in the blender branch, under NM_FINAL=1")


def triangle_checks():
    """blender_reenact.check_triangles: a model at the 100,000-triangle limit passes, one more triangle fails."""
    import blender_reenact as bl
    bl.check_triangles(100000, "x")
    try:
        bl.check_triangles(100001, "x")
        raised = False
    except bl.Fail:
        raised = True
    check(raised, "check_triangles(100001) raises Fail, and check_triangles(100000) passes")


def tag_checks():
    """words.strip_tags, the text Kokoro and the caption timing get: tags out, everything else kept."""
    from words import strip_tags, tag_kind
    cases = [
        ("[deadpan] I didn't see nothing.", "I didn't see nothing."),
        ("At 3:12 AM, [beat] someone moved Deb.", "At 3:12 AM, someone moved Deb."),
        ("My client (allegedly) was right here [sighs].", "My client (allegedly) was right here."),
        ("[whispering][said angrily in French accent] Nothing. [light rain]", "Nothing."),
        ("He said ([laughs] obviously) no.", "He said (obviously) no."),
        ("No tags: (asides), 3:12, 1994, $5 & \"quotes\"?!", "No tags: (asides), 3:12, 1994, $5 & \"quotes\"?!"),
        ("Odd  spacing stays when there's no tag ", "Odd  spacing stays when there's no tag "),
        ("[3:12] and [ x ] aren't tags", "[3:12] and [ x ] aren't tags"),
        ('"[whispers] Hello there," she said.', '"Hello there," she said.'),
        ("Wait [beat]— no.", "Wait— no."),
        ("Hello[laughs]world, hello [laughs]world.", "Hello world, hello world."),
    ]
    bad = [(say, strip_tags(say)) for say, want in cases if strip_tags(say) != want]
    check(not bad, f"strip_tags drops audio tags and keeps punctuation, quotes, dashes, 3:12 and (parentheses) {bad or ''}".rstrip())
    kinds = {"[deadpan]": "direction", "[too quickly]": "direction", "[with contempt]": "direction",
             "[said angrily in French accent]": "direction", "[beat]": "pause", "[sighs]": "sound",
             "[clears throat]": "sound", "[light rain]": "sound", "[phone buzzing]": "sound"}
    bad = {t: tag_kind(t) for t, want in kinds.items() if tag_kind(t) != want}
    check(not bad, f"tag_kind: directions take no time, [beat] is a pause, [sighs] and [light rain] are sounds {bad or ''}".rstrip())


def check_lines_checks(tmp):
    """build_audio.check_lines() on one-shot episodes: what stops the build, what only warns, what passes."""
    import build_audio as ba
    os.makedirs(os.path.join(tmp, "recordings"))
    with open(os.path.join(tmp, "recordings", "s_2.wav"), "wb") as f:     # line 2 of shot "s" is recorded
        f.write(tone(180, 0.5))
    L = lambda who, text, say=None: ("line", who, text, say or text)
    cast = {"NARRATOR": {"voice": "bm_george", "speed": 1.0},
            "DEB": {"provider": "elevenlabs", "voice_id": "voice456", "model": "eleven_v4"},
            "OLD": {"provider": "elevenlabs", "voice_id": "voice123"}}

    def lines(*items):
        """(exit message or "", stderr) of check_lines() on shot "s" holding `items`."""
        ba.ep = types.SimpleNamespace(SHOTS=[{"id": "s", "items": list(items)}], CAST=cast, DIR=tmp)
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                ba.check_lines()
        except SystemExit as e:
            return str(e), err.getvalue()
        return "", err.getvalue()

    check(lines(L("NARRATOR", "His statement: [REDACTED].", "His statement: redacted."),
                L("DEB", "He said [inaudible].", "He said something inaudible."),
                L("NARRATOR", "Exhibit [A]", "Exhibit A")) == ("", ""),
          "brackets shown only in a caption, with separate spoken text, pass ([REDACTED], [inaudible], [A])")
    stop, _ = lines(L("DEB", "[deadpan] Fine."))
    check("shot s, line 1 (DEB)" in stop and "L('DEB', 'Fine.', '[deadpan] Fine.')" in stop
          and "L('DEB', '[deadpan] Fine.', 'deadpan Fine.')" in stop,
          "a tag in a caption with no spoken text stops, naming the line and showing both fixes")
    stop, _ = lines(L("DEB", "[sighs] Fine.", "[sighs] Fine, fine."))
    check("L('DEB', 'Fine.', '[sighs] Fine, fine.')" in stop, "a tag in both the caption and the spoken text stops")
    stop, _ = lines(L("NARRATOR", "Timestamp [03:12:07]. Nothing moves."))
    check("third argument without brackets" in stop and "'Timestamp 03:12:07. Nothing moves.'" in stop,
          "a caption's bracket that would reach the voice stops, asking for spoken text without brackets")
    stop, _ = lines(L("DEB", "Fine.", "[sighs Fine."))
    check("square bracket" in stop, "an unclosed tag in the spoken text stops")
    stop, _ = lines(L("NARRATOR", "", "[sighs]"))
    check("only audio tags" in stop, "a Kokoro line that is only tags stops before voicing")
    stop, _ = lines(L("NOBODY", "Hi."))
    check("not in the cast" in stop, "a speaker missing from the cast stops before voicing")
    cast["PH"] = {"provider": "elevenlabs", "voice_id": "<fill after design>", "model": "eleven_v4"}
    stop, _ = lines(L("PH", "Hi."))
    check("placeholder" in stop and "NM_VOICES" in stop, "an ElevenLabs voice whose voice_id is still a placeholder stops")
    stop, err = lines(L("NARRATOR", "Hi.", "[whispering] Hi."), L("DEB", "x"), L("NARRATOR", "Bye.", "[quietly] Bye."))
    check(not stop and err.count("Kokoro voice, which leaves audio tags") == 1, "tags on a Kokoro voice warn, once per character")
    stop, err = lines(L("OLD", "Hi.", "[sighs] Hi."))
    check(not stop and "may read audio tags out loud" in err, "tags on an ElevenLabs model that may not take them warn")
    check(lines(L("DEB", "x"), L("NARRATOR", "Timestamp [03:12:07].")) == ("", "")
          and lines(L("DEB", "x"), L("OLD", "[sighs] Hi.")) == ("", ""),
          "a recorded line skips the checks: nothing of it is sent to a voice")


def voice_line_checks(tmp):
    """build_audio.voice_line() with Kokoro and ElevenLabs stubbed out: what each provider is sent, and
    which edits voice a line again."""
    import build_audio as ba
    ba.CACHE = os.path.join(tmp, "voice")
    os.makedirs(ba.CACHE)
    cast = {"GARRISON": {"voice": "am_fenrir", "speed": 1.0},
            "DEB": {"provider": "elevenlabs", "voice_id": "voice456", "model": "eleven_v4"}}
    ba.ep = types.SimpleNamespace(SHOTS=[], CAST=cast, DIR=tmp)
    kokoro_said, eleven_said = [], []

    class Kokoro:
        def create(self, text, voice, speed, lang):
            kokoro_said.append(text)
            return tone_samples(200, 0.6), 24000

    ba._kokoro = Kokoro()
    real_tts = ba.stock.elevenlabs_tts
    ba.stock.elevenlabs_tts = lambda text, cast: (eleven_said.append(text), tone(220, 0.6))[1]
    files = lambda: sorted(os.listdir(ba.CACHE))
    try:
        ba.voice_line("GARRISON", "[deadpan] Fine. [sighs]", "s_9")
        tagged = files()
        ba.voice_line("GARRISON", "Fine.", "s_9")
        check(kokoro_said == ["Fine."] and files() == tagged,
              f"Kokoro gets the line without its tags, cached as the untagged line ({kokoro_said})")
        ba.voice_line("DEB", "[deadpan] Fine.", "s_9")
        ba.voice_line("DEB", "Fine.", "s_9")
        check(eleven_said == ["[deadpan] Fine.", "Fine."] and len(files()) == len(tagged) + 4,
              "ElevenLabs gets the tags, and a tag-only edit voices the line again")
        before = files()
        cast["DEB"] = dict(cast["DEB"], lang="en-gb")
        ba.voice_line("DEB", "Fine.", "s_9")
        check(files() == before, '"lang" (word timing only) changes no cache key')
        cast["DEB"] = dict(cast["DEB"], altered=True)
        ba.voice_line("DEB", "Fine.", "s_9")
        check(len(eleven_said) == 2 and len(files()) > len(before),
              "an FX change (altered, pitch) re-processes the cached clip without calling ElevenLabs")
    finally:
        ba.stock.elevenlabs_tts = real_tts


# ---------------------------------------------------------------- reenactments

BLOCKS = [(200, 30, 30), (30, 160, 40), (30, 50, 200), (210, 120, 20), (150, 30, 160), (20, 150, 150),
          (230, 230, 230), (100, 60, 20)]     # rx_test: one colour per 0.25 s block
STILL_RGB = (40, 60, 80)                      # jpeg(): the episode's own "garrison" still
YELLOW = (242, 194, 48)

EP98 = '''
TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 98: REENACTED"
NEXT_UP = "NEXT: NOTHING"
CORNER_LABEL = "NOBODY MOVES"
L = lambda who, text, say=None: ("line", who, text, say or text)
P = lambda s: ("pause", s)
V = lambda img, a, b, look=None: {{"img": img, "kb": (a, b), "look": look}}
CAST = {{"NARRATOR": {{"provider": "elevenlabs", "voice_id": "voice123", "model": "eleven_multilingual_v2", "seed": 7}},
        "DEB": {{"provider": "elevenlabs", "voice_id": "voice456", "model": "eleven_v4"}}}}
MOTION = {motion!r}
CLIPS = {{"rx_test": "Locked-off camera; the camera never moves. The colour blocks change. No people, no text. " + MOTION,
         "rx_slow": "Locked-off camera; the camera never moves. A grey card slides left. " + MOTION,
         "rx_nope": "Locked-off camera; the camera never moves. Nothing is filed for this one. " + MOTION}}
CLIP_SOURCES = {{"rx_test": {{"keyframe": "rx_test_key", "keyframe_refs": ["garrison"], "negative": "person, people, text"}}}}
HUMAN_TAKES = {{"rx_1": "test"}}
G = V("garrison", (0.5, 0.5, 1.0), (0.5, 0.5, 1.0))
SHOTS = [
    {{"id": "cold", "kind": "doorbell", "frame_a": "garrison", "frame_b": "garrison", "clock_start": "03:11:59",
      "jump_after": 1, "flicker": False, "kb": ((0.5, 0.5, 1.0), (0.5, 0.5, 1.0)),
      "items": [L("NARRATOR", "Three twelve.")], "post": 2.5}},
    {{"id": "hook", "kind": "still", "views": [G], "items": [L("NARRATOR", "Who moved?")], "post": 0.5}},
    {{"id": "rx", "kind": "reenactment", "clip": "rx_test", "speed": 0.5, "label": "REENACTMENT · AI",
      "stamp": "THEORY #2: THE GOOSE (DIRECTOR'S CUT)", "fallback": [G], "pre": 0.3,
      "items": [L("NARRATOR", "The goose did it.")]}},
    {{"id": "deny", "kind": "still", "music": "out", "pre": 0.5, "views": [G], "items": [L("DEB", "I was right here.")],
      "post": 0.4}},
    {{"id": "react", "kind": "still", "views": [G], "items": [], "min": 1.6,
      "lower_third": ("MR. BASIN", "Birdbath", "Facing: up."), "lower_third_at": "cut"}},
    {{"id": "rx_fit", "kind": "reenactment", "clip": "rx_test", "speed": "fit", "fallback": [G], "pre": 0.3,
      "items": [L("NARRATOR", "Or the gnome did.")]}},
    {{"id": "rx_missing", "kind": "reenactment", "clip": "rx_nope", "fallback": [V("garrison", (0.5, 0.5, 1.2), (0.5, 0.5, 1.3))],
      "dur": 3.0, "pre": 0.3, "items": [L("NARRATOR", "Or nobody.")]}},
    {{"id": "deny2", "kind": "still", "music": "out", "pre": 0.5, "views": [G], "items": [L("DEB", "Nobody moves.")],
      "post": 0.3}},
    {{"id": "end", "kind": "end", "items": [], "min": 2.6, "sfx": ["sting_end"]}},
]
'''


def video(path, frames, fps, audio=False):
    """Encode RGB frames (n, h, w, 3) uint8 to an H.264 MP4 (with a test tone when audio=True)."""
    import imageio_ffmpeg
    n, h, w, _ = frames.shape
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{w}x{h}", "-r", str(fps), "-i", "-"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={n / fps}", "-c:a", "aac", "-shortest"]
    subprocess.run(cmd + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "12", path],
                   input=frames.tobytes(), check=True)


def blocks_clip(path, w=1280, h=720, fps=24, seconds=2.0):
    n = int(seconds * fps)
    frames = np.zeros((n, h, w, 3), np.uint8)
    for i in range(n):
        frames[i] = BLOCKS[min(7, int(i / fps / 0.25))]
    video(path, frames, fps, audio=True)


def odd_clips(folder):
    """{"rot": a 320x180 clip with a 90° display rotation (shown 180x320), "sar": 320x180 with 2:1 pixels
    (shown 640x180)}, each 1.5 s at 30 fps; a key is left out when this ffmpeg can't write it."""
    import imageio_ffmpeg
    ff = lambda *a: subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", *a],   # noqa: E731
                                   capture_output=True).returncode == 0
    src = ["-f", "lavfi", "-i", "testsrc=size=320x180:rate=30:duration=1.5"]
    enc = ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    out = {}
    land = os.path.join(folder, "land.mp4")
    if ff(*src, *enc, land) and ff("-display_rotation", "90", "-i", land, "-c", "copy", os.path.join(folder, "rot.mp4")):
        out["rot"] = os.path.join(folder, "rot.mp4")
    if ff(*src, "-vf", "setsar=2/1", *enc, os.path.join(folder, "sar.mp4")):
        out["sar"] = os.path.join(folder, "sar.mp4")
    return out


def patch(frame, x0, y0, x1, y1):
    return np.asarray(frame, dtype=np.float32)[y0:y1, x0:x1].reshape(-1, 3).mean(axis=0)


def near(got, want, tol=12):
    return bool(np.all(np.abs(np.asarray(got) - np.asarray(want)) <= tol))


def text_mask(txt, bare, t):
    """Pixels where text is drawn at time t: a render with text against one without (as safezones does)."""
    fi = int(round(t * 30))
    a = np.asarray(txt.render(t, fi), dtype=np.int16)
    b = np.asarray(bare.render(t, fi), dtype=np.int16)
    return np.abs(a - b).max(axis=2) > 24


def recorder(mod):
    """Make the renderer record every text() call it draws: [(text, fill)]."""
    from PIL import ImageDraw
    calls = []

    class Rec(ImageDraw.ImageDraw):
        def text(self, xy, text, *a, **k):
            calls.append((text, k.get("fill")))
            return super().text(xy, text, *a, **k)

    mod.ImageDraw = types.SimpleNamespace(Draw=lambda im, mode=None: Rec(im, mode))
    return calls


def end_card_checks(ep99):
    """The end card's disclosure on an episode without a reenactment: it names the voices only when the
    soundtrack holds an ElevenLabs voice, as timeline.json records it, whatever the cast says now."""
    import safezones
    mod = safezones.load_renderer(ep99, "_rx_end99")
    calls = recorder(mod)
    end = next(s for s in mod.SHOTS if s["kind"] == "end")
    mod.render(end["start"] + 2.0, 0)
    check(("Reenactments and voices made with AI.", (150, 150, 150, 255)) in calls,
          "ep99 (ElevenLabs voices, no reenactment): the end card reads \"Reenactments and voices made with AI.\"")
    bare = safezones.load_renderer(ep99, "_rx_end99_bare", text=False)
    band = lambda t: text_mask(mod, bare, t)[1310:1395].any()   # noqa: E731
    check(not band(end["start"] + 1.3) and band(end["start"] + 2.0), "... at the card's usual timing (nothing before 1.4 s)")
    kokoro = {"voice": "bm_george", "speed": 1.0}
    mod.ep.CAST = {"NARRATOR": kokoro, "DEB": kokoro, "GARRISON": kokoro}
    mod.AI_VOICES = mod.ai_voices()
    del calls[:]
    mod.render(end["start"] + 2.0, 0)
    check(("Reenactments and voices made with AI.", (150, 150, 150, 255)) in calls,
          "... and still with every character on Kokoro in the cast now: the card follows the timeline, not the cast")
    mod.ep.CAST["UNUSED"] = {"provider": "elevenlabs", "voice_id": "voice123"}
    for c in mod.CAPTIONS:                   # a timeline built on Kokoro: no line carries an ElevenLabs voice
        for k in ("provider", "voice_id", "model"):
            c.pop(k, None)
    mod.AI_VOICES = mod.ai_voices()
    del calls[:]
    mod.render(end["start"] + 2.0, 0)
    check(("Reenactments dramatized with AI.", (150, 150, 150, 255)) in calls,
          "a soundtrack built on Kokoro, an unused ElevenLabs entry left in CAST: the card is unchanged")


def reenactment_checks(tmp, env, render_mp4=False):
    """The reenactment shot kind: filing clips, the timeline, build errors, frames, the label, the hard
    cut in picture and sound, the end card, review, SCRIPT.md and the contact sheet."""
    import clips as cliptools
    import review
    import safezones
    from common import rx_tag_width
    ep = os.path.join(tmp, "ep98_rx")
    os.makedirs(os.path.join(ep, "stills"))
    with open(os.path.join(ep, "stills", "garrison.jpg"), "wb") as f:
        f.write(jpeg())
    with open(os.path.join(ep, "episode.py"), "w") as f:
        f.write(EP98.format(motion=cliptools.suffixes().get("motion", "")))
    src = open(os.path.join(ep, "episode.py")).read()
    fx = os.path.join(tmp, "fixtures")
    os.makedirs(fx)
    blocks_clip(os.path.join(fx, "rx_src.mp4"))
    blocks_clip(os.path.join(fx, "short.mp4"), 320, 180, 24, 0.2)
    blocks_clip(os.path.join(fx, "slow.mp4"), 320, 180, 24, 1.2)
    with open(os.path.join(fx, "notes.mp4"), "w") as f:
        f.write("not a video")
    rotated = odd_clips(fx)     # {"rot": a 320x180 clip shown turned 90°, "sar": 320x180 with 2:1 pixels}

    # 1. intake
    run(["pipeline/clips.py", "add", ep, "rx_test", os.path.join(fx, "rx_src.mp4"), "--generator", "selftest"], env)
    mez = os.path.join(ep, "clips", "rx_test.mp4")
    from common import clip_info
    info = clip_info(mez)
    check(info and abs(info["fps"] - 30) < 0.01 and not info["audio"] and (info["w"], info["h"]) == (1280, 720)
          and abs(info["seconds"] - 2.0) < 0.05,
          f"clips.py add files a 30 fps mezzanine with no audio, same size and length ({info})")
    entry = json.load(open(os.path.join(ep, "clips", "clips.json")))["rx_test"]
    check(entry["sha1"] and entry["prompt"].startswith("Locked-off camera") and entry["negative"] == "person, people, text"
          and entry["ai_generated"] is True and entry["keyframe"] == "rx_test_key",
          "clips.json records the sha1, the prompt from CLIPS, the negative and keyframe from CLIP_SOURCES, ai_generated")
    r = run(["pipeline/clips.py", "add", ep, "rx_test", os.path.join(fx, "rx_src.mp4"), "--generator", "x"], env, expect_ok=False)
    check("--force" in r.stderr, "a second add without --force refuses")
    r = run(["pipeline/clips.py", "add", ep, "rx_short", os.path.join(fx, "short.mp4"), "--generator", "x", "--prompt", "A box."],
            env, expect_ok=False)
    check("must be 1-10 s" in r.stderr, "a 0.2 s clip is rejected")
    r = run(["pipeline/clips.py", "add", ep, "rx_text", os.path.join(fx, "notes.mp4"), "--generator", "x", "--prompt", "A box."],
            env, expect_ok=False)
    check("no video stream" in r.stderr, "a file with no video is rejected")
    r = run(["pipeline/clips.py", "add", ep, "rx_man", os.path.join(fx, "slow.mp4"), "--generator", "x",
             "--prompt", "A man pushes Deb across the lawn."], env, expect_ok=False)
    check("names a person (man)" in r.stderr, "the lint refuses a motion prompt with a person in it")
    check(not cliptools.lint_prompt("Locked-off camera. The goose slides. No people, no text.", "motion")[0],
          "\"No people, no text.\" passes the lint (negated clauses are stripped first)")
    run(["pipeline/clips.py", "add", ep, "rx_slow", os.path.join(fx, "slow.mp4"), "--generator", "x", "--retime", "0.5"], env)
    slow = clip_info(os.path.join(ep, "clips", "rx_slow.mp4"))
    check(abs(slow["seconds"] - 2.4) < 0.1 and abs(slow["fps"] - 30) < 0.01, f"--retime 0.5 doubles the length ({slow['seconds']} s)")
    for key, want, what in (("rot", (180, 320), "a clip with a 90° display rotation is filed upright"),
                            ("sar", (640, 180), "a clip with 2:1 pixels is filed at its display width, square pixels")):
        if key not in rotated:
            print(f"skip  {what} (this ffmpeg can't write the test clip)")
            continue
        src_info = clip_info(rotated[key])
        run(["pipeline/clips.py", "add", ep, f"rx_{key}", rotated[key], "--generator", "x", "--prompt", "A box."], env)
        got = clip_info(os.path.join(ep, "clips", f"rx_{key}.mp4"))
        check((got["w"], got["h"]) == want and got["sar"] == (1, 1) and not got["rotation"]
              and (key != "rot" or (src_info["w"], src_info["h"], src_info["rotation"]) == (180, 320, 90.0))
              and (key != "sar" or src_info["sar"] == (2, 1)),
              f"{what} ({src_info['w']}x{src_info['h']} rotation {src_info['rotation']:g} SAR {src_info['sar']} -> "
              f"{got['w']}x{got['h']} SAR {got['sar']})")

    # 2. the timeline
    r = run(["pipeline/build_audio.py", ep, "--stems"], env)
    tl = json.load(open(os.path.join(ep, "build", "timeline.json")))
    S = {s["id"]: s for s in tl["shots"]}
    length = lambda sid: S[sid]["end"] - S[sid]["start"]   # noqa: E731
    check(abs(length("rx") - 4.0) <= 1 / 30 + 1e-3 and '"speed" 0.5' in r.stderr,
          f"rx lasts 4.0 s (2.0 s of clip at 0.5x, longer than its line) and warns about the speed ({length('rx'):.3f} s)")
    check(abs(S["rx_fit"]["clip_speed"] - 2.0 / length("rx_fit")) < 1e-3,
          f"speed \"fit\" plays the clip in the shot's length ({S['rx_fit']['clip_speed']:.3f}x over {length('rx_fit'):.2f} s)")
    check(abs(length("rx_missing") - 3.0) < 1e-6 and S["rx_missing"]["clip_missing"] is True
          and S["rx_missing"]["clip_fallback"] == "garrison" and "rx_nope is missing" in r.stderr,
          "a missing clip: exactly its dur, clip_missing, its fallback still, and a warning")
    line = next(x for x in r.stderr.splitlines() if "rx_nope is missing" in x)
    check(f"clips.py add {os.path.relpath(ep, SHOW)} rx_nope <file>" in line and f"add {ep} " not in line,
          "the missing-clip warning names the episode by its path from the show folder, as the README's command does")
    check(S["rx"]["clip_sha1"] == entry["sha1"][:12] and S["rx"]["label"] == "REENACTMENT · AI" and S["rx"]["cue"] is True,
          "the timeline records the clip's sha1 and the resolved label and cue")
    check("flicker_at" not in S["cold"], "a doorbell with \"flicker\": False gets no flicker")
    import build_audio as ba
    cold, door = {"kind": "doorbell", "flicker": False, "start": 0.0}, {"kind": "doorbell", "start": 30.0}
    check(ba.climax_at(tl["shots"], 99.0) == 99.0 and review.pacing(tl)["score_builds_to"] == "end card"
          and ba.climax_at([cold, door], 99.0) == 30.0
          and ba.climax_at([cold, door, {"kind": "still", "start": 5.0, "climax": True}], 99.0) == 5.0,
          "the score never builds to a \"flicker\": False cold open: to the last flickering doorbell, a marked "
          "climax, else the end card (build_audio and review agree)")

    # 3. build errors and warnings, each appended to episode.py
    for line, expect, what in [
        ('SHOTS[2]["label"] = ""', "label must read exactly", "an empty label"),
        ('SHOTS[2]["label"] = "REENACTMENT"', "label must read exactly", "a label without · AI"),
        ('SHOTS[2]["label"] = "REENACTMENT (DIRECTOR\'S CUT) · AI"', "label must read exactly", "an escalation in the label"),
        ('SHOTS[2]["stamp"] = "THEORY #2: THE GOOSE (DIRECTOR\'S CUT, EXTENDED EDITION)"', "past x 930", "a tag ending past x 930"),
        ('SHOTS[6]["dur"] = 0.8', "longer than \"dur\"", "lines longer than dur"),
        ('del SHOTS[3:]', "can't be the last shot", "a reenactment as the last shot"),
        ('SHOTS[2]["music"] = "out"', "\"music\": \"out\" isn't allowed", "music out on a reenactment"),
        ('SHOTS[2]["kind"] = "reenactmnet"', "did you mean 'reenactment'", "a misspelled kind"),
        ('SHOTS[-1]["min"] = 2.0', "disclosure", "an end card too short for the AI disclosure"),
        ('SHOTS[4]["lower_third_at"] = "last"', "needs a line", "lower_third_at \"last\" on a shot with no lines"),
        ('SHOTS[3]["id"] = "rx"', "shot ids must be unique", "two shots with the same id (clips are keyed by it)"),
        ('SHOTS[5]["items"] = []; SHOTS[5]["pre"] = 0.0', "no length to stretch it over",
         "speed \"fit\" on a shot with nothing to give it a length (was a ZeroDivisionError once its clip existed)"),
    ]:
        with open(os.path.join(ep, "episode.py"), "w") as f:
            f.write(src + "\n" + line + "\n")
        r = run(["pipeline/build_audio.py", ep], env, expect_ok=False)
        check(expect in r.stderr, f"build error: {what} ({line})")
    for line, expect, what in [
        ('del SHOTS[4]["lower_third_at"]', "fully legible for 0.70 s", "a 1.6 s silent shot's name card with the default timing"),
        ('SHOTS[4]["lower_third"] = ("MR. BASIN", "Birdbath", "Declined to comment, on the advice of counsel")',
         "on a silent shot the name card is the joke", "a silent card's 45-character note"),
        ('SHOTS[1]["post"] = 0.15', "under reenact_hit's 0.35 s suck-in", "a line ending 0.15 s before a reenactment"),
    ]:
        with open(os.path.join(ep, "episode.py"), "w") as f:
            f.write(src + "\n" + line + "\n")
        r = run(["pipeline/build_audio.py", ep], env)
        check(expect in r.stderr, f"warning: {what}")
    for key, expect in (("rot", "rotation"), ("sar", "non-square pixels")):
        if key not in rotated:
            continue
        shutil.copy(rotated[key], os.path.join(ep, "clips", f"rx_{key}_raw.mp4"))   # copied by hand, not filed
        with open(os.path.join(ep, "episode.py"), "w") as f:
            f.write(src + f'\nSHOTS[2]["clip"] = "rx_{key}_raw"\n')
        r = run(["pipeline/build_audio.py", ep], env, expect_ok=False)
        check(expect in r.stderr and "clips.py add" in r.stderr, f"build error: a hand-copied clip with {expect}")
        os.remove(os.path.join(ep, "clips", f"rx_{key}_raw.mp4"))
    with open(os.path.join(ep, "episode.py"), "w") as f:
        f.write(src + '\nSHOTS[-1]["items"] = [P(3.0)]\ndel SHOTS[-1]["min"]\n')
    r = run(["pipeline/build_audio.py", ep], env)
    check("disclosure" not in r.stderr, "an end card of P(3.0) and no min builds: its pauses count toward the disclosure")
    with open(os.path.join(ep, "episode.py"), "w") as f:
        f.write(src)
    run(["pipeline/build_audio.py", ep, "--stems"], env)
    tl = json.load(open(os.path.join(ep, "build", "timeline.json")))
    S = {s["id"]: s for s in tl["shots"]}

    # 4. frame mapping and the cover crop
    txt = safezones.load_renderer(ep, "_rx_text")
    bare = safezones.load_renderer(ep, "_rx_bare", text=False)
    from PIL import Image
    want = [patch(txt.grade(txt.bloom(Image.new("RGB", (1080, 1920), c)), 0, grain=0.0, vignette=False,
                             extra=txt.rx_grade), 500, 680, 580, 760) for c in BLOCKS]
    t = S["rx"]["start"] + 1.375
    fr = txt.render(t, int(t * 30))
    centre, edge = patch(fr, 500, 680, 580, 760), patch(fr, 0, 600, 20, 860)
    nearest = int(np.argmin([np.abs(centre - w).sum() for w in want]))
    check(nearest == 2 and near(centre, want[2]) and near(edge, want[2]),
          f"rx at 1.375 s plays source 0.6875 s (block 2), cover-cropped with no bars ({centre.round()}, edge {edge.round()})")

    # 5. the label, the name card on the cut, no corner badge on a reenactment
    w = rx_tag_width("REENACTMENT · AI", "THEORY #2: THE GOOSE (DIRECTOR'S CUT)")
    for sid in ("rx", "rx_missing"):
        t = (S[sid]["start"] + S[sid]["end"]) / 2
        m = text_mask(txt, bare, t)
        tag = m[190:330, 64:64 + w]
        check(tag.sum() > 500 and (sid != "rx" or m[280:330, 584:64 + w].any()),
              f"{sid}: the tag and stamp are drawn at (64, 190), sized to the text ({w} px; the stamp passes x 584)")
    r0, r1 = S["react"]["start"], S["react"]["end"] - 1 / 30
    a, b = text_mask(txt, bare, r0)[1262:1492], text_mask(txt, bare, r1)[1262:1492]
    check(a.sum() > 500 and (a & b).sum() / max(1, (a | b).sum()) > 0.95,
          "lower_third_at \"cut\": the name card is fully on from the first frame to the last, no fade")
    yellow = lambda fr: int(np.all(np.abs(np.asarray(fr, np.int16)[190:430, 64:700] - YELLOW) <= 20, axis=2).sum())  # noqa: E731
    tr = (S["rx"]["start"] + S["rx"]["end"]) / 2
    check(yellow(txt.render(tr, int(tr * 30))) == 0 and yellow(txt.render(S["end"]["start"] + 1.0, 0)) == 0
          and yellow(txt.render(S["hook"]["start"] + 0.5, 0)) > 1000,
          "no corner badge on a reenactment, nor on an end card that repeats the title; a still shot keeps it")

    # 6. the hard cut, in picture and captions
    end = S["rx"]["end"]
    a = txt.render(end - 1 / 30, int(end * 30) - 1)
    b = txt.render(end, int(end * 30))
    check(near(patch(a, 500, 680, 580, 760), want[7]) and near(patch(b, 500, 680, 580, 760), STILL_RGB),
          "the last frame before the cut is the clip, the next is the still: a hard cut")
    for sid in ("rx", "rx_fit"):
        t = S[sid]["end"] + 0.03
        check(not text_mask(txt, bare, t)[1040:1262].any(), f"no caption from {sid} bleeds across its cut")

    # 7. sequential decoding equals random access
    seq = safezones.load_renderer(ep, "_rx_seq")
    f0 = int(math.ceil(S["rx"]["start"] * 30))
    keep = {f0 + 40: None, f0 + 20: None, f0 + 5: None}
    for fi in range(f0, f0 + 45):
        im = seq.render(fi / 30, fi)
        if fi in keep:
            keep[fi] = np.asarray(im)
    check(all(np.array_equal(seq.render(fi / 30, fi), keep[fi]) for fi in sorted(keep, reverse=True)),
          "frames decoded in order match the same frames decoded again, out of order")
    for mod in (txt, bare, seq):
        mod.close_clips()

    # 9. audio
    import soundfile as sf
    score, sr = sf.read(os.path.join(ep, "build", "stems", "score.wav"), always_2d=True)
    effects, _ = sf.read(os.path.join(ep, "build", "stems", "effects.wav"), always_2d=True)
    dbfs = lambda x: 10 * np.log10(np.mean(np.square(x)) + 1e-20)   # noqa: E731
    after = score[int((end + 0.03) * sr): int((end + 0.55) * sr)]
    loud = max(dbfs(after[i: i + sr // 20]) for i in range(0, len(after) - sr // 20, sr // 40))
    check(loud < -60, f"the score is silent after the hard cut (loudest 50 ms {loud:.1f} dBFS)")
    swell = dbfs(score[int((end - 0.2) * sr): int(end * sr)])
    check(swell > -30, f"the swell is up in the reenactment's last 0.2 s ({swell:.1f} dBFS)")
    cold = S["cold"]
    jump = cold["start"] + 1.0
    rest = dbfs(effects[int((jump + 0.7) * sr): int(cold["end"] * sr)])
    check(rest < -60, f"no flicker glitches, riser or reveal hit after a \"flicker\": False doorbell ({rest:.1f} dBFS)")
    r = run(["pipeline/mixcheck.py", ep, "--json"], env)
    rep = json.loads(r.stdout)
    names = {c["name"]: c["ok"] for c in rep["checks"] if c["hard"]}
    check(rep["ok"] and names.get("reenactment cut") and names.get("music-out silence"),
          f"mixcheck passes, with its reenactment-cut and music-out checks ({names})")
    buried = [f"{r['shot']} {r['db']} dB" for r in rep["dialogue"]["warnings"] if r["shot"] in ("rx", "rx_fit", "rx_missing")]
    check(not buried, f"the hit dies away before the narration: no reenactment line under 8 dB over the bed {buried or ''}".rstrip())

    # 10. the end card's disclosure with a reenactment
    calls = recorder(txt)
    txt.render(S["end"]["start"] + 0.7, 0)
    check(("Footage, reenactments and voices made with AI.", (150, 150, 150, 255)) in calls,
          "with a reenactment the end card reads \"Footage, reenactments and voices made with AI.\", fully on at 0.7 s")
    mask = text_mask(txt, bare, S["end"]["start"] + 0.7)[1310:1395]
    txt.ep.CAST = {"NARRATOR": {"voice": "bm_george", "speed": 1.0}, "DEB": {"voice": "bf_isabella", "speed": 1.0}}
    txt.AI_VOICES = txt.ai_voices()
    check(mask.any() and np.array_equal(mask, text_mask(txt, bare, S["end"]["start"] + 0.7)[1310:1395]),
          "... and the same line with NARRATOR and DEB on Kokoro: with a reenactment the cast doesn't change it")

    # 11. review and SCRIPT.md
    door2 = dict(cold, id="cliff", start=tl["total"], end=tl["total"] + 6, flicker=True, flicker_at=tl["total"] + 2)
    tl2 = dict(tl, shots=tl["shots"] + [door2])
    names = [b[0] for b in review.beats(tl2)]
    check("payoff" not in names and review.pacing(tl2)["payoff_at_s"] is None and "reenact" in names and "cut back" in names,
          f"review: no payoff beat for a cold open without a flicker; reenact and cut-back beats ({names})")
    check(review.pacing(tl)["reenactments"].startswith("3, ") and any("rx_nope missing" in w for w in review.rx_warnings(tl)),
          f"review: reenactments in the pacing ({review.pacing(tl)['reenactments']}) and the missing clip warned")
    run(["pipeline/script_md.py", ep], env)
    script = open(os.path.join(ep, "SCRIPT.md")).read()
    check("record as `rx_1` ★:" in script and "## Lines to record by a human\n\nThe fallback: a line goes to a human only"
          in script and "NOTES.md" not in script, "SCRIPT.md stars HUMAN_TAKES and lists them, with no NOTES.md line (none exists)")
    check("> REENACTMENT: clip `rx_test` · 4.00 s at 0.5x (source 0.00–2.00 s)" in script
          and "CLIP MISSING, fallback still `garrison`" in script and "- `rx_test` (rx): selftest. Prompt: Locked-off" in script,
          "SCRIPT.md shows each reenactment's clip and lists the clips' generator and prompt")

    # 12. the contact sheet: two cells per reenactment
    run(["pipeline/render.py", ep, "--contact"], env)
    sheet = np.asarray(Image.open(os.path.join(ep, "build", "contact.png")).convert("L"))
    cell = lambda i: sheet[(i // 7) * 480: (i // 7 + 1) * 480, (i % 7) * 270: (i % 7 + 1) * 270]   # noqa: E731
    n = len(tl["shots"]) + 3
    check(cell(n - 1).mean() > 3 and not cell(n).any(), f"render.py --contact draws {n} cells: one extra per reenactment")
    rgb = np.asarray(Image.open(os.path.join(ep, "build", "contact.png")).convert("RGB")).astype(int)[50:62, 2 * 270 + 20: 2 * 270 + 60]
    red = ((rgb[..., 0] > 150) & (rgb[..., 1] < 90) & (rgb[..., 2] < 90)).mean()
    check(red > 0.25, f"the contact sheet's RX/FALLBACK row sits under the cell, so the red tag stays visible ({red:.0%} red)")
    run(["pipeline/clips.py", "sheet", ep], env)
    clipsheet = np.asarray(Image.open(os.path.join(ep, "build", "review", "clips.png")).convert("L"))
    check(all(clipsheet[52:585, x: x + 300].mean() > 25 for x in (232, 544, 856)),
          "clips.py sheet shows the first, middle and last frame of each clip (the last one too)")

    if render_mp4:   # 13. the whole episode, rendered and reviewed
        run(["pipeline/render.py", ep], env)
        r = run(["pipeline/review.py", ep, "--file", "master", "--no-zones"], env)
        check(os.path.exists(os.path.join(ep, "build", "review", "reenact.png")) and "FAIL" not in r.stdout,
              "the full render passes review.py and writes reenact.png")

    # 8. a clip replaced after the build stops the render
    shutil.copy(os.path.join(ep, "clips", "rx_slow.mp4"), mez)
    r = run(["pipeline/render.py", ep, "--preview", f"{S['rx']['start'] + 1:.2f}"], env, expect_ok=False)
    check("rebuild the audio" in r.stderr + r.stdout, "a clip replaced after build_audio.py stops the render: rebuild the audio")


EP97 = '''
import os
TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 97: VOICES"
NEXT_UP = "NEXT: NOTHING"
L = lambda who, text, say=None: ("line", who, text, say or text)
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}
if os.environ.get("NM_VOICES") == "v4":   # like the remake's CAST: the v4 voice only when the build asks for it
    CAST = {"NARRATOR": {"provider": "elevenlabs", "voice_id": "voice456", "model": "eleven_v4"}}
SHOTS = [
    {"id": "hook", "kind": "still", "views": [V("garrison", (0.5, 0.5, 1.0), (0.5, 0.5, 1.1))],
     "items": [L("NARRATOR", "Nobody moves.")], "post": 0.5},
    {"id": "end", "kind": "end", "items": [], "min": 2.0},
]
'''


EP96 = '''
TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 96: RENDERED"
NEXT_UP = "NEXT: NOTHING"
L = lambda who, text, say=None: ("line", who, text, say or text)
V = lambda img, a, b, look=None: {"img": img, "kb": (a, b), "look": look}
CAST = {"NARRATOR": {"provider": "elevenlabs", "voice_id": "voice123", "model": "eleven_multilingual_v2", "seed": 7}}
G = V("garrison", (0.5, 0.5, 1.0), (0.5, 0.5, 1.0))
CLIPS = {"rx_ai": "Locked-off camera; the camera never moves. The gnome slides left. No people, no text."}
SHOTS = [
    {"id": "hook", "kind": "still", "views": [G], "items": [L("NARRATOR", "Who moved?")], "post": 0.5},
    {"id": "rx", "kind": "reenactment", "clip": "rx_gnome_bl", "in": 0.0, "speed": 1.0, "dur": 3.0,
     "label": "REENACTMENT · AI", "stamp": "THEORY #1: THE GNOME", "fallback": [G], "pre": 0.3,
     "blender": {"template": "heist", "subject": "garrison", "move_on": "move", "move_at": 1.5},
     "items": [L("NARRATOR", "Then he made his move.")]},
    {"id": "deny", "kind": "still", "music": "out", "pre": 0.5, "views": [G], "items": [L("NARRATOR", "Nobody moves.")]},
    {"id": "end", "kind": "end", "items": [], "min": 2.6},
]
'''


def blender_checks(tmp, env):
    """A Blender reenactment (pipeline/blender_reenact.py) from the pipeline's side, with no Blender needed:
    --has-shots, its fields checked by build_audio.py, a rendered clip filed through clips.add() and recorded in
    the timeline, review.py and deliver.py on a proxy draft. Then the tool's own selftest, rendering half
    included where Blender is found."""
    import clips as cliptools
    import review
    ep = os.path.join(tmp, "ep96_blender")
    os.makedirs(os.path.join(ep, "stills"))
    with open(os.path.join(ep, "stills", "garrison.jpg"), "wb") as f:
        f.write(jpeg())
    with open(os.path.join(ep, "episode.py"), "w") as f:
        f.write(EP96)
    r = run(["pipeline/blender_reenact.py", ep, "--has-shots"], env)
    r2 = run(["pipeline/blender_reenact.py", os.path.join(tmp, "ep99_selftest"), "--has-shots"], env)
    check(r.stdout.strip() == "yes" and r2.stdout.strip() == "no",
          "blender_reenact.py --has-shots prints yes for an episode with a blender dict, no otherwise (make_episode.sh)")
    for line, expect, what in [
        ('SHOTS[1]["blender"]["template"] = "caper"', "unknown template", "an unknown template"),
        ('SHOTS[1]["clip"] = "rx_ai"', "AI clip's key", "a Blender clip on an AI clip's key"),
        ('del SHOTS[1]["dur"]', "dur is required", "a Blender reenactment without dur"),
    ]:
        with open(os.path.join(ep, "episode.py"), "w") as f:
            f.write(EP96 + "\n" + line + "\n")
        r = run(["pipeline/build_audio.py", ep], env, expect_ok=False)
        check(expect in r.stderr, f"build error on a blender shot: {what} ({line})")
    with open(os.path.join(ep, "episode.py"), "w") as f:
        f.write(EP96)
    r = run(["pipeline/build_audio.py", ep], env)
    tl = json.load(open(os.path.join(ep, "build", "timeline.json")))
    rx = next(s for s in tl["shots"] if s["id"] == "rx")
    check(rx["clip_missing"] and rx["blender"]["template"] == "heist" and "clip_blender" not in rx
          and f"render it with pipeline/blender_reenact.py {os.path.relpath(ep, SHOW)} --build" in r.stderr,
          "a missing Blender clip plays its fallback, and the warning names blender_reenact.py --build")
    # what blender_reenact.py's --build does once the frames exist: clips.add() with the Blender provenance
    src = os.path.join(tmp, "bl_frames.mp4")
    blocks_clip(src, 108, 192, 30, 3.0)
    cliptools.add(ep, "rx_gnome_bl", src, "Blender 5.0.1, blender_reenact heist v2", prompt="heist: garrison glides left",
                  force=True, ai_generated=False, described=True, low_res_fix="a draft",
                  extra={"quality": "draft", "proxy": True, "sidecar": "rx_gnome_bl.blender.json"})
    entry = cliptools.clip_entry(os.path.join(ep, "clips"), "rx_gnome_bl")
    check(entry["sidecar"] == "rx_gnome_bl.blender.json" and entry["ai_generated"] is False and entry["proxy"] is True
          and entry["sha1"] and entry["generator"].startswith("Blender"),
          "clips.add() files a rendered clip with its provenance as extra clips.json fields")
    r = run(["pipeline/build_audio.py", ep], env)
    tl = json.load(open(os.path.join(ep, "build", "timeline.json")))
    rx = next(s for s in tl["shots"] if s["id"] == "rx")
    check(not rx["clip_missing"] and rx["clip_blender"] == {"quality": "draft", "proxy": True,
                                                            "sidecar": "rx_gnome_bl.blender.json"}
          and "deliver.py refuses it" in r.stderr,
          "the timeline records a filed Blender clip as clip_blender, and the build warns about a proxy draft")
    warns = review.rx_warnings(tl)
    check(any("PROXY" in w for w in warns) and any("draft render, not final" in w for w in warns),
          "review.py warns about a proxy model and a draft quality")
    r = run(["pipeline/deliver.py", ep], env, expect_ok=False)
    check("not delivered" in r.stderr and "a PROXY model, quality draft" in r.stderr,
          "deliver.py refuses a proxy draft (without --allow-draft)")
    r = run(["pipeline/blender_reenact.py", "--selftest", "--allow-skip"], env)
    last = r.stdout.strip().splitlines()[-1]
    check(last.startswith("selftest: ") and "FAILED" not in r.stdout,
          f"blender_reenact.py --selftest --allow-skip: {last.removeprefix('selftest: ')}")
    if "SKIPPED" in last:
        print("SKIP  the Blender rendering checks did not run here. They run on your own machine only (remote sessions "
              "never render Blender); locally, install Blender (./setup.sh --blender, or set NM_BLENDER to a blender "
              "binary or a python with bpy) and run pipeline/blender_reenact.py --selftest")


def voices_checks(tmp, env):
    """Voice provenance: build_audio.py records which captions an ElevenLabs voice made, and which are
    locked v4 takes (recordings/<rec>.v4.*), so the end card and SCRIPT.md follow the soundtrack, not the
    cast in force when they run; NM_VOICES=kokoro skips a locked v4 take; a take without .v4 is human."""
    import safezones
    ep = os.path.join(tmp, "ep97_voices")
    os.makedirs(os.path.join(ep, "stills"))
    with open(os.path.join(ep, "stills", "garrison.jpg"), "wb") as f:
        f.write(jpeg())
    with open(os.path.join(ep, "episode.py"), "w") as f:
        f.write(EP97)
    env = {k: v for k, v in env.items() if k != "NM_VOICES"}
    old = os.environ.pop("NM_VOICES", None)            # the in-process renders run with NM_VOICES unset
    calls = lambda: len([h for h in HITS if "/text-to-speech/" in h[1]])   # noqa: E731
    caption = lambda: json.load(open(os.path.join(ep, "build", "timeline.json")))["captions"][0]   # noqa: E731
    script = lambda: (run(["pipeline/script_md.py", ep], env), open(os.path.join(ep, "SCRIPT.md")).read())[1]   # noqa: E731
    built = [0]

    def card():
        built[0] += 1
        mod = safezones.load_renderer(ep, f"_v97_{built[0]}")
        drawn = recorder(mod)
        end = next(s for s in mod.SHOTS if s["kind"] == "end")
        mod.render(end["start"] + 2.0, 0)
        return next((x for x, _ in drawn if x.endswith(" with AI.")), None)

    try:
        n = calls()
        run(["pipeline/build_audio.py", ep], dict(env, NM_VOICES="v4"))
        cap = caption()
        check((cap.get("provider"), cap.get("voice_id"), cap.get("model")) == ("elevenlabs", "voice456", "eleven_v4")
              and calls() == n + 1, "built with NM_VOICES=v4: the caption records the ElevenLabs voice that made it")
        check(card() == "Reenactments and voices made with AI.",
              "... rendered with NM_VOICES unset (the cast is Kokoro now): the end card still names the voices")
        check("| NARRATOR | ElevenLabs voice456 on eleven_v4 |" in script(),
              "... and SCRIPT.md, written with NM_VOICES unset, names the voice the line was built with")
        voice = os.path.join(ep, "build", "voice")
        raw = max((os.path.join(voice, x) for x in os.listdir(voice) if x.startswith("NARRATOR_") and x.endswith("_raw.wav")),
                  key=os.path.getmtime)
        os.makedirs(os.path.join(ep, "recordings"))
        locked = os.path.join(ep, "recordings", "hook_1.v4.wav")
        shutil.copy(raw, locked)                        # the zero-code take lock
        n = calls()
        run(["pipeline/build_audio.py", ep], env)       # NM_VOICES unset: the NARRATOR is Kokoro in the cast
        cap = caption()
        check(cap["recorded"] and cap.get("generated") is True and "provider" not in cap and calls() == n,
              "a locked take (recordings/hook_1.v4.wav) replaces the API, marked \"generated\"")
        check(card() == "Reenactments and voices made with AI.", "... and the end card still names the voices")
        md = script()
        check("v4 take `hook_1`" in md and "0 of 1 lines are recorded. 1 more is a locked v4 take" in md
              and "| NARRATOR | ElevenLabs (1 locked v4 take) |" in md,
              "... and SCRIPT.md counts it as a locked v4 take, not a human recording")
        run(["pipeline/build_audio.py", ep], dict(env, NM_VOICES="kokoro"))
        cap = caption()
        check(not cap["recorded"] and "generated" not in cap and "provider" not in cap
              and card() == "Reenactments dramatized with AI.",
              "NM_VOICES=kokoro skips the locked v4 take: the Kokoro arm stays Kokoro, and so does its end card")
        os.rename(locked, os.path.join(ep, "recordings", "hook_1.wav"))
        run(["pipeline/build_audio.py", ep], env)
        cap = caption()
        check(cap["recorded"] and "generated" not in cap and card() == "Reenactments dramatized with AI.",
              "a take copied without .v4 counts as a human take: the end card drops \"voices\"")
    finally:
        if old is not None:
            os.environ["NM_VOICES"] = old


def preroll_checks():
    """build_audio.check_timeline()'s pre-roll warning on times rounded as timeline.json rounds them: a
    "post" of exactly HIT_PREROLL must not warn, though 9.35 - 9.0 is a hair under 0.35 in floats."""
    import build_audio as ba

    def warnings(gap):
        cut = round(9.0 + gap, 3)
        shots = [{"id": "q", "kind": "still", "start": 6.0, "end": cut, "lines": [{"start": 6.0, "end": 9.0}]},
                 {"id": "rx", "kind": "reenactment", "cue": True, "start": cut, "end": cut + 4.0,
                  "lines": [{"start": cut + 0.35, "end": cut + 3.0}]},
                 {"id": "end", "kind": "end", "start": cut + 4.0, "end": 40.0, "lines": []}]
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ba.check_timeline(shots, 40.0)
        return err.getvalue()
    check(9.35 - 9.0 < ba.HIT_PREROLL and "suck-in" not in warnings(0.35) and "suck-in" in warnings(0.34),
          "the hit's pre-roll warning: none on a \"post\" of exactly 0.35 s despite float rounding, one at 0.34 s")


def rx_share_checks():
    """build_audio.check_timeline()'s reenactment budget: a main episode's 20% share; a Confessional (its
    EPISODE starts "CONFESSIONAL", or it runs under 30 s) has at most one reenactment of 5 s or less, and its
    share, always over 20% in a 15-25 s short, isn't held against it."""
    import build_audio as ba

    def warnings(total, lens, episode="EPISODE 9: X"):
        ba.ep = types.SimpleNamespace(EPISODE=episode)
        shots, t = [], 0.0
        for i, d in enumerate(lens):
            shots += [{"id": f"s{i}", "kind": "still", "start": t, "end": t + 3.0, "lines": []},
                      {"id": f"rx{i}", "kind": "reenactment", "cue": False, "start": t + 3.0, "end": t + 3.0 + d, "lines": []}]
            t += 3.0 + d
        shots.append({"id": "end", "kind": "end", "start": t, "end": total, "lines": []})
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ba.check_timeline(shots, total)
        return err.getvalue()
    check(warnings(20.0, [4.5], "CONFESSIONAL: GARRISON") == "" and "at most one reenactment" in warnings(20.0, [5.5], "CONFESSIONAL: GARRISON")
          and "at most one reenactment" in warnings(22.0, [4.0, 4.0]),
          "a Confessional: one reenactment of 4.5 s (22% of 20 s) passes; one of 5.5 s, or two, warn")
    check(warnings(46.0, [4.5, 4.5]) == "" and "of the runtime" in warnings(46.0, [5.5, 5.5]),
          "a main episode: two reenactments at 19.6% pass, at 23.9% warn about the share")


def cast_checks():
    """cast.py: Kokoro by default, every character on Eleven v4 with NM_VOICES=v4, a clear stop on a typo."""
    from common import load_source

    def load(value):
        old = os.environ.pop("NM_VOICES", None)
        if value is not None:
            os.environ["NM_VOICES"] = value
        try:
            return load_source("_cast", os.path.join(SHOW, "cast.py"))
        finally:
            os.environ.pop("NM_VOICES", None)
            if old is not None:
                os.environ["NM_VOICES"] = old

    default, v4, kokoro = load(None), load("v4"), load("kokoro")
    check(default.CAST == {**default.CAST_KOKORO, **{k: default.CAST_V4[k] for k in default.FINAL_V4}}
          and all(c["model"] == "eleven_v4" and "seed" not in c and "voice_settings" not in c for c in v4.CAST.values())
          and kokoro.CAST == kokoro.CAST_KOKORO,
          "cast.py: the decided cast by default, every character on eleven_v4 (no seed or voice_settings) with NM_VOICES=v4")
    check(kokoro.CAST["CHIME"].get("fx_on_recordings") and v4.CAST["CHIME"].get("fx_on_recordings"),
          "the CHIME keeps its disguise on a human or locked take in both casts (fx_on_recordings)")
    try:
        load("eleven")
        check(False, "NM_VOICES=eleven should stop")
    except SystemExit as e:
        check("NM_VOICES" in str(e), "an unknown NM_VOICES value stops with a clear message")


def main():
    load_checks()
    tag_checks()
    cast_checks()
    preroll_checks()
    rx_share_checks()
    placeholder_gate_checks()
    triangle_checks()
    unit = tempfile.mkdtemp(prefix="nm-selftest-unit-")
    try:
        check_lines_checks(unit)
        voice_line_checks(unit)
    finally:
        shutil.rmtree(unit, ignore_errors=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Mock)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    tmp = tempfile.mkdtemp(prefix="nm-selftest-")
    try:
        ep = os.path.join(tmp, "ep99_selftest")
        os.makedirs(os.path.join(ep, "stills"))
        os.makedirs(os.path.join(ep, "recordings"))
        with open(os.path.join(ep, "stills", "garrison.jpg"), "wb") as f:   # its own still: works in any show
            f.write(jpeg())
        with open(os.path.join(ep, "episode.py"), "w") as f:
            f.write(EPISODE.format(base=base))
        with open(os.path.join(ep, "local_sting.wav"), "wb") as f:
            f.write(tone(110, 3.0))
        with open(os.path.join(ep, "recordings", "hook_2.wav"), "wb") as f:
            f.write(tone(180, 1.2))
        stock_dir = os.path.join(tmp, "stock")
        env = dict(os.environ, NOBODY_MOVES_STOCK_DIR=stock_dir, NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost",
                   FREESOUND_API_URL=f"{base}/fs", ELEVENLABS_API_URL=f"{base}/el", PEXELS_API_URL=f"{base}/px",
                   FREESOUND_API_KEY="fs-key", ELEVENLABS_API_KEY="el-key", PEXELS_API_KEY="px-key")

        run(["pipeline/build_audio.py", ep], env)
        lock = json.load(open(os.path.join(stock_dir, "sources.lock.json")))
        check(len(lock) == 4, f"4 network sounds fetched and pinned in the lock file ({len(lock)})")
        check(all(os.path.exists(os.path.join(SHOW, e["file"])) for e in lock.values()), "every pinned file exists")
        tl = json.load(open(os.path.join(ep, "build", "timeline.json")))
        creds = {c.get("title") or c.get("author") for c in tl["credits"]}
        check({"Test sting, recorded by me", "Test sound 1234", "Test sound 4242", "ominous solo piano"} <= creds,
              f"episode credits list the local, Freesound and ElevenLabs sounds ({sorted(creds)})")
        check([c["recorded"] for c in tl["captions"]] == [False, True, False], "hook_2 used the recording, hook_1 and hook_3 ElevenLabs voices")
        tts = [h for h in HITS if "/text-to-speech/" in h[1]]
        check(len(tts) == 2, "ElevenLabs TTS called twice (the recorded line skipped it)")
        deb = dict(SAID)["voice456"]
        check(deb["text"] == "[deadpan] I was asleep at three twelve. [yawns]" and deb["model_id"] == "eleven_v4",
              "audio tags reached ElevenLabs as written, with model_id eleven_v4")
        cap = tl["captions"][2]
        check(abs(cap["words"][0][1] - cap["start"]) < 0.05 and cap["words"][-1][2] < cap["end"] - 0.5,
              f"word timing: [deadpan] takes no time, the [yawns] after the words lights no word ({cap['words']}, "
              f"line ends {cap['end']})")
        check(cap["tags"] == ["[deadpan]", "[yawns]"] and tl["captions"][1]["tags"] == ["[sighs]"]
              and "tags" not in tl["captions"][0], "timeline.json keeps a line's tags, and only on lines that have them")
        rec = tl["captions"][1]
        check(abs(rec["words"][0][1] - rec["start"]) < 0.05,
              f"a Kokoro character's [sighs] gets no time in the word timing: its voice never got it ({rec['words'][0]})")
        credits_md = open(os.path.join(stock_dir, "CREDITS.md")).read()
        check("mock_user" in credits_md and "creativecommons" in credits_md, "stock/CREDITS.md written with author and license")

        n = len(HITS)
        run(["pipeline/build_audio.py", ep], env)
        check(len(HITS) == n, "rebuild made no network calls (lock + voice cache)")
        shutil.rmtree(os.path.join(ep, "build"))
        run(["pipeline/build_audio.py", ep], env)
        check([h for h in HITS[n:] if "/text-to-speech/" not in h[1]] == [], "clean rebuild re-fetched no sounds (pinned)")

        run(["pipeline/script_md.py", ep], env)
        script = open(os.path.join(ep, "SCRIPT.md")).read()
        check("## Credits" in script and "recorded `hook_2`" in script and "ElevenLabs voice123 on eleven_multilingual_v2" in script,
              "SCRIPT.md shows credits, recording names and the ElevenLabs voice and model")
        check("I was asleep at 3:12. *(deadpan, yawns)*" in script and "ElevenLabs voice456 on eleven_v4" in script,
              "SCRIPT.md shows a line's tags as a direction")
        run(["pipeline/render.py", ep, "--preview", "3.0"], env)
        check(os.path.exists(os.path.join(ep, "build", "preview_03.00.png")), "renderer accepts the new timeline")
        end_card_checks(ep)

        run(["pipeline/stock.py", "image", ep, "aerial", "--pexels", "suburban street"], env)
        check(os.path.exists(os.path.join(ep, "stills", "aerial.jpg")), "Pexels still saved to stills/aerial.jpg")
        run(["pipeline/stock.py", "image", ep, "aerial", "--pexels", "suburban street"], env, expect_ok=False)
        check(True, "refuses to overwrite an existing still without --force")
        check("Pexels License" in open(os.path.join(stock_dir, "CREDITS.md")).read(), "Pexels still credited")

        src = open(os.path.join(ep, "episode.py")).read()
        voice_dir = os.path.join(ep, "build", "voice")
        shutil.rmtree(voice_dir)    # so voicing any line, even a cached one, would show
        n = len(HITS)
        for line, expect in [('L("DEB", "[sighs] Never.")', ["shot hook, line 4 (DEB)", "[sighs]"]),
                             ('L("DEB", "Never.", "[sighs Never.")', ["shot hook, line 4 (DEB)", "square bracket"])]:
            with open(os.path.join(ep, "episode.py"), "w") as f:
                f.write(src + f'\nSHOTS[1]["items"].append({line})\n')
            r = run(["pipeline/build_audio.py", ep], env, expect_ok=False)
            check(all(e in r.stderr for e in expect), f"{line} stops the build, naming the shot and line")
        check(len(HITS) == n and not (os.path.isdir(voice_dir) and os.listdir(voice_dir)),
              "both stopped before voicing anything (no ElevenLabs call, no voice clip written)")
        with open(os.path.join(ep, "episode.py"), "w") as f:
            f.write(src + '\nCAST["DEB"]["model"] = "eleven_multilingual_v2"\n')
        r = run(["pipeline/build_audio.py", ep], env)
        check("DEB's ElevenLabs model eleven_multilingual_v2 may read audio tags out loud" in r.stderr,
              "tags on a model that may not read them give a warning")
        with open(os.path.join(ep, "episode.py"), "w") as f:
            f.write(src)

        bad = dict(env, ELEVENLABS_API_KEY="")
        shutil.rmtree(os.path.join(ep, "build", "voice"))
        r = run(["pipeline/build_audio.py", ep], bad, expect_ok=False)
        check("ELEVENLABS_API_KEY" in r.stderr, "missing API key gives a clear error")
        with open(os.path.join(ep, "episode.py"), "a") as f:
            f.write('\nSOUNDS["explosion"] = {"file": "x.wav"}\n')
        r = run(["pipeline/build_audio.py", ep], env, expect_ok=False)
        check("unknown sound name" in r.stderr, "unknown sound name gives a clear error")
        print("\nall stock-source checks passed\n")
        reenactment_checks(tmp, env, render_mp4="--full" in sys.argv)
        print("\nall reenactment checks passed\n")
        voices_checks(tmp, env)
        print("\nall voice provenance checks passed\n")
        blender_checks(tmp, env)
        print("\nall Blender reenactment checks passed")
    finally:
        server.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
