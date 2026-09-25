"""Verify a rendered episode and review it side by side against another episode.

  python pipeline/review.py episodes/<ep> [--ref episodes/<ref>] [--file tiktok|master] [--no-zones] [--json]
  python pipeline/review.py episodes/<ep> --grab 12.5,40,81.2          # extra labelled frames, one sheet

Reads <ep>/build/timeline.json and the rendered MP4 (the TikTok copy by default). Checks (exit 1 on any FAIL):
  FAIL  the file exists; 1080x1920 H.264 at 30 fps; AAC 48 kHz stereo
  FAIL  video and audio streams both match the timeline total (within 0.15 s)
  FAIL  the TikTok copy is under 29 MB (decimal MB, as deliver.py prints it)
  FAIL  a black stretch (0.4 s or longer) outside question cards and the end card's fade-in
  WARN  a doorbell call to action on screen for less than 1.5 s (too short to read)
  WARN  text under TikTok's, Instagram Reels' or YouTube Shorts' own buttons, top bar or description
        (pipeline/safezones.py; writes build/review/zones.png; about 45 s, skip with --no-zones)
  info  the file's loudness (about -14 LUFS, true peak about -1.0 to -1.2 dBFS after AAC)
  info  pacing and structure: shots, shot lengths, when the title/payoff/first question land,
        words per minute, speech share, music-out shots, the shot the score builds to
With --ref it measures the reference episode the same way, prints the deltas and a one-line
summary of the reference's own checks, and writes <ep>/build/review/beats_vs_<ref>_1.png and _2.png:
the same story beats from both episodes, frame-grabbed from the MP4s at phone size, reference on
top. The beats: hook, title, payoff (the replay's call to action), first question card, first
exhibit, first interview name card, the first music-out beat, board, the cliffhanger's frame A,
the cliffhanger paused on frame B with its call to action, end card. Open them and look: those
sheets are the review. Reports: <ep>/build/review/report_<file>[_vs_<ref>].json.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import safezones
from common import CTA_DELAY, FONTS, doorbell_clock

FPS = 30
MAX_MB = 29.0                      # decimal MB, the unit deliver.py prints
CTA_MIN_S = 1.5
CELL_W, CELL_H = 300, 533          # about phone-preview size
PER_SHEET = 6
BEATS = ["hook", "title", "payoff", "question", "exhibit", "interview", "silence", "board",
         "cliff A", "cliff B + CTA", "end card"]


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
    """Streams, stream lengths, size and bitrate of an MP4 (there is no ffprobe: parse ffmpeg)."""
    info = {"path": path, "exists": os.path.exists(path)}
    if not info["exists"]:
        return info
    info["size_mb"] = round(os.path.getsize(path) / 1e6, 2)
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


def black_by_design(shots, s0, s1):
    """Question cards are black cards; the end card fades up from black (about 0.4 s)."""
    shot = shot_at(shots, (s0 + s1) / 2)
    if shot["kind"] == "qcard":
        return True
    return shot["kind"] == "end" and s0 <= shot["start"] + 0.1 and s1 <= shot["start"] + 0.8


# ---------- the story

def beats(tl):
    """Named moments to compare between episodes: (name, time, shot id), clipped inside their shot."""
    shots = tl["shots"]
    out = []

    def add(name, shot, t):
        if shot is not None and t is not None:
            out.append((name, round(min(max(t, shot["start"]), shot["end"] - 1.0 / FPS), 2), shot["id"]))

    first = lambda pred, after=0.0: next((s for s in shots if s["start"] >= after and pred(s)), None)  # noqa: E731
    doors = [s for s in shots if s["kind"] == "doorbell"]
    add("hook", shots[0], 0.6)
    title = first(lambda s: s["kind"] == "title")
    add("title", title, title and title["start"] + 1.6)
    if len(doors) > 1:                      # the replay that pays off last episode's clue
        add("payoff", doors[0], doors[0].get("flicker_at", doors[0]["end"]) + CTA_DELAY + 0.5)
    q = first(lambda s: s["kind"] == "qcard")
    add("question", q, q and q["start"] + 0.15 + 0.6 * (q["end"] - q["start"]) + 0.35)
    ev = first(lambda s: s["kind"] == "evidence")
    add("exhibit", ev, ev and (ev["lines"][-1]["start"] + 0.5 if ev["lines"] else ev["start"] + 0.5))
    iv = first(lambda s: s.get("lower_third"), q["start"] if q else 0.0)   # the first interview after a question
    if iv:
        at = iv["lines"][-1]["start"] if iv.get("lower_third_at") == "last" and iv["lines"] else iv["start"] + 0.35
        add("interview", iv, at + 0.8)
    mo = first(lambda s: s.get("music") == "out")
    add("silence", mo, mo and (mo["lines"][-1]["start"] + 0.5 if mo["lines"] else mo["start"] + 0.5))
    board = first(lambda s: s["kind"] == "board")
    add("board", board, board and board["end"] - 0.25)
    if doors:
        d = doors[-1]
        jump = d["start"] + doorbell_clock(d)[1]
        add("cliff A", d, min(jump, d.get("flicker_at", jump)) - 0.5)
        add("cliff B + CTA", d, d.get("flicker_at", d["end"]) + CTA_DELAY + 0.8)
    end = first(lambda s: s["kind"] == "end")
    add("end card", end, end and end["start"] + 1.8)
    # a beat that lands on the same moment as an earlier one (e.g. the music-out shot is the exhibit)
    # is marked, so the sheet says "same as" instead of repeating the frame
    seen = []
    for i, (name, t, sid) in enumerate(out):
        dup = next((n for n, t2, s2 in seen if s2 == sid and abs(t2 - t) < 0.5), None)
        out[i] = (name, t, sid, dup)
        seen.append((name, t, sid))
    return out


def cta_holds(tl):
    """Seconds each doorbell's call to action stays on screen before the cut."""
    return {s["id"]: round(s["end"] - (s["flicker_at"] + CTA_DELAY), 2)
            for s in tl["shots"] if s["kind"] == "doorbell" and s.get("flicker_at")}


