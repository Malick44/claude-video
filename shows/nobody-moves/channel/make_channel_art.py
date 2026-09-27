"""Channel art for NOBODY MOVES: the profile picture every platform shares, and the YouTube banner.

  .venv/bin/python channel/make_channel_art.py             # -> channel/art/
  .venv/bin/python channel/make_channel_art.py --preview   # also channel/build/: the art at the sizes the apps show it

Built from the series library (stills/) and the show's fonts, like the episodes. The profile picture
is the title, not a character, so it stays the same when a new season brings a new cast. A new
season changes BANNER_POLAROIDS and CASE_LINE and runs this again. See channel/CHANNEL.md.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "pipeline"))
import render as R  # noqa: E402  (fonts, stills, polaroid look, night vision)

R.STILLS_DIR = os.path.join(R.SHOW_DIR, "stills")
ART, BUILD = os.path.join(HERE, "art"), os.path.join(HERE, "build")
YELLOW, INK = R.YELLOW, (14, 14, 16)

# Profile picture: 1080 square, read by every app as a circle (TikTok's feed shows it at about 48 px).
AV = 1080

# YouTube banner: 2560x1440. Every device shows the middle 423 px band (y 508-931); phones only its
# middle 1546 px (x 507-2053), tablets 1855, computers the full width, TVs the whole image.
BW, BH = 2560, 1440
BAND = (508, 931)
PHONE_X = (507, 2053)

# Season 1's witnesses, left to right: (still, crop x0, y0, x1 as fractions, label, center x, rotation, look).
# look: None, or "flash" to lift a night still like an evidence photo. The two beside the case card
# are the ones a phone shows; the outer ones only show on bigger screens.
BANNER_POLAROIDS = [
    ("ray_lit", (0.18, 0.44, 0.78), "RAY", 150, 4, None),
    ("porch", (0.234, 0.466, 0.978), "MR. BASIN", 428, -3, None),
    ("garrison", (0.228, 0.335, 0.717), "GARRISON", 702, 3, None),
    ("yard_before", (0.555, 0.455, 0.765), "DEB (MOVED)", 1858, -3, "flash"),
    ("lorraine", (0.17, 0.27, 0.69), "LORRAINE", 2132, 4, None),
    ("chime", (0.52, 0.02, 0.94), "ANON.", 2410, -4, None),
]
CARD_W, CARD_H = 830, 318
CASE_LINE = "CASE FILE 01  ·  7 BIRCHWOOD COURT"
TAGLINE = "EVERY WITNESS IS A LAWN ORNAMENT."


def fit(text, name, weight, max_w, size, spacing=0.0):
    """Largest size (down from `size`) at which `text`, letter-spaced by spacing * size, fits in max_w."""
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while size > 10:
        f = R.font(name, size, weight)
        w = sum(d.textlength(ch, font=f) for ch in text) + spacing * size * (len(text) - 1)
        if w <= max_w:
            return f, size
        size -= 2
    return R.font(name, size, weight), size


def grain(im, amount, seed):
    a = np.asarray(im, dtype=np.float32)
    n = np.random.default_rng(seed).normal(0, amount, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- profile picture

def avatar(bg, ink, rule):
    """NOBODY / MOVES stacked, as on the title card. Everything sits well inside the circle crop."""
    im = Image.new("RGB", (AV, AV), bg)
    d = ImageDraw.Draw(im)
    f, size = fit("NOBODY", "Oswald", "Bold", 760, 320, spacing=0.04)
    top, bottom = d.textbbox((0, 0), "NOBODY", font=f)[1::2]   # the glyphs' own extent, not the line's
    gap = int((bottom - top) * 0.22)                             # from the rule to each word
    for word, y in (("NOBODY", AV / 2 - gap - (bottom - top)), ("MOVES", AV / 2 + gap)):
        R.spaced_text(d, (AV / 2, y - top), word, f, ink, 0.04 * size)
    d.rectangle((AV / 2 - 190, AV / 2 - 6, AV / 2 + 190, AV / 2 + 6), fill=rule)
    return grain(im, 3.0, 5)


def lorraine_avatar(key="lorraine"):
    """Season 1 option: Lorraine's close-up. Her outfit stills share one framing, so every outfit crops the same."""
    src = R.load_still(key)[0]
    s = int(0.52 * src.width)
    x0, y0 = int(0.17 * src.width), int(0.27 * src.height)
    return src.resize((AV, AV), Image.LANCZOS, box=(x0, y0, x0 + s, y0 + s))


# ---------------------------------------------------------------- YouTube banner

