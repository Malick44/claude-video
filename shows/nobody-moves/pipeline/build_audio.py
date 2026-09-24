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

ep = None  # set in main()
BUILD = CACHE = None
SR = 24000
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


# ---------------------------------------------------------------- synth (score + sfx)

rng = np.random.default_rng(7)


def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def piano_note(freq, dur=4.0, vel=1.0):
    t = t_axis(dur)
    y = np.zeros_like(t)
    B = 0.0004  # inharmonicity
    for n in range(1, 10):
        fn = n * freq * np.sqrt(1 + B * n * n)
        if fn > SR / 2 - 500:
            break
        amp = (1.0 / n ** 1.2) * (1.15 if n == 2 else 1.0)
        decay = 1.1 + 0.55 * n + freq / 400
        y += amp * np.sin(2 * np.pi * fn * t + rng.uniform(0, 6.28)) * np.exp(-decay * t)
    # hammer thump
    k = int(0.012 * SR)
    y[:k] += rng.normal(0, 0.15, k) * np.linspace(1, 0, k)
    y *= np.minimum(1, t / 0.004)  # tiny attack
    return vel * y / (np.max(np.abs(y)) + 1e-9)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def reverb(y, seconds=2.2, wet=0.35):
    n = int(seconds * SR)
    ir = rng.normal(0, 1, n) * np.exp(-np.linspace(0, 7, n))
    ir[0] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    size = 1 << int(np.ceil(np.log2(len(y) + n)))
    wetsig = np.fft.irfft(np.fft.rfft(y, size) * np.fft.rfft(ir, size), size)[: len(y) + n]
    out = np.zeros(len(y) + n)
    out[: len(y)] += y * (1 - wet)
    out += wetsig * wet * 0.6
    return out


def fft_band(y, lo, hi):
    Y = np.fft.rfft(y)
    f = np.fft.rfftfreq(len(y), 1 / SR)
    Y[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(Y, len(y))


def sting(dur=5.0):
    # low A-minor cluster with a sub boom
    y = np.zeros(int(dur * SR))
    for n, v in [(33, 1.0), (40, 0.8), (45, 0.7), (48, 0.55), (52, 0.35)]:
        note = piano_note(midi(n), dur, v)
        y[: len(note)] += note
    t = t_axis(dur)
    boom = np.sin(2 * np.pi * (48 - 18 * np.minimum(t, 1)) * t) * np.exp(-2.2 * t)
    y += 0.9 * boom
    y = reverb(y, 2.8, 0.4)
    return y / np.max(np.abs(y))


def motif_bed(total):
    """Sparse, ominous piano ostinato (A minor), true-crime style."""
    y = np.zeros(int(total * SR) + SR * 4)
    pattern = [69, 72, 76, 72, 69, 72, 75, 72]  # A C E C A C D# C  (the flat-5 is the unease)
    step = 0.62
    t = 0.0
    i = 0
    while t < total:
        n = pattern[i % len(pattern)]
        if (i // len(pattern)) % 2 == 1 and i % len(pattern) == 6:
            n = 74  # vary the turn on alternate bars
        note = piano_note(midi(n - 12), 2.2, 0.55 if i % 4 else 0.8)
        s = int(t * SR)
        y[s: s + len(note)] += note[: len(y) - s]
        t += step
        i += 1
    # low drone
    tt = t_axis(len(y) / SR)
    drone = 0.35 * np.sin(2 * np.pi * 55 * tt) + 0.2 * np.sin(2 * np.pi * 82.4 * tt + 1)
    drone *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * tt)
    y = reverb(y, 2.4, 0.45)[: len(y)] + drone * 0.5
    return y / np.max(np.abs(y))


def shutter():
    t = t_axis(0.25)
    click1 = rng.normal(0, 1, len(t)) * np.exp(-t * 90)
    click2 = np.zeros_like(t)
    s = int(0.07 * SR)
    click2[s:] = rng.normal(0, 1, len(t) - s) * np.exp(-(t[s:] - t[s]) * 60)
    y = fft_band(click1 + 0.8 * click2, 900, 9000)
    # flash whine
    t2 = t_axis(0.25)
    y += 0.08 * np.sin(2 * np.pi * (2500 + 3000 * t2) * t2) * np.exp(-t2 * 12)
    return y / np.max(np.abs(y))


def typewriter_click():
    t = t_axis(0.06)
    y = rng.normal(0, 1, len(t)) * np.exp(-t * 180)
    y = fft_band(y, 1500, 8000) + 0.6 * np.sin(2 * np.pi * 180 * t) * np.exp(-t * 120)
    return y / np.max(np.abs(y))


def carriage_ding():
    t = t_axis(1.2)
    y = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in [(2093, 3), (4186, 5), (6280, 8)])
    return y / np.max(np.abs(y))


