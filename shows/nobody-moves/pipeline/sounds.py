"""The show's sound library: score and sound effects, synthesized in code (no samples).

Every generator is deterministic: it seeds its own random stream, so a sound comes out
identical in every episode no matter what else the episode contains. build_audio.py mixes
these into each episode; sound_kit.py exports them as WAVs for editing apps.
"""
import functools
import hashlib

import numpy as np

SR = 24000

# Mix levels (dBFS gain) shared by every episode, so the show always sounds balanced the same way.
LEVELS = {
    "bed": -21,          # piano ostinato under the whole episode (ducked under dialogue)
    "sting": -5,         # title card
    "sting_end": -6,     # end card
    "sting_soft": -14,   # under the episode's big question
    "shutter": -9,       # evidence-photo flash
    "typewriter": -20,   # interviewer question cards (per key)
    "ding": -26,         # typewriter bell
    "wind": -24,         # anonymous-source ambience
    "chimes": -23,
    "crickets": -27,     # doorbell-cam night ambience
    "glitch": -24,       # doorbell-cam frame flicker
    "jump": -18,         # doorbell-cam jump cut
}

# The theme: a sparse A-minor ostinato. The D# (flat five) is the unease.
THEME_NOTES = [69, 72, 76, 72, 69, 72, 75, 72]   # MIDI note numbers, played an octave lower
THEME_TURN = 74                                  # replaces the D# on every other bar
THEME_STEP = 0.62                                # seconds per note


def _rng(*key):
    """A random stream fixed by `key` (stable across runs, unlike Python's hash())."""
    seed = int.from_bytes(hashlib.sha256(repr(key).encode()).digest()[:8], "little")
    return np.random.default_rng(seed)


def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def normalize(y):
    return y / (np.max(np.abs(y)) + 1e-9)


def fft_band(y, lo, hi):
    Y = np.fft.rfft(y)
    f = np.fft.rfftfreq(len(y), 1 / SR)
    Y[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(Y, len(y))


@functools.lru_cache(maxsize=None)
def _room(seconds):
    """Impulse response of the show's one 'room': exponentially decaying noise, fixed per length."""
    n = int(seconds * SR)
    ir = _rng("room", seconds).normal(0, 1, n) * np.exp(-np.linspace(0, 7, n))
    ir[0] = 0
    return ir / np.sqrt(np.sum(ir ** 2))


def reverb(y, seconds=2.2, wet=0.35):
    ir = _room(seconds)
    n = len(ir)
    size = 1 << int(np.ceil(np.log2(len(y) + n)))
    wetsig = np.fft.irfft(np.fft.rfft(y, size) * np.fft.rfft(ir, size), size)[: len(y) + n]
    out = np.zeros(len(y) + n)
    out[: len(y)] += y * (1 - wet)
    out += wetsig * wet * 0.6
    return out


def piano_note(freq, dur=4.0, vel=1.0):
    """Additive piano: 9 slightly stretched harmonics with per-harmonic decay, plus a hammer thump."""
    rng = _rng("piano", round(freq, 3), dur)
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
    k = int(0.012 * SR)
    y[:k] += rng.normal(0, 0.15, k) * np.linspace(1, 0, k)
    y *= np.minimum(1, t / 0.004)  # tiny attack
    return vel * normalize(y)


def sting(dur=5.0):
    """Low A-minor piano cluster with a sub-bass boom."""
    y = np.zeros(int(dur * SR))
    for n, v in [(33, 1.0), (40, 0.8), (45, 0.7), (48, 0.55), (52, 0.35)]:
        y += piano_note(midi(n), dur, v)
    t = t_axis(dur)
    y += 0.9 * np.sin(2 * np.pi * (48 - 18 * np.minimum(t, 1)) * t) * np.exp(-2.2 * t)
    return normalize(reverb(y, 2.8, 0.4))


def motif_bed(total):
    """The theme as a bed of `total` seconds (+ reverb tail): ostinato over a low drone."""
    y = np.zeros(int(total * SR) + SR * 4)
    t, i = 0.0, 0
    while t < total:
        n = THEME_NOTES[i % len(THEME_NOTES)]
        if (i // len(THEME_NOTES)) % 2 == 1 and i % len(THEME_NOTES) == 6:
            n = THEME_TURN
        note = piano_note(midi(n - 12), 2.2, 0.55 if i % 4 else 0.8)
        s = int(t * SR)
        y[s: s + len(note)] += note[: len(y) - s]
        t += THEME_STEP
        i += 1
    tt = t_axis(len(y) / SR)
    drone = 0.35 * np.sin(2 * np.pi * 55 * tt) + 0.2 * np.sin(2 * np.pi * 82.4 * tt + 1)
    drone *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * tt)
    return normalize(reverb(y, 2.4, 0.45)[: len(y)] + drone * 0.5)


def shutter():
    """Camera shutter: two filtered clicks and a flash-charge whine."""
    rng = _rng("shutter")
    t = t_axis(0.25)
    click1 = rng.normal(0, 1, len(t)) * np.exp(-t * 90)
    click2 = np.zeros_like(t)
    s = int(0.07 * SR)
    click2[s:] = rng.normal(0, 1, len(t) - s) * np.exp(-(t[s:] - t[s]) * 60)
    y = fft_band(click1 + 0.8 * click2, 900, 9000)
    y += 0.08 * np.sin(2 * np.pi * (2500 + 3000 * t) * t) * np.exp(-t * 12)
    return normalize(y)


def typewriter_click(i=0):
    """One typewriter key; `i` picks one of a fixed set of slightly different strikes."""
    rng = _rng("typewriter", i % 16)
    t = t_axis(0.06)
    y = rng.normal(0, 1, len(t)) * np.exp(-t * 180)
    y = fft_band(y, 1500, 8000) + 0.6 * np.sin(2 * np.pi * 180 * t) * np.exp(-t * 120)
    return normalize(y)


def typewriter_gain(i):
    """Per-key loudness jitter in dB, fixed per key index."""
    return float(_rng("typewriter-gain", i).uniform(-3, 2))


def carriage_ding():
    t = t_axis(1.2)
    return normalize(sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in [(2093, 3), (4186, 5), (6280, 8)]))


