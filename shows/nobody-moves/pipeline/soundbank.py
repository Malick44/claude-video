"""Resolve the show's named sounds: synthesized by default, or a stock asset per soundtrack.py.

Names: theme, sting, sting_end, sting_soft, shutter, typewriter, ding, wind, chimes,
crickets, glitch, jump. Looped names are looped (with a crossfade) or trimmed to fit.
"""
import sys

import numpy as np

import sounds as snd
import stock

SYNTH = {
    "theme": lambda sec, i: snd.motif_bed(sec),
    "sting": lambda sec, i: snd.sting(5.0),
    "sting_end": lambda sec, i: snd.sting(6.0),
    "sting_soft": lambda sec, i: snd.sting(4.0),
    "shutter": lambda sec, i: snd.shutter(),
    "typewriter": lambda sec, i: snd.typewriter_click(i),
    "ding": lambda sec, i: snd.carriage_ding(),
    "wind": lambda sec, i: snd.wind(sec),
    "chimes": lambda sec, i: snd.chimes(sec),
    "crickets": lambda sec, i: snd.crickets(sec),
    "glitch": lambda sec, i: snd.glitch(),
    "jump": lambda sec, i: snd.glitch(),
}
LOOPED = {"theme", "wind", "chimes", "crickets"}


def fit(y, seconds, xfade=1.0):
    """Loop `y` with crossfades (or trim it) to exactly `seconds`, with a short fade-out."""
    n = int(seconds * snd.SR)
    if len(y) >= n:
        out = y[:n].copy()
    else:
        x = min(int(xfade * snd.SR), len(y) // 4)
        out = np.zeros(n)
        piece = y.copy()
        if x:
            piece[-x:] *= np.linspace(1, 0, x)
        first = True
        pos = 0
        while pos < n:
            seg = piece.copy()
            if x and not first:
                seg[:x] *= np.linspace(0, 1, x)
            end = min(n, pos + len(seg))
            out[pos:end] += seg[: end - pos]
            pos += len(y) - x
            first = False
    k = min(int(0.3 * snd.SR), n // 4)
    if k:
        out[-k:] *= np.linspace(1, 0, k)
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
            self._decoded[path] = snd.normalize(stock.decode_audio(path))
        y = self._decoded[path]
        if name in LOOPED and seconds:
            y = fit(y, seconds)
        return y * 10 ** (spec.get("gain_db", 0) / 20)
