"""Voice the script with Kokoro TTS, lay it on a timeline, and mix the soundtrack.

  python pipeline/build_audio.py episodes/<episode>

Outputs (in <episode>/build/):
  timeline.json  - shot/caption/sfx timings consumed by render.py
  soundtrack.wav - final mix (voice + synthesized score + sfx)
"""
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

from common import MODELS, load_episode
from sounds import (LEVELS, SR, carriage_ding, chimes, crickets, glitch, motif_bed, shutter, sting,
                    typewriter_click, typewriter_gain, wind)

ep = None  # set in main()
BUILD = CACHE = None
FFMPEG = None


def ffmpeg():
    global FFMPEG
    if FFMPEG is None:
        import imageio_ffmpeg
        FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    return FFMPEG


def db(x):
    return 10 ** (x / 20)


# ---------------------------------------------------------------- voice

_kokoro = None


def kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(MODELS, "kokoro.onnx"), os.path.join(MODELS, "voices.bin"))
    return _kokoro


def trim(y, thresh=db(-45), pad=0.03):
    idx = np.where(np.abs(y) > thresh)[0]
    if not len(idx):
        return y
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(y), idx[-1] + int(pad * SR))
    return y[a:b]


def fx(path_in, path_out, cast):
    filters = []
    if cast.get("pitch", 1.0) != 1.0:
        filters.append(f"rubberband=pitch={cast['pitch']}")
    if cast.get("altered"):
        # documentary "voice altered": pitch-down (above) + a little grit and phone-ish band.
        filters += ["highpass=f=120", "lowpass=f=5200", "acrusher=bits=10:mix=0.25:mode=log", "vibrato=f=5.5:d=0.08"]
    if not filters:
        return path_in
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", path_in, "-af", ",".join(filters), "-ar", str(SR), path_out], check=True)
    return path_out


def voice_line(who, say):
    cast = ep.CAST[who]
    key = hashlib.sha1(json.dumps([cast, say]).encode()).hexdigest()[:12]
    raw = os.path.join(CACHE, f"{who}_{key}_raw.wav")
    out = os.path.join(CACHE, f"{who}_{key}.wav")
    if not os.path.exists(out):
        samples, sr = kokoro().create(say, voice=cast["voice"], speed=cast["speed"], lang="en-us" if cast["voice"][0] == "a" else "en-gb")
        assert sr == SR, sr
        sf.write(raw, samples, SR)
        processed = fx(raw, out + ".fx.wav", cast)
        y, _ = sf.read(processed)
        y = trim(y)
        # loudness-match every line: RMS target, peak-capped
        rms = np.sqrt(np.mean(y ** 2)) + 1e-9
        y = y * (db(-17) / rms)
        peak = np.max(np.abs(y))
        if peak > db(-1.5):
            y = y * (db(-1.5) / peak)
        sf.write(out, y, SR)
    y, _ = sf.read(out)
    return y


# ---------------------------------------------------------------- timeline + mix


