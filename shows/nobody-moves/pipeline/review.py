"""Verify a rendered episode and review it side by side against another episode.

  python pipeline/review.py episodes/<ep> [--ref episodes/<ref>] [--file tiktok|master] [--json]

Reads <ep>/build/timeline.json and the rendered MP4 (the TikTok copy by default). Checks (exit 1 on any FAIL):
  FAIL  the file exists; 1080x1920 H.264 at 30 fps; AAC 48 kHz stereo
  FAIL  video and audio streams both match the timeline total (within 0.15 s)
  FAIL  the TikTok copy is under 29 MB
  FAIL  a black stretch (0.4 s or longer) outside the black-by-design question cards
  info  the file's loudness (it should still be about -14 LUFS after encoding)
  info  pacing and structure: shots, shot lengths, when the hook/title/payoff/cliffhanger land,
        words per minute, caption load, music-out shots, where the score peaks
With --ref it measures the reference episode the same way, prints the deltas, and writes
<ep>/build/review/beats_vs_<ref>.png: the same story beats from both episodes (hook name card,
title, payoff, first question card, first exhibit, first name card, board, cliffhanger jump,
cliffhanger call to action, end card), frame-grabbed from the MP4s at phone size, reference on
top. Open it and look: that sheet is the review. Report: <ep>/build/review/report.json.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from common import CTA_DELAY, FONTS, doorbell_clock

FPS = 30
MAX_MB = 29.0
CELL_W, CELL_H = 300, 533          # about phone-preview size
BEATS = ["hook", "title", "payoff", "question", "exhibit", "name card", "board", "cliff jump", "cliff CTA", "end card"]


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def run_ff(*args):
    return subprocess.run([ffmpeg(), "-hide_banner", *args], capture_output=True, text=True).stderr


def episode_paths(ep_dir, which):
    ep_dir = os.path.abspath(ep_dir.rstrip("/"))
    slug = os.path.basename(ep_dir)
    build = os.path.join(ep_dir, "build")
    name = f"{slug}_tiktok.mp4" if which == "tiktok" else f"{slug}.mp4"
    return slug, build, os.path.join(build, name)


# ---------- the file

def probe(path):
    """Streams, stream durations, size and bitrate of an MP4 (there is no ffprobe: parse ffmpeg)."""
    info = {"path": path, "exists": os.path.exists(path)}
    if not info["exists"]:
        return info
    info["size_mb"] = round(os.path.getsize(path) / 2 ** 20, 2)
    head = run_ff("-i", path)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", head)
    info["duration"] = round(int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]), 3) if m else None
    v = re.search(r"Video: (\w+).*?, (\d+)x(\d+).*?, ([\d.]+) fps", head)
    a = re.search(r"Audio: (\w+).*?, (\d+) Hz, (\w+)", head)
    b = re.search(r"bitrate: (\d+) kb/s", head)
    info["video"] = {"codec": v[1], "w": int(v[2]), "h": int(v[3]), "fps": float(v[4])} if v else None
    info["audio"] = {"codec": a[1], "rate": int(a[2]), "layout": a[3]} if a else None
    info["kbps"] = int(b[1]) if b else None
    # stream lengths, each read on its own (a container duration can hide a short stream). A stream
    # copy reports the last packet's time; the last video frame lasts one more frame.
    info["video_s"] = stream_end(path, "0:v:0", 1.0 / FPS)
    info["audio_s"] = stream_end(path, "0:a:0", 0.0)
    return info


def stream_end(path, stream, last_packet):
    t = re.findall(r"time=(\d+):(\d+):([\d.]+)", run_ff("-i", path, "-map", stream, "-c", "copy", "-f", "null", "-"))
    return round(int(t[-1][0]) * 3600 + int(t[-1][1]) * 60 + float(t[-1][2]) + last_packet, 3) if t else None


def loudness(path):
    out = run_ff("-i", path, "-vn", "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-")
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", out)
    return {"lufs": float(i[-1]) if i else None, "true_peak": float(p[-1]) if p else None}


def black_stretches(path):
    out = run_ff("-i", path, "-an", "-vf", "scale=270:-2,blackdetect=d=0.4:pix_th=0.10", "-f", "null", "-")
    return [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", out)]


def shot_at(shots, t):
    return next((s for s in shots if s["start"] <= t < s["end"]), shots[-1])


# ---------- the story

def beats(tl):
    """Named moments to compare between episodes: (name, time), clipped inside their shot."""
    shots = tl["shots"]
    out = []

    def add(name, shot, t):
        if shot is not None:
            out.append((name, round(min(max(t, shot["start"]), shot["end"] - 1.0 / FPS), 2), shot["id"]))

    first = lambda pred: next((s for s in shots if pred(s)), None)  # noqa: E731
    doors = [s for s in shots if s["kind"] == "doorbell"]
    add("hook", shots[0], 0.6)
    title = first(lambda s: s["kind"] == "title")
    add("title", title, title and title["start"] + 1.6)
    if len(doors) > 1:                      # the replay that pays off last episode's clue
        add("payoff", doors[0], doors[0].get("flicker_at", doors[0]["end"]) + CTA_DELAY + 0.9)
    q = first(lambda s: s["kind"] == "qcard")
    add("question", q, q and q["start"] + 0.15 + 0.6 * (q["end"] - q["start"]) + 0.35)
    ev = first(lambda s: s["kind"] == "evidence")
    add("exhibit", ev, ev and ev["start"] + 0.5)
    lt = first(lambda s: s.get("lower_third") and s is not shots[0])
    if lt:
        at = lt["lines"][-1]["start"] if lt.get("lower_third_at") == "last" and lt["lines"] else lt["start"] + 0.35
        add("name card", lt, at + 0.8)
    board = first(lambda s: s["kind"] == "board")
    add("board", board, board and board["end"] - 0.25)
    if doors:
        d = doors[-1]
        add("cliff jump", d, d["start"] + doorbell_clock(d)[1] + 0.4)
        add("cliff CTA", d, d.get("flicker_at", d["end"]) + CTA_DELAY + 1.0)
    end = first(lambda s: s["kind"] == "end")
    add("end card", end, end and end["start"] + 1.8)
    return out


def pacing(tl):
    shots, caps, total = tl["shots"], tl["captions"], tl["total"]
    lens = [s["end"] - s["start"] for s in shots if s["kind"] != "end"]
    kinds = {}
    for s in shots:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    words = sum(len(c["text"].split()) for c in caps)
    spoken = sum(c["end"] - c["start"] for c in caps)
    marked = [s["start"] for s in shots if s.get("climax")]
    doors = [s["start"] for s in shots if s["kind"] == "doorbell"]
    title = next((s["start"] for s in shots if s["kind"] == "title"), None)
    first_q = next((s["start"] for s in shots if s["kind"] == "qcard"), None)
    replay = [s for s in shots if s["kind"] == "doorbell"]
    longest = max((s for s in shots if s["kind"] != "end"), key=lambda s: s["end"] - s["start"])
    return {
        "runtime_s": round(total, 2),
        "shots": len(shots),
        "kinds": " ".join(f"{k}:{n}" for k, n in kinds.items()),
        "mean_shot_s": round(float(np.mean(lens)), 2),
        "longest_shot": f'{longest["id"]} {longest["end"] - longest["start"]:.1f}s',
        "first_line_s": round(caps[0]["start"], 2) if caps else None,
        "title_at_s": title,
        "payoff_at_s": round(replay[0]["flicker_at"] + CTA_DELAY, 2) if len(replay) > 1 and replay[0].get("flicker_at") else None,
        "first_question_at_s": first_q,
        "lines": len(caps),
        "words_per_min": round(words / (total / 60), 1),
        "speech_share": round(spoken / total, 2),
        "longest_caption_chars": max((len(c["text"]) for c in caps), default=0),
        "music_out_shots": [s["id"] for s in shots if s.get("music") == "out"],
        "score_peak_at_s": (marked or doors or [None])[-1],
    }


# ---------- the sheet

def grab(path, t, dst):
    run_ff("-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-y", dst)
    return Image.open(dst).convert("RGB") if os.path.exists(dst) else None


def font(size):
    for name in ("Inter-SemiBold.ttf", "Inter-Regular.ttf"):
        p = os.path.join(FONTS, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def sheet(rows, out):
    """rows: [(label, path, [(beat, t, shot)...])]; columns are the union of beat names, in story order."""
    present = {b[0] for _, _, bs in rows for b in bs}
    order = [b for b in BEATS if b in present]
    pad, head, left = 10, 46, 110
    img = Image.new("RGB", (left + len(order) * (CELL_W + pad) + pad, len(rows) * (CELL_H + head + pad) + pad), (18, 18, 18))
    d = ImageDraw.Draw(img)
    f, fs = font(22), font(17)
    tmp = os.path.join(os.path.dirname(out), "_grab.png")
    for r, (label, path, bs) in enumerate(rows):
        y = pad + r * (CELL_H + head + pad)
        d.text((pad, y + head + CELL_H // 2 - 12), label, font=f, fill=(242, 194, 48))
        at = {b[0]: b for b in bs}
        for c, name in enumerate(order):
            x = left + pad + c * (CELL_W + pad)
            if name not in at:
                d.rectangle((x, y + head, x + CELL_W, y + head + CELL_H), fill=(40, 40, 40))
                d.text((x + 12, y + 8), f"{name}: none", font=fs, fill=(150, 150, 150))
                continue
            _, t, sid = at[name]
            fr = grab(path, t, tmp)
            d.text((x + 2, y + 4), f"{name}", font=f, fill=(235, 235, 235))
            d.text((x + 2, y + 27), f"{t:.2f}s  {sid}", font=fs, fill=(160, 160, 160))
            if fr is not None:
                img.paste(fr.resize((CELL_W, CELL_H), Image.LANCZOS), (x, y + head))
    if os.path.exists(tmp):
        os.remove(tmp)
    img.save(out)
    return out


# ---------- checks

def check_file(info, tl, which):
    checks = []

    def add(name, ok, value, target):
        checks.append({"check": name, "ok": bool(ok), "value": value, "target": target})

    if not info["exists"]:
        add("file", False, "missing", info["path"])
        return checks
    v, a = info["video"] or {}, info["audio"] or {}
    add("video", v.get("codec") == "h264" and (v.get("w"), v.get("h")) == (1080, 1920) and v.get("fps") == FPS,
        f'{v.get("codec")} {v.get("w")}x{v.get("h")} {v.get("fps")} fps', "h264 1080x1920 30 fps")
    add("audio", a.get("codec") == "aac" and a.get("rate") == 48000 and a.get("layout") == "stereo",
        f'{a.get("codec")} {a.get("rate")} Hz {a.get("layout")}', "aac 48000 Hz stereo")
    total = tl["total"]
    for key in ("video_s", "audio_s"):
        got = info.get(key)
        add(key.replace("_s", " length"), got is not None and abs(got - total) <= 0.15,
            f"{got} s" if got is not None else "unreadable", f"{total} s +/- 0.15")
    if which == "tiktok":
        add("size", info["size_mb"] < MAX_MB, f'{info["size_mb"]} MB', f"< {MAX_MB} MB")
    return checks


def review(ep_dir, which, with_black=True):
    slug, build, path = episode_paths(ep_dir, which)
    tl_path = os.path.join(build, "timeline.json")
    if not os.path.exists(tl_path):
        sys.exit(f"missing {tl_path}: build the episode first")
    with open(tl_path) as f:
        tl = json.load(f)
    info = probe(path)
    res = {"episode": slug, "file": path, "probe": info, "pacing": pacing(tl), "beats": beats(tl),
           "checks": check_file(info, tl, which)}
    if info["exists"]:
        res["loudness"] = loudness(path)
        if with_black:
            bad = []
            for s0, s1 in black_stretches(path):
                kind = shot_at(tl["shots"], (s0 + s1) / 2)["kind"]
                if kind != "qcard":
                    bad.append({"start": s0, "end": s1, "shot": shot_at(tl["shots"], (s0 + s1) / 2)["id"]})
            res["checks"].append({"check": "black frames", "ok": not bad,
                                  "value": ", ".join(f'{b["shot"]} {b["start"]:.2f}-{b["end"]:.2f}s' for b in bad) or "none outside question cards",
                                  "target": "none outside question cards"})
    return res


def main(argv):
    if not argv or argv[0].startswith("--"):
        sys.exit("usage: review.py episodes/<ep> [--ref episodes/<ref>] [--file tiktok|master] [--json]")
    which = argv[argv.index("--file") + 1] if "--file" in argv else "tiktok"
    new = review(argv[0], which)
    ref = review(argv[argv.index("--ref") + 1], which, with_black=False) if "--ref" in argv else None
    out_dir = os.path.join(os.path.dirname(new["file"]), "review")
    os.makedirs(out_dir, exist_ok=True)
    if ref and new["probe"]["exists"] and ref["probe"]["exists"]:
        new["sheet"] = sheet([(ref["episode"].split("_")[0] + " (ref)", ref["file"], ref["beats"]),
                              (new["episode"].split("_")[0], new["file"], new["beats"])],
                             os.path.join(out_dir, f"beats_vs_{ref['episode']}.png"))
    report = {"new": new, "ref": ref}
    with open(os.path.join(out_dir, "report.json"), "w") as f:
        json.dump(report, f, indent=1)
    failed = [c["check"] for c in new["checks"] if not c["ok"]]
    if "--json" in argv:
        print(json.dumps(report, indent=1))
        return 1 if failed else 0

    print(f"REVIEW {new['episode']} ({which} copy)" + (f" vs {ref['episode']}" if ref else ""))
    for c in new["checks"]:
        print(f"  {'PASS' if c['ok'] else 'FAIL':4s}  {c['check']:13s} {c['value']:40s} {c['target']}")
    if new.get("loudness"):
        ln = new["loudness"]
        print(f"  info  loudness      {ln['lufs']} LUFS, true peak {ln['true_peak']} dBFS (encoded audio; target about -14)")
    print()
    keys = list(new["pacing"])
    width = max(len(k) for k in keys)
    print(f"  {'pacing':{width}s}  {new['episode'][:22]:24s}" + (f"{ref['episode'][:22]:24s}delta" if ref else ""))
    for k in keys:
        a = new["pacing"][k]
        line = f"  {k:{width}s}  {str(a):24s}"
        if ref:
            b = ref["pacing"].get(k)
            delta = f"{a - b:+.2f}" if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) else ""
            line += f"{str(b):24s}{delta}"
        print(line)
    if new.get("sheet"):
        print(f"\n  beats sheet: {new['sheet']}")
    print(f"  report: {os.path.join(out_dir, 'report.json')}")
    print(f"\nRESULT: {'FAIL - ' + ', '.join(failed) if failed else 'PASS'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
