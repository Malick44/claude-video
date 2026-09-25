"""Measure the show's named sounds one at a time, for agents that can't listen.

  cd shows/nobody-moves
  .venv/bin/python <this skill>/scripts/soundprobe.py [name ...] [--episode episodes/<ep>] [--determinism] [--json]
  .venv/bin/python <this skill>/scripts/soundprobe.py --stems episodes/<ep> [--json]
  .venv/bin/python <this skill>/scripts/soundprobe.py --lines episodes/<ep> [--all] [--json]

Each name is resolved exactly as the episodes resolve it: soundtrack.py first, otherwise the
synthesized version from pipeline/sounds.py (soundbank.SYNTH). --episode resolves names as that
episode does instead (its own SOUNDS over soundtrack.py, files looked up in the episode folder
first), so an episode-only replacement can be probed before and after. With no names, every
SYNTH name is probed. Looped names (theme, wind, chimes, crickets) are made 20 s long, the riser 2 s.

Per sound: length, channels, peak (dBFS), RMS over the whole sound, RMS of its loudest 0.5 s
window (the window mixcheck's hit list uses; whole-sound RMS understates a short hit with a long
tail), "placed" level (loudest 0.5 s + its LEVELS gain: compare this between sounds to set a
new sound's level), share of energy above 250 Hz (what a phone speaker plays), share below
60 Hz (mud), L/R correlation, and a short sha256 of the samples.

--determinism generates every probed sound again in two fresh processes, one with names in
reverse order, each with a different PYTHONHASHSEED, and exits 1 if any digest differs. That
catches Python hash(), unseeded random/np.random, and generators sharing one random stream.

--stems episodes/<ep> measures a built episode instead: RMS, share above 250 Hz and share
below 60 Hz for each of build/stems/{dialogue,score,effects}.wav and build/soundtrack.wav
(mixcheck.py covers everything else; build the stems with build_audio.py <ep> --stems).

--lines episodes/<ep> splits the bed under each line into its two stems, to find what buries a
line. Per caption window, on the mono fold-down mixcheck uses: dialogue over bed (mixcheck's
number), dialogue, score and effects RMS, which stem is louder, and the sounds build_audio.py
places over the line: on the score stem the bed, sting_soft and risers (the `under` bus); on
the effects stem the shot's ambiences and any named hit placed from 3 s before the line to its
end (mixcheck.cues). The 5 worst lines by default, every line with --all. The stems must come
from a `build_audio.py <ep> --stems` run after the last sound change.
"""
import hashlib
import json
import os
import subprocess
import sys

import numpy as np


def _pipeline_dir():
    """The show's pipeline/: the working directory's, else shows/nobody-moves in this repo (said on stderr,
    so a copied show run from the wrong folder isn't silently measured as NOBODY MOVES)."""
    here = os.path.join(os.getcwd(), "pipeline")
    if os.path.exists(os.path.join(here, "sounds.py")):
        return here
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))))
    alt = os.path.join(repo, "shows", "nobody-moves", "pipeline")
    if os.path.exists(os.path.join(alt, "sounds.py")):
        if "--worker" not in sys.argv:
            print(f"note: no pipeline/ in {os.getcwd()}; measuring {os.path.dirname(alt)}. "
                  "Run from the show's folder to measure that show.", file=sys.stderr)
        return alt
    sys.exit("run this from the show's folder, e.g. shows/nobody-moves (no pipeline/sounds.py found)")


sys.path.insert(0, _pipeline_dir())
import sounds as snd  # noqa: E402
from common import CTA_DELAY, SHOW_DIR, load_episode, load_sound_sources  # noqa: E402
from soundbank import LOOPED, SYNTH, Bank  # noqa: E402

LEVEL_KEY = {"theme": "bed"}  # sound name -> LEVELS key, where they differ
FLOOR = -120.0
AMBIENCES = ("wind", "chimes", "crickets")
SWELL_SECONDS = 7.0   # sting_soft: a 4 s swell plus its 3 s hall tail
HIT_LOOKBACK = 3.0    # s before a line in which a placed hit's tail can still sit under it


def option(argv, flag):
    """The value after `flag` in argv, or None."""
    if flag not in argv:
        return None
    i = argv.index(flag)
    if i + 1 >= len(argv) or argv[i + 1].startswith("-"):
        sys.exit(f"{flag} needs a value: episodes/<ep>")
    return argv[i + 1].rstrip("/")


