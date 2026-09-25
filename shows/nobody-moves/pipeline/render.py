"""Render an episode to a 1080x1920 TikTok MP4 from its stills + build/timeline.json.

  python pipeline/render.py episodes/<episode>                        # -> build/<episode>.mp4
  python pipeline/render.py episodes/<episode> --preview 1.0,9.5,20   # build/preview_*.png at those seconds
  python pipeline/render.py episodes/<episode> --contact              # one frame per shot -> build/contact.png

Run build_audio.py first. Stills are read from <episode>/stills/<key>.(png|jpg|webp);
a shot uses the first of its views whose still exists, else a labelled placeholder.
"""
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from common import CTA_DELAY, FONTS, SHOW_DIR, doorbell_clock, fmt_clock, load_episode

W, H, FPS = 1080, 1920, 30
YELLOW = (242, 194, 48)
RED = (208, 52, 44)

# set by init()
ep = BUILD = STILLS_DIR = None
SHOTS, TOTAL, CAPTIONS, CHUNKS = [], 0.0, [], []


def init(ep_dir):
    global ep, BUILD, STILLS_DIR, SHOTS, TOTAL, CAPTIONS, CHUNKS
    ep = load_episode(ep_dir)
    BUILD, STILLS_DIR = ep.BUILD, ep.STILLS_DIR
    tl_path = os.path.join(BUILD, "timeline.json")
    if not os.path.exists(tl_path):
        sys.exit(f"missing {tl_path} - run build_audio.py first")
    with open(tl_path) as f:
        tl = json.load(f)
    SHOTS, TOTAL, CAPTIONS = tl["shots"], tl["total"], tl["captions"]
    CHUNKS = caption_chunks()


# ---------------------------------------------------------------- helpers

_fonts = {}


def font(name, size, weight=None):
    key = (name, size, weight)
    if key not in _fonts:
        f = ImageFont.truetype(os.path.join(FONTS, f"{name}.ttf"), size)
        if weight:
            f.set_variation_by_name(weight)
        _fonts[key] = f
    return _fonts[key]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def spaced_text(draw, xy, text, fnt, fill, spacing, anchor_center=True, stroke=0, stroke_fill=None):
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x, y = xy
    if anchor_center:
        x -= total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        x += w + spacing
    return total


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def with_alpha(img, a):
    if a >= 0.999:
        return img
    r, g, b, al = img.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge("RGBA", (r, g, b, al))


# ---------------------------------------------------------------- sources

def placeholder(key):
    im = Image.new("RGB", (W, H))
    arr = np.linspace(40, 12, H)[:, None, None] * np.array([0.8, 0.9, 1.1])[None, None, :]
    im = Image.fromarray(np.broadcast_to(arr, (H, W, 3)).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.text((W / 2, H / 2 - 60), key.upper(), font=font("Oswald", 90, "Bold"), fill=(200, 200, 200), anchor="mm")
    d.text((W / 2, H / 2 + 40), "still pending", font=font("PlexMono", 30), fill=(150, 150, 150), anchor="mm")
    return im


def still_path(key):
    """The episode's own still, else the series library in <show>/stills/ (recurring sets and cast)."""
    for folder in (STILLS_DIR, os.path.join(SHOW_DIR, "stills")):
        for ext in ("png", "jpg", "jpeg", "webp"):
            p = os.path.join(folder, f"{key}.{ext}")
            if os.path.exists(p):
                return p
    return None


def load_still(key):
    p = still_path(key)
    if p:
        return Image.open(p).convert("RGB"), True
    return placeholder(key), False


def pick_view(shot):
    """First view whose still exists (optional upgrades listed first, user images as fallback)."""
    for v in shot["views"]:
        if still_path(v["img"]):
            return v
    return shot["views"][-1]


def apply_look(im, look):
    if not look:
        return im
    a = np.asarray(im, dtype=np.float32) / 255.0
    if look == "anon":
        # hidden-identity interview: soft focus, crushed and cold
        a = np.asarray(im.filter(ImageFilter.GaussianBlur(5)), dtype=np.float32) / 255.0
        a = a ** 1.7 * np.array([0.55, 0.68, 1.0]) * 1.1
    elif look == "longlens":
        # long-lens stakeout: slight softness, lifted blacks, a touch desaturated
        a = np.asarray(im.filter(ImageFilter.GaussianBlur(1.6)), dtype=np.float32) / 255.0
        lum = a.mean(axis=2, keepdims=True)
        a = 0.8 * a + 0.2 * lum
        a = 0.06 + 0.94 * a * 1.08
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))


_src = {}


