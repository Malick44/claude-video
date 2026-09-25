"""Where TikTok, Instagram Reels and YouTube Shorts cover the video with their own UI, and whether
any of an episode's text sits there.

  .venv/bin/python pipeline/safezones.py episodes/<ep>      # review.py also runs it

Each app draws its buttons, the account name and the post's description over the video. ZONES
lists those areas on the 1080x1920 frame for an ordinary (not sponsored) post. The values are
typical ones from 2026 safe-zone guides, and the apps move their UI from time to time: check the
first upload on a phone and update the table when an app changes. Meta's guide for Reels *ads*
keeps text out of the bottom 35% (from y 1248), because a sponsored Reel adds a button there; that
line is reported as info, since it only matters for a boosted Reel.

To find the text, it renders each sample moment twice from the timeline: once as usual and once
with every text call switched off. The difference is exactly the pixels text covers: captions,
name cards, tags, the doorbell readout and call to action, and the cards. Nothing is listed by
hand, so a new shot kind is checked too. The samples are the middle of every caption chunk and
two moments per shot: about 1 s in, and 0.3 s before its end, when name cards, calls to action
and cards are fully in.

Writes build/review/zones.png: key moments per app, with the covered areas shaded and any text
inside them in magenta.
"""
import contextlib
import importlib.util
import io
import json
import os
import sys
import types

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30

# (x0, y0, x1, y1): what each app covers on an ordinary post. Approximate: the top bars, button
# widths and description depths follow 2026 safe-zone guides (TikTok top 130 / right 140 / bottom
# 324-484, Shorts right 120 / bottom 380, Reels right about 10%); the height where each button
# column starts (its profile picture or first button: about halfway down on TikTok, lower on Shorts
# and Reels) is an estimate from the apps' layouts, which no guide gives.
ZONES = {
    "TikTok": {"top bar": (0, 0, W, 130), "buttons": (940, 880, W, H), "description": (0, 1500, W, H)},
    "Reels": {"top bar": (0, 0, W, 200), "buttons": (950, 1100, W, H), "description": (0, 1500, W, H)},
    "Shorts": {"top bar": (0, 0, W, 160), "buttons": (960, 1000, W, H), "description": (0, 1540, W, H)},
}
ADS_BOTTOM = 1248          # Meta's guide for Reels ads: no text in the bottom 35%
DIFF = 24                  # a pixel is text where the two renders differ by more than this
MIN_PIXELS = 60            # text pixels inside a zone before it counts (stray antialiasing aside)
CELL_W, CELL_H = 270, 480
MAX_COLS = 6


def zone_summary(zones):
    t, b, d = zones["top bar"], zones["buttons"], zones["description"]
    return f"top {t[3]}, buttons x {b[0]}+ from y {b[1]}, description y {d[1]}+"


def load_renderer(ep_dir, name, text=True):
    """A private copy of render.py, initialized for the episode; text=False draws no text at all."""
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "render.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not text:
        class NoText(ImageDraw.ImageDraw):
            def text(self, *args, **kwargs):
                return None
        mod.ImageDraw = types.SimpleNamespace(Draw=lambda im, mode=None: NoText(im, mode))
    with contextlib.redirect_stdout(io.StringIO()):
        mod.init(ep_dir)
    return mod


def sample_times(mod):
    ts = {round((c["start"] + c["end"]) / 2, 2) for c in mod.CHUNKS}
    for s in mod.SHOTS:
        dur = s["end"] - s["start"]
        ts.add(round(s["start"] + min(1.0, dur / 2), 2))
        if dur > 0.8:
            ts.add(round(s["end"] - 0.3, 2))
    return sorted(t for t in ts if 0 <= t < mod.TOTAL)


def bbox(mask, x0=0, y0=0):
    ys, xs = np.nonzero(mask)
    return [int(x0 + xs.min()), int(y0 + ys.min()), int(x0 + xs.max() + 1), int(y0 + ys.max() + 1)]


def check(ep_dir, out_dir=None):
    """Render, compare and report: {"samples", "platforms": {app: {"zones", "hits"}}, "ads", "sheet"}."""
    ep_dir = os.path.abspath(ep_dir.rstrip("/"))
    out_dir = out_dir or os.path.join(ep_dir, "build", "review")
    os.makedirs(out_dir, exist_ok=True)
    full = load_renderer(ep_dir, "_render_text")
    bare = load_renderer(ep_dir, "_render_bare", text=False)
    samples = []
    for t in sample_times(full):
        fi = int(t * FPS)
        a = np.asarray(full.render(t, fi), dtype=np.int16)
        b = np.asarray(bare.render(t, fi), dtype=np.int16)
        mask = np.abs(a - b).max(axis=2) > DIFF
        shot = full.shot_at(t)
        samples.append({"t": t, "shot": shot["id"], "kind": shot["kind"], "mask": mask,
                        "thumb": Image.fromarray(a.astype(np.uint8)).resize((CELL_W, CELL_H), Image.LANCZOS),
                        "bottom": int(np.nonzero(mask.any(axis=1))[0].max()) + 1 if mask.any() else 0})
    platforms = {}
    for app, zones in ZONES.items():
        hits = {}
        for s in samples:
            for zname, (x0, y0, x1, y1) in zones.items():
                sub = s["mask"][y0:y1, x0:x1]
                n = int(np.count_nonzero(sub))
                key = (zname, s["shot"])
                if n >= MIN_PIXELS and n > hits.get(key, {}).get("pixels", 0):
                    hits[key] = {"zone": zname, "shot": s["shot"], "t": s["t"], "pixels": n, "box": bbox(sub, x0, y0)}
        platforms[app] = {"zones": zones, "hits": sorted(hits.values(), key=lambda h: h["t"])}
    ads = {}
    for s in samples:
        sub = s["mask"][ADS_BOTTOM:]
        if np.count_nonzero(sub) >= MIN_PIXELS and s["shot"] not in ads:
            ads[s["shot"]] = {"shot": s["shot"], "t": s["t"], "box": bbox(sub, 0, ADS_BOTTOM)}
    res = {"samples": len(samples), "platforms": platforms, "ads": {"bottom_from": ADS_BOTTOM, "shots": list(ads.values())},
           "text_bottom": max(s["bottom"] for s in samples)}
    res["sheet"] = zone_sheet(samples, platforms, out_dir)
    return res


