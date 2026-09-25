"""Stock assets: local files, direct URLs and third-party APIs (Freesound, ElevenLabs, Pexels).

Anything fetched over the network is saved once under stock/ (commit it with the show) and
pinned in stock/sources.lock.json with its license and credit. Every later build, and every
episode, reuses that exact file without calling the API again. Delete a lock entry (or its
file) to fetch it again.

API keys come from the environment or from shows/nobody-moves/.env (gitignored):
  FREESOUND_API_KEY   https://freesound.org/apiv2/apply
  ELEVENLABS_API_KEY  https://elevenlabs.io (Profile -> API keys)
  PEXELS_API_KEY      https://www.pexels.com/api/

CLI:
  python pipeline/stock.py image episodes/<ep> <still_key> --pexels "suburban street at night"
  python pipeline/stock.py image episodes/<ep> <still_key> --url https://.../photo.jpg [--credit "..."]
  python pipeline/stock.py credits          # rewrite stock/CREDITS.md from the lock file
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

import numpy as np

from common import SHOW_DIR

SR = 24000
STOCK = os.environ.get("NOBODY_MOVES_STOCK_DIR", os.path.join(SHOW_DIR, "stock"))
LOCK = os.path.join(STOCK, "sources.lock.json")
API = {
    "freesound": os.environ.get("FREESOUND_API_URL", "https://freesound.org/apiv2"),
    "elevenlabs": os.environ.get("ELEVENLABS_API_URL", "https://api.elevenlabs.io/v1"),
    "pexels": os.environ.get("PEXELS_API_URL", "https://api.pexels.com/v1"),
}
# Freesound licenses allowed by default: no NonCommercial, since a monetized TikTok is commercial.
FREESOUND_LICENSES = '("Creative Commons 0" OR "Attribution")'


# ---------------------------------------------------------------- keys + http

def _load_env():
    path = os.path.join(SHOW_DIR, ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def api_key(name):
    _load_env()
    value = os.environ.get(name)
    if not value:
        sys.exit(f"{name} is not set: add it to shows/nobody-moves/.env (gitignored) or export it")
    return value


def _redact(url):
    return re.sub(r"(token=)[^&]+", r"\1***", url)


def http(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    req.add_header("User-Agent", "nobody-moves-pipeline/1")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        body = e.read()[:300].decode(errors="replace")
        sys.exit(f"{method or 'GET'} {_redact(url)} failed: HTTP {e.code} {body}")
    except urllib.error.URLError as e:
        sys.exit(f"{method or 'GET'} {_redact(url)} failed: {e.reason}")


def http_json(url, headers=None):
    return json.loads(http(url, headers=headers))


# ---------------------------------------------------------------- lock + credits

def _lock_load():
    if os.path.exists(LOCK):
        with open(LOCK) as f:
            return json.load(f)
    return {}


def _lock_save(lock):
    os.makedirs(STOCK, exist_ok=True)
    with open(LOCK, "w") as f:
        json.dump(lock, f, indent=1, sort_keys=True)
        f.write("\n")
    write_credits(lock)


def spec_key(kind, spec):
    return kind + ":" + json.dumps(spec, sort_keys=True)


def write_credits(lock=None):
    lock = _lock_load() if lock is None else lock
    rows = ["# Stock asset credits", "",
            "Generated from sources.lock.json. Credit every **Attribution** (CC-BY) item in the video description.", "",
            "| File | What | Author | License | Source |", "|---|---|---|---|---|"]
    for entry in sorted(lock.values(), key=lambda e: e["file"]):
        c = entry.get("credit") or {}
        rows.append(f"| `{entry['file']}` | {c.get('title', '')} | {c.get('author', '')} | {c.get('license', '')} | {c.get('source', '')} |")
    with open(os.path.join(STOCK, "CREDITS.md"), "w") as f:
        f.write("\n".join(rows) + "\n")


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:40] or "asset"


def _ext_from_url(url, default):
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lstrip(".").lower()
    return ext if re.fullmatch(r"[a-z0-9]{2,5}", ext or "") else default


# ---------------------------------------------------------------- providers

def _freesound(spec):
    token = api_key("FREESOUND_API_KEY")
    fields = "id,name,username,license,url,previews,duration"
    if "freesound" in spec:
        sound = http_json(f"{API['freesound']}/sounds/{int(spec['freesound'])}/?fields={fields}&token={token}")
    else:
        filt = f"license:{FREESOUND_LICENSES}"
        if spec.get("max_seconds"):
            filt += f" duration:[0 TO {spec['max_seconds']}]"
        q = urllib.parse.urlencode({"query": spec["freesound_search"], "filter": filt, "sort": "rating_desc",
                                    "fields": fields, "page_size": 5, "token": token})
        results = http_json(f"{API['freesound']}/search/text/?{q}").get("results") or []
        if not results:
            sys.exit(f"Freesound: no CC0/CC-BY results for {spec['freesound_search']!r}")
        sound = results[0]
    data = http(sound["previews"]["preview-hq-mp3"])
    credit = {"title": sound.get("name", ""), "author": sound.get("username", ""),
              "license": sound.get("license", ""), "source": sound.get("url", ""), "freesound_id": sound.get("id")}
    return data, "mp3", credit, f"freesound-{sound.get('id')}-{_slug(sound.get('name'))}"


def _elevenlabs_sfx(spec):
    body = {"text": spec["elevenlabs_sfx"], "prompt_influence": spec.get("prompt_influence", 0.3)}
    if spec.get("seconds"):
        body["duration_seconds"] = spec["seconds"]
    data = http(f"{API['elevenlabs']}/sound-generation", json.dumps(body).encode(),
                {"xi-api-key": api_key("ELEVENLABS_API_KEY"), "Content-Type": "application/json",
                 "Accept": "audio/mpeg"}, "POST")
    credit = {"title": spec["elevenlabs_sfx"], "author": "ElevenLabs sound effects",
              "license": "per your ElevenLabs plan", "source": "elevenlabs.io"}
    return data, "mp3", credit, f"elevenlabs-{_slug(spec['elevenlabs_sfx'])}"


def _url(spec, default_ext):
    data = http(spec["url"])
    credit = dict({"source": spec["url"]}, **(spec.get("credit") or {}))
    name = os.path.splitext(os.path.basename(urllib.parse.urlparse(spec["url"]).path))[0]
    return data, _ext_from_url(spec["url"], default_ext), credit, f"url-{_slug(name)}"


def elevenlabs_tts(text, cast):
    """One line of dialogue from an ElevenLabs voice (cast entry with provider "elevenlabs")."""
    body = {"text": text, "model_id": cast.get("model", "eleven_multilingual_v2")}
    for k in ("voice_settings", "seed"):
        if k in cast:
            body[k] = cast[k]
    return http(f"{API['elevenlabs']}/text-to-speech/{cast['voice_id']}?output_format=mp3_44100_128",
                json.dumps(body).encode(),
                {"xi-api-key": api_key("ELEVENLABS_API_KEY"), "Content-Type": "application/json",
                 "Accept": "audio/mpeg"}, "POST")


# ---------------------------------------------------------------- resolve

def fetch(spec, kind, base_dirs):
    """Resolve a stock spec to (absolute path, credit or None), fetching and locking on first use."""
    if "file" in spec:
        f = os.path.expanduser(spec["file"])
        for path in [f] if os.path.isabs(f) else [os.path.join(b, f) for b in base_dirs]:
            if os.path.exists(path):
                credit = spec.get("credit")
                return os.path.abspath(path), {"title": credit} if isinstance(credit, str) else credit
        sys.exit(f"stock file not found: {spec['file']} (looked in {', '.join(base_dirs)})")
    lock = _lock_load()
    key = spec_key(kind, spec)
    entry = lock.get(key)
    if entry and os.path.exists(os.path.join(SHOW_DIR, entry["file"])):
        return os.path.join(SHOW_DIR, entry["file"]), entry.get("credit")
    if "url" in spec:
        data, ext, credit, name = _url(spec, "mp3" if kind == "audio" else "jpg")
    elif "freesound" in spec or "freesound_search" in spec:
        data, ext, credit, name = _freesound(spec)
    elif "elevenlabs_sfx" in spec:
        data, ext, credit, name = _elevenlabs_sfx(spec)
    else:
        sys.exit(f"unknown stock source {spec!r} (use file, url, freesound, freesound_search or elevenlabs_sfx)")
    folder = os.path.join(STOCK, kind)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{name}-{hashlib.sha1(key.encode()).hexdigest()[:8]}.{ext}")
    with open(path, "wb") as f:
        f.write(data)
    lock[key] = {"file": os.path.relpath(path, SHOW_DIR), "credit": credit}
    _lock_save(lock)
    print(f"fetched {os.path.relpath(path, SHOW_DIR)} ({credit.get('license') or 'no license info'})")
    return path, credit


def decode_audio(path, sr=SR, channels=1):
    """Any audio file ffmpeg can read -> float array at `sr`: mono (n,) or, with channels=2, (n, 2)."""
    import imageio_ffmpeg
    out = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", path, "-ac", str(channels),
                          "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
    if out.returncode or not out.stdout:
        sys.exit(f"could not decode audio {path}: {out.stderr.decode(errors='replace')[:300]}")
    y = np.frombuffer(out.stdout, np.float32).astype(np.float64)
    return y.reshape(-1, channels) if channels > 1 else y


def decode_audio_bytes(data, sr=SR):
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".audio") as f:
        f.write(data)
        f.flush()
        return decode_audio(f.name, sr)


# ---------------------------------------------------------------- images (CLI)

def fetch_image(ep_dir, still_key, query=None, url=None, credit_text=None, force=False):
    stills = os.path.join(ep_dir, "stills")
    os.makedirs(stills, exist_ok=True)
    existing = [f for f in os.listdir(stills) if os.path.splitext(f)[0] == still_key]
    if existing and not force:
        sys.exit(f"stills/{existing[0]} already exists; pass --force to replace it")
    if query:
        q = urllib.parse.urlencode({"query": query, "orientation": "portrait", "per_page": 1})
        photos = http_json(f"{API['pexels']}/search?{q}", {"Authorization": api_key("PEXELS_API_KEY")}).get("photos") or []
        if not photos:
            sys.exit(f"Pexels: no results for {query!r}")
        p = photos[0]
        url = p["src"].get("large2x") or p["src"]["original"]
        credit = {"title": p.get("alt") or query, "author": p.get("photographer", ""),
                  "license": "Pexels License", "source": p.get("url", "")}
    else:
        credit = {"title": still_key, "source": url, **({"author": credit_text} if credit_text else {})}
    data = http(url)
    for f in existing:
        os.remove(os.path.join(stills, f))
    path = os.path.join(stills, f"{still_key}.{_ext_from_url(url, 'jpg').replace('jpeg', 'jpg')}")
    with open(path, "wb") as f:
        f.write(data)
    lock = _lock_load()
    lock[spec_key("image", {"episode": os.path.basename(ep_dir.rstrip('/')), "still": still_key})] = {
        "file": os.path.relpath(path, SHOW_DIR), "credit": credit}
    _lock_save(lock)
    print(f"wrote {os.path.relpath(path, SHOW_DIR)} ({credit.get('license', 'license: check source')})")


def main(argv):
    if argv[:1] == ["credits"]:
        write_credits()
        print("wrote", os.path.join(STOCK, "CREDITS.md"))
        return
    if len(argv) >= 3 and argv[0] == "image":
        opts = argv[3:]
        get = lambda flag: opts[opts.index(flag) + 1] if flag in opts else None  # noqa: E731
        if not (get("--pexels") or get("--url")):
            sys.exit("image needs --pexels QUERY or --url URL")
        fetch_image(os.path.abspath(argv[1]), argv[2], query=get("--pexels"), url=get("--url"),
                    credit_text=get("--credit"), force="--force" in opts)
        return
    sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