def resolver(ep_dir):
    """(sources, base dirs) for names: soundtrack.py, or an episode's merged SOUNDS."""
    if not ep_dir:
        return load_sound_sources(), [SHOW_DIR]
    ep = load_episode(ep_dir)
    return ep.SOUNDS, [ep.DIR, SHOW_DIR]


def seconds_for(name):
    if name in LOOPED:
        return 20.0
    return 2.0 if name == "riser" else None


def render(bank, name):
    y = np.asarray(bank.get(name, seconds_for(name)), dtype=np.float64)
    return y if y.ndim == 2 else y[:, None]


def digest(y):
    return hashlib.sha256(np.ascontiguousarray(y, dtype=np.float64).tobytes()).hexdigest()[:12]


def db(x):
    return max(FLOOR, float(10 * np.log10(x))) if x > 0 else FLOOR


def share(y, lo=None, hi=None):
    """Share of energy (all channels) above lo Hz or below hi Hz."""
    spec = np.abs(np.fft.rfft(y, axis=0)) ** 2
    f = np.fft.rfftfreq(len(y), 1 / snd.SR)
    total = spec.sum()
    mask = f > lo if lo is not None else f < hi
    return float(spec[mask].sum() / total) if total > 0 else 0.0


def loudest_window(y, win=0.5, hop=0.05):
    """RMS (dBFS) of the loudest `win`-second window, zero-padded if the sound is shorter."""
    power = np.mean(y ** 2, axis=1)
    k, h = int(win * snd.SR), int(hop * snd.SR)
    power = np.pad(power, (0, max(0, k - len(power))))
    csum = np.concatenate([[0.0], np.cumsum(power)])
    starts = np.arange(0, len(power) - k + 1, h)
    return db(float(np.max(csum[starts + k] - csum[starts]) / k))


def measure(bank, sources, name):
    y = render(bank, name)
    peak = float(np.max(np.abs(y)))
    rms = db(float(np.mean(y ** 2)))
    win = loudest_window(y)
    level = snd.LEVELS.get(LEVEL_KEY.get(name, name))
    corr = None
    if y.shape[1] == 2:
        left, right = y[:, 0], y[:, 1]
        den = np.sqrt(np.dot(left, left) * np.dot(right, right))
        corr = round(float(np.dot(left, right) / den), 3) if den > 0 else 1.0
    spec = sources.get(name)
    return {"name": name, "source": "synth" if not spec or spec == "synth" else "stock",
            "seconds": round(len(y) / snd.SR, 2), "channels": int(y.shape[1]),
            "peak_dbfs": round(20 * np.log10(peak), 1) + 0.0 if peak > 0 else FLOOR, "rms_dbfs": round(rms, 1),
            "loudest_05s_dbfs": round(win, 1),
            "level_db": level, "placed_dbfs": None if level is None else round(win + level, 1),
            "above_250hz": round(share(y, lo=250), 3), "below_60hz": round(share(y, hi=60), 3),
            "lr_correlation": corr, "sha256": digest(y)}


def worker(names, ep_dir):
    """Hidden mode for --determinism: print {name: digest} for names, generated in this order."""
    bank = Bank(*resolver(ep_dir))
    print(json.dumps({n: digest(render(bank, n)) for n in names}))


def determinism(names, first, ep_dir):
    """Compare this process's digests with two fresh processes (other hash seeds, reverse order)."""
    runs = {"this process": first}
    scope = ["--episode", ep_dir] if ep_dir else []
    for label, seed, order in (("fresh process", "1", names), ("fresh process, reversed", "2", names[::-1])):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        out = subprocess.run([sys.executable, os.path.realpath(__file__), "--worker", *scope, *order],
                             capture_output=True, text=True, env=env, cwd=os.getcwd())
        if out.returncode:
            sys.exit(f"determinism worker failed:\n{out.stderr[-800:]}")
        runs[label] = json.loads(out.stdout.strip().splitlines()[-1])
    bad = [n for n in names if len({r[n] for r in runs.values()}) > 1]
    return {"ok": not bad, "differs": bad, "runs": list(runs)}


