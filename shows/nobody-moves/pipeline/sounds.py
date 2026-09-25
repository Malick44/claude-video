"""The show's sound library: a cinematic score and sound effects, synthesized in code (no samples).

48 kHz stereo. The palette is the trailer toolkit: a piano ostinato (the show's signature) over
a detuned string pad, a heartbeat pulse and a high shimmer that come in as tension builds;
braams (low brass-like blasts), impacts (sub drop + a punchy mid body that phone speakers can
play + a transient crack), risers that sweep into each hit, and whooshes on cuts. Everything
sits in one shared stereo hall.

Every generator is deterministic: it seeds its own random stream, so a sound comes out
identical in every episode no matter what else the episode contains. build_audio.py mixes
these (and decides the dynamics from the timeline); sound_kit.py exports them as WAVs.
"""
import functools
import hashlib

import numpy as np

SR = 48000

# Mix levels (dB gain) shared by every episode, so the show always sounds balanced the same way.
# The master is loudness-normalized afterwards, so these are relative.
LEVELS = {
    "bed": -17,          # theme layers under the whole episode (ducked under dialogue)
    "sting": -4,         # title: braam + impact + piano cluster
    "sting_end": -4,     # end card
    "sting_soft": -11,   # low swell under the episode's big question
    "riser": -13,        # sweeps into the title and the cliffhanger reveal
    "impact": -7,        # evidence flash, cliffhanger reveal
    "braam": -9,         # cliffhanger reveal
    "whoosh": -17,       # into each question card
    "shutter": -9,       # evidence-photo flash
    "typewriter": -20,   # interviewer question cards (per key)
    "ding": -26,         # typewriter bell
    "wind": -22,         # anonymous-source ambience
    "chimes": -22,
    "crickets": -25,     # doorbell-cam night ambience
    "glitch": -22,       # doorbell-cam frame flicker
    "jump": -14,         # doorbell-cam jump cut (glitch + sub hit)
}

# The theme: a sparse A-minor ostinato. The D# (flat five) is the unease.
THEME_NOTES = [69, 72, 76, 72, 69, 72, 75, 72]   # MIDI note numbers, played an octave lower
THEME_TURN = 74                                  # replaces the D# on every other bar
THEME_STEP = 0.62                                # seconds per note
# String pad under it: i - VI - iv - V in A minor, two ostinato bars per chord.
PAD_CHORDS = [(45, 48, 52, 57), (41, 45, 48, 53), (50, 53, 57, 62), (40, 44, 47, 52)]


# ---------------------------------------------------------------- helpers

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


def stereo(y):
    """Mono -> stereo (n, 2); stereo passes through."""
    return y if y.ndim == 2 else np.stack([y, y], axis=1)


def pan(y, p):
    """Equal-power pan of a mono signal, p in [-1 (left), 1 (right)]."""
    a = (p + 1) * np.pi / 4
    return np.stack([y * np.cos(a), y * np.sin(a)], axis=1) * np.sqrt(2)


def _filter(y, response):
    """Zero-phase FFT filter; `response(freqs)` gives the gain per frequency."""
    n = len(y)
    size = 1 << int(np.ceil(np.log2(n)))
    f = np.fft.rfftfreq(size, 1 / SR)
    return np.fft.irfft(np.fft.rfft(y, size) * response(f), size)[:n]


def lowpass(y, fc, order=2):
    return _filter(y, lambda f: 1 / np.sqrt(1 + (f / fc) ** (2 * order)))


def highpass(y, fc, order=2):
    return _filter(y, lambda f: 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * order)))


def bandpass(y, lo, hi):
    return highpass(lowpass(y, hi, 3), lo, 3)


def saw(freq, t, phase=0.0):
    return 2 * np.mod(freq * t + phase, 1.0) - 1


def softclip(y, drive=2.0):
    return np.tanh(drive * y) / np.tanh(drive)