def pacing(tl):
    shots, caps, total = tl["shots"], tl["captions"], tl["total"]
    lens = [s["end"] - s["start"] for s in shots if s["kind"] != "end"]
    kinds = {}
    for s in shots:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    words = sum(len(c["text"].split()) for c in caps)
    spoken = sum(c["end"] - c["start"] for c in caps)
    marked = [s for s in shots if s.get("climax")]
    doors = [s for s in shots if s["kind"] == "doorbell"]
    peak = (marked or doors or [None])[-1]
    longest = max((s for s in shots if s["kind"] != "end"), key=lambda s: s["end"] - s["start"])
    return {
        "runtime_s": round(total, 2),
        "shots": len(shots),
        "kinds": " ".join(f"{k}:{n}" for k, n in kinds.items()),
        "mean_shot_s": round(float(np.mean(lens)), 2),
        "longest_shot": f'{longest["id"]} {longest["end"] - longest["start"]:.1f}s',
        "title_at_s": next((s["start"] for s in shots if s["kind"] == "title"), None),
        "payoff_at_s": round(doors[0]["flicker_at"] + CTA_DELAY, 2) if len(doors) > 1 and doors[0].get("flicker_at") else None,
        "first_question_at_s": next((s["start"] for s in shots if s["kind"] == "qcard"), None),
        "lines": len(caps),
        "words_per_min": round(words / (total / 60), 1),
        "speech_share": round(spoken / total, 2),
        "longest_caption_chars": max((len(c["text"]) for c in caps), default=0),
        "music_out_shots": " ".join(s["id"] for s in shots if s.get("music") == "out") or "none",
        "cta_on_screen_s": " ".join(f"{k}:{v}" for k, v in cta_holds(tl).items()) or "none",
        "score_builds_to": f'{peak["id"]} {peak["start"]:.1f}s' if peak else "end card",
    }


# ---------- sheets

def grab(path, t, dst):
    run_ff("-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-y", dst)
    return Image.open(dst).convert("RGB") if os.path.exists(dst) else None


def font(size):
    p = os.path.join(FONTS, "Inter.ttf")
    return ImageFont.truetype(p, size) if os.path.exists(p) else ImageFont.load_default()


