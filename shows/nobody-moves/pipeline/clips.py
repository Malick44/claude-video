"""File the generated 3D clips that reenactments play, and check them.

  python pipeline/clips.py add episodes/<ep> <key> <file> --generator "Kling 2.5" [--prompt "..."]
                               [--retime 0.5] [--credit "..."] [--force]
  python pipeline/clips.py add series <key> <file> --generator "..." [--episode episodes/<ep> | --prompt "..."]
  python pipeline/clips.py sheet episodes/<ep>       # first, middle and last frame of each clip -> build/review/clips.png
  python pipeline/clips.py lint episodes/<ep>        # the prompt lint on CLIPS and the rx_ keyframes in STILLS

Clips live like stills: episodes/<ep>/clips/<key>.mp4 for one episode, <show>/clips/<key>.mp4 for the
series library; an episode's clip overrides a library clip with the same key. Prefix keys with rx_.

`add` takes any video file a generator gave you and files a mezzanine: H.264, yuv420p, CRF 17, a constant
30 fps, no audio (a generator's audio is random; the mix makes its own), longest side 1920 or less, never
cropped (the episode's "kb" frames it), turned upright and with square pixels (a phone clip's display
rotation and a non-square pixel aspect are applied, since the renderer reads neither). It refuses a file with no video, under 1 s or over 10 s, and an
existing clip without --force. --retime F retimes once, here, with optical flow (0.5 = half speed), so
the episode plays the take at speed 1.0 and nothing is slowed twice. The prompt and negative come from
the episode's CLIPS and CLIP_SOURCES (pass --prompt only for a clip with no CLIPS entry), and every
filing is recorded in clips/clips.json with both files' sha1, the generator and "ai_generated" (true for a
generated clip).
It warns when a 9:16 cover crop leaves under 720 px of width, when the clip starts or ends black, and
when its middle frame is too dark for the reenactment look.

lint_prompt() is shared with build_audio.py, which lints an episode's CLIPS and rx_ keyframes on every
build. Motion prompts must name no person: the person who puts the yard back is never shown.

Every clip is filed through add(), whatever made it: pipeline/blender_reenact.py files a Blender render by
calling add() on its frames (as a lossless intermediate), with its provenance as extra clips.json fields
("quality", "proxy", "sidecar": <key>.blender.json, ...), so a rendered clip lands in the same mezzanine, the
same checks and the same index as a generated one. record_entry() and clip_entry() are the one reader and
writer of clips.json.
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import numpy as np

from common import (CLIP_FPS, SHOW_DIR, clip_info, clip_path, ffmpeg_exe, file_sha1, load_episode)

MIN_S, MAX_S = 1.0, 10.0          # accepted clip lengths, after any retime
MAX_SIDE = 1920
MIN_CROP_W = 720                  # width left after a 9:16 cover crop, below which a clip looks soft
DARK_LUMA = 60                    # mean luma (0-255) of the middle frame; the reenactment look aims at 100

# Human words a motion prompt may not use, once its negated clauses are stripped ("No people, no text."
# is fine). Canon: the person who puts the yard back is never shown, and a reenactment shows no human.
HUMAN = re.compile(r"\b(person|persons|people|man|men|woman|women|human|humans|hand|hands|arm|arms|finger|fingers|"
                   r"homeowner|homeowners|gardener|gardeners|child|children|kid|kids|figure|figures)\b|silhouette of a",
                   re.I)
NEGATED = re.compile(r"\b(?:no|never|not|without)\b[^,;.]*", re.I)
MONTH = re.compile(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b")
CLOCK = re.compile(r"\d:\d\d|\b\d{1,2}/\d{1,2}\b|\b(?:AM|PM|a\.m\.|p\.m\.)(?=\W|$)")
ASPECT = re.compile(r"\b(?:9:16|16:9|4:5|5:4|3:4|4:3|2:3|3:2|1:1|21:9)\b")   # aspect ratios aren't clock times


# ---------------------------------------------------------------- the prompt lint

def suffixes():
    """{"still": ..., "motion": ...}: the bible's shared 3D style suffixes, read from SERIES.md (the
    quoted paragraph after "**The still suffix**" / "**The motion suffix**"), so the lint follows it."""
    path = os.path.join(SHOW_DIR, "SERIES.md")
    if not os.path.exists(path):
        return {}
    lines = open(path, encoding="utf-8").read().splitlines()
    out = {}
    for kind in ("still", "motion"):
        for i, ln in enumerate(lines):
            if f"**The {kind} suffix**" in ln:
                quote = next((x for x in lines[i + 1:i + 4] if x.startswith(">")), None)
                if quote:
                    out[kind] = quote.lstrip("> ").strip()
                break
    return out


def lint_prompt(prompt, kind):
    """(errors, warnings) for a generator prompt. kind "motion" (a CLIPS entry): fails on human words
    outside negated clauses, warns without the motion suffix. kind "keyframe" (an rx_ key in STILLS): not
    checked for human words (they quote reference blocks with hands), but warns without the still
    suffix, or with a date, a clock time or "slow motion", which image models draw as text or blur."""
    errors, warnings = [], []
    sfx = suffixes()
    if kind == "motion":
        kept = NEGATED.sub("", prompt)
        found = sorted({m.group(0).lower() for m in HUMAN.finditer(kept)})
        if found:
            errors.append(f"names a person ({', '.join(found)}): a reenactment never shows a human. Say what moves "
                          "as a rigid object, and put people only in a negated clause (\"no people\") or the negative")
        if sfx.get("motion") and sfx["motion"] not in prompt:
            warnings.append("doesn't end with the motion suffix from SERIES.md (\"Shared 3D style suffixes\")")
    elif kind == "keyframe":
        if sfx.get("still") and sfx["still"] not in prompt:
            warnings.append("doesn't end with the still suffix from SERIES.md (\"Shared 3D style suffixes\")")
        when = MONTH.findall(prompt) + CLOCK.findall(ASPECT.sub("", prompt))
        if when:
            warnings.append(f"has a date or clock time ({', '.join(sorted(set(when)))}): image models draw it as text; "
                            "say \"Time and state: night.\" instead")
        if re.search(r"slow[- ]motion", prompt, re.I):
            warnings.append("asks for slow motion: a still prompt that asks for motion gets motion blur")
    else:
        raise ValueError(kind)
    return errors, warnings


def lint_episode(ep):
    """[(key, kind, errors, warnings)] for every CLIPS prompt and every rx_ keyframe in STILLS."""
    out = []
    for key, prompt in getattr(ep, "CLIPS", {}).items():
        out.append((key, "motion", *lint_prompt(prompt, "motion")))
    for key, prompt in getattr(ep, "STILLS", {}).items():
        if key.startswith("rx_") and isinstance(prompt, str):
            out.append((key, "keyframe", *lint_prompt(prompt, "keyframe")))
    return out


# ---------------------------------------------------------------- add

def ffmpeg(*args):
    r = subprocess.run([ffmpeg_exe(), "-hide_banner", "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg failed: {r.stderr[-600:]}")


def black_ends(path, seconds):
    """Which ends ("start", "end") of a clip are black (ffmpeg blackdetect)."""
    err = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", path, "-an", "-vf", "blackdetect=d=0.1:pix_th=0.10",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    spans = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    return [name for name, hit in (("start", any(a < 0.05 for a, _ in spans)),
                                   ("end", any(b > seconds - 0.1 for _, b in spans))) if hit]


def frame_at(path, t, w=None):
    """One frame of a clip as a PIL image (for checks and the sheet; renders use render.ClipReader).
    t=None is the last frame (a seek to its exact time can land past it and return nothing)."""
    from PIL import Image
    tmp = tempfile.mkdtemp(prefix="nm-clip-")
    try:
        out = os.path.join(tmp, "f.png")
        scale = ["-vf", f"scale={w}:-2"] if w else []
        if t is None:       # decode the last 0.3 s, keeping only the final frame
            ffmpeg("-sseof", "-0.3", "-i", path, "-update", "1", *scale, out)
        else:
            ffmpeg("-ss", f"{max(0.0, t):.3f}", "-i", path, "-frames:v", "1", *scale, out)
        return Image.open(out).convert("RGB") if os.path.exists(out) else None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def mean_luma(img):
    return float(np.asarray(img.convert("L"), dtype=np.float32).mean())


def clip_entry(folder, key):
    """clips/clips.json's entry for `key` (None if the clip has none)."""
    index = os.path.join(folder, "clips.json")
    if not os.path.exists(index):
        return None
    with open(index, encoding="utf-8") as f:
        return json.load(f).get(key)


