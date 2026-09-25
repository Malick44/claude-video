"""Derive this episode's clue frame from the series library (no image generation needed).

  .venv/bin/python episodes/ep03_the_goose/make_stills.py

shows/nobody-moves/stills/yard_gone.webp is stills/yard_after.webp with Lorraine removed from the
porch step, so doorbell frames 427 -> 428 differ only by the missing goose. It goes in the series
library, not this episode's stills/, because every later frame of that night (428 on) shows the
empty step and later episodes replay it. It is a pixel edit of the same
photo, which keeps every other detail identical (two separately generated images never are).
The fill is a harmonic (smooth) inpaint plus matching grain: invisible at phone size in night
vision, a soft smudge if you zoom in. Deterministic; re-run it if yard_after changes.
"""
import os
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "stills", "yard_after.webp")
OUT = os.path.join(HERE, "..", "..", "stills", "yard_gone.webp")

# Lorraine in yard_after (fractions): body x 0.720-0.781, y 0.219-0.278; the porch post ends at x 0.7205
BOX = (0.7205, 0.215, 0.786, 0.281)
CHEST = (0.745, 0.255)
FEET = (0.7225, 0.266, 0.768, 0.281)
TAIL = (0.762, 0.244, 0.786, 0.264)


def goose_mask(lum, W, H):
    X = lambda f: int(round(f * W))  # noqa: E731
    Y = lambda f: int(round(f * H))  # noqa: E731
    x0, y0, x1, y1 = X(BOX[0]), Y(BOX[1]), X(BOX[2]), Y(BOX[3])
    bright = np.zeros((H, W), bool)
    bright[y0:y1, x0:x1] = lum[y0:y1, x0:x1] > 70
    # the goose is the bright blob connected to her chest (not the siding or the post)
    seed = (Y(CHEST[1]), X(CHEST[0]))
    m = np.zeros_like(bright)
    m[seed] = True
    q = deque([seed])
    while q:
        y, x = q.popleft()
        for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if bright[yy, xx] and not m[yy, xx]:
                m[yy, xx] = True
                q.append((yy, xx))
    m[Y(FEET[1]):Y(FEET[3]), X(FEET[0]):X(FEET[2])] = True
    tail = np.zeros_like(m)
    tail[Y(TAIL[1]):Y(TAIL[3]), X(TAIL[0]):X(TAIL[2])] = True
    m |= tail & (lum > 45)
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    m[:, :x0] = False
    return m, x0


def main():
    im = Image.open(SRC).convert("RGB")
    orig = np.asarray(im, dtype=np.float32)
    a = orig.copy()
    H, W, _ = a.shape
    m, post = goose_mask(a.mean(-1), W, H)

    ys, xs = np.nonzero(m)
    r0, r1, c0, c1 = ys.min() - 2, ys.max() + 3, xs.min() - 2, xs.max() + 3
    patch, mk = a[r0:r1, c0:c1].copy(), m[r0:r1, c0:c1]
    # harmonic fill; the porch post floats too, so its bright edge doesn't bleed into the step
    free = mk.copy()
    free[:, : post - c0] = True
    free[:2] = free[-2:] = False
    free[:, -2:] = False
    keep = patch.copy()
    patch[free] = patch[~free].mean(0)
    for _ in range(6000):
        avg = (np.roll(patch, 1, 0) + np.roll(patch, -1, 0) + np.roll(patch, 1, 1) + np.roll(patch, -1, 1)) / 4
        patch[free] = avg[free]
    patch[~mk] = keep[~mk]
    patch[mk] += np.random.default_rng(428).normal(0, 1.2, (int(mk.sum()), 1))  # the stills are clean
    a[r0:r1, c0:c1] = patch

    soft = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)),
                      dtype=np.float32)[..., None] / 255
    res = orig * (1 - soft) + a * soft
    res[m] = a[m]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    Image.fromarray(np.clip(res, 0, 255).astype(np.uint8)).save(OUT, quality=92)
    print(f"wrote {OUT} ({int(m.sum())} px filled)")


if __name__ == "__main__":
    main()
