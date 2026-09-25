"""Derive this episode's two doorbell frames from the series library (no image generation needed).

  .venv/bin/python episodes/ep05_saturday/make_stills.py

Two pixel edits of the same photo, so every other detail stays identical (two separately generated
images never are). Both go in the series library, not this episode's stills/, because later
episodes replay this night:

  stills/yard_turned.webp  frames 431-435: stills/yard_gone.webp (Lorraine already gone) with
                           Garrison mirrored in place, the state Ep. 4's frame 431 revealed. It
                           carries that clue forward, so a later frame doesn't quietly un-turn him.
  stills/yard_back.webp    frame 436: yard_turned with Lorraine put back on the porch step, her
                           pixels copied straight out of stills/yard_after.webp. yard_gone was made
                           by inpainting her out of yard_after, so copying that region back restores
                           her exactly, down to the grain.

Frames 435 -> 436 then differ only by the goose. Deterministic; re-run it if yard_after,
yard_gone or GARRISON_BOX changes.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "..", "stills")
AFTER = os.path.join(LIB, "yard_after.webp")     # Lorraine on the step, Garrison facing Deb
GONE = os.path.join(LIB, "yard_gone.webp")       # frame 428: the step is empty (ep03/make_stills.py)
TURNED = os.path.join(LIB, "yard_turned.webp")
BACK = os.path.join(LIB, "yard_back.webp")

# Garrison in yard_gone, the same box Ep. 4 mirrors as alter_box on frame 431
GARRISON_BOX = (0.112, 0.486, 0.215, 0.612)
# Lorraine's footprint on the step in yard_after, from ep03/make_stills.py's BOX, with a margin so
# the copy brings her whole silhouette and the inpaint under her is fully covered
GOOSE_BOX = (0.7185, 0.211, 0.789, 0.285)


def px(box, W, H):
    x0, y0, x1, y1 = box
    return int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)


def turn_around(im, box):
    """Mirror a region in place, the way render.py's alter_box does, so the still matches the
    frame Ep. 4 showed: a rounded, feathered paste with no hard seam."""
    b = px(box, im.width, im.height)
    region = im.crop(b).transpose(Image.FLIP_LEFT_RIGHT)
    mask = Image.new("L", region.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((6, 4, region.width - 6, region.height - 4), radius=18, fill=255)
    im.paste(region, b[:2], mask.filter(ImageFilter.GaussianBlur(4)))
    return im


def put_back(dst, src, box):
    """Copy Lorraine out of yard_after into the empty step, feathered at the edges only."""
    b = px(box, dst.width, dst.height)
    mask = Image.new("L", (b[2] - b[0], b[3] - b[1]), 0)
    ImageDraw.Draw(mask).rounded_rectangle((3, 3, b[2] - b[0] - 3, b[3] - b[1] - 3), radius=10, fill=255)
    dst.paste(src.crop(b), b[:2], mask.filter(ImageFilter.GaussianBlur(2.0)))
    return dst


def main():
    gone = Image.open(GONE).convert("RGB")
    after = Image.open(AFTER).convert("RGB")
    if gone.size != after.size:
        raise SystemExit(f"yard_gone {gone.size} and yard_after {after.size} must match")

    turned = turn_around(gone.copy(), GARRISON_BOX)
    turned.save(TURNED, quality=92)

    back = put_back(turned.copy(), after, GOOSE_BOX)
    back.save(BACK, quality=92)

    moved = int((np.asarray(back, int) != np.asarray(turned, int)).any(-1).sum())
    for p in (TURNED, BACK):
        print("wrote", os.path.relpath(p, os.path.join(HERE, "..", "..")))
    print(f"frames 435 -> 436 differ by {moved} px (the goose)")


if __name__ == "__main__":
    main()
