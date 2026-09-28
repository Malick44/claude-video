"""Build platform-ready account art for the NOBODY MOVES launch kit.

Run from anywhere:

    shows/nobody-moves/.venv/bin/python shows/nobody-moves/channel/make_launch_art.py

All images are deterministic compositions of this show's existing stills and title art.
The source files under channel/art/ are read, never overwritten. The resulting files
live under channel/{tiktok,facebook,youtube}/art/ so a setup agent can upload them
without cropping or guessing which variant belongs to which platform.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

import make_channel_art as C


HERE = Path(__file__).resolve().parent
SHOW = HERE.parent
STILLS = SHOW / "stills"
YELLOW = C.YELLOW
WHITE = (248, 246, 238)
INK = (8, 11, 15)


def still(name: str) -> Image.Image:
    path = STILLS / f"{name}.webp"
    if not path.exists():
        raise FileNotFoundError(path)
    return Image.open(path).convert("RGB")


def cover_crop(im: Image.Image, size: tuple[int, int], y: float = 0.5) -> Image.Image:
    return ImageOps.fit(im, size, method=Image.Resampling.LANCZOS, centering=(0.5, y))


def darken(im: Image.Image, top: float, bottom: float) -> Image.Image:
    """Smooth black veil that leaves the photographic texture intact."""
    a = np.asarray(im, dtype=np.float32)
    shade = np.linspace(top, bottom, im.height, dtype=np.float32)[:, None, None]
    return Image.fromarray(np.clip(a * (1 - shade), 0, 255).astype(np.uint8), "RGB")


def draw_center(d: ImageDraw.ImageDraw, text: str, y: int, *, size: int,
                max_width: int, canvas_width: int, color: tuple[int, int, int] = WHITE,
                font: str = "Oswald", weight: str | None = "Bold") -> int:
    while size > 15:
        f = C.R.font(font, size, weight)
        if d.textbbox((0, 0), text, font=f)[2] <= max_width:
            break
        size -= 2
    d.text((canvas_width / 2, y), text, font=f, fill=color, anchor="mm")
    return size


def photo_avatar() -> Image.Image:
    """A season-one character option: Lorraine reads clearly inside a circle at 48 px."""
    im = C.lorraine_avatar("lorraine").convert("RGB")
    d = ImageDraw.Draw(im)
    d.ellipse((17, 17, im.width - 18, im.height - 18), outline=YELLOW, width=28)
    return im


def vertical_cover_clue() -> Image.Image:
    # The solved object is visible but no arrow gives away the later frame change.
    im = cover_crop(still("yard_after"), (1080, 1920))
    im = darken(im, 0.47, 0.08)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((96, 322, 594, 392), radius=9, fill=YELLOW)
    d.text((345, 357), "EP 01  ·  FICTIONAL SERIES", font=C.R.font("PlexMono", 30),
           fill=INK, anchor="mm")
    draw_center(d, "WHO MOVED", 548, size=132, max_width=910, canvas_width=1080)
    draw_center(d, "THE FLAMINGO?", 706, size=112, max_width=920,
                canvas_width=1080, color=YELLOW)
    d.rectangle((110, 806, 970, 811), fill=YELLOW)
    d.text((540, 858), "NOBODY MOVES  /  THREE FEET", font=C.R.font("PlexMono", 31),
           fill=WHITE, anchor="mm")
    return im


def vertical_cover_witnesses() -> Image.Image:
    im = cover_crop(still("garrison"), (1080, 1920))
    im = darken(im, 0.58, 0.11)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((96, 326, 594, 396), radius=9, fill=YELLOW)
    d.text((345, 361), "EP 01  ·  FICTIONAL SERIES", font=C.R.font("PlexMono", 30),
           fill=INK, anchor="mm")
    draw_center(d, "THE GNOME", 544, size=138, max_width=910, canvas_width=1080)
    draw_center(d, "SAW NOTHING.", 701, size=132, max_width=920,
                canvas_width=1080, color=YELLOW)
    d.rectangle((110, 797, 970, 802), fill=YELLOW)
    d.text((540, 847), "NOBODY MOVES  /  THREE FEET", font=C.R.font("PlexMono", 31),
           fill=WHITE, anchor="mm")
    return im


def central_case_card(base: Image.Image, box: tuple[int, int, int, int],
                      heading: str, subline: str, case_line: str) -> Image.Image:
    """Place crucial copy in a crop-safe center card."""
    out = base.convert("RGBA")
    x0, y0, x1, y1 = box
    overlay = Image.new("RGBA", out.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    shadow_box = (x0 + 14, y0 + 16, x1 + 14, y1 + 16)
    d.rounded_rectangle(shadow_box, radius=13, fill=(0, 0, 0, 120))
    overlay = overlay.filter(ImageFilter.GaussianBlur(14))
    out.alpha_composite(overlay)
    d = ImageDraw.Draw(out)
    d.rounded_rectangle(box, radius=12, fill=(9, 11, 14, 246), outline=YELLOW, width=3)
    cx = (x0 + x1) // 2
    title_y = y0 + int((y1 - y0) * 0.32)
    f, _ = C.fit(heading, "Oswald", "Bold", x1 - x0 - 90,
                 int((y1 - y0) * 0.32), spacing=0.06)
    d.text((cx, title_y), heading, font=f, fill=WHITE, anchor="mm")
    rule_y = y0 + int((y1 - y0) * 0.54)
    d.rectangle((cx - 155, rule_y, cx + 155, rule_y + 5), fill=YELLOW)
    f, _ = C.fit(subline, "Inter", "SemiBold", x1 - x0 - 80,
                 int((y1 - y0) * 0.12))
    d.text((cx, y0 + int((y1 - y0) * 0.69)), subline,
           font=f, fill=WHITE, anchor="mm")
    f, _ = C.fit(case_line, "PlexMono", None, x1 - x0 - 80,
                 int((y1 - y0) * 0.082))
    d.text((cx, y0 + int((y1 - y0) * 0.86)), case_line,
           font=f, fill=YELLOW, anchor="mm")
    return out.convert("RGB")


def facebook_cover_clue() -> Image.Image:
    im = cover_crop(still("aerial"), (1640, 624), y=0.51)
    im = darken(im, 0.46, 0.48)
    return central_case_card(im, (366, 99, 1274, 528),
                             "NOBODY MOVES", "WHO MOVED THE FLAMINGO?",
                             "FICTIONAL CASE FILE 01  ·  7 BIRCHWOOD COURT")


def facebook_cover_witnesses() -> Image.Image:
    w, h = 1640, 624
    cork, _ = C.wide_cork(w, h, w / 2, h / 2)
    out = cork.copy()
    # Witness portraits live outside the mobile crop; the title card remains centered.
    for key, box in (("garrison", (0, 0, 420, h)), ("lorraine", (1220, 0, w, h))):
        portrait = cover_crop(still(key), (box[2] - box[0], h), y=0.50)
        out.paste(darken(portrait, 0.22, 0.30), box[:2])
    return central_case_card(out, (420, 98, 1220, 527),
                             "NOBODY MOVES", "EVERY WITNESS IS A LAWN ORNAMENT.",
                             "FICTIONAL TRUE-CRIME PARODY  ·  SEASON 01")


def youtube_banner_clue() -> Image.Image:
    w, h = 2560, 1440
    im = cover_crop(still("aerial"), (w, h), y=0.51)
    im = darken(im, 0.54, 0.54)
    # The middle 1546 x 423 band is visible on phones. Keep every word there.
    return central_case_card(im, (610, 542, 1950, 918),
                             "NOBODY MOVES", "WHO MOVED THE FLAMINGO?",
                             "FICTIONAL TRUE-CRIME PARODY  ·  CASE FILE 01")


def save_jpeg(im: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "JPEG", quality=93, subsampling=0, optimize=True)


def preview_sheet(dirs: dict[str, Path]) -> None:
    """Small proof sheet; intentionally kept out of upload folders."""
    sheet = Image.new("RGB", (1600, 1480), (16, 19, 23))
    d = ImageDraw.Draw(sheet)
    big = C.R.font("Oswald", 52, "Bold")
    small = C.R.font("PlexMono", 23)

    def label(s: str, x: int, y: int) -> None:
        d.text((x, y), s, font=small, fill=YELLOW)

    d.text((55, 28), "NOBODY MOVES  /  ACCOUNT ART", font=big, fill=WHITE)
    label("PROFILE  /  TITLE + CHARACTER", 55, 108)
    for i, name in enumerate(("avatar_title.png", "avatar_character.png")):
        with Image.open(dirs["tiktok"] / name) as im:
            sheet.paste(im.resize((190, 190), Image.Resampling.LANCZOS), (55 + i * 230, 150))

    label("EPISODE 01  /  VERTICAL COVER OPTIONS", 55, 390)
    for i, name in enumerate(("cover_clue.jpg", "cover_witnesses.jpg")):
        with Image.open(dirs["tiktok"] / name) as im:
            sheet.paste(im.resize((225, 400), Image.Resampling.LANCZOS), (55 + i * 260, 430))

    label("FACEBOOK PAGE COVER  /  1640 x 624", 630, 108)
    for i, name in enumerate(("cover_clue.jpg", "cover_witnesses.jpg")):
        with Image.open(dirs["facebook"] / name) as im:
            sheet.paste(im.resize((880, 335), Image.Resampling.LANCZOS), (630, 150 + i * 390))

    label("YOUTUBE BANNER  /  2560 x 1440", 55, 905)
    for i, name in enumerate(("banner_clue.jpg", "banner_witnesses.jpg")):
        with Image.open(dirs["youtube"] / name) as im:
            sheet.paste(im.resize((695, 391), Image.Resampling.LANCZOS), (55 + i * 750, 950))

    out = HERE / "launch_contact_sheet.jpg"
    save_jpeg(sheet, out)
    print(f"preview: {out}")


def main() -> None:
    dirs = {name: HERE / name / "art" for name in ("tiktok", "facebook", "youtube")}
    for dest in dirs.values():
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HERE / "art" / "avatar.png", dest / "avatar_title.png")
        photo_avatar().save(dest / "avatar_character.png", optimize=True)
    with Image.open(HERE / "art" / "avatar.png") as im:
        im.resize((300, 300), Image.Resampling.LANCZOS).save(
            dirs["youtube"] / "watermark.png", optimize=True)

    verticals = {
        "clue": vertical_cover_clue(),
        "witnesses": vertical_cover_witnesses(),
    }
    for name, im in verticals.items():
        save_jpeg(im, dirs["tiktok"] / f"cover_{name}.jpg")
        save_jpeg(im, dirs["youtube"] / f"cover_{name}.jpg")
        save_jpeg(im, dirs["facebook"] / f"reel_cover_{name}.jpg")

    save_jpeg(facebook_cover_clue(), dirs["facebook"] / "cover_clue.jpg")
    save_jpeg(facebook_cover_witnesses(), dirs["facebook"] / "cover_witnesses.jpg")
    save_jpeg(youtube_banner_clue(), dirs["youtube"] / "banner_clue.jpg")
    shutil.copyfile(HERE / "art" / "youtube_banner.jpg",
                    dirs["youtube"] / "banner_witnesses.jpg")

    for platform, dest in dirs.items():
        for path in sorted(dest.iterdir()):
            with Image.open(path) as im:
                print(f"{platform}/{path.name}: {im.width}x{im.height}, {path.stat().st_size / 1024:.0f} KiB")
    if "--preview" in sys.argv[1:]:
        preview_sheet(dirs)


if __name__ == "__main__":
    main()