def wide_cork(w, h, lamp_x, lamp_y):
    """Cork under one desk lamp, falling off to near black at the edges (the board's look, widened)."""
    rng = np.random.default_rng(11)
    n1 = rng.normal(0, 1, (h // 6, w // 6)).astype(np.float32)
    n1 = np.asarray(Image.fromarray(((n1 * 30) + 128).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) - 128
    n2 = rng.normal(0, 1, (h, w)).astype(np.float32) * 16
    specks = (rng.random((h, w)) < 0.02).astype(np.uint8) * 255
    specks = np.asarray(Image.fromarray(specks).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    tex = np.array([168, 118, 70], np.float32) + (0.7 * n1 + n2)[..., None] * np.array([1.0, 0.8, 0.6], np.float32)
    tex -= specks[..., None] * np.array([80, 62, 44], np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    lamp = np.exp(-(((xx - lamp_x) / (0.62 * w)) ** 2 + ((yy - lamp_y) / (0.34 * w)) ** 2))
    return Image.fromarray(np.clip(tex * (0.10 + 0.95 * lamp)[..., None], 0, 255).astype(np.uint8)), lamp


def photo_card(key, crop, label, size, rot, look):
    if look != "flash":
        return R.polaroid(key, crop, label, size, rot)
    # a night still lifted like a flash evidence photo, on the same card
    src = R.load_still(key)[0]         # the original, not source()'s sharpened copy: a small crop shows it
    x0, y0, x1 = crop
    side, bx, by = int((x1 - x0) * src.width), int(x0 * src.width), int(y0 * src.height)
    tmp = src.crop((bx, by, bx + side, by + side)).resize((2 * size, 2 * size), Image.LANCZOS)
    a = np.asarray(tmp.filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float32) / 255
    a = np.clip((a / np.percentile(a, 99.5)) ** 0.62, 0, 1) * 255
    R._src[(f"flash_{key}", None)] = Image.fromarray(a.astype(np.uint8))
    return R.polaroid(f"flash_{key}", (0, 0, 1), label, size, rot)


def string(d, p0, p1, sag=22):
    """Red string between two pins, sagging a little in the middle."""
    pts = []
    for i in range(33):
        t = i / 32
        pts.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t + sag * 4 * t * (1 - t)))
    d.line(pts, fill=R.RED + (235,), width=5, joint="curve")


def pin(d, x, y):
    d.ellipse((x - 15, y - 15, x + 15, y + 15), fill=(190, 30, 30, 255))
    d.ellipse((x - 7, y - 9, x + 1, y - 1), fill=(255, 150, 150, 255))


def banner():
    cy = (BAND[0] + BAND[1]) / 2
    cork, lamp = wide_cork(BW, BH, BW / 2, cy)
    board = cork.convert("RGBA")
    layer = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    cx0, cy0 = int(BW / 2 - CARD_W / 2), int(cy - CARD_H / 2)
    left, right = [], []
    for key, crop, label, x, rot, look in BANNER_POLAROIDS:
        if not R.still_path(key):
            sys.exit(f"missing still: {key}")
        card = photo_card(key, crop, label, 236, rot, look)
        px, py = int(x - card.width / 2), int(cy - card.height / 2 + 4)
        shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
        shadow.putalpha(card.split()[3].point(lambda v: int(v * 0.6)))
        layer.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(12)), (px + 12, py + 16))
        layer.alpha_composite(card, (px, py))
        (left if x < BW / 2 else right).append((x, py + 26))

    # the case card: the title card's type on black, pinned at both top corners
    card = Image.new("RGBA", (CARD_W, CARD_H), (10, 10, 12, 255))
    dc = ImageDraw.Draw(card)
    f, size = fit("NOBODY MOVES", "Oswald", "Bold", CARD_W - 120, 130, spacing=0.08)
    top, bottom = dc.textbbox((0, 0), "NOBODY MOVES", font=f)[1::2]
    R.spaced_text(dc, (CARD_W / 2, 50 - top), "NOBODY MOVES", f, (255, 255, 255), 0.08 * size)
    ry = 50 + (bottom - top) + 28
    dc.rectangle((CARD_W / 2 - 130, ry, CARD_W / 2 + 130, ry + 4), fill=YELLOW)
    ft, st = fit(TAGLINE, "Inter", "SemiBold", CARD_W - 130, 34, spacing=0.12)
    R.spaced_text(dc, (CARD_W / 2, ry + 30), TAGLINE, ft, (232, 232, 232), 0.12 * st)
    fc, _ = fit(CASE_LINE, "PlexMono", None, CARD_W - 160, 26)
    dc.text((CARD_W / 2, CARD_H - 40), CASE_LINE, font=fc, fill=YELLOW, anchor="mm")
    shadow = Image.new("RGBA", card.size, (0, 0, 0, 170))
    layer.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)), (cx0 + 14, cy0 + 18))
    layer.alpha_composite(card, (cx0, cy0))

    # one string runs through every witness on each side and ends on the case card
    d = ImageDraw.Draw(layer)
    card_pins = [(cx0 + 30, cy0 + 26), (cx0 + CARD_W - 30, cy0 + 26)]
    chain = left + [card_pins[0]], [card_pins[1]] + right
    for ps in chain:
        for p0, p1 in zip(ps, ps[1:]):
            string(d, p0, p1)
    for p in left + right + card_pins:
        pin(d, *p)

    # everything pinned takes the lamp's falloff, except the card, which stays readable
    la = np.asarray(layer, dtype=np.float32)
    light = (0.30 + 0.75 * np.clip(lamp / lamp.max(), 0, 1))[..., None]
    inside = np.zeros((BH, BW, 1), np.float32)
    inside[cy0 + 40:cy0 + CARD_H, cx0:cx0 + CARD_W] = 1
    la[..., :3] *= light * (1 - inside) + inside
    board.alpha_composite(Image.fromarray(np.clip(la, 0, 255).astype(np.uint8), "RGBA"))
    return grain(board.convert("RGB"), 4.0, 7)