def draw_sheet(rows, cols, out, tmp):
    """rows: [(label, path, {col: (t, shot_id)})]; one cell per (row, col); gray where a row lacks a col."""
    pad, head, left = 12, 64, 150
    img = Image.new("RGB", (left + len(cols) * (CELL_W + pad) + pad, len(rows) * (CELL_H + head + pad) + pad), (18, 18, 18))
    d = ImageDraw.Draw(img)
    f, fs = font(26), font(20)
    for r, (label, path, at) in enumerate(rows):
        y = pad + r * (CELL_H + head + pad)
        d.text((pad, y + head + CELL_H // 2 - 14), label, font=f, fill=(242, 194, 48))
        for c, name in enumerate(cols):
            x = left + pad + c * (CELL_W + pad)
            d.text((x + 2, y + 4), name, font=f, fill=(235, 235, 235))
            if name not in at:
                d.text((x + 2, y + 36), "none", font=fs, fill=(150, 150, 150))
                d.rectangle((x, y + head, x + CELL_W, y + head + CELL_H), fill=(40, 40, 40))
                continue
            t, sid, dup = (at[name] + (None,))[:3]
            if dup:
                d.text((x + 2, y + 36), f"same as {dup}", font=fs, fill=(150, 150, 150))
                d.rectangle((x, y + head, x + CELL_W, y + head + CELL_H), fill=(40, 40, 40))
                continue
            d.text((x + 2, y + 36), f"{t:.2f}s  {sid}", font=fs, fill=(170, 170, 170))
            fr = grab(path, t, tmp)
            if fr is not None:
                img.paste(fr.resize((CELL_W, CELL_H), Image.LANCZOS), (x, y + head))
    img.save(out)
    return out


def clear(out_dir, prefix):
    """Remove an earlier run's numbered sheets, so a shorter run can't leave a stale _2.png behind."""
    for f in os.listdir(out_dir):
        if f.startswith(prefix) and f.endswith(".png"):
            os.remove(os.path.join(out_dir, f))


def beat_sheets(ref, new, out_dir):
    present = {b[0] for r in (ref, new) for b in r["beats"]}
    cols = [b for b in BEATS if b in present]
    rows = [(r["episode"].split("_")[0] + (" (ref)" if r is ref else ""), r["file"], {b[0]: (b[1], b[2], b[3]) for b in r["beats"]})
            for r in (ref, new)]
    clear(out_dir, f"beats_vs_{ref['episode']}_")
    tmp = os.path.join(out_dir, "_grab.png")
    outs = []
    for i in range(0, len(cols), PER_SHEET):
        n = i // PER_SHEET + 1
        outs.append(draw_sheet(rows, cols[i:i + PER_SHEET], os.path.join(out_dir, f"beats_vs_{ref['episode']}_{n}.png"), tmp))
    if os.path.exists(tmp):
        os.remove(tmp)
    return outs


def grab_sheet(res, times, out_dir):
    shots = res["timeline"]["shots"]
    cols = [f"{t:.2f}s" for t in times]
    at = {c: (t, shot_at(shots, t)["id"]) for c, t in zip(cols, times)}
    clear(out_dir, "grabs_")
    tmp = os.path.join(out_dir, "_grab.png")
    outs = []
    for i in range(0, len(cols), PER_SHEET):
        n = i // PER_SHEET + 1
        outs.append(draw_sheet([(res["episode"].split("_")[0], res["file"], at)], cols[i:i + PER_SHEET],
                               os.path.join(out_dir, f"grabs_{n}.png"), tmp))
    if os.path.exists(tmp):
        os.remove(tmp)
    return outs


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


def review(ep_dir, which, with_black=True, measure=True):
    slug, build, path = episode_paths(ep_dir, which)
    tl_path = os.path.join(build, "timeline.json")
    if not os.path.exists(tl_path):
        sys.exit(f"missing {tl_path}: build the episode first")
    with open(tl_path) as f:
        tl = json.load(f)
    info = probe(path)
    res = {"episode": slug, "file": path, "timeline": tl, "probe": info, "pacing": pacing(tl), "beats": beats(tl),
           "checks": check_file(info, tl, which), "warnings": []}
    for sid, hold in cta_holds(tl).items():
        if hold < CTA_MIN_S:
            res["warnings"].append(f"{sid}: call to action on screen {hold} s (under {CTA_MIN_S} s); raise the shot's \"post\"")
    if info["exists"] and measure:
        res["loudness"] = loudness(path)
        if with_black:
            bad = [(s0, s1) for s0, s1 in black_stretches(path) if not black_by_design(tl["shots"], s0, s1)]
            res["checks"].append({"check": "black frames", "ok": not bad,
                                  "value": ", ".join(f'{shot_at(tl["shots"], (a + b) / 2)["id"]} {a:.2f}-{b:.2f}s' for a, b in bad)
                                  or "none unexpected", "target": "only question cards, end fade"})
    return res


def print_report(new, ref, which, out_dir):
    print(f"REVIEW {new['episode']} ({which} copy)" + (f" vs {ref['episode']}" if ref else ""))
    for c in new["checks"]:
        print(f"  {'PASS' if c['ok'] else 'FAIL':4s}  {c['check']:13s} {c['value']:36s} {c['target']}")
    for w in new["warnings"]:
        print(f"  WARN  {w}")
    if new.get("loudness"):
        ln = new["loudness"]
        print(f"  info  loudness      {ln['lufs']} LUFS, true peak {ln['true_peak']} dBFS (encoded; about -14, peak -1.0 to -1.2)")
    for status, text in new.get("zone_rows", []):
        print(f"  {status:4s}  {text}")
    if ref:
        bad = [c["check"] for c in ref["checks"] if not c["ok"]]
        print(f"  ref   {ref['episode']}: {'all file checks pass' if not bad else 'FAILS ' + ', '.join(bad) + ' - its beat grabs may be misplaced; re-render it'}")
    print()
    keys = [k for k in new["pacing"] if k != "kinds"]     # kinds is long: printed under the table
    kw = max(len(k) for k in keys)
    vw = max(24, *(len(str(new["pacing"][k])) + 2 for k in keys), *((len(str(ref["pacing"][k])) + 2 for k in keys) if ref else [0]))
    print(f"  {'pacing':{kw}s}  {new['episode'][:vw - 2]:{vw}s}" + (f"{ref['episode'][:vw - 2]:{vw}s}delta" if ref else ""))
    for k in keys:
        a = new["pacing"][k]
        line = f"  {k:{kw}s}  {str(a):{vw}s}"
        if ref:
            b = ref["pacing"].get(k)
            num = isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool)
            line += f"{str(b):{vw}s}{f'{a - b:+.2f}' if num else ''}"
        print(line)
    for r in (new, ref):
        if r:
            print(f"  {'kinds':{kw}s}  {r['episode']}: {r['pacing']['kinds']}")
    for s in new.get("sheets", []):
        print(f"\n  sheet: {s}", end="")
    print(f"\n  report: {new['report']}")


def main(argv):
    usage = "usage: review.py episodes/<ep> [--ref episodes/<ref>] [--file tiktok|master] [--grab t1,t2,...] [--no-zones] [--json]"
    if argv[:1] in (["-h"], ["--help"]):
        print(usage + "\n\n" + __doc__.strip())
        return 0
    if not argv or argv[0].startswith("--"):
        sys.exit(usage)
    which = argv[argv.index("--file") + 1] if "--file" in argv else "tiktok"
    new = review(argv[0], which, measure="--grab" not in argv)   # grabs need only the timeline and the file
    out_dir = os.path.join(os.path.dirname(new["file"]), "review")
    os.makedirs(out_dir, exist_ok=True)
    if "--grab" in argv:
        times = [float(x) for x in argv[argv.index("--grab") + 1].split(",")]
        for s in grab_sheet(new, times, out_dir):
            print("wrote", s)
        return 0
    ref = review(argv[argv.index("--ref") + 1], which, with_black=False) if "--ref" in argv else None
    if ref and new["probe"]["exists"] and ref["probe"]["exists"]:
        new["sheets"] = beat_sheets(ref, new, out_dir)
    if "--no-zones" not in argv:                           # rendered from the timeline, not read from the file
        new["zones"] = safezones.check(argv[0], out_dir)
        new["zone_rows"] = safezones.report_lines(new["zones"])
        new.setdefault("sheets", []).append(new["zones"]["sheet"])
    new["report"] = os.path.join(out_dir, f"report_{which}" + (f"_vs_{ref['episode']}" if ref else "") + ".json")
    report = {"new": new, "ref": ref}
    for r in (new, ref):
        if r:
            r.pop("timeline", None)
    with open(new["report"], "w") as f:
        json.dump(report, f, indent=1)
    failed = [c["check"] for c in new["checks"] if not c["ok"]]
    warns = len(new["warnings"]) + sum(1 for status, _ in new.get("zone_rows", []) if status == "WARN")
    if "--json" in argv:
        print(json.dumps(report, indent=1))
    else:
        print_report(new, ref, which, out_dir)
        print(f"\nRESULT: {'FAIL - ' + ', '.join(failed) if failed else 'PASS'}"
              + (f" ({warns} warning{'s' if warns != 1 else ''})" if warns else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