def main():
    global ep, BUILD, CACHE
    if len(sys.argv) != 2:
        sys.exit("usage: build_audio.py episodes/<episode>")
    ep = load_episode(sys.argv[1])
    BUILD = ep.BUILD
    CACHE = os.path.join(BUILD, "voice")
    os.makedirs(CACHE, exist_ok=True)
    t = 0.0
    shots, captions, voice = [], [], []
    for shot in ep.SHOTS:
        start = t
        t += shot.get("pre", 0.0)
        lines = []
        for item in shot["items"]:
            if item[0] == "pause":
                t += item[1]
                continue
            _, who, text, say = item
            y = voice_line(who, say)
            dur = len(y) / SR
            voice.append((t, y))
            captions.append({"start": round(t, 3), "end": round(t + dur, 3), "who": who, "text": text, "shot": shot["id"]})
            lines.append({"start": round(t, 3), "end": round(t + dur, 3), "text": text})
            t += dur
        t += shot.get("post", 0.0)
        t = max(t, start + shot.get("min", 0.0))
        shots.append({k: v for k, v in shot.items() if k != "items"} | {"start": round(start, 3), "end": round(t, 3), "lines": lines})
        print(f"{shot['id']:10s} {start:6.2f} -> {t:6.2f}  ({t - start:4.2f}s)")
    total = t
    print(f"TOTAL {total:.2f}s")

    n = int((total + 0.5) * SR)
    vox = np.zeros(n)
    for s, y in voice:
        i = int(s * SR)
        vox[i: i + len(y)] += y[: n - i]

    music = np.zeros(n)
    sfx = np.zeros(n)

    def put(buf, at, y, gain_db):
        i = int(at * SR)
        if i >= n:
            return
        seg = y[: n - i]
        buf[i: i + len(seg)] += seg * db(gain_db)

    # score: ostinato bed from the title card (first "sting") to the end card, ducked under dialogue
    bed_start = next((s["start"] for s in shots if "sting" in s.get("sfx", [])), 0.0)
    bed_end = next((s["start"] for s in shots if s["kind"] == "end"), total) + 0.4
    bed = motif_bed(bed_end - bed_start + 2)
    fade = np.ones(int((bed_end - bed_start) * SR))
    k = int(1.5 * SR)
    fade[-k:] = np.linspace(1, 0, k)
    put(music, bed_start, bed[: len(fade)] * fade, LEVELS["bed"])

    for s in shots:
        for name in s.get("sfx", []):
            if name == "sting":
                put(music, s["start"], sting(), LEVELS["sting"])
            elif name == "sting_end":
                put(music, s["start"], sting(6.0), LEVELS["sting_end"])
            elif name == "sting_soft":
                # a soft sting under the shot's last line (the question the episode asks)
                put(music, s["lines"][-1]["start"] - 0.1, sting(4.0), LEVELS["sting_soft"])
            elif name == "shutter":
                put(sfx, s["start"], shutter(), LEVELS["shutter"])
            elif name == "wind":
                put(sfx, s["start"], wind(s["end"] - s["start"]), LEVELS["wind"])
            elif name == "chimes":
                put(sfx, s["start"], chimes(s["end"] - s["start"]), LEVELS["chimes"])
            elif name == "crickets":
                put(sfx, s["start"], crickets(s["end"] - s["start"]), LEVELS["crickets"])
            else:
                sys.exit(f"shot {s['id']}: unknown sfx {name!r}")
        if s["kind"] == "qcard":
            # typing: one click per character across the first 60% of the card
            txt = s["text"]
            span = (s["end"] - s["start"]) * 0.6
            for j, ch in enumerate(txt):
                if ch != " ":
                    put(sfx, s["start"] + 0.15 + span * j / len(txt), typewriter_click(j), LEVELS["typewriter"] + typewriter_gain(j))
            put(sfx, s["start"] + 0.15 + span + 0.05, carriage_ding(), LEVELS["ding"])
        if s["kind"] == "doorbell":
            flick = s["lines"][-1]["end"] + 0.15
            for j in range(6):
                put(sfx, flick + j * 0.3, glitch(), LEVELS["glitch"])
            s["flicker_at"] = round(flick, 3)
            # the jump cut when the clock rolls over to the next minute
            put(sfx, s["start"] + (60 - s["clock_start"]), glitch(), LEVELS["jump"])

    # duck the score under dialogue (smoothed voice envelope)
    env = np.abs(vox)
    w = int(0.25 * SR)
    env = np.convolve(env, np.ones(w) / w, mode="same")
    duck = 1 - 0.55 * np.clip(env / (db(-26)), 0, 1)
    mix = vox + music * duck + sfx
    peak = np.max(np.abs(mix))
    mix = mix * (db(-1.0) / peak)
    out = os.path.join(BUILD, "soundtrack.wav")
    sf.write(out, mix, SR)

    with open(os.path.join(BUILD, "timeline.json"), "w") as f:
        json.dump({"total": round(total, 3), "shots": shots, "captions": captions}, f, indent=1)
    print("wrote", out)


if __name__ == "__main__":
    sys.exit(main())