def record_entry(folder, key, entry):
    """Write `key`'s entry into <folder>/clips.json (the one writer: add() for every clip), through a temp file
    so an interrupted write never leaves half an index."""
    index = os.path.join(folder, "clips.json")
    entries = json.load(open(index, encoding="utf-8")) if os.path.exists(index) else {}
    entries[key] = entry
    tmp = index + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, index)


def add(target, key, src, generator, prompt=None, retime=None, credit=None, force=False, episode=None, *,
        extra=None, ai_generated=True, described=False, low_res_fix="generate 9:16"):
    """File `src` as clip `key` in episodes/<ep>/clips/ or the series library (target "series").

    Keyword options, for a clip made by a tool rather than a generator (blender_reenact.py): `extra` adds fields
    to the clips.json entry (they override the standard ones); `ai_generated` records whether AI made it;
    `described` marks `prompt` as a description of a rendered scene, which no generator ever reads, so the
    prompt lint (for generator prompts) skips it; `low_res_fix` is the advice the low-width warning gives."""
    if target == "series":
        folder = os.path.join(SHOW_DIR, "clips")
        ep = load_episode(episode) if episode else None
    else:
        ep = load_episode(target)
        folder = ep.CLIPS_DIR
    if not key.startswith("rx_"):
        print(f"warning: clip key {key!r} doesn't start with rx_ (reenactment clips do)", file=sys.stderr)
    clips = getattr(ep, "CLIPS", {}) if ep else {}
    sources = getattr(ep, "CLIP_SOURCES", {}).get(key, {}) if ep else {}
    prompt = prompt or clips.get(key)
    if not prompt:
        sys.exit(f"no prompt for {key}: add it to CLIPS in episode.py (or pass --prompt for a clip with no CLIPS entry"
                 + (", or --episode for a series clip)" if target == "series" else ")"))
    errors, warnings = ([], []) if described else lint_prompt(prompt, "motion")
    if errors:
        sys.exit(f"{key}: the motion prompt " + "; ".join(errors))
    for w in warnings:
        print(f"warning: {key}: the motion prompt {w}", file=sys.stderr)
    out = os.path.join(folder, f"{key}.mp4")
    if os.path.exists(out) and not force:
        sys.exit(f"{out} already exists; pass --force to replace it")
    if not os.path.exists(src):
        sys.exit(f"no such file: {src}")
    info = clip_info(src)
    if not info:
        sys.exit(f"{src} has no video stream")
    seconds = info["seconds"] / (retime or 1.0)
    if not MIN_S <= seconds <= MAX_S:
        sys.exit(f"{src} is {seconds:.2f} s{' after the retime' if retime else ''}; a clip must be {MIN_S:g}-{MAX_S:g} s")
    # the picture as displayed: clip_info's frame is already upright (ffmpeg applies a display rotation
    # here too), and a non-square pixel aspect is resolved to square pixels (setsar=1), which the renderer needs
    dw, dh = info["w"] * info["sar"][0] / info["sar"][1], info["h"]
    scale = min(1.0, MAX_SIDE / max(dw, dh))
    w, h = int(dw * scale) // 2 * 2, int(dh * scale) // 2 * 2
    vf = []
    if retime:
        # optical flow, once, at intake: interpolate to 30/F fps, then stretch the timestamps by 1/F
        vf += [f"minterpolate=fps={CLIP_FPS / retime:g}:mi_mode=mci", f"setpts=PTS/{retime:g}"]
    vf += [f"fps={CLIP_FPS}", f"scale={w}:{h}:flags=lanczos", "setsar=1", "format=yuv420p"]
    os.makedirs(folder, exist_ok=True)
    tmp = out + ".tmp.mp4"
    ffmpeg("-i", src, "-an", "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "slow", "-crf", "17",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp)
    got = clip_info(tmp)
    if not got or not MIN_S <= got["seconds"] <= MAX_S + 0.1:
        os.remove(tmp)
        sys.exit(f"{src}: the mezzanine came out {got and got['seconds']} s; not filed")
    os.replace(tmp, out)
    crop_w = min(got["w"], got["h"] * 9 / 16)
    if crop_w < MIN_CROP_W:
        print(f"warning: {key}: a 9:16 cover crop leaves {crop_w:.0f} px of width (under {MIN_CROP_W}); "
              f"{low_res_fix}", file=sys.stderr)
    for end in black_ends(out, got["seconds"]):
        print(f"warning: {key}: the clip {'starts' if end == 'start' else 'ends'} black; trim it before filing, "
              "or set the shot's \"in\"/\"out\" past it (review.py fails black frames inside a reenactment)", file=sys.stderr)
    try:
        mid = frame_at(out, got["seconds"] / 2)
    except ImportError:     # no PIL in this Python (Blender's own): the luma check is skipped, nothing else
        mid = None
        print(f"note: {key}: no PIL here, so the middle frame's luma isn't checked", file=sys.stderr)
    if mid is not None and mean_luma(mid) < DARK_LUMA:
        print(f"warning: {key}: the middle frame's mean luma is {mean_luma(mid):.0f}/255, too dark for the "
              f"reenactment look (under {DARK_LUMA}; aim for 100)", file=sys.stderr)
    record_entry(folder, key, {
        "file": f"{key}.mp4", "source": os.path.basename(src), "source_sha1": file_sha1(src), "sha1": file_sha1(out),
        "generator": generator, "prompt": prompt, "negative": sources.get("negative"),
        "keyframe": sources.get("keyframe"), "references": sources.get("keyframe_refs"), "retime": retime,
        "date": datetime.date.today().isoformat(), "w": got["w"], "h": got["h"], "seconds": got["seconds"],
        "credit": credit, "ai_generated": bool(ai_generated), **(extra or {}),
    })
    print(f"wrote {out} ({got['w']}x{got['h']}, {got['seconds']:.2f} s at {CLIP_FPS} fps) and its clips.json entry")
    return out


# ---------------------------------------------------------------- the review sheet

def sheet(ep_dir):
    """build/review/clips.png: the first, middle and last frame of every clip the episode's shots use."""
    from PIL import Image, ImageDraw, ImageFont
    ep = load_episode(ep_dir)
    keys = []
    for s in ep.SHOTS:
        if s.get("clip") and s["clip"] not in keys:
            keys.append(s["clip"])
    if not keys:
        sys.exit("this episode's shots use no clips")
    cell_w, cell_h, pad, head, left = 300, 533, 12, 40, 220
    img = Image.new("RGB", (left + 3 * (cell_w + pad) + pad, len(keys) * (cell_h + head + pad) + pad), (18, 18, 18))
    d = ImageDraw.Draw(img)
    fp = os.path.join(SHOW_DIR, "assets", "fonts", "Inter.ttf")
    f = ImageFont.truetype(fp, 22) if os.path.exists(fp) else ImageFont.load_default()
    for r, key in enumerate(keys):
        y = pad + r * (cell_h + head + pad)
        path = clip_path(ep.DIR, key)
        d.text((pad, y + head + cell_h // 2 - 12), key, font=f, fill=(242, 194, 48))
        if not path:
            d.text((left + pad, y + head + cell_h // 2 - 12), "not filed yet (the shot renders its fallback still)",
                   font=f, fill=(208, 52, 44))
            continue
        info = clip_info(path)
        last = max(0.0, (info["frames"] - 1) / info["fps"])
        for c, (name, t) in enumerate((("first", 0.0), ("middle", last / 2), ("last", last))):
            x = left + pad + c * (cell_w + pad)
            d.text((x + 2, y + 6), f"{name} {t:.2f}s", font=f, fill=(235, 235, 235))
            fr = frame_at(path, None if name == "last" else t)
            if fr is not None:
                fr.thumbnail((cell_w, cell_h))
                img.paste(fr, (x + (cell_w - fr.width) // 2, y + head + (cell_h - fr.height) // 2))
    out = os.path.join(ep.BUILD, "review", "clips.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)
    print("wrote", out)
    return out


# ---------------------------------------------------------------- CLI

def opt(argv, name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    cmd = argv[0]
    if cmd == "add":
        pos = []
        skip = False
        for a in argv[1:]:                          # positionals: everything that isn't an option or its value
            if skip:
                skip = False
            elif a.startswith("--"):
                skip = a != "--force"
            else:
                pos.append(a)
        if len(pos) != 3 or "--generator" not in argv:
            sys.exit('usage: clips.py add <episodes/<ep>|series> <key> <file> --generator "..." [--prompt "..."] '
                     '[--retime F] [--credit "..."] [--episode episodes/<ep>] [--force]')
        retime = float(opt(argv, "--retime")) if "--retime" in argv else None
        if retime is not None and not 0.1 <= retime <= 4.0:
            sys.exit("--retime is a playback rate, 0.1-4.0 (0.5 = half speed)")
        add(pos[0], pos[1], pos[2], opt(argv, "--generator"), opt(argv, "--prompt"), retime, opt(argv, "--credit"),
            "--force" in argv, opt(argv, "--episode"))
        return 0
    if cmd == "sheet" and len(argv) == 2:
        sheet(argv[1])
        return 0
    if cmd == "lint" and len(argv) == 2:
        bad = 0
        for key, kind, errors, warnings in lint_episode(load_episode(argv[1])):
            for e in errors:
                bad += 1
                print(f"FAIL  {key} ({kind}): {e}")
            for w in warnings:
                print(f"WARN  {key} ({kind}): {w}")
            if not errors and not warnings:
                print(f"ok    {key} ({kind})")
        return 1 if bad else 0
    sys.exit("usage: clips.py add|sheet|lint ... (see clips.py --help)")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
