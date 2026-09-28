"""Grid covers for NOBODY MOVES: one 1080x1920 cover per episode and Confessional, for the profile grids.

  .venv/bin/python channel/make_covers.py                     # every episode -> channel/covers/<episode>.jpg
  .venv/bin/python channel/make_covers.py ep07_the_finale     # only these
  .venv/bin/python channel/make_covers.py --preview           # also channel/build/preview_grid.png

Each app crops a 9:16 cover differently: Instagram's grid to 3:4 (y 240-1680), TikTok's to 3:4 or a
square (y 420-1500) depending on the version, YouTube's Shorts shelf not at all. Everything that has
to read sits in that square, clear of the corners the apps draw on: the pinned badge (top left) and
the view count (bottom left). Episodes carry a yellow number tag; Confessionals are desaturated with
a typewriter label, so the numbered episodes stand out in the grid.

The background is the episode's entry in COVERS, or else its hook shot. See channel/CHANNEL.md.
"""
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "pipeline"))
import render as R  # noqa: E402  (fonts, stills, framing, grade, night vision)
from common import load_episode  # noqa: E402

R.STILLS_DIR = os.path.join(R.SHOW_DIR, "stills")
EPISODES = os.path.join(R.SHOW_DIR, "episodes")
OUT, BUILD = os.path.join(HERE, "covers"), os.path.join(HERE, "build")
W, H, YELLOW = R.W, R.H, R.YELLOW
SQUARE = (420, 1500)      # the part of the cover every grid shows

# Background per episode: still, framing (center x, center y, zoom, as in an episode's V()), and
# optional look ("night" for the doorbell cam, "anon" for the hidden-identity blur) and circle
# (x, y, radius as fractions of the still) drawn in the show's evidence yellow.
# The subject sits in the upper half of the square, above the title.
COVERS = {
    "ep01_three_feet": {"still": "yard_before", "view": (0.656, 0.562, 2.2), "look": "night",
                        "circle": (0.656, 0.511, 0.095)},
    "ep02_i_was_right_here": {"still": "lorraine", "view": (0.47, 0.47, 1.25)},
    "ep03_the_goose": {"still": "lorraine_bee", "view": (0.47, 0.47, 1.25)},
    "ep04_only_when_its_sunny": {"still": "ray_lit", "view": (0.37, 0.64, 1.6)},
    "ep05_saturday": {"still": "mower_shadow", "view": (0.55, 0.62, 1.05)},
    "ep06_the_inflatable": {"still": "snowman_flat", "view": (0.42, 0.76, 2.1)},
    "ep07_the_finale": {"still": "deb", "view": (0.47, 0.53, 1.2)},
    "ep01c_deb_consent": {"still": "deb", "view": (0.40, 0.44, 2.0)},
    "ep02c_chime_anonymous": {"still": "chime", "view": (0.61, 0.40, 1.3)},
    "ep04c_ray_hat": {"still": "ray_sun", "view": (0.33, 0.62, 2.0)},     # the sunset his joke is about
    "ep04c_basin_frog": {"still": "basin_counsel", "view": (0.60, 0.50, 1.35)},
    "ep05c_garrison_doorbell": {"still": "garrison", "view": (0.46, 0.50, 1.4)},
    "ep05c_lorraine_changed": {"still": "lorraine_fitting", "view": (0.47, 0.47, 1.25)},
}


def parse(ep):
    """("episode", "1", "THREE FEET") or ("confessional", None, "DEB") from the episode's title card line."""
    m = re.match(r"EPISODE (\d+): (.+)", ep.EPISODE)
    if m:
        return "episode", m.group(1), m.group(2)
    m = re.match(r"CONFESSIONAL: (.+)", ep.EPISODE)
    if m:
        return "confessional", None, m.group(1)
    sys.exit(f"{ep.SLUG}: can't read EPISODE {ep.EPISODE!r}")


def spec_for(ep):
    if ep.SLUG in COVERS:
        return COVERS[ep.SLUG]
    hook = ep.SHOTS[0]
    v = next((v for v in hook["views"] if R.still_path(v["img"])), hook["views"][-1])
    return {"still": v["img"], "view": v["kb"][0], "look": v.get("look")}


def fit_lines(text, max_w, size, min_size, max_lines=2):
    """Largest Oswald size that sets `text` in at most max_lines lines of max_w px."""
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while True:
        f = R.font("Oswald", size, "Bold")
        lines = R.wrap(d, text, f, max_w)
        if (len(lines) <= max_lines and all(d.textlength(ln, font=f) <= max_w for ln in lines)) or size <= min_size:
            return f, lines
        size -= 4


def background(spec):
    look = spec.get("look")
    src = R.source(spec["still"], look if look in ("anon", "longlens") else None)   # an episode look
    view = tuple(spec["view"])
    frame, to_screen, scale = R.kb_view(src, (view, view), 0)
    if look == "night":
        frame = R.night_vision(frame)
    if spec.get("circle"):
        cx, cy, r = spec["circle"]
        x, y = to_screen(cx, cy)
        rr = r * scale
        d = ImageDraw.Draw(frame)
        d.ellipse((x - rr, y - rr * 0.9, x + rr, y + rr * 0.9), outline=YELLOW, width=12)
    return frame


