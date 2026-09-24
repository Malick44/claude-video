"""Resolve the show's named sounds: synthesized by default, or a stock asset per soundtrack.py.

Names: theme, sting, sting_end, sting_soft, riser, impact, braam, whoosh, shutter, typewriter,
ding, wind, chimes, crickets, glitch, jump. Looped names are looped (with a crossfade) or
trimmed to fit. Sounds come back as mono (n,) or stereo (n, 2) float arrays at sounds.SR.
"""
import sys

import numpy as np

import sounds as snd
import stock

SYNTH = {
    "theme": lambda sec, i: snd.motif_bed(sec),
    "sting": lambda sec, i: snd.sting(5.0),
    "sting_end": lambda sec, i: snd.sting(6.0),
    "sting_soft": lambda sec, i: snd.swell(4.0),
    "riser": lambda sec, i: snd.riser(sec or 2.0),
    "impact": lambda sec, i: snd.impact(),
    "braam": lambda sec, i: snd.braam(),
    "whoosh": lambda sec, i: snd.whoosh(),
    "shutter": lambda sec, i: snd.shutter(),
    "typewriter": lambda sec, i: snd.typewriter_click(i),
    "ding": lambda sec, i: snd.carriage_ding(),
    "wind": lambda sec, i: snd.wind(sec),
    "chimes": lambda sec, i: snd.chimes(sec),
    "crickets": lambda sec, i: snd.crickets(sec),
    "glitch": lambda sec, i: snd.glitch(),
    "jump": lambda sec, i: snd.jump(),
}
LOOPED = {"theme", "wind", "chimes", "crickets"}


def _ramp(a, b, k, like):
    r = np.linspace(a, b, k)
    return r[:, None] if like.ndim == 2 else r


def fit(y, seconds, xfade=1.0):
    """Loop `y` (mono or stereo) with crossfades, or trim it, to exactly `seconds`; short fade-out."""
    n = int(seconds * snd.SR)
    if len(y) >= n:
        out = y[:n].copy()
    else:
        x = min(int(xfade * snd.SR), len(y) // 4)
        out = np.zeros((n,) + y.shape[1:])
        piece = y.copy()
        if x:
            piece[-x:] *= _ramp(1, 0, x, y)
        first = True
        pos = 0
        while pos < n:
            seg = piece.copy()
            if x and not first:
                seg[:x] *= _ramp(0, 1, x, y)
            end = min(n, pos + len(seg))
            out[pos:end] += seg[: end - pos]
            pos += len(y) - x
            first = False
    k = min(int(0.3 * snd.SR), n // 4)
    if k:
        out[-k:] *= _ramp(1, 0, k, out)
    return out


class Bank:
    def __init__(self, sources, base_dirs):
        unknown = sorted(set(sources) - set(SYNTH))
        if unknown:
            sys.exit(f"unknown sound name(s) {unknown}; known: {', '.join(SYNTH)}")
        self.sources = sources
        self.base_dirs = base_dirs
        self.credits = {}
        self._decoded = {}

    def get(self, name, seconds=None, i=0):
        spec = self.sources.get(name)
        if not spec or spec == "synth":
            return SYNTH[name](seconds, i)
        path, credit = stock.fetch(spec, "audio", self.base_dirs)
        if credit:
            self.credits[path] = credit
        if path not in self._decoded:
            self._decoded[path] = snd.normalize(stock.decode_audio(path, snd.SR, channels=2))
        y = self._decoded[path]
        if name in LOOPED and seconds:
            y = fit(y, seconds)
        return y * 10 ** (spec.get("gain_db", 0) / 20)