def sweep_noise(dur, f0, f1, width=0.6, curve=1.0, seed="sweep"):
    """Noise through a band whose center glides from f0 to f1 (STFT band mask, log spaced)."""
    n = int(dur * SR)
    noise = _rng(seed, dur, f0, f1).normal(0, 1, n + 4096)
    win, hop = 2048, 512
    w = np.hanning(win)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    out = np.zeros(len(noise))
    norm = np.zeros(len(noise))
    for start in range(0, len(noise) - win, hop):
        u = min(1.0, start / max(1, n)) ** curve
        fc = f0 * (f1 / f0) ** u
        mask = np.exp(-0.5 * (np.log2(np.maximum(freqs, 1) / fc) / width) ** 2)
        seg = np.fft.irfft(np.fft.rfft(noise[start:start + win] * w) * mask, win)
        out[start:start + win] += seg * w
        norm[start:start + win] += w ** 2
    return out[:n] / np.maximum(norm[:n], 1e-3)


# ---------------------------------------------------------------- the room

@functools.lru_cache(maxsize=None)
def _hall(seconds, side):
    """One channel of the show's hall: decaying noise, darker as it decays."""
    n = int(seconds * SR)
    rng = _rng("hall", seconds, side)
    ir = rng.normal(0, 1, n) * np.exp(-np.linspace(0, 6.5, n))
    ir = 0.5 * ir + 0.5 * lowpass(ir, 3500)            # damped highs
    ir[: int(0.012 * SR)] = 0                          # pre-delay
    return ir / np.sqrt(np.sum(ir ** 2))


def reverb(y, seconds=3.0, wet=0.35):
    """Stereo hall: dry signal centered, two decorrelated tails for width. Returns (n + tail, 2)."""
    dry = stereo(y)
    n = len(dry)
    m = int(seconds * SR)
    size = 1 << int(np.ceil(np.log2(n + m)))
    out = np.zeros((n + m, 2))
    out[:n] += dry * (1 - wet)
    mono = dry.mean(axis=1)
    spec = np.fft.rfft(mono, size)
    for ch in (0, 1):
        tail = np.fft.irfft(spec * np.fft.rfft(_hall(seconds, ch), size), size)[: n + m]
        out[:, ch] += tail * wet * 0.7
    return out


# ---------------------------------------------------------------- instruments

@functools.lru_cache(maxsize=None)
def piano_note(freq, dur=4.0, vel=1.0):
    """Additive piano: 12 slightly stretched harmonics with per-harmonic decay, plus a hammer thump."""
    rng = _rng("piano", round(freq, 3), dur)
    t = t_axis(dur)
    y = np.zeros_like(t)
    B = 0.0004  # inharmonicity
    for n in range(1, 13):
        fn = n * freq * np.sqrt(1 + B * n * n)
        if fn > SR / 2 - 2000:
            break
        amp = (1.0 / n ** 1.15) * (1.15 if n == 2 else 1.0)
        decay = 1.0 + 0.5 * n + freq / 400
        y += amp * np.sin(2 * np.pi * fn * t + rng.uniform(0, 6.28)) * np.exp(-decay * t)
    k = int(0.012 * SR)
    y[:k] += rng.normal(0, 0.15, k) * np.linspace(1, 0, k)
    y *= np.minimum(1, t / 0.004)
    return vel * normalize(y)


def _ensemble(notes, t, cents=(-12, -5, 0, 6, 11), seed="ens"):
    """Detuned sawtooth section (strings/brass body) playing `notes` together."""
    rng = _rng(seed, tuple(notes), len(t))
    y = np.zeros_like(t)
    for n in notes:
        for c in cents:
            y += saw(midi(n) * 2 ** (c / 1200), t, rng.uniform())
    return y / (len(notes) * len(cents))


def string_pad(total, start_at=0.0):
    """The chord bed: i-VI-iv-V strings, two ostinato bars per chord, slow swells between chords."""
    bar = THEME_STEP * len(THEME_NOTES) * 2
    t = t_axis(total)
    y = np.zeros_like(t)
    k = 0
    pos = 0.0
    while pos < total:
        seg_len = min(bar + 1.5, total - pos)
        s0 = int(pos * SR)
        tt = t_axis(seg_len)
        chord = PAD_CHORDS[k % len(PAD_CHORDS)]
        voice = (_ensemble(chord, tt, seed=("pad", k))
                 + 0.4 * _ensemble((chord[0] - 12,), tt, (-4, 0, 5), ("cello", k))
                 + 0.3 * _ensemble(tuple(x + 12 for x in chord[1:]), tt, (-7, 0, 8), ("violins", k)))
        env = np.minimum(1, tt / 1.2) * np.minimum(1, np.maximum(0, (seg_len - tt) / 1.5))
        seg = (voice * env)[: len(y) - s0]   # int() rounding can leave one sample less room
        y[s0: s0 + len(seg)] += seg
        pos += bar
        k += 1
    y = highpass(lowpass(y, 2600, 2), 70, 1)
    y *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.09 * t)          # slow bowing swell
    return normalize(y)