def stems(ep_dir, as_json):
    """Low end and phone presence of an episode's stems and mix."""
    import soundfile as sf
    build = os.path.join(ep_dir, "build")
    files = [os.path.join(build, "stems", f"{k}.wav") for k in ("dialogue", "score", "effects")]
    files.append(os.path.join(build, "soundtrack.wav"))
    rows = []
    for path in files:
        if not os.path.exists(path):
            sys.exit(f"missing {path} - run pipeline/build_audio.py {ep_dir} --stems")
        y, _ = sf.read(path, dtype="float64", always_2d=True)
        rows.append({"file": os.path.relpath(path, build), "rms_dbfs": round(db(float(np.mean(y ** 2))), 1),
                     "above_250hz": round(share(y, lo=250), 3), "below_60hz": round(share(y, hi=60), 3)})
    if as_json:
        print(json.dumps({"episode": os.path.basename(os.path.abspath(ep_dir)), "files": rows}, indent=1))
        return 0
    print(f"{'file':22s} {'rms':>6s} {'>250Hz':>7s} {'<60Hz':>6s}")
    for r in rows:
        print(f"{r['file']:22s} {r['rms_dbfs']:6.1f} {r['above_250hz']:7.0%} {r['below_60hz']:6.0%}")
    return 0


def placed_over(shots, cue_list, c):
    """What build_audio.py places under caption c: (score-stem sounds, effects-stem sounds)."""
    a, b = c["start"], c["end"]
    shot = next((s for s in shots if s["id"] == c["shot"]), {})
    bed_start = next((s["start"] for s in shots if "sting" in s.get("sfx", [])), 0.0)
    bed_end = next((s["start"] for s in shots if s["kind"] == "end"), shots[-1]["end"]) + 0.4
    score, fx = [], []
    if bed_start < b and a < bed_end and shot.get("music") != "out":
        score.append("bed")
    for s in shots:   # the `under` bus: sting_soft and risers, ducked like the bed but never gated
        sfx = s.get("sfx", [])
        if "sting_soft" in sfx and s["lines"]:
            at = s["lines"][-1]["start"] - 0.1
            if at < b and a < at + SWELL_SECONDS:
                score.append(f"sting_soft ({'this line' if abs(at + 0.1 - a) < 1e-3 else s['id']})")
        if "sting" in sfx and s["start"] - min(2.0, s["start"]) < b and a < s["start"]:
            score.append("title riser")
        if s["kind"] == "doorbell" and "flicker_at" in s and s["flicker_at"] < b and a < s["flicker_at"] + CTA_DELAY:
            score.append(f"{s['id']} riser")
    fx += [n for n in shot.get("sfx", []) if n in AMBIENCES]
    for t, name, _ in sorted(cue_list, key=lambda q: abs(q[0] - a)):
        if a - HIT_LOOKBACK <= t <= b:
            fx.append(f"{name} {a - t:.2f} s before" if t <= a else f"{name} {t - a:.2f} s in")
    return score, fx


def lines(ep_dir, every, as_json):
    """Per line: dialogue over bed, and the bed split into its score and effects stems."""
    import soundfile as sf
    try:
        from mixcheck import cues
    except ImportError:
        sys.exit("pipeline/mixcheck.py is missing; --lines labels hits with its cues()")
    build = os.path.join(ep_dir, "build")
    paths = {k: os.path.join(build, "stems", f"{k}.wav") for k in ("dialogue", "score", "effects")}
    tl_path = os.path.join(build, "timeline.json")
    for path in (*paths.values(), tl_path):
        if not os.path.exists(path):
            sys.exit(f"missing {path} - run pipeline/build_audio.py {ep_dir} --stems")
    with open(tl_path) as f:
        tl = json.load(f)
    st = {k: sf.read(p, dtype="float64", always_2d=True)[0] for k, p in paths.items()}
    cue_list = cues(tl["shots"])
    rows = []
    for c in tl["captions"]:
        i, j = int(c["start"] * snd.SR), int(c["end"] * snd.SR)
        mono = {k: v[i:j].mean(axis=1) for k, v in st.items()}
        lvl = {k: db(float(np.mean(v ** 2))) if len(v) else FLOOR for k, v in mono.items()}
        bed = mono["score"] + mono["effects"]
        lvl["bed"] = db(float(np.mean(bed ** 2))) if len(bed) else FLOOR
        gap = lvl["score"] - lvl["effects"]
        score, fx = placed_over(tl["shots"], cue_list, c)
        rows.append({"shot": c["shot"], "start": c["start"], "who": c["who"], "text": c["text"],
                     "db": round(lvl["dialogue"] - lvl["bed"], 1), "dialogue_dbfs": round(lvl["dialogue"], 1),
                     "score_dbfs": round(lvl["score"], 1), "effects_dbfs": round(lvl["effects"], 1),
                     "louder": "both" if abs(gap) < 3 else ("score" if gap > 0 else "effects"),
                     "score_sounds": score, "effects_sounds": fx})
    shown = rows if every else sorted(rows, key=lambda r: r["db"])[:5]
    if as_json:
        print(json.dumps({"episode": os.path.basename(os.path.abspath(ep_dir)), "lines": shown}, indent=1))
        return 0
    print(f"{'over bed':>8s}  {'shot':10s} {'start':>6s}  {'who':9s} {'dlg':>6s} {'score':>6s} {'fx':>6s}  louder   "
          "placed over the line (score stem | effects stem)")
    for r in shown:
        placed = f"{', '.join(r['score_sounds']) or '-'} | {', '.join(r['effects_sounds']) or '-'}"
        print(f"{r['db']:5.1f} dB  {r['shot']:10s} {r['start']:6.2f}  {r['who']:9s} {r['dialogue_dbfs']:6.1f} "
              f"{r['score_dbfs']:6.1f} {r['effects_dbfs']:6.1f}  {r['louder']:7s}  {placed}")
    print("dBFS, mono, caption window; over bed = dialogue minus (score + effects), as in mixcheck; louder = the stem\n"
          "at least 3 dB above the other. The score stem is the bed plus the `under` bus (sting_soft, risers).")
    return 0


