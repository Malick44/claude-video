"""Offline self-test for stock sources, against a local mock of Freesound, ElevenLabs and Pexels.

  .venv/bin/python pipeline/selftest.py

Builds a throwaway episode that uses every source type (local file, URL, Freesound id and
search, ElevenLabs sound effects and voice, your own recording, a Pexels still) and checks
fetching, lock-file pinning, rebuilds without network, and credits. Touches nothing in the
real stock/ folder or episodes/.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SHOW = os.path.dirname(HERE)
PY = sys.executable
HITS = []


def tone(freq, seconds, sr=24000):
    t = np.arange(int(seconds * sr)) / sr
    y = (0.5 * np.sin(2 * np.pi * freq * t) * np.minimum(1, t / 0.01) * np.exp(-t)).astype(np.float32)
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
        if self.path.startswith("/el/text-to-speech/voice123"):
            assert body["model_id"] == "eleven_multilingual_v2" and body["seed"] == 7, body
            return self._send(tone(220, 0.5 + 0.04 * len(body["text"])), "audio/mpeg")
        self._send(b"not found", "text/plain", 404)


EPISODE = '''
TITLE = "NOBODY MOVES"
EPISODE = "EPISODE 99: SELF TEST"
NEXT_UP = "NEXT: NOTHING"
L = lambda who, text, say=None: ("line", who, text, say or text)
V = lambda img, a, b, look=None: {{"img": img, "kb": (a, b), "look": look}}
CAST = {{"NARRATOR": {{"provider": "elevenlabs", "voice_id": "voice123", "model": "eleven_multilingual_v2", "seed": 7}}}}
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
      "items": [L("NARRATOR", "This is a test."), L("GARRISON", "I didn't see nothing.")]}},
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


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Mock)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    tmp = tempfile.mkdtemp(prefix="nm-selftest-")
    try:
        ep = os.path.join(tmp, "ep99_selftest")
        os.makedirs(os.path.join(ep, "stills"))
        os.makedirs(os.path.join(ep, "recordings"))
        shutil.copy(os.path.join(SHOW, "episodes/ep01_three_feet/stills/garrison.webp"), os.path.join(ep, "stills"))
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
        check([c["recorded"] for c in tl["captions"]] == [False, True], "hook_2 used the recording, hook_1 the ElevenLabs voice")
        tts = [h for h in HITS if "/text-to-speech/" in h[1]]
        check(len(tts) == 1, "ElevenLabs TTS called once (the recorded line skipped it)")
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
        check("## Credits" in script and "recorded `hook_2`" in script and "ElevenLabs voice123" in script,
              "SCRIPT.md shows credits, recording names and the ElevenLabs voice")
        run(["pipeline/render.py", ep, "--preview", "3.0"], env)
        check(os.path.exists(os.path.join(ep, "build", "preview_03.00.png")), "renderer accepts the new timeline")

        run(["pipeline/stock.py", "image", ep, "aerial", "--pexels", "suburban street"], env)
        check(os.path.exists(os.path.join(ep, "stills", "aerial.jpg")), "Pexels still saved to stills/aerial.jpg")
        run(["pipeline/stock.py", "image", ep, "aerial", "--pexels", "suburban street"], env, expect_ok=False)
        check(True, "refuses to overwrite an existing still without --force")
        check("Pexels License" in open(os.path.join(stock_dir, "CREDITS.md")).read(), "Pexels still credited")

        bad = dict(env, ELEVENLABS_API_KEY="")
        shutil.rmtree(os.path.join(ep, "build", "voice"))
        r = run(["pipeline/build_audio.py", ep], bad, expect_ok=False)
        check("ELEVENLABS_API_KEY" in r.stderr, "missing API key gives a clear error")
        with open(os.path.join(ep, "episode.py"), "a") as f:
            f.write('\nSOUNDS["explosion"] = {"file": "x.wav"}\n')
        r = run(["pipeline/build_audio.py", ep], env, expect_ok=False)
        check("unknown sound name" in r.stderr, "unknown sound name gives a clear error")
        print("\nall stock-source checks passed")
    finally:
        server.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