def heartbeat(total, beat=THEME_STEP * 2):
    """Low 'lub-dub' pulse locked to the ostinato."""
    y = np.zeros(int(total * SR) + SR)
    tt = t_axis(0.35)
    thump = (np.sin(2 * np.pi * (70 - 25 * tt / 0.35) * tt) + 0.5 * np.sin(2 * np.pi * 140 * tt)) * np.exp(-tt * 14)
    pos = 0.0
    while pos < total:
        for off, g in ((0.0, 1.0), (0.22, 0.6)):
            s = int((pos + off) * SR)
            y[s: s + len(tt)] += thump[: len(y) - s] * g
        pos += beat
    return normalize(y[: int(total * SR)])


def shimmer(total):
    """High string tremolo on A and E, for the last stretch before the reveal."""
    t = t_axis(total)
    y = sum(np.sin(2 * np.pi * midi(n) * t + i) for i, n in enumerate((81, 88, 93)))
    y *= 0.55 + 0.45 * np.sin(2 * np.pi * 7.5 * t)
    return normalize(highpass(y, 600))


def theme_layers(total):
    """The score as separate stereo layers, so build_audio can shape intensity per episode."""
    piano = np.zeros(int(total * SR) + SR * 4)
    t, i = 0.0, 0
    while t < total:
        n = THEME_NOTES[i % len(THEME_NOTES)]
        if (i // len(THEME_NOTES)) % 2 == 1 and i % len(THEME_NOTES) == 6:
            n = THEME_TURN
        note = piano_note(midi(n - 12), 2.2, 0.55 if i % 4 else 0.8)
        s = int(t * SR)
        piano[s: s + len(note)] += note[: len(piano) - s]
        t += THEME_STEP
        i += 1
    tt = t_axis(len(piano) / SR)
    drone = 0.35 * np.sin(2 * np.pi * 55 * tt) + 0.2 * np.sin(2 * np.pi * 82.4 * tt + 1)
    drone *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * tt)
    n = int(total * SR)

    def fit(y):
        y = stereo(y)[:n]
        return np.pad(y, ((0, n - len(y)), (0, 0)))

    return {
        "piano": fit(normalize(reverb(piano, 3.2, 0.42)[: len(piano)])),
        "pad": fit(normalize(reverb(string_pad(total), 3.2, 0.45))),
        "drone": fit(normalize(drone) * 0.6),
        "pulse": fit(heartbeat(total)),
        "shimmer": fit(normalize(reverb(shimmer(total), 3.2, 0.55))),
    }


def motif_bed(total, intensity=0.6):
    """The theme mixed down at a fixed intensity (for the sound kit and simple uses)."""
    L = theme_layers(total)
    y = L["piano"] * 0.9 + L["pad"] * (0.45 + 0.45 * intensity) + L["drone"] * 0.5
    y += L["pulse"] * 0.6 * max(0.0, intensity - 0.5) * 2 + L["shimmer"] * 0.35 * max(0.0, intensity - 0.75) * 4
    return normalize(y)


# ---------------------------------------------------------------- trailer hits

def impact(dur=3.5):
    """Cinematic hit: sub drop + punchy mid body (audible on phones) + transient crack, in the hall."""
    rng = _rng("impact")
    t = t_axis(dur)
    sub = np.sin(2 * np.pi * np.cumsum(30 + 45 * np.exp(-t * 4)) / SR) * np.exp(-t * 3.2)
    body = np.sin(2 * np.pi * np.cumsum(75 + 60 * np.exp(-t * 18)) / SR) * np.exp(-t * 7)
    body += 0.45 * np.sin(2 * np.pi * 180 * t) * np.exp(-t * 12)
    k = int(0.012 * SR)
    crack = np.zeros_like(t)
    crack[:k] = bandpass(rng.normal(0, 1, k), 1000, 7000) * np.linspace(1, 0, k) ** 2
    boom = bandpass(rng.normal(0, 1, len(t)), 250, 1600) * np.exp(-t * 5)
    slam = (np.sin(2 * np.pi * 220 * t) + 0.6 * np.sin(2 * np.pi * 330 * t + 1)) * np.exp(-t * 18)
    low = 0.7 * sub + 0.8 * body
    # the low end's overtones, so phone speakers (which can't play < ~250 Hz) still feel the hit
    harmonics = highpass(np.tanh(6 * normalize(low)), 220, 2)
    y = softclip(low + 0.7 * normalize(crack) + 1.3 * normalize(boom) + 0.9 * slam + 1.1 * harmonics, 1.6)
    return normalize(reverb(y, 3.5, 0.3))