def shade(frame, confessional):
    a = np.asarray(frame, dtype=np.float32)
    if confessional:
        lum = a.mean(axis=2, keepdims=True)
        a = (0.4 * a + 0.6 * lum) * np.array([0.9, 0.95, 1.05])
    ys = np.arange(H, dtype=np.float32)[:, None, None]
    bottom = np.clip((ys - 860) / 560, 0, 1) ** 1.2 * 0.78        # dark under the title
    top = np.clip((620 - ys) / 620, 0, 1) * 0.45                     # and a little under the wordmark
    a = a * (1 - np.maximum(bottom, top))
    return R.grade(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), 0, grain=5)


def shadowed(frame, draw_fn, blur=10, strength=0.85):
    """Run draw_fn on a transparent layer, then composite it over a soft dark copy of itself."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.putalpha(layer.split()[3].point(lambda v: int(v * strength)))
    frame.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(blur)), (0, 6))
    frame.alpha_composite(layer)


def cover(ep):
    kind, number, title = parse(ep)
    spec = spec_for(ep)
    if not R.still_path(spec["still"]):
        print(f"  {ep.SLUG}: still {spec['still']!r} missing, using a placeholder")
    frame = shade(background(spec), kind == "confessional").convert("RGBA")

    def wordmark(d):
        f = R.font("Oswald", 46, "Bold")
        R.spaced_text(d, (W / 2, SQUARE[0] + 34), ep.TITLE, f, (255, 255, 255, 235), 7)
    shadowed(frame, wordmark, blur=6)

    tf, lines = fit_lines(title, 900, 176, 104)
    lh = int(tf.size * 1.08)
    title_bottom = 1352                 # clear of the view count in the square's bottom-left corner
    title_top = title_bottom - lh * len(lines)

    def text(d):
        if kind == "episode":
            label = f"EP. {number}"
            f = R.font("Oswald", 96, "Bold")
            tw = d.textlength(label, font=f)
            x0, y1 = W / 2 - tw / 2 - 30, title_top - 30
            d.rounded_rectangle((x0, y1 - 130, x0 + tw + 60, y1), radius=10, fill=YELLOW + (255,))
            d.text((W / 2, y1 - 65), label, font=f, fill=(14, 14, 16, 255), anchor="mm")
        else:
            d.text((W / 2, title_top - 58), "CONFESSIONAL", font=R.font("SpecialElite", 66),
                   fill=YELLOW + (255,), anchor="mm")
        for i, ln in enumerate(lines):
            d.text((W / 2, title_top + i * lh), ln, font=tf, fill=(255, 255, 255, 255), anchor="ma")
    shadowed(frame, text)
    return frame.convert("RGB")


# ---------------------------------------------------------------- preview

def grid_sheet(covers, pinned):
    """A 3-column profile grid at phone scale, newest first, the pinned episode first, cropped to 3:4."""
    order = [s for s in pinned if s in covers] + [s for s in reversed(list(covers)) if s not in pinned]
    tw, th, gap = 300, 400, 4
    rows = (len(order) + 2) // 3
    sheet = Image.new("RGB", (3 * tw + 2 * gap, rows * (th + gap)), (0, 0, 0))
    for i, slug in enumerate(order):
        tile = covers[slug].crop((0, 240, W, 1680)).resize((tw, th), Image.LANCZOS)
        x, y = (i % 3) * (tw + gap), (i // 3) * (th + gap)
        sheet.paste(tile, (x, y))
        d = ImageDraw.Draw(sheet)
        if slug in pinned:
            d.rounded_rectangle((x + 8, y + 8, x + 78, y + 34), radius=4, fill=(254, 44, 85))
            d.text((x + 43, y + 21), "Pinned", font=R.font("Inter", 16, "Bold"), fill=(255, 255, 255), anchor="mm")
        d.text((x + 10, y + th - 12), "▷ 12.3K", font=R.font("Inter", 18, "Bold"), fill=(255, 255, 255), anchor="ls")
    return sheet


def posting_order(slugs):
    """Episode 1, its Confessionals, Episode 2, ... (a Confessional's folder sorts after its episode)."""
    return sorted(slugs, key=lambda s: (s[:4], "c_" in s[:6], s))


def main(argv):
    names = [a for a in argv if not a.startswith("--")]
    slugs = names or [d for d in os.listdir(EPISODES) if os.path.exists(os.path.join(EPISODES, d, "episode.py"))]
    slugs = posting_order(slugs)
    os.makedirs(OUT, exist_ok=True)
    made = {}
    for slug in slugs:
        ep = load_episode(os.path.join(EPISODES, slug))
        made[slug] = cover(ep)
        made[slug].save(os.path.join(OUT, f"{slug}.jpg"), quality=90, optimize=True)
        print(f"  {slug}.jpg")
    print(f"wrote {len(made)} covers to {os.path.relpath(OUT)}")
    if "--preview" in argv:
        os.makedirs(BUILD, exist_ok=True)
        grid_sheet(made, pinned=[s for s in slugs if s.startswith("ep01_")]).save(os.path.join(BUILD, "preview_grid.png"))
        print("preview in", os.path.relpath(os.path.join(BUILD, "preview_grid.png")))


if __name__ == "__main__":
    main(sys.argv[1:])
