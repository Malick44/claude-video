#!/usr/bin/env python3
"""Synthesize the explainer's score + scene-timed SFX -> public/score.mp3.

Reads src/timeline.json so the hits stay locked to the scene cuts.
Needs numpy and ffmpeg. Deterministic (seeded)."""
import json, subprocess, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
tl = json.loads((ROOT / "src/timeline.json").read_text())
FPS, TR = tl["fps"], tl["transition"]
SR = 44100
rng = np.random.default_rng(7)

starts, acc = [], 0
for s in tl["scenes"]:
    starts.append(acc / FPS)
    acc += s["frames"] - TR
total_frames = sum(s["frames"] for s in tl["scenes"]) - TR * (len(tl["scenes"]) - 1)
DUR = total_frames / FPS
N = int(DUR * SR) + SR
t_all = np.arange(N) / SR
mix = np.zeros((N, 2))

def add(sig, at, pan=0.0, gain=1.0):
    i = int(at * SR)
    if i >= N: return
    sig = sig[: N - i]
    mix[i : i + len(sig), 0] += sig * gain * (1 - max(0, pan))
    mix[i : i + len(sig), 1] += sig * gain * (1 + min(0, pan))

def midi(n): return 440 * 2 ** ((n - 69) / 12)
def env_ad(n, a, d_tau):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d_tau)

def noise_band(dur, lo, hi):
    n = int(dur * SR)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec *= ((f > lo) & (f < hi))
    x = np.fft.irfft(spec, n)
    return x / (np.abs(x).max() + 1e-9)

def sweep_noise(dur, f0, f1):
    n = int(dur * SR)
    out = np.zeros(n)
    base = rng.standard_normal(n)
    spec = np.fft.rfft(base)
    f = np.fft.rfftfreq(n, 1 / SR)
    # piecewise band sweep
    seg = 24
    for k in range(seg):
        a, b = k * n // seg, (k + 1) * n // seg
        c = f0 * (f1 / f0) ** (k / seg)
        mask = np.exp(-((np.log(f + 1) - np.log(c)) ** 2) / 0.35)
        x = np.fft.irfft(spec * mask, n)
        out[a:b] = x[a:b]
    out /= np.abs(out).max() + 1e-9
    t = np.linspace(0, 1, n)
    return out * np.sin(np.pi * t) ** 1.5

# ---------------------------------------------------------------- harmony
BPM = 100
BEAT = 60 / BPM
BAR = BEAT * 4
# roots (midi) + chord tones per section
SEC = {
    "tense": [(38, [0, 3, 7]), (34, [0, 4, 7]), (31, [0, 3, 7]), (33, [0, 4, 7])],   # Dm Bb Gm A
    "drive": [(38, [0, 3, 7]), (34, [0, 4, 7]), (41, [0, 4, 7]), (36, [0, 4, 7])],   # Dm Bb F C
    "hope":  [(41, [0, 4, 7]), (36, [0, 4, 7]), (38, [0, 3, 7]), (34, [0, 4, 7])],   # F C Dm Bb
}
def section(sec_idx):
    return "tense" if sec_idx <= 2 else "drive" if sec_idx <= 5 else "hope"

# intensity curve 0..1 over time
def intensity(t):
    pts = [(0, .25), (starts[1], .45), (starts[2], .4), (starts[3], .6), (starts[4], .8), (starts[5], .85),
           (starts[6], .8), (starts[7], .9), (starts[8], 1.0), (DUR - 2, .6), (DUR, 0)]
    return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])

inten = intensity(t_all)

# ---------------------------------------------------------------- pad + bass + arp
pad = np.zeros((N, 2))
bass = np.zeros(N)
arp = np.zeros((N, 2))
bar_i = 0
t0 = 0.0
while t0 < DUR:
    sec_idx = max(i for i, s in enumerate(starts) if s <= t0 + 1e-6)
    root, tones = SEC[section(sec_idx)][bar_i % 4]
    n = int((BAR + 0.8) * SR)
    t = np.arange(n) / SR
    e = np.minimum(1, t / 0.9) * np.where(t < BAR, 1, np.exp(-(t - BAR) / 0.3))
    for k, tone in enumerate(tones + [12]):
        for oct_ in (12, 24):
            f = midi(root + tone + oct_)
            for det, ch in ((-0.004, 0), (0.004, 1)):
                v = np.sin(2 * np.pi * f * (1 + det) * t) + 0.3 * np.sin(2 * np.pi * 2 * f * (1 + det) * t) * 0.5
                i = int(t0 * SR)
                m = min(n, N - i)
                pad[i : i + m, ch] += (v * e)[:m] * (0.05 if oct_ == 12 else 0.03)
    # bass
    fb = midi(root)
    b = np.sin(2 * np.pi * fb * t) * e * 0.5
    i = int(t0 * SR); m = min(n, N - i)
    bass[i : i + m] += b[:m] * 0.5
    # arpeggio, 8th notes, from the squeeze scene on
    if t0 >= starts[1] - 0.01:
        seq = [0, 1, 2, 3, 2, 1, 2, 1]
        pool = [root + 24 + x for x in tones] + [root + 36]
        for q in range(8):
            at = t0 + q * BEAT / 2
            if at >= DUR: break
            note = pool[seq[q] % len(pool)]
            nn = int(0.55 * SR)
            tt = np.arange(nn) / SR
            f = midi(note)
            v = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * 2 * f * tt) * np.exp(-tt * 9)) * np.exp(-tt * 7)
            pan = -0.5 + (q % 4) / 4
            add(v, at, pan, 0.11 * float(inten[int(min(at, DUR) * SR)]) )
    t0 += BAR
    bar_i += 1