def braam(dur=3.2, root=33):
    """Low brass-like blast: detuned saw power chord, filter opening on the attack, saturated."""
    t = t_axis(dur)
    y = _ensemble((root, root + 7, root + 12, root + 19, root + 24), t, (-15, -6, 0, 7, 14), "braam")
    env = np.minimum(1, t / 0.12) * np.exp(-np.maximum(0, t - 0.4) * 1.1)
    bright = lowpass(y, 3400, 2)
    dark = lowpass(y, 320, 2)
    open_ = np.minimum(1, t / 0.25) * np.exp(-np.maximum(0, t - 0.3) * 2.0)
    y = softclip((dark * (1 - open_) + bright * open_) * env * 2.2, 2.5)
    y += 0.7 * highpass(np.tanh(5 * normalize(y)), 250, 2)       # phone-speaker presence
    return normalize(reverb(y, 3.5, 0.3))


def riser(dur=2.0):
    """Noise sweep + rising tones + accelerating tremolo, peaking at the end (lands on a hit)."""
    t = t_axis(dur)
    noise = sweep_noise(dur, 250, 7000, width=0.5, curve=1.6, seed="riser")
    f = 180 * 2 ** (2.2 * (t / dur) ** 1.5)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.6 * np.sin(2 * np.pi * np.cumsum(f * 1.498) / SR)
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(4 + 22 * (t / dur) ** 2) / SR)
    env = (t / dur) ** 2.2
    y = (0.8 * normalize(noise) + 0.5 * tone * trem) * env
    y[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
    return normalize(reverb(y, 1.2, 0.2)[: len(t)])


def whoosh(dur=0.9):
    """A swell that passes from left to right: noise band up then down."""
    t = t_axis(dur)
    up = sweep_noise(dur, 300, 3200, width=0.45, seed="whoosh")
    env = np.sin(np.pi * np.minimum(1, t / dur)) ** 2
    pos = np.clip(2 * t / dur - 1, -1, 1)
    a = (pos + 1) * np.pi / 4
    y = normalize(up) * env
    return normalize(np.stack([y * np.cos(a), y * np.sin(a)], axis=1))


def sting(dur=5.0):
    """Title/end sting: braam + impact + the low A-minor piano cluster."""
    y = np.zeros(int(dur * SR))
    for n, v in [(33, 1.0), (40, 0.8), (45, 0.7), (48, 0.55), (52, 0.35)]:
        y += piano_note(midi(n), dur, v)
    piano = reverb(y, 3.2, 0.4)
    out = np.zeros((max(len(piano), int(dur * SR) + SR * 4), 2))
    for part, g in ((piano, 0.7), (braam(min(dur, 3.2)), 0.8), (impact(3.5), 1.0)):
        out[: len(part)] += stereo(part) * g
    return normalize(out[: int((dur + 1.5) * SR)])


def swell(dur=4.0):
    """Soft sting: the A-minor string chord rising out of nothing, with a sub underneath."""
    t = t_axis(dur)
    pad = lowpass(_ensemble(PAD_CHORDS[0], t, seed="swell"), 1600)
    env = (np.minimum(1, t / (dur * 0.6))) ** 2 * np.minimum(1, (dur - t) / 0.8)
    sub = np.sin(2 * np.pi * 55 * t) * np.minimum(1, t / 1.5) * np.exp(-np.maximum(0, t - 2.5) * 1.5)
    return normalize(reverb(pad * env + 0.6 * sub, 3.0, 0.4))


# ---------------------------------------------------------------- foley + ambiences

def shutter():
    """Camera shutter: two filtered clicks and a flash-charge whine."""
    rng = _rng("shutter")
    t = t_axis(0.25)
    click1 = rng.normal(0, 1, len(t)) * np.exp(-t * 90)
    click2 = np.zeros_like(t)
    s = int(0.07 * SR)
    click2[s:] = rng.normal(0, 1, len(t) - s) * np.exp(-(t[s:] - t[s]) * 60)
    y = bandpass(click1 + 0.8 * click2, 900, 9000)
    y += 0.08 * np.sin(2 * np.pi * (2500 + 3000 * t) * t) * np.exp(-t * 12)
    return normalize(y)


def typewriter_click(i=0):
    """One typewriter key; `i` picks one of a fixed set of slightly different strikes."""
    rng = _rng("typewriter", i % 16)
    t = t_axis(0.06)
    y = rng.normal(0, 1, len(t)) * np.exp(-t * 180)
    y = bandpass(y, 1500, 8000) + 0.6 * np.sin(2 * np.pi * 180 * t) * np.exp(-t * 120)
    return normalize(y)


def typewriter_gain(i):
    """Per-key loudness jitter in dB, fixed per key index."""
    return float(_rng("typewriter-gain", i).uniform(-3, 2))


def carriage_ding():
    t = t_axis(1.2)
    return normalize(sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in [(2093, 3), (4186, 5), (6280, 8)]))


