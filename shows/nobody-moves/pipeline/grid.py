"""Overlay a coordinate grid on a still, in the same fractions episode.py uses.

  python pipeline/grid.py stills/yard_after.webp                       # whole image, 0.05 grid
  python pipeline/grid.py stills/yard_after.webp --box 0.55,0.55,0.8,0.7 --bright 2.5
  python pipeline/grid.py stills/yard_after.webp -o /tmp/grid.png

Use it to place Ken Burns centers, annot_arrow / annot_circles, polaroid crops and the
doorbell alter_box / alter_glow: read the x,y fractions straight off the labels.
Writes <image>_grid.png next to the build folder unless -o is given.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(os.path.dirname(HERE), "assets", "fonts", "PlexMono.ttf")


def main(argv):
    if not argv or argv[0].startswith("-"):
        sys.exit(__doc__)
    path = argv[0]
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
    x0, y0, x1, y1 = (float(v) for v in opt("--box", "0,0,1,1").split(","))
    bright = float(opt("--bright", "1"))
    im = Image.open(path).convert("RGB")
    W, H = im.size
    crop = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
    if bright != 1:
        crop = ImageEnhance.Brightness(crop).enhance(bright)
    scale = max(1.0, 900 / crop.width)
    crop = crop.resize((int(crop.width * scale), int(crop.height * scale)), Image.LANCZOS)
    span = max(x1 - x0, y1 - y0)
    step = float(opt("--step", "0.05" if span > 0.5 else "0.01" if span < 0.15 else "0.025"))
    d = ImageDraw.Draw(crop)
    try:
        f = ImageFont.truetype(FONT, 18)
    except OSError:
        f = ImageFont.load_default()

    def ticks(a, b):
        v = round((int(a / step) + 1) * step, 6)
        while v < b:
            yield v
            v = round(v + step, 6)

    for fx in ticks(x0, x1):
        X = (fx - x0) / (x1 - x0) * crop.width
        major = round(fx / (step * 2), 6).is_integer()
        d.line((X, 0, X, crop.height), fill=(255, 40, 40) if major else (255, 170, 170), width=1)
        d.text((X + 3, 3), f"{fx:g}", font=f, fill=(255, 255, 0), stroke_width=2, stroke_fill=(0, 0, 0))
    for fy in ticks(y0, y1):
        Y = (fy - y0) / (y1 - y0) * crop.height
        major = round(fy / (step * 2), 6).is_integer()
        d.line((0, Y, crop.width, Y), fill=(255, 40, 40) if major else (255, 170, 170), width=1)
        d.text((3, Y + 3), f"{fy:g}", font=f, fill=(255, 255, 0), stroke_width=2, stroke_fill=(0, 0, 0))
    out = opt("-o") or os.path.splitext(path)[0] + "_grid.png"
    crop.save(out)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1:])