def source(key, look=None):
    """Upscaled (2x output width) + lightly sharpened master for smooth Ken Burns moves."""
    if (key, look) not in _src:
        im, real = load_still(key)
        target_w = 2 * W
        im = im.resize((target_w, round(im.height * target_w / im.width)), Image.LANCZOS)
        if real and look != "anon":
            im = im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=45, threshold=2))
        _src[(key, look)] = apply_look(im, look)
    return _src[(key, look)]


def kb_view(src, kb, u):
    (cx0, cy0, z0), (cx1, cy1, z1) = kb
    e = u
    cx, cy = cx0 + (cx1 - cx0) * e, cy0 + (cy1 - cy0) * e
    z = z0 * (z1 / z0) ** e
    sw, sh = src.size
    base_w = min(sw, sh * W / H)
    base_h = base_w * H / W
    cw, ch = base_w / z, base_h / z
    x0 = clamp(cx * sw - cw / 2, 0, sw - cw)
    y0 = clamp(cy * sh - ch / 2, 0, sh - ch)
    frame = src.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))

    def to_screen(fx, fy):
        return ((fx * sw - x0) / cw * W, (fy * sh - y0) / ch * H)

    return frame, to_screen, W / cw * sw  # last: source-width in screen px (for radii)


# ---------------------------------------------------------------- grading

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.62)) ** 2)
VIGNETTE = np.clip(1.0 - 0.55 * np.clip(_r - 0.45, 0, None) ** 1.6, 0.35, 1.0)[..., None].astype(np.float32)
_rng = np.random.default_rng(3)
GRAIN = []
for _ in range(10):
    g = _rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    g = np.asarray(Image.fromarray(((g * 40) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), dtype=np.float32) - 128
    GRAIN.append((g / 40)[..., None])
SCANLINES = np.ones((H, 1, 1), np.float32)
SCANLINES[::3] = 0.82


def grade(img, fi, grain=6.0, vignette=True, extra=None):
    a = np.asarray(img, dtype=np.float32)
    if vignette:
        a = a * VIGNETTE
    if extra is not None:
        a = extra(a)
    a = a + GRAIN[fi % len(GRAIN)] * grain
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- overlays

GRADIENT = None


def bottom_gradient():
    global GRADIENT
    if GRADIENT is None:
        a = np.zeros((H, W), np.float32)
        ys = np.arange(H)
        a[:] = (np.clip((ys - 880) / (H - 880), 0, 1) ** 1.3 * 200)[:, None]
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        g.putalpha(Image.fromarray(a.astype(np.uint8)))
        GRADIENT = g
    return GRADIENT


CAP_SIZE, CAP_LH, CAP_STROKE, CAP_W, CAP_X, CAP_Y = 68, 82, 8, 840, 500, 1052   # x left of TikTok's buttons
CAP_MAX_LINES = 2          # keeps a caption clear of the name card at y 1262
CAP_GAP = 4                # px added to each space: words are drawn one by one


def cap_font():
    return font("Inter", CAP_SIZE, "ExtraBold")


SENTENCE_END = re.compile(r"[.?!]['\")]*$")
CLAUSE_END = re.compile(r"[,;:\u2014\u2013]['\")]*$")
ABBREV = re.compile(r"(No|Mr|Mrs|Ms|Dr|St)\.$")
FUNCTION_WORDS = set("a an the of to for and but or nor in on at with by from into onto that this "
                     "these those my your our their his her its is was were be been as than".split())


def ends_sentence(word):
    return bool(SENTENCE_END.search(word)) and not ABBREV.fullmatch(word)


def split_words(words, cap_start, cap_end, long_caption, fits):
    """Best split of one caption's timed words into chunks that each fit in two lines.
    Cheapest wins: every chunk costs 1; a cut costs 0 at a sentence end (a bonus in a long caption,
    as before), 0.3 at a comma, 1 mid-clause, and 2 after a word like "a" or "the" or inside a
    name; a fragment of one or two words cut off from its phrase, or a chunk on screen under 0.7 s,
    costs 2 more; a little extra evens out the lengths."""
    n = len(words)
    start = lambda i: cap_start if i == 0 else words[i][1]  # noqa: E731
    end = lambda j: cap_end if j == n else words[j][1]      # noqa: E731
    best, back = [0.0] + [float("inf")] * n, [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(j - 1, -1, -1):
            ws = [w[0] for w in words[i:j]]
            if not fits(ws) and j - i > 1:     # a single word always gets a chunk
                break
            cost = 1 + 0.3 * (len(" ".join(ws)) / 40) ** 2
            if j < n:
                cost += -1.2 if ends_sentence(ws[-1]) and long_caption else \
                    0 if ends_sentence(ws[-1]) else 0.3 if CLAUSE_END.search(ws[-1]) else \
                    2 if ws[-1].lower() in FUNCTION_WORDS else 1
                if ws[-1][:1].isupper() and words[j][0][:1].isupper() and not ends_sentence(ws[-1]):
                    cost += 1                  # don't split a name: "Birchwood / Court"
            phrase = lambda w: ends_sentence(w) or CLAUSE_END.search(w)  # noqa: E731
            if len(ws) <= 2 and not ((i == 0 or phrase(words[i - 1][0])) and (j == n or phrase(ws[-1]))):
                cost += 2
            if end(j) - start(i) < 0.7 and (i, j) != (0, n):
                cost += 2
            if best[i] + cost < best[j]:
                best[j], back[j] = best[i] + cost, i
    cuts, j = [], n
    while j:
        cuts.append((back[j], j))
        j = back[j]
    return [words[i:j] for i, j in reversed(cuts)]


def caption_chunks():
    """Timed caption chunks. With word timings (build_audio's "words"), each chunk is at most two
    lines, starts when its first word is spoken and highlights the current word. Older timelines
    fall back to splitting by sentence, timed by length."""
    out = []
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    fits = lambda ws: len(wrap(tmp, " ".join(ws), cap_font(), CAP_W)) <= CAP_MAX_LINES  # noqa: E731
    for c in CAPTIONS:
        words = c.get("words")
        if not words:
            out += legacy_chunks(c)
            continue
        groups = split_words(words, c["start"], c["end"], len(c["text"]) > 40, fits)
        for g, grp in enumerate(groups):
            start = c["start"] if g == 0 else grp[0][1]
            end = groups[g + 1][0][1] if g + 1 < len(groups) else c["end"]
            out.append(dict(c, start=start, end=end, text=" ".join(w[0] for w in grp),
                            words=[(w[0], w[1]) for w in grp]))
    return out


def legacy_chunks(c):
    """Split a multi-sentence caption into chunks timed by length (timelines without word timings)."""
    text = c["text"]
    parts = re.split(r"(?<!\bNo\.)(?<!\bMr\.)(?<=[.?!])\s+(?=[A-Z])", text)
    if len(text) <= 40 or len(parts) == 1:
        return [c]
    merged = []
    for p in parts:
        if merged and len(merged[-1]) < 18:
            merged[-1] += " " + p
        else:
            merged.append(p)
    total, t, out = sum(len(p) for p in merged), c["start"], []
    for p in merged:
        d = (c["end"] - c["start"]) * len(p) / total
        out.append(dict(c, start=t, end=t + d, text=p))
        t += d
    return out


_cap_cache = {}


def caption_layout(text):
    """Lines of (word, x) positions for a caption, centered on CAP_X."""
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    fnt = cap_font()
    space = tmp.textlength(" ", font=fnt) + CAP_GAP    # a little extra so the outlines don't touch
    layout = []
    for ln in wrap(tmp, text, fnt, CAP_W):
        ws = ln.split()
        widths = [tmp.textlength(w, font=fnt) for w in ws]
        x = CAP_X - (sum(widths) + space * (len(ws) - 1)) / 2
        row = []
        for w, wd in zip(ws, widths):
            row.append((w, x))
            x += wd + space
        layout.append(row)
    return layout


def caption_image(text, active=None):
    """The caption in white; the word at index `active` (spoken now) in the show's yellow."""
    key = (text, active)
    if key not in _cap_cache:
        fnt = cap_font()
        layout = caption_layout(text)
        im = Image.new("RGBA", (W, CAP_LH * len(layout) + 34), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        i = 0
        for r, row in enumerate(layout):
            for w, x in row:
                d.text((x, 10 + r * CAP_LH), w, font=fnt, fill=YELLOW if i == active else (255, 255, 255),
                       stroke_width=CAP_STROKE, stroke_fill=(0, 0, 0))
                i += 1
        _cap_cache[key] = im
    return _cap_cache[key]


def lower_third(name, sub, note):
    im = Image.new("RGBA", (W, 230), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 88
    d.rectangle((64, 12, 72, 196), fill=YELLOW)
    d.text((x, 0), name, font=font("Oswald", 74, "Bold"), fill=(255, 255, 255))
    d.text((x, 100), sub, font=font("Inter", 36, "SemiBold"), fill=(230, 230, 230))
    d.text((x, 152), note, font=font("PlexMono", 31), fill=YELLOW)
    return im


_lt_cache = {}


def draw_lower_third(frame, shot, lt):
    spec = shot.get("lower_third")
    if not spec:
        return
    t0 = shot["lines"][-1]["start"] - shot["start"] if shot.get("lower_third_at") == "last" else 0.35
    dur = shot["end"] - shot["start"]
    a = smooth((lt - t0) / 0.3) * (1 - smooth((lt - (dur - 0.25)) / 0.25))
    if a <= 0:
        return
    key = tuple(spec)
    if key not in _lt_cache:
        _lt_cache[key] = lower_third(*spec)
    im = with_alpha(_lt_cache[key], a)
    frame.alpha_composite(im, (int(-30 * (1 - a)), 1262))


def draw_caption(frame, t):
    for c in CHUNKS:
        if c["start"] - 0.02 <= t < c["end"] + 0.12:
            active = None
            for i, (_, w0) in enumerate(c.get("words", [])):   # the last word to have started
                if w0 - 0.02 <= t:
                    active = i
            frame.alpha_composite(caption_image(c["text"], active), (0, CAP_Y))
            return


def exhibit_tag(label, stamp):
    im = Image.new("RGBA", (520, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font("Oswald", 46, "Bold")
    tw = d.textlength(label, font=f)
    d.rounded_rectangle((0, 0, tw + 44, 72), radius=6, fill=YELLOW)
    d.text((22, 36), label, font=f, fill=(15, 15, 15), anchor="lm")
    d.text((4, 92), stamp, font=font("PlexMono", 30), fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    return im


def dashed_arrow(d, p0, p1, progress, color, width=9, dash=34, gap=20):
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    end = L * progress
    s = 0.0
    while s < end:
        e = min(s + dash, end)
        d.line((x0 + ux * s, y0 + uy * s, x0 + ux * e, y0 + uy * e), fill=color, width=width)
        s += dash + gap
    if progress >= 0.999:
        # arrowhead at p1
        ang = math.atan2(uy, ux)
        for da in (2.6, -2.6):
            d.line((x1, y1, x1 + 46 * math.cos(ang + da), y1 + 46 * math.sin(ang + da)), fill=color, width=width)
    # end ticks
    for (px, py) in ((x0, y0),):
        d.line((px - uy * 26, py + ux * 26, px + uy * 26, py - ux * 26), fill=color, width=width)


# ---------------------------------------------------------------- shot renderers

def shot_at(t):
    for s in SHOTS:
        if s["start"] <= t < s["end"]:
            return s
    return SHOTS[-1]


def render_still(shot, lt, fi, dur):
    v = pick_view(shot)
    frame, to_screen, sw = kb_view(source(v["img"], v["look"]), v["kb"], lt / dur)
    frame = grade(frame, fi).convert("RGBA")
    frame.alpha_composite(bottom_gradient())
    return frame, to_screen, sw


def render_evidence(shot, lt, fi, dur, t):
    frame, to_screen, sw = render_still(shot, lt, fi, dur)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    arrow = shot.get("annot_arrow")
    if arrow:
        ls = shot["lines"][-1]["start"] - shot["start"]
        p = smooth((lt - ls) / 0.7)
        if p > 0:
            a = to_screen(*arrow["from"])
            b = to_screen(*arrow["to"])
            dashed_arrow(d, a, b, p, YELLOW + (255,))
            if p > 0.6:
                mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                d.text((mx, my - 40), arrow["label"], font=font("PermanentMarker", 96), fill=YELLOW + (int(255 * smooth((p - 0.6) / 0.4)),), anchor="ms", stroke_width=4, stroke_fill=(0, 0, 0, 200))
    circles = shot.get("annot_circles")
    if circles:
        ls = shot["lines"][0]["start"] - shot["start"] + 0.3
        for i, (cx, cy, r) in enumerate(circles):
            p = smooth((lt - ls - 0.35 * i) / 0.45)
            if p <= 0:
                continue
            x, y = to_screen(cx, cy)
            rr = r * sw
            d.arc((x - rr, y - rr * 0.9, x + rr, y + rr * 0.9), start=-100, end=-100 + 370 * p, fill=YELLOW + (255,), width=10)
    frame.alpha_composite(ov)
    tag_a = smooth((lt - 0.2) / 0.25)
    if tag_a > 0:
        frame.alpha_composite(with_alpha(exhibit_tag(shot["label"], shot["stamp"]), tag_a), (64, 190))
    flash = 1.0 if lt < 0.06 else clamp(1 - (lt - 0.06) / 0.35)
    if flash > 0:
        frame = Image.blend(frame, Image.new("RGBA", (W, H), (255, 255, 255, 255)), flash * 0.95)
    return frame


def render_title(shot, lt, fi, dur):
    v = pick_view(shot)
    frame, _, _ = kb_view(source(v["img"], v["look"]), v["kb"], lt / dur)
    frame = grade(frame, fi, extra=lambda a: a * 0.5).convert("RGBA")
    a = smooth((lt - 0.15) / 0.6) * (1 - smooth((lt - (dur - 0.3)) / 0.3))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    alpha = int(255 * a)
    spaced_text(d, (W / 2, 700), ep.TITLE, font("Oswald", 124, "Bold"), (255, 255, 255, alpha), 10)
    d.rectangle((W / 2 - 170, 900, W / 2 + 170, 904), fill=YELLOW + (alpha,))
    spaced_text(d, (W / 2, 935), ep.EPISODE, font("Inter", 40, "SemiBold"), (235, 235, 235, alpha), 7)
    frame.alpha_composite(ov)
    return frame


def render_qcard(shot, lt, fi, dur):
    base = Image.new("RGB", (W, H), (8, 8, 9))
    frame = grade(base, fi, grain=5, vignette=False).convert("RGBA")
    d = ImageDraw.Draw(frame)
    txt = shot["text"]
    span = dur * 0.6
    n = int(len(txt) * clamp((lt - 0.15) / span))
    fnt = font("SpecialElite", 70)
    lines = wrap(d, txt, fnt, 780)            # centered, so lines end before x 930: clear of the apps' buttons
    d.text((W / 2, 760), "INTERVIEWER", font=font("PlexMono", 30), fill=(130, 130, 130), anchor="mm")
    y = 840
    shown = n
    last_xy = (W / 2, y)
    for ln in lines:
        full_w = d.textlength(ln, font=fnt)
        x = W / 2 - full_w / 2
        part = ln[: max(0, shown)]
        d.text((x, y), part, font=fnt, fill=(240, 240, 240))
        if shown > 0:
            last_xy = (x + d.textlength(part, font=fnt), y)
        shown -= len(ln) + 1
        y += 92
    if int(lt * 2.2) % 2 == 0 or n < len(txt):
        cx, cy = last_xy
        d.rectangle((cx + 6, cy + 8, cx + 36, cy + 72), fill=(240, 240, 240))
    return frame


_board = {}


def polaroid(key, crop, label, size, rot, look=None):
    src = source(key, look)
    x0, y0, x1 = crop
    side = (x1 - x0) * src.width
    bx, by = x0 * src.width, y0 * src.height
    ph = src.resize((size, size), Image.LANCZOS, box=(bx, by, bx + side, by + side))
    pad, bottom = int(size * 0.07), int(size * 0.28)
    card = Image.new("RGBA", (size + 2 * pad, size + pad + bottom), (236, 232, 222, 255))
    card.paste(ph, (pad, pad))
    d = ImageDraw.Draw(card)
    fs = int(size * 0.13)
    while fs > 12 and d.textlength(label, font=font("PermanentMarker", fs)) > card.width - 2 * pad:
        fs -= 2
    d.text((card.width / 2, size + pad + bottom * 0.52), label, font=font("PermanentMarker", fs), fill=(30, 30, 40), anchor="mm")
    return card.rotate(rot, resample=Image.BICUBIC, expand=True)


def procedural_cork():
    """Cork board lit by a desk lamp from the upper left, drawn at 1x then upscaled to the 2x master size."""
    rng = np.random.default_rng(11)
    w, h = W, H
    n1 = rng.normal(0, 1, (h // 6, w // 6)).astype(np.float32)
    n1 = np.asarray(Image.fromarray(((n1 * 30) + 128).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) - 128
    n2 = rng.normal(0, 1, (h, w)).astype(np.float32) * 16
    specks = (rng.random((h, w)) < 0.02).astype(np.uint8) * 255
    specks = np.asarray(Image.fromarray(specks).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    tex = np.array([168, 118, 70], np.float32) + (0.7 * n1 + n2)[..., None] * np.array([1.0, 0.8, 0.6], np.float32)
    tex -= specks[..., None] * np.array([80, 62, 44], np.float32)
    lamp = np.exp(-(((_xx - 0.25 * w) / (0.8 * w)) ** 2 + ((_yy - 0.18 * h) / (0.7 * h)) ** 2))
    tex *= (0.22 + 1.0 * lamp)[..., None]
    # dark wooden frame + wall beyond it
    m = 46
    inside = (_xx > m) & (_xx < w - m) & (_yy > m) & (_yy < h - m)
    wood = np.array([70, 44, 26], np.float32) * (0.3 + 0.8 * lamp)[..., None]
    tex = np.where(inside[..., None], tex, wood)
    im = Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8))
    return im.resize((2 * W, 2 * H), Image.BICUBIC)


def board_sources(shot):
    if shot["id"] in _board:
        return _board[shot["id"]]
    cork = (source("cork") if still_path("cork") else procedural_cork()).copy().convert("RGBA")
    sw, sh = cork.size
    lum = np.asarray(cork.convert("L"), dtype=np.float32) / 255.0
    layer = Image.new("RGBA", cork.size, (0, 0, 0, 0))
    strings = Image.new("RGBA", cork.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(strings)
    pins = []
    for key, crop, label, fx, fy, size, rot, look in shot["polaroids"]:
        card = polaroid(key, crop, label, size, rot, look)
        x, y = int(fx * sw - card.width / 2), int(fy * sh - card.height / 2)
        shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
        shadow.putalpha(card.split()[3].point(lambda v: int(v * 0.55)))
        layer.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)), (x + 18, y + 24))
        layer.alpha_composite(card, (x, y))
        pins.append((fx * sw, y + 40))
    center = pins[0]
    for p in pins[1:]:
        ds.line((p[0], p[1], center[0], center[1]), fill=RED + (235,), width=7)
    layer.alpha_composite(strings)
    dp = ImageDraw.Draw(layer)
    for px, py in pins:
        dp.ellipse((px - 20, py - 20, px + 20, py + 20), fill=(190, 30, 30, 255))
        dp.ellipse((px - 9, py - 12, px + 1, py - 2), fill=(255, 150, 150, 255))
    # relight: pinned items take the lamp falloff of the board behind them
    la = np.asarray(layer, dtype=np.float32)
    light = (0.35 + 0.9 * np.clip(lum / (np.percentile(lum, 97) + 1e-6), 0, 1))[..., None]
    la[..., :3] *= light
    layer = Image.fromarray(np.clip(la, 0, 255).astype(np.uint8), "RGBA")
    no_card = cork.copy()
    no_card.alpha_composite(layer)
    # index card that lands on "who moved Deb?"
    card = Image.new("RGBA", (1180, 330), (246, 244, 236, 255))
    dc = ImageDraw.Draw(card)
    for yy in range(95, 330, 56):
        dc.line((0, yy, 1180, yy), fill=(150, 180, 220, 255), width=3)
    dc.line((0, 70, 1180, 70), fill=(220, 90, 90, 255), width=3)
    text = shot.get("card", "WHO MOVED DEB?")
    size = 100
    while size > 50 and dc.textlength(text, font=font("PermanentMarker", size)) > 1080:
        size -= 4
    dc.text((590, 190), text, font=font("PermanentMarker", size), fill=(20, 20, 30, 255), anchor="mm")
    card = card.rotate(-4, resample=Image.BICUBIC, expand=True)
    with_card = no_card.copy()
    cx, cy = int(0.50 * sw - card.width / 2), int(0.72 * sh - card.height / 2)
    sh_ = Image.new("RGBA", card.size, (0, 0, 0, 0))
    sh_.putalpha(card.split()[3].point(lambda v: int(v * 0.6)))
    with_card.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(16)), (cx + 20, cy + 26))
    with_card.alpha_composite(card, (cx, cy))
    dp = ImageDraw.Draw(with_card)
    dp.ellipse((sw * 0.5 - 22, cy + 18, sw * 0.5 + 22, cy + 62), fill=(190, 30, 30, 255))
    _board[shot["id"]] = {"a": no_card.convert("RGB"), "b": with_card.convert("RGB")}
    return _board[shot["id"]]


def render_board(shot, lt, fi, dur):
    b = board_sources(shot)
    card_t = shot["lines"][-1]["start"] - shot["start"]
    src = b["b"] if lt >= card_t else b["a"]
    frame, _, _ = kb_view(src, shot["kb"], lt / dur)
    frame = grade(frame, fi).convert("RGBA")
    frame.alpha_composite(bottom_gradient())
    return frame


_door = {}


def night_vision(src):
    g = np.asarray(src.convert("L"), dtype=np.float32)
    lo, hi = np.percentile(g, 2), np.percentile(g, 99.6)
    g = np.clip((g - lo) / (hi - lo), 0, 1) ** 0.85 * 238
    return Image.fromarray(np.clip(np.stack([g * 0.86, g * 1.0, g * 0.88], -1), 0, 255).astype(np.uint8))


def glow(img, gx, gy, gr):
    """A light at (gx, gy) (fractions of the image), radius gr (fraction of the width)."""
    cx, cy, rad = gx * img.width, gy * img.height, gr * img.width
    yy, xx = np.mgrid[0:img.height, 0:img.width].astype(np.float32)
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * rad ** 2)))[..., None]
    arr = np.asarray(img, dtype=np.float32)
    return Image.fromarray(np.clip(arr + g * 235 * np.array([0.86, 1.0, 0.88]), 0, 255).astype(np.uint8))


def door_sources(shot):
    """Night-vision frames A and B. Frame B carries the hidden clue:
    alter_box (x0, y0, x1, y1) mirrors that region (something turned around);
    alter_glow (x, y, r) lights up a point (something switched on).
    lit [(x, y, r), ...] are lights already on in both frames (continuity, not a clue)."""
    if shot["id"] in _door:
        return _door[shot["id"]]
    a = night_vision(source(shot["frame_a"]))
    b = night_vision(source(shot["frame_b"]))
    for gx, gy, gr in shot.get("lit", []):
        a, b = glow(a, gx, gy, gr), glow(b, gx, gy, gr)
    if shot.get("alter_box"):
        x0, y0, x1, y1 = shot["alter_box"]
        box = (int(x0 * b.width), int(y0 * b.height), int(x1 * b.width), int(y1 * b.height))
        region = b.crop(box).transpose(Image.FLIP_LEFT_RIGHT)
        mask = Image.new("L", region.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((6, 4, region.width - 6, region.height - 4), radius=18, fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(4))
        b.paste(region, box[:2], mask)
    if shot.get("alter_glow"):
        b = glow(b, *shot["alter_glow"])
    _door[shot["id"]] = {"a": a, "b": b}
    return _door[shot["id"]]


def render_doorbell(shot, lt, fi, dur):
    ds = door_sources(shot)
    fl = shot["flicker_at"] - shot["start"]
    phase = int((lt - fl) / 0.3) if lt >= fl else -1
    paused = phase >= 6
    base, jump = doorbell_clock(shot)
    frame_a, frame_b = shot.get("frames", (417, 418))
    if phase < 0:
        use_b = lt >= jump
        clock = fmt_clock(base + int(lt))
    else:
        use_b = phase % 2 == 1 or paused
        clock = fmt_clock(base + jump if use_b else base + jump - 1)
    frame, _, _ = kb_view(ds["b"] if use_b else ds["a"], shot["kb"], lt / dur)
    frame = grade(frame, fi, grain=15, extra=lambda a: a * SCANLINES).convert("RGBA")
    frame.alpha_composite(bottom_gradient())
    d = ImageDraw.Draw(frame)
    mono = font("PlexMono", 34)
    if paused:
        d.text((70, 200), "❚❚ PAUSED", font=mono, fill=(255, 255, 255))
    elif int(lt * 2) % 2 == 0:
        d.ellipse((72, 206, 100, 234), fill=(230, 40, 40))
        d.text((114, 200), "REC", font=mono, fill=(255, 255, 255))
    else:
        d.text((114, 200), "REC", font=mono, fill=(255, 255, 255))
    d.text((W - 70, 200), shot.get("camera", "FRONT DOOR · NO. 5"), font=mono, fill=(255, 255, 255), anchor="ra")
    d.text((70, 252), f"{shot.get('date', '06/14/2026')}  {clock} AM", font=mono, fill=(255, 255, 255))
    if phase >= 0:
        d.text((W - 70, 252), f"FRAME {frame_b if use_b else frame_a}", font=mono, fill=YELLOW, anchor="ra")
    cta_t = fl + CTA_DELAY
    a = smooth((lt - cta_t) / 0.3)
    if a > 0:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        do = ImageDraw.Draw(ov)
        f1 = font("Oswald", 66, "Bold")
        y = 1040
        for ln in shot.get("cta", ("SOMETHING ELSE IN", "THIS FRAME MOVED.")):
            tw = do.textlength(ln, font=f1)
            do.rectangle((500 - tw / 2 - 22, y - 6, 500 + tw / 2 + 22, y + 86), fill=YELLOW + (255,))
            do.text((500, y + 40), ln, font=f1, fill=(15, 15, 15, 255), anchor="mm")
            y += 92
        do.text((500, y + 40), shot.get("cta_sub", "Comment the object + timestamp ↓"), font=font("Inter", 42, "ExtraBold"), fill=(255, 255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0, 255))
        frame.alpha_composite(with_alpha(ov, a))
    return frame


def render_end(shot, lt, fi, dur):
    base = Image.new("RGB", (W, H), (6, 6, 7))
    frame = grade(base, fi, grain=5, vignette=False).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    a1 = int(255 * smooth((lt - 0.25) / 0.5))
    a2 = int(255 * smooth((lt - 0.9) / 0.4))
    a3 = int(255 * smooth((lt - 1.4) / 0.4))
    spaced_text(d, (W / 2, 690), ep.TITLE, font("Oswald", 116, "Bold"), (255, 255, 255, a1), 9)
    d.rectangle((W / 2 - 150, 870, W / 2 + 150, 874), fill=YELLOW + (a1,))
    size = 38                                  # shrink a long "NEXT" line to end before x 930 (the apps' buttons)
    while size > 26 and d.textlength(ep.NEXT_UP, font=font("Inter", size, "Bold")) > 780:
        size -= 1
    d.text((W / 2, 930), ep.NEXT_UP, font=font("Inter", size, "Bold"), fill=YELLOW + (a2,), anchor="mm")
    d.text((W / 2, 1020), "Follow the case.", font=font("Inter", 54, "ExtraBold"), fill=(255, 255, 255, a3), anchor="mm")
    d.text((W / 2, 1330), "Reenactments dramatized with AI.", font=font("Inter", 30, "Regular"), fill=(150, 150, 150, a3), anchor="mm")
    d.text((W / 2, 1374), "The flamingo is real.", font=font("Inter", 30, "Regular"), fill=(150, 150, 150, a3), anchor="mm")
    frame.alpha_composite(ov)
    fade_in = smooth(lt / 0.2)
    if fade_in < 1:
        frame = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), frame, fade_in)
    return frame


def render(t, fi):
    shot = shot_at(t)
    lt = t - shot["start"]
    dur = shot["end"] - shot["start"]
    k = shot["kind"]
    if k == "still":
        frame, _, _ = render_still(shot, lt, fi, dur)
    elif k == "evidence":
        frame = render_evidence(shot, lt, fi, dur, t)
    elif k == "title":
        frame = render_title(shot, lt, fi, dur)
    elif k == "qcard":
        frame = render_qcard(shot, lt, fi, dur)
    elif k == "board":
        frame = render_board(shot, lt, fi, dur)
    elif k == "doorbell":
        frame = render_doorbell(shot, lt, fi, dur)
    else:
        frame = render_end(shot, lt, fi, dur)
    if k in ("still", "evidence", "board"):
        draw_lower_third(frame, shot, lt)
    if k not in ("qcard", "end", "title"):
        draw_caption(frame, t)
    return frame.convert("RGB")


def report_fallbacks():
    """Every shot that isn't using its first-choice still, and every still that will draw as a placeholder."""
    fb, ph = [], []
    for s in SHOTS:
        if s.get("views"):
            v = pick_view(s)
            if not still_path(v["img"]):
                ph.append(f'{s["id"]} ({s["views"][0]["img"]})')
            elif v is not s["views"][0]:
                skipped = [w["img"] for w in s["views"][: s["views"].index(v)]]
                fb.append(f'{s["id"]}: {", ".join(skipped)} -> {v["img"]}')
        keys = [s.get("frame_a"), s.get("frame_b")] + [p[0] for p in s.get("polaroids", [])]
        ph += [f'{s["id"]} ({k})' for k in keys if k and not still_path(k)]
    if fb:
        print("fallback views (shot: missing stills -> used):", "; ".join(fb))
    if ph:
        print("PLACEHOLDERS (no still found):", "; ".join(ph))


def main(argv):
    if not argv or argv[0].startswith("--"):
        sys.exit("usage: render.py episodes/<episode> [--preview t1,t2,... | --contact]")
    init(argv[0])
    argv = argv[1:]
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    missing = [k for k in getattr(ep, "STILLS", {}) if not still_path(k)]
    if missing:
        print("not provided (using fallbacks):", ", ".join(missing))
    report_fallbacks()
    if "--preview" in argv:
        ts = [float(x) for x in argv[argv.index("--preview") + 1].split(",")]
        for t in ts:
            render(t, int(t * FPS)).save(os.path.join(BUILD, f"preview_{t:05.2f}.png"))
        return
    if "--contact" in argv:
        thumbs = []
        label = ImageFont.truetype(os.path.join(FONTS, "Inter.ttf"), 20)
        for s in SHOTS:
            t = s["start"] + (s["end"] - s["start"]) * 0.75
            if s["kind"] == "doorbell" and s.get("flicker_at"):   # the paused clue frame, not mid-flicker
                t = min(s["end"] - 1.0 / FPS, s["flicker_at"] + CTA_DELAY + 0.6)
            im = render(t, int(t * FPS)).resize((270, 480), Image.LANCZOS)
            d = ImageDraw.Draw(im)
            d.rectangle((0, 0, 270, 30), fill=(0, 0, 0))
            d.text((6, 4), f'{s["id"]}  {t:.2f}s', font=label, fill=(242, 194, 48))
            thumbs.append(im)
        cols = 7
        sheet = Image.new("RGB", (cols * 270, math.ceil(len(thumbs) / cols) * 480), (0, 0, 0))
        for i, im in enumerate(thumbs):
            sheet.paste(im, ((i % cols) * 270, (i // cols) * 480))
        sheet.save(os.path.join(BUILD, "contact.png"))
        print("wrote", os.path.join(BUILD, "contact.png"))
        return
    out = os.path.join(BUILD, f"{ep.SLUG}.mp4")
    n = int(math.ceil(TOTAL * FPS))
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", os.path.join(BUILD, "soundtrack.wav"),
        "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "9M", "-bufsize", "18M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out,
    ], stdin=subprocess.PIPE)
    for fi in range(n):
        proc.stdin.write(render(fi / FPS, fi).tobytes())
        if fi % 150 == 0:
            print(f"frame {fi}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1:])