# ---------------------------------------------------------------- rhythm
def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 48 + 90 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9)

def thump(f0=55, tau=0.22):
    n = int(0.6 * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f0 + 60 * np.exp(-t * 25)) / SR
    return np.sin(ph) * np.exp(-t / tau)

K = kick()
HH = noise_band(0.08, 6000, 15000) * np.exp(-np.arange(int(0.08 * SR)) / SR * 60)
t = starts[3]
while t < starts[8] + 3:
    add(K, t, 0, 0.55 * float(intensity(t)))
    add(HH, t + BEAT / 2, 0.3, 0.12 * float(intensity(t)))
    t += BEAT
# heartbeat through the tense opening and the paycheck-stops scene
for a, b in ((0.0, starts[1] + 1), (starts[2] + 4.0, starts[3])):
    t = a
    while t < b:
        add(thump(52, .12), t, 0, 0.5)
        add(thump(46, .14), t + 0.32, 0, 0.35)
        t += 1.05

# ---------------------------------------------------------------- SFX
def boom():
    n = int(1.1 * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(70 * np.exp(-t * 4) + 30) / SR
    body = np.sin(ph) * np.exp(-t * 4.5)
    crack = noise_band(0.25, 300, 6000)[: n] if False else None
    out = body
    c = noise_band(0.3, 200, 5000) * np.exp(-np.arange(int(0.3 * SR)) / SR * 14)
    out[: len(c)] += c * 0.7
    return out

for fr in (6, 22, 36, 48, 58):
    add(boom(), fr / FPS, 0, 0.9)

for i in range(1, len(starts)):
    cut = starts[i] + TR / FPS * 0.0 - TR / FPS * 0.5
    add(sweep_noise(0.7, 400, 6000), cut - 0.25, 0.0, 0.32)
    add(thump(60, .25), cut + 0.2, 0, 0.5)

# coin pings in the paycheck scene
for i in range(14):
    fr = i * 9
    if fr > 140: break
    tt = np.arange(int(0.35 * SR)) / SR
    p = (np.sin(2 * np.pi * 1760 * tt) + 0.5 * np.sin(2 * np.pi * 2637 * tt)) * np.exp(-tt * 14)
    add(p, starts[2] + (fr + 70) / FPS / 1.0, 0.4, 0.12)
# paycheck dies: descending tone
n = int(1.2 * SR); tt = np.arange(n) / SR
fall = np.sin(2 * np.pi * np.cumsum(520 * np.exp(-tt * 2.2) + 60) / SR) * np.exp(-tt * 2.5)
add(fall, starts[2] + 140 / FPS, 0, 0.35)
# DIME letter pops + total sting
for fr in (26, 32, 38, 44):
    tt = np.arange(int(0.3 * SR)) / SR
    add(np.sin(2 * np.pi * midi(72 + (fr - 26) // 6 * 2) * tt) * np.exp(-tt * 10), starts[3] + fr / FPS, 0, 0.18)
for fr in (70, 160, 250, 340):
    add(thump(90, .12), starts[3] + fr / FPS, 0, 0.5)
# flip-card swooshes
for i in range(4):
    add(sweep_noise(0.45, 600, 5000), starts[6] + (90 + i * 70) / FPS - 0.1, 0.0, 0.22)
# stamp
add(boom(), starts[7] + 310 / FPS, 0, 0.8)
# resolving chime on the shield
for k, n_ in enumerate((77, 81, 84, 88)):
    tt = np.arange(int(2.5 * SR)) / SR
    v = (np.sin(2 * np.pi * midi(n_) * tt) + 0.3 * np.sin(2 * np.pi * midi(n_) * 2.01 * tt)) * np.exp(-tt * 1.6)
    add(v, starts[8] + (120 + k * 5) / FPS, 0, 0.1)

# ---------------------------------------------------------------- reverb + master
def reverb(x, secs=2.2, wet=0.28):
    n = int(secs * SR)
    ir = rng.standard_normal((n, 2)) * np.exp(-np.arange(n) / SR * 3.0)[:, None]
    L = 1 << int(np.ceil(np.log2(len(x) + n)))
    out = np.zeros_like(x)
    for ch in range(2):
        out[:, ch] = np.fft.irfft(np.fft.rfft(x[:, ch], L) * np.fft.rfft(ir[:, ch], L), L)[: len(x)]
    out /= np.abs(out).max() + 1e-9
    return out * wet * np.abs(x).max()

music = pad * (0.5 + inten[:, None] * 0.8) + arp
music[:, 0] += bass * 0.9; music[:, 1] += bass * 0.9
music = music + reverb(music)
final = music + mix
final *= np.minimum(1, t_all[:, None] / 0.5)
final *= np.clip((DUR + 0.8 - t_all[:, None]) / 2.0, 0, 1)
final = np.tanh(final * 1.15)
final *= 0.89 / np.abs(final).max()

pcm = (final[: int((DUR + 0.8) * SR)] * 32767).astype("<i2")
wav = ROOT / "public/score.wav"
with wave.open(str(wav), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5:LRA=9",
                "-b:a", "192k", str(ROOT / "public/score.mp3")], check=True)
wav.unlink()
print("score.mp3", f"{DUR:.1f}s")
