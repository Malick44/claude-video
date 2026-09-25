"""Derive a night, lit-up Ray from the series library (no image generation needed).

  .venv/bin/python episodes/ep04_only_when_its_sunny/make_stills.py

shows/nobody-moves/stills/ray_night.webp is stills/ray.webp (Ray under grey skies) turned to night
and relit from inside, as if his solar light were on: a cool night grade over the whole frame, the
porch lantern kept, and a soft green glow on Ray with a brighter spot on his solar panel. It is the
fallback for his testimony until a generated `ray_lit` still exists (the prompt is in episode.py's
STILLS). It goes in the series library because later episodes will replay Ray's testimony.
Deterministic; re-run it if ray.webp changes.
"""
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "stills", "ray.webp")
OUT = os.path.join(HERE, "..", "..", "stills", "ray_night.webp")

BODY = (0.31, 0.60, 0.15)     # Ray's body in ray.webp: center (fractions) and glow radius (fraction of width)
PANEL = (0.245, 0.54, 0.05)   # the solar panel on his back
EYE = (0.43, 0.514, 0.018)


def blob(W, H, cx, cy, r):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return np.exp(-(((xx - cx * W) ** 2 + (yy - cy * H) ** 2) / (2 * (r * W) ** 2)))[..., None]


def main():
    im = Image.open(SRC).convert("RGB")
    orig = np.asarray(im, dtype=np.float32)
    H, W, _ = orig.shape
    night = orig * 0.24 * np.array([0.78, 0.92, 1.22], dtype=np.float32)       # cool, dark
    lum = orig.mean(axis=2, keepdims=True)
    practical = np.clip((lum - 175) / 55, 0, 1)                                   # keep the porch lantern lit
    night = night * (1 - practical) + orig * practical
    body = blob(W, H, *BODY) * 0.95
    relit = orig * np.array([0.95, 1.18, 0.88], dtype=np.float32) * 1.1           # his own light, a little green
    out = night * (1 - body) + relit * body
    out += blob(W, H, *PANEL) * np.array([120, 200, 140], dtype=np.float32)       # the panel glows
    out += blob(W, H, *EYE) * np.array([90, 150, 100], dtype=np.float32)
    out += np.random.default_rng(4).normal(0, 1.2, out.shape[:2] + (1,))         # matching grain
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT, quality=92)
    print("wrote", os.path.relpath(OUT, os.path.join(HERE, "..", "..")))


if __name__ == "__main__":
    main()