def chimes(dur):
    """Tubular wind chimes: random strikes of five pitches with inharmonic partials."""
    rng = _rng("chimes")
    y = np.zeros(int(dur * SR))
    freqs = [1318.5, 1568.0, 1760.0, 2093.0, 2349.3]
    tt = t_axis(2.5)
    t = 0.3
    while t < dur - 0.2:
        f = freqs[rng.integers(len(freqs))]
        note = sum(a * np.sin(2 * np.pi * f * m * tt) for m, a in [(1, 1), (2.76, 0.4), (5.4, 0.15)]) * np.exp(-tt * 1.6)
        s = int(t * SR)
        seg = note[: len(y) - s]
        y[s: s + len(seg)] += seg * rng.uniform(0.3, 0.8)
        t += rng.uniform(0.25, 1.4)
    return normalize(y)


def wind(dur):
    """Low band-passed noise with slow gusts."""
    y = fft_band(_rng("wind").normal(0, 1, int(dur * SR)), 80, 900)
    tt = t_axis(dur)
    y *= 0.55 + 0.45 * np.sin(2 * np.pi * 0.23 * tt) * np.sin(2 * np.pi * 0.11 * tt + 1)
    return normalize(y)


def crickets(dur):
    """Three crickets at different pitches and rates, plus a faint 60 Hz porch-light hum."""
    rng = _rng("crickets")
    y = np.zeros(int(dur * SR))
    tt = t_axis(0.12)
    for f0, rate, phase in [(4400, 3.1, 0.0), (4750, 2.4, 0.5), (5100, 3.7, 0.2)]:
        chirp = np.sin(2 * np.pi * f0 * tt) * (np.sin(2 * np.pi * 30 * tt) > 0) * np.hanning(len(tt))
        t = phase
        while t < dur:
            s = int(t * SR)
            seg = chirp[: len(y) - s]
            y[s: s + len(seg)] += seg * rng.uniform(0.3, 0.6)
            t += 1 / rate + rng.uniform(0, 0.05)
    tt = t_axis(dur)
    hum = 0.08 * np.sin(2 * np.pi * 60 * tt) + 0.04 * np.sin(2 * np.pi * 120 * tt)
    return normalize(y) + hum


def glitch():
    """Digital video glitch: a square-wave buzz in noise."""
    t = t_axis(0.18)
    y = np.sign(np.sin(2 * np.pi * 880 * t)) * 0.5 + _rng("glitch").normal(0, 0.6, len(t))
    return normalize(y * np.exp(-t * 18))
