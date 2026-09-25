"""Derive this episode's stills from the series library (no image generation needed).

  .venv/bin/python episodes/ep05_saturday/make_stills.py

shows/nobody-moves/stills/yard_shadow.webp: doorbell frame 343 (03:10:00). It is yard_before with a
long, rounded shadow reaching across the lawn from the left edge, cast by something off-frame under
the street light. Everything else is identical, so frames 342 -> 343 differ only by the shadow. It
goes in the series library because Episode 6 replays it (the inflatable, timer set for 3:10 AM).

episodes/ep05_saturday/stills/mower_shadow.webp: the stand-in for the Mower reenactment until a
generated `mower` exists. It is holes (the lawn at dawn) with the long shadow of a push mower and
the one pushing it falling across the grass toward the camera, away from the low sun.

Both are soft-edged darkenings of the original pixels, so grass and grain stay real. Deterministic.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "..", "stills")


def shade(src, dst, shapes, blur, depth, tint=(0.92, 0.96, 1.08)):
    """Darken the union of `shapes` ([("ellipse"|"polygon", points in fractions), ...])."""
    im = Image.open(src).convert("RGB")
    W, H = im.size
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for kind, pts in shapes:
        px = [(x * W, y * H) for x, y in pts]
        if kind == "ellipse":
            d.ellipse([px[0], px[1]], fill=255)
        else:
            d.polygon(px, fill=255)
    m = np.asarray(mask.filter(ImageFilter.GaussianBlur(blur * W)), dtype=np.float32)[..., None] / 255
    a = np.asarray(im, dtype=np.float32)
    out = a * (1 - m * depth * np.array(tint, dtype=np.float32) / max(tint))
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst, quality=92)
    print("wrote", os.path.relpath(dst, os.path.join(HERE, "..", "..")))


def rotated_ellipse(cx, cy, rx, ry, angle, n=40):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ca, sa = np.cos(angle), np.sin(angle)
    return [(cx + rx * np.cos(u) * ca - ry * np.sin(u) * sa, cy + rx * np.cos(u) * sa + ry * np.sin(u) * ca) for u in t]


def main():
    # frame 343: a snowman-shaped shadow (body, then head) stretched from the left edge toward Deb
    ang = np.arctan2(0.10, 0.40)                      # down and to the right, away from the street light
    shadow = [("polygon", rotated_ellipse(0.06, 0.365, 0.16, 0.045, ang)),     # body
              ("polygon", rotated_ellipse(0.265, 0.418, 0.085, 0.030, ang)),   # head
              ("polygon", [(-0.05, 0.33), (0.02, 0.33), (0.02, 0.40), (-0.05, 0.40)])]  # base, off the edge
    shade(os.path.join(LIB, "yard_before.webp"), os.path.join(LIB, "yard_shadow.webp"), shadow, 0.012, 0.55)

    # the Mower: deck, handle, and the legs and body of whoever pushes it, all stretched toward the camera
    mower = [("polygon", [(0.28, 0.47), (0.44, 0.45), (0.50, 0.53), (0.33, 0.56)]),            # deck
             ("polygon", [(0.40, 0.53), (0.45, 0.52), (0.66, 0.74), (0.62, 0.76)]),            # handle, left bar
             ("polygon", [(0.46, 0.51), (0.50, 0.505), (0.72, 0.71), (0.68, 0.73)]),           # handle, right bar
             ("polygon", [(0.60, 0.74), (0.74, 0.69), (0.75, 0.715), (0.61, 0.765)]),          # crossbar
             ("polygon", [(0.63, 0.77), (0.68, 0.75), (0.86, 1.02), (0.78, 1.02)]),            # legs
             ("polygon", [(0.69, 0.74), (0.74, 0.72), (0.97, 1.02), (0.89, 1.02)]),
             ("polygon", [(0.60, 0.78), (0.78, 0.70), (1.05, 1.05), (0.70, 1.05)])]           # body, out of frame
    shade(os.path.join(LIB, "holes.webp"), os.path.join(HERE, "stills", "mower_shadow.webp"), mower, 0.008, 0.88)


if __name__ == "__main__":
    main()