def key_moments(samples, platforms):
    """Columns for the sheet: a name card, the lowest text, the last call to action, the end card,
    then moments with text under an app's UI."""
    picks = []

    def add(s, label):
        if s and all(s is not p for p, _ in picks) and len(picks) < MAX_COLS:
            picks.append((s, label))

    ends = {}
    for s in samples:                              # the last sample of each shot: name cards and CTAs are in
        ends[s["shot"]] = s
    named = [s for s in ends.values() if s["kind"] in ("still", "evidence") and s["mask"][1262:1480].any()]
    add(named[0] if named else None, "name card")
    add(max(samples, key=lambda s: s["bottom"]), "lowest text")
    doors = [s for s in ends.values() if s["kind"] == "doorbell"]
    add(doors[-1] if doors else None, "call to action")
    add(ends.get(samples[-1]["shot"]) if samples[-1]["kind"] == "end" else None, "end card")
    for app, p in platforms.items():
        for h in p["hits"]:
            add(next(s for s in samples if s["t"] == h["t"]), f"{app}: {h['zone']}")
    return picks


def zone_sheet(samples, platforms, out_dir):
    picks = key_moments(samples, platforms)
    pad, head, left = 12, 64, 110
    img = Image.new("RGB", (left + len(picks) * (CELL_W + pad) + pad, len(platforms) * (CELL_H + head + pad) + pad), (18, 18, 18))
    d = ImageDraw.Draw(img)
    fp = os.path.join(HERE, "..", "assets", "fonts", "Inter.ttf")
    f, fs = (ImageFont.truetype(fp, 24), ImageFont.truetype(fp, 18)) if os.path.exists(fp) else (ImageFont.load_default(),) * 2
    sx, sy = CELL_W / W, CELL_H / H
    for r, (app, p) in enumerate(platforms.items()):
        y = pad + r * (CELL_H + head + pad)
        d.text((pad, y + head + CELL_H // 2 - 12), app, font=f, fill=(242, 194, 48))
        for c, (s, label) in enumerate(picks):
            x = left + pad + c * (CELL_W + pad)
            d.text((x + 2, y + 4), label, font=f, fill=(235, 235, 235))
            d.text((x + 2, y + 36), f"{s['t']:.2f}s  {s['shot']}", font=fs, fill=(170, 170, 170))
            cell = s["thumb"].convert("RGBA")
            shade = Image.new("RGBA", cell.size, (0, 0, 0, 0))
            ds = ImageDraw.Draw(shade)
            covered = np.zeros((H, W), dtype=bool)
            for x0, y0, x1, y1 in p["zones"].values():
                ds.rectangle((x0 * sx, y0 * sy, x1 * sx, y1 * sy), fill=(220, 40, 40, 70))
                covered[y0:y1, x0:x1] = True
            clash = Image.fromarray(((s["mask"] & covered) * 255).astype(np.uint8)).resize(cell.size, Image.BOX)
            shade.paste((255, 0, 255, 255), mask=clash.point(lambda v: 255 if v > 20 else 0))
            img.paste(Image.alpha_composite(cell, shade).convert("RGB"), (x, y + head))
    out = os.path.join(out_dir, "zones.png")
    img.save(out)
    return out


def report_lines(res):
    """(status, text) rows, as review.py prints them."""
    rows = []
    for app, p in res["platforms"].items():
        if not p["hits"]:
            rows.append(("PASS", f"{app:13s} {'no text under the app':36s} {zone_summary(p['zones'])}"))
        for h in p["hits"]:
            x0, y0, x1, y1 = h["box"]
            rows.append(("WARN", f"{app}: {h['shot']} {h['t']:.2f}s, text under the {h['zone']} (x {x0}-{x1}, y {y0}-{y1})"))
    ads = res["ads"]["shots"]
    if ads:
        rows.append(("info", f"{'Reels ads':13s} text below y {res['ads']['bottom_from']} in {len(ads)} shot{'s' if len(ads) != 1 else ''} "
                             f"(Meta's guide for sponsored Reels); fine for ordinary posts"))
    rows.append(("info", f"{'text reaches':13s} y {res['text_bottom']} at its lowest ({res['samples']} moments checked)"))
    return rows


def main(argv):
    if not argv or argv[0].startswith("-"):
        print(__doc__.strip())
        return 0 if argv[:1] in (["-h"], ["--help"]) else 2
    res = check(argv[0])
    for status, text in report_lines(res):
        print(f"  {status:4s}  {text}")
    print(f"\n  sheet: {res['sheet']}")
    if "--json" in argv:
        print(json.dumps({k: v for k, v in res.items()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