def chimes(dur):
    y = np.zeros(int(dur * SR))
    freqs = [1318.5, 1568.0, 1760.0, 2093.0, 2349.3]
    t = 0.3
    while t < dur - 0.2:
        f = freqs[rng.integers(len(freqs))]
        tt = t_axis(2.5)
        note = sum(a * np.sin(2 * np.pi * f * m * tt) for m, a in [(1, 1), (2.76, 0.4), (5.4, 0.15)]) * np.exp(-tt * 1.6)
        s = int(t * SR)
        seg = note[: len(y) - s]
        y[s: s + len(seg)] += seg * rng.uniform(0.3, 0.8)
        t += rng.uniform(0.25, 1.4)
    return y / (np.max(np.abs(y)) + 1e-9)


def wind(dur):
    n = int(dur * SR)
    y = fft_band(rng.normal(0, 1, n), 80, 900)
    tt = t_axis(dur)
    y *= 0.55 + 0.45 * np.sin(2 * np.pi * 0.23 * tt) * np.sin(2 * np.pi * 0.11 * tt + 1)
    return y / np.max(np.abs(y))


def crickets(dur):
    y = np.zeros(int(dur * SR))
    for f0, rate, phase in [(4400, 3.1, 0.0), (4750, 2.4, 0.5), (5100, 3.7, 0.2)]:
        t = phase
        while t < dur:
            tt = t_axis(0.12)
            chirp = np.sin(2 * np.pi * f0 * tt) * (np.sin(2 * np.pi * 30 * tt) > 0) * np.hanning(len(tt))
            s = int(t * SR)
            seg = chirp[: len(y) - s]
            y[s: s + len(seg)] += seg * rng.uniform(0.3, 0.6)
            t += 1 / rate + rng.uniform(0, 0.05)
    tt = t_axis(dur)
    hum = 0.08 * np.sin(2 * np.pi * 60 * tt) + 0.04 * np.sin(2 * np.pi * 120 * tt)
    return y / (np.max(np.abs(y)) + 1e-9) + hum


def glitch():
    t = t_axis(0.18)
    y = np.sign(np.sin(2 * np.pi * 880 * t)) * 0.5 + rng.normal(0, 0.6, len(t))
    y *= np.exp(-t * 18)
    return y / np.max(np.abs(y))


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
    put(music, bed_start, bed[: len(fade)] * fade, -21)

    for s in shots:
        for name in s.get("sfx", []):
            if name == "sting":
                put(music, s["start"], sting(), -5)
            elif name == "sting_end":
                put(music, s["start"], sting(6.0), -6)
            elif name == "sting_soft":
                # a soft sting under the shot's last line (the question the episode asks)
                put(music, s["lines"][-1]["start"] - 0.1, sting(4.0), -14)
            elif name == "shutter":
                put(sfx, s["start"], shutter(), -9)
            elif name == "wind":
                put(sfx, s["start"], wind(s["end"] - s["start"]), -24)
            elif name == "chimes":
                put(sfx, s["start"], chimes(s["end"] - s["start"]), -23)
            elif name == "crickets":
                put(sfx, s["start"], crickets(s["end"] - s["start"]), -27)
        if s["kind"] == "qcard":
            # typing: one click per character across the first 60% of the card
            txt = s["text"]
            span = (s["end"] - s["start"]) * 0.6
            for j, ch in enumerate(txt):
                if ch != " ":
                    put(sfx, s["start"] + 0.15 + span * j / len(txt), typewriter_click(), -20 + rng.uniform(-3, 2))
            put(sfx, s["start"] + 0.15 + span + 0.05, carriage_ding(), -26)
        if s["kind"] == "doorbell":
            flick = s["lines"][-1]["end"] + 0.15
            for j in range(6):
                put(sfx, flick + j * 0.3, glitch(), -24)
            s["flicker_at"] = round(flick, 3)
            # the jump cut when the clock rolls over to the next minute
            put(sfx, s["start"] + (60 - s["clock_start"]), glitch(), -18)

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