def main(argv):
    if "-h" in argv or "--help" in argv:
        sys.exit(__doc__)
    if "--stems" in argv:
        return stems(option(argv, "--stems"), "--json" in argv)
    if "--lines" in argv:
        return lines(option(argv, "--lines"), "--all" in argv, "--json" in argv)
    ep_dir = option(argv, "--episode")
    names = [a for i, a in enumerate(argv) if not a.startswith("-") and not (i and argv[i - 1] == "--episode")]
    if "--worker" in argv:
        return worker(names, ep_dir)
    unknown = [n for n in names if n not in SYNTH]
    if unknown:
        sys.exit(f"unknown sound name(s) {unknown}; known: {', '.join(SYNTH)}")
    names = names or list(SYNTH)
    sources, base_dirs = resolver(ep_dir)
    bank = Bank(sources, base_dirs)
    rows = [measure(bank, sources, n) for n in names]
    rep = {"sounds": rows} | ({"episode": os.path.basename(os.path.abspath(ep_dir))} if ep_dir else {})
    if "--determinism" in argv:
        rep["determinism"] = determinism(names, {r["name"]: r["sha256"] for r in rows}, ep_dir)
    if "--json" in argv:
        print(json.dumps(rep, indent=1))
    else:
        print(f"{'name':11s} {'src':5s} {'sec':>6s} {'ch':>2s} {'peak':>6s} {'rms':>6s} {'0.5s':>6s} {'level':>5s} "
              f"{'placed':>7s} {'>250Hz':>7s} {'<60Hz':>6s} {'L/R':>6s}  sha256")
        for r in rows:
            placed = "" if r["placed_dbfs"] is None else f"{r['placed_dbfs']:.1f}"
            level = "" if r["level_db"] is None else f"{r['level_db']:g}"
            corr = "" if r["lr_correlation"] is None else f"{r['lr_correlation']:.2f}"
            print(f"{r['name']:11s} {r['source']:5s} {r['seconds']:6.2f} {r['channels']:2d} {r['peak_dbfs']:6.1f} "
                  f"{r['rms_dbfs']:6.1f} {r['loudest_05s_dbfs']:6.1f} {level:>5s} {placed:>7s} {r['above_250hz']:7.0%} "
                  f"{r['below_60hz']:6.0%} {corr:>6s}  {r['sha256']}")
        print("dBFS; 0.5s = loudest 0.5 s window; placed = 0.5s + LEVELS gain (pre-master, compare between sounds);\n"
              ">250Hz = what a phone speaker plays; <60Hz = mud")
        if "determinism" in rep:
            d = rep["determinism"]
            print("determinism: " + ("PASS, identical in " + ", ".join(d["runs"]) if d["ok"]
                                     else "FAIL, differs across runs: " + ", ".join(d["differs"])))
    return 0 if rep.get("determinism", {"ok": True})["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