def chimes(dur):
    """Tubular wind chimes: random strikes of five pitches with inharmonic partials, spread in stereo."""
    rng = _rng("chimes")
    y = np.zeros((int(dur * SR), 2))
    freqs = [1318.5, 1568.0, 1760.0, 2093.0, 2349.3]
    tt = t_axis(2.5)
    t = 0.3
    while t < dur - 0.2:
        f = freqs[rng.integers(len(freqs))]
        note = sum(a * np.sin(2 * np.pi * f * m * tt) for m, a in [(1, 1), (2.76, 0.4), (5.4, 0.15)]) * np.exp(-tt * 1.6)
        s = int(t * SR)
        seg = pan(note, rng.uniform(-0.6, 0.6))[: len(y) - s]
        y[s: s + len(seg)] += seg * rng.uniform(0.3, 0.8)
        t += rng.uniform(0.25, 1.4)
    return normalize(reverb(y, 2.5, 0.3)[: len(y)])


def wind(dur):
    """Low band-passed noise with slow gusts, decorrelated left and right."""
    tt = t_axis(dur)
    gust = 0.55 + 0.45 * np.sin(2 * np.pi * 0.23 * tt) * np.sin(2 * np.pi * 0.11 * tt + 1)
    chans = [bandpass(_rng("wind", ch).normal(0, 1, len(tt)), 80, 900) * gust for ch in (0, 1)]
    return normalize(np.stack(chans, axis=1))


def crickets(dur):
    """Three crickets at different pitches, rates and positions, plus a faint porch-light hum."""
    rng = _rng("crickets")
    y = np.zeros((int(dur * SR), 2))
    tt = t_axis(0.12)
    for f0, rate, phase, p in [(4400, 3.1, 0.0, -0.7), (4750, 2.4, 0.5, 0.6), (5100, 3.7, 0.2, 0.1)]:
        chirp = pan(np.sin(2 * np.pi * f0 * tt) * (np.sin(2 * np.pi * 30 * tt) > 0) * np.hanning(len(tt)), p)
        t = phase
        while t < dur:
            s = int(t * SR)
            seg = chirp[: len(y) - s]
            y[s: s + len(seg)] += seg * rng.uniform(0.3, 0.6)
            t += 1 / rate + rng.uniform(0, 0.05)
    tt = t_axis(dur)
    hum = 0.08 * np.sin(2 * np.pi * 60 * tt) + 0.04 * np.sin(2 * np.pi * 120 * tt)
    return normalize(y) + stereo(hum)


def glitch():
    """Digital video glitch: a square-wave buzz in noise."""
    t = t_axis(0.18)
    y = np.sign(np.sin(2 * np.pi * 880 * t)) * 0.5 + _rng("glitch").normal(0, 0.6, len(t))
    return normalize(y * np.exp(-t * 18))


def jump():
    """Doorbell-cam jump cut: the glitch over a short sub hit."""
    t = t_axis(0.6)
    sub = np.sin(2 * np.pi * np.cumsum(90 * np.exp(-t * 6) + 35) / SR) * np.exp(-t * 7)
    y = np.zeros(len(t))
    g = glitch()
    y[: len(g)] += g
    return normalize(y + 0.8 * sub + 1.0 * highpass(np.tanh(5 * sub), 220, 2))