# ---------------------------------------------------------------- previews

def circle(im, size):
    im = im.resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), m.resize((size, size), Image.LANCZOS))
    return out


def avatar_sheet(options):
    """Each option in a circle at 180, 110 and 48 px, on a dark and a light app background."""
    sizes, row_h = (180, 110, 48), 230
    sheet = Image.new("RGB", (2 * 470, row_h * len(options) + 20), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    d.rectangle((470, 0, 940, sheet.height), fill=(255, 255, 255))
    for i, (name, im) in enumerate(options):
        y = 20 + i * row_h
        for col, fg in ((0, (200, 200, 200)), (470, (60, 60, 60))):
            x = col + 20
            for s in sizes:
                c = circle(im, s)
                sheet.paste(c, (x, y + (180 - s) // 2), c)
                x += s + 24
            d.text((col + 20, y + 190), name, font=R.font("PlexMono", 20), fill=fg)
    return sheet


def banner_sheet(im):
    """The banner with each device's visible area marked, and the phone crop at phone scale."""
    marked = im.copy()
    d = ImageDraw.Draw(marked)
    d.rectangle((0, BAND[0], BW - 1, BAND[1]), outline=(80, 200, 255), width=6)
    d.rectangle((PHONE_X[0], BAND[0], PHONE_X[1], BAND[1]), outline=(255, 60, 60), width=6)
    d.text((PHONE_X[0] + 10, BAND[0] - 40), "phone", font=R.font("PlexMono", 32), fill=(255, 60, 60))
    d.text((12, BAND[0] - 40), "computer", font=R.font("PlexMono", 32), fill=(80, 200, 255))
    d.text((12, 12), "TV: the whole image", font=R.font("PlexMono", 32), fill=(255, 255, 255))
    phone = im.crop((PHONE_X[0], BAND[0], PHONE_X[1], BAND[1])).resize((1170, 320), Image.LANCZOS)
    sheet = Image.new("RGB", (1280, 720 + 40 + 320), (0, 0, 0))
    sheet.paste(marked.resize((1280, 720), Image.LANCZOS), (0, 0))
    sheet.paste(phone, (55, 760))
    return sheet


def main(argv):
    os.makedirs(ART, exist_ok=True)
    dark = avatar((8, 8, 10), (255, 255, 255), YELLOW)
    yellow = avatar(YELLOW, INK, INK)
    yellow.save(os.path.join(ART, "avatar.png"))
    dark.save(os.path.join(ART, "avatar_dark.png"))
    b = banner()
    b.save(os.path.join(ART, "youtube_banner.jpg"), quality=92, optimize=True)
    print("wrote", ", ".join(sorted(os.listdir(ART))), "to", os.path.relpath(ART))
    if "--preview" in argv:
        os.makedirs(BUILD, exist_ok=True)
        options = [("avatar.png", yellow), ("avatar_dark.png", dark)]
        options += [(f"{k} (season 1 option)", lorraine_avatar(k)) for k in ("lorraine", "lorraine_bee")]
        avatar_sheet(options).save(os.path.join(BUILD, "preview_avatars.png"))
        banner_sheet(b).save(os.path.join(BUILD, "preview_banner.png"))
        print("previews in", os.path.relpath(BUILD))


if __name__ == "__main__":
    main(sys.argv[1:])
