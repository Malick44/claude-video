"""Measure an episode's mix, for agents that can't listen: one command, all the numbers.

  python pipeline/mixcheck.py episodes/<episode> [--json]

Reads <episode>/build/soundtrack.wav and timeline.json, plus build/stems/{dialogue,score,effects}.wav
when present (write them with `pipeline/build_audio.py episodes/<episode> --stems`). Without
stems, or with stems that no longer match the soundtrack, only the soundtrack-level checks run.
Prints a table (one JSON object with --json) and exits 1 if any HARD check fails.

Run `build_audio.py <episode> --stems` right before this. Stems from an earlier mix of the same
timeline (a sound or level changed, then a build without --stems) still correlate with the new
soundtrack at ~0.93, so they read as matching and the per-line and hit numbers describe the old
mix. The only hint is their age: a --stems build writes them ~10 s before soundtrack.wav, so
anything older than STEMS_MAX_AGE gets a NOTE.

  HARD  loudness: integrated -14 +/- 1 LUFS and true peak <= -1.0 dBTP (ffmpeg ebur128)
  HARD  dialogue over bed: in each caption window, dialogue-stem RMS minus (score + effects)
        RMS, both folded to mono (one phone speaker); the median over all lines must be
        >= 12 dB (aim for 15+). Lines under 8 dB are warnings: ambience scenes (wind, chimes)
        sit near 10 dB on purpose, lower is buried.
  HARD  music out: every shot marked "music": "out" has a silent score stem (loudest 100 ms
        under -60 dBFS, ignoring 0.25 s at each edge where the fades live)
  HARD  length: the soundtrack is at least the timeline total (the video is cut there)
  info  loudness range; the 6 loudest 0.5 s windows of the effects stem and the shot (and cue)
        each lands on; share of energy above 250 Hz (what a phone speaker plays) in the effects
        stem and the mix; L/R correlation and mono-sum loudness vs stereo; the level of the last
        100 ms before the timeline total (a decaying tail, not a hard cut)
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

from common import CTA_DELAY, doorbell_clock
from sounds import LEVELS

LUFS_TARGET, LUFS_TOL = -14.0, 1.0
TP_MAX = -1.0          # dBTP; the master aims at -1.5; above -1 the AAC encodes can clip
DIALOGUE_MIN = 12.0    # dB, median over lines (HARD)
DIALOGUE_AIM = 15.0
DIALOGUE_WARN = 8.0    # dB, a single line under this is probably buried
SILENT = -60.0         # dBFS
EDGE = 0.25            # s trimmed off each end of a music-out shot (score fades)
HIT_WIN, N_HITS = 0.5, 6
PHONE_HZ = 250         # phone speakers play little below this
TAIL = 0.1             # s
FLOOR = -120.0         # dBFS reported for digital silence (JSON has no -inf)
STEMS_MAX_AGE = 30.0   # s; --stems writes the stems ~10 s before the master, a plain rebuild takes 40 s+
STEMS = ("dialogue", "score", "effects")


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def rms_db(x):
    """RMS level in dBFS over every sample and channel of x."""
    if not x.size:
        return FLOOR
    ms = float(np.mean(np.square(x, dtype=np.float64)))
    return max(FLOOR, float(10 * np.log10(ms))) if ms > 0 else FLOOR


def ebur128(path, mono=False):
    """Integrated loudness, loudness range and true peak from ffmpeg's ebur128 filter.

    mono=True measures the mono fold-down (L+R)/2 on both channels, so a fully correlated mix
    reads the same as stereo and anything lost to phase shows up as a lower number.
    """
    af = "ebur128=peak=true:framelog=quiet"
    if mono:
        af = "pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1," + af
    err = subprocess.run([ffmpeg(), "-hide_banner", "-nostats", "-i", path, "-af", af, "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    summary = err.split("Summary:")[-1]
    num = r"(-?inf|-?[\d.]+)"
    found = [re.search(p, summary) for p in (rf"I:\s+{num} LUFS", rf"LRA:\s+{num} LU", rf"Peak:\s+{num} dBFS")]
    if "Summary:" not in err or not all(found):
        sys.exit(f"ffmpeg ebur128 failed on {path}:\n{err[-800:]}")
    i, lra, tp = (max(FLOOR, float(m.group(1))) for m in found)
    return {"integrated_lufs": i, "lra_lu": lra, "true_peak_dbtp": tp}


def shot_at(shots, t):
    """(shot id, seconds into that shot) for time t."""
    for s in shots:
        if s["start"] <= t < s["end"]:
            return s["id"], t - s["start"]
    last = shots[-1]
    return (last["id"], t - last["start"]) if t >= last["end"] else (shots[0]["id"], t - shots[0]["start"])


def cues(shots):
    """(time, name, nominal dB) where build_audio.py places the named hits, to label the loudest windows."""
    out = []
    for s in shots:
        sfx = s.get("sfx", [])
        if "sting" in sfx:
            out.append((s["start"], "title sting", LEVELS["sting"]))
        if "sting_end" in sfx:
            out.append((s["start"], "end sting", LEVELS["sting_end"]))
        if "shutter" in sfx:
            out.append((s["start"], "shutter", max(LEVELS["shutter"], LEVELS["impact"] - 4)))
        if s["kind"] == "qcard":
            out.append((s["start"] - 0.45, "whoosh", LEVELS["whoosh"]))
        if s["kind"] == "doorbell" and "flicker_at" in s:
            if "clock_start" in s:
                out.append((s["start"] + doorbell_clock(s)[1], "doorbell jump", LEVELS["jump"]))
            out.append((s["flicker_at"], "flicker", LEVELS["glitch"]))
            out.append((s["flicker_at"] + CTA_DELAY, "reveal hit", max(LEVELS["impact"], LEVELS["braam"])))
    return out


def cue_in(cue_list, a, b):
    """The loudest cue placed inside [a - 0.15, b] (braams and stings peak ~0.3 s after placement)."""
    inside = [c for c in cue_list if a - 0.15 <= c[0] <= b]
    return max(inside, key=lambda c: c[2]) if inside else None


# ---------------------------------------------------------------- checks

def dialogue_over_bed(stems, sr, captions):
    """Per caption window, on the mono fold-down (what one phone speaker plays)."""
    rows = []
    for c in captions:
        a, b = int(c["start"] * sr), int(c["end"] * sr)
        d = rms_db(stems["dialogue"][a:b].mean(axis=1))
        m = rms_db((stems["score"][a:b].astype(np.float64) + stems["effects"][a:b]).mean(axis=1))
        rows.append({"shot": c["shot"], "start": c["start"], "who": c["who"], "text": c["text"],
                     "db": round(d - m, 1), "dialogue_dbfs": round(d, 1), "bed_dbfs": round(m, 1)})
    return rows


def music_out(score, sr, shots):
    rows = []
    blk = int(0.1 * sr)
    for s in shots:
        if s.get("music") != "out":
            continue
        a, b = s["start"] + EDGE, s["end"] - EDGE
        if b <= a:
            a, b = s["start"], s["end"]
        seg = score[int(a * sr): int(b * sr)]
        loudest = max((rms_db(seg[i: i + blk]) for i in range(0, max(1, len(seg) - blk + 1), blk // 2)),
                      default=FLOOR)
        rows.append({"shot": s["id"], "start": s["start"], "end": s["end"], "rms_dbfs": round(rms_db(seg), 1),
                     "loudest_100ms_dbfs": round(loudest, 1), "silent": bool(loudest < SILENT)})
    return rows


def hits(fx, sr, shots, cue_list):
    """The N_HITS loudest non-overlapping HIT_WIN windows (50 ms grid), loudest first.

    Only windows louder than every window within HIT_WIN either side count, so a long sting's
    decay isn't listed again as the next "hit".
    """
    hop = int(0.05 * sr)
    power = np.mean(np.square(fx, dtype=np.float64), axis=1)
    nb = len(power) // hop
    blocks = power[: nb * hop].reshape(nb, hop).mean(axis=1)
    k = int(round(HIT_WIN * sr / hop))
    win = np.convolve(blocks, np.ones(k) / k, mode="valid")
    padded = np.pad(win, k, constant_values=-1.0)
    free = win >= np.max(np.lib.stride_tricks.sliding_window_view(padded, 2 * k + 1), axis=1)
    rows = []
    for _ in range(N_HITS):
        cand = np.where(free, win, -1.0)
        i = int(np.argmax(cand))
        if cand[i] <= 0:
            break
        free[max(0, i - k + 1): i + k] = False
        a = i * hop
        peak = (a + int(np.argmax(np.max(np.abs(fx[a: a + k * hop]), axis=1)))) / sr
        sid, into = shot_at(shots, peak)
        cue = cue_in(cue_list, a / sr, a / sr + HIT_WIN)
        rows.append({"start": round(a / sr, 2), "peak_at": round(peak, 2), "rms_dbfs": round(10 * np.log10(cand[i]), 1),
                     "shot": sid, "into_shot": round(into, 2), "cue": cue[1] if cue else "",
                     "peak_after_cue": round(peak - cue[0], 2) if cue else None})
    return rows


def above_hz(x, sr, hz=PHONE_HZ):
    """Share of the signal's energy above hz (both channels)."""
    spec = np.abs(np.fft.rfft(x, axis=0)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / sr)
    total = spec.sum()
    return float(spec[f > hz].sum() / total) if total > 0 else 0.0


def correlation(left, right):
    """Phase-meter correlation: +1 mono, 0 unrelated, -1 cancels in mono."""
    den = np.sqrt(np.dot(left, left) * np.dot(right, right))
    return float(np.dot(left, right) / den) if den > 0 else 1.0


def mono_check(mix, sr, shots, total):
    left, right = mix[:, 0].astype(np.float64), mix[:, 1].astype(np.float64)
    worst = None
    w, hop = sr, sr // 2
    for a in range(0, min(len(mix), int(total * sr)) - w + 1, hop):
        if rms_db(mix[a: a + w]) < -40:   # skip near-silence, its correlation means nothing
            continue
        c = correlation(left[a: a + w], right[a: a + w])
        if worst is None or c < worst["correlation"]:
            worst = {"correlation": round(c, 2), "start": round(a / sr, 1), "shot": shot_at(shots, a / sr + 0.5)[0]}
    return {"correlation": round(correlation(left, right), 3), "lowest_1s_window": worst}


def stem_match(stems, mix, sr, max_lag=0.02):
    """(correlation, lag in s) of the stem sum with the mastered soundtrack, at the best lag.

    The master's limiter looks ahead, so the soundtrack runs a few ms behind the stems. A low
    correlation at every lag means the stems come from another build.
    """
    n = 1 << int(np.log2(min(len(mix), *(len(s) for s in stems.values()))))  # power of 2: fast FFT
    a = sum(stems[k][:n].astype(np.float64) for k in STEMS).mean(axis=1)
    b = mix[:n].astype(np.float64).mean(axis=1)
    xc = np.fft.irfft(np.conj(np.fft.rfft(a)) * np.fft.rfft(b), n)   # xc[k] = sum a[t] * b[t + k]
    k = int(max_lag * sr)
    lags = np.r_[0: k + 1, -k: 0]
    best = int(lags[np.argmax(xc[lags])])
    den = np.sqrt(np.dot(a, a) * np.dot(b, b))
    return (float(xc[best] / den) if den > 0 else 0.0), best / sr


# ---------------------------------------------------------------- report

def measure(ep_dir):
    build = os.path.join(ep_dir, "build")
    track, tl_path = os.path.join(build, "soundtrack.wav"), os.path.join(build, "timeline.json")
    for p in (track, tl_path):
        if not os.path.exists(p):
            sys.exit(f"missing {p} - run pipeline/build_audio.py {ep_dir} --stems first")
    with open(tl_path) as f:
        tl = json.load(f)
    shots, total = tl["shots"], tl["total"]
    mix, sr = sf.read(track, dtype="float32", always_2d=True)
    rebuild = f"pipeline/build_audio.py {ep_dir} --stems"
    rep = {"episode": os.path.basename(os.path.abspath(ep_dir)), "checks": [], "notes": []}

    def check(name, hard, ok, value, target=""):
        rep["checks"].append({"name": name, "hard": hard, "ok": bool(ok) if hard else None, "value": value, "target": target})

    # ---- soundtrack level
    loud = ebur128(track)
    mono = ebur128(track, mono=True)
    rep["loudness"] = loud
    check("loudness", True, abs(loud["integrated_lufs"] - LUFS_TARGET) <= LUFS_TOL,
          f"{loud['integrated_lufs']:.1f} LUFS", f"{LUFS_TARGET:g} +/- {LUFS_TOL:g}")
    check("true peak", True, loud["true_peak_dbtp"] <= TP_MAX, f"{loud['true_peak_dbtp']:.1f} dBTP", f"<= {TP_MAX:g}")
    check("loudness range", False, None, f"{loud['lra_lu']:.1f} LU")

    # ---- stems
    paths = {k: os.path.join(build, "stems", f"{k}.wav") for k in STEMS}
    stems = None
    if all(os.path.exists(p) for p in paths.values()):
        stems = {k: sf.read(p, dtype="float32", always_2d=True)[0] for k, p in paths.items()}
        match, lag = stem_match(stems, mix, sr)
        rep["stem_match"] = {"correlation": round(match, 3), "soundtrack_lag_ms": round(lag * 1000, 1)}
        # a matching build reads ~0.93 (the master compresses and limits); stems from another cut ~0
        if match < 0.8 or len({len(s) for s in stems.values()} | {len(mix)}) > 1:
            rep["notes"].append(f"stems don't match soundtrack.wav (correlation {match:.2f}); "
                                f"per-line checks skipped - rebuild with: {rebuild}")
            stems = None
            rep["stems"] = "stale"
        else:
            rep["stems"] = "present"
            age = os.path.getmtime(track) - min(os.path.getmtime(p) for p in paths.values())
            rep["stem_match"]["stems_older_s"] = round(age, 1)
            if age > STEMS_MAX_AGE:
                old = f"{age:.0f} s" if age < 120 else f"{age / 60:.0f} min"
                rep["notes"].append(f"stems are {old} older than soundtrack.wav (a --stems build writes them ~10 s "
                                    f"before it), so soundtrack.wav was probably rebuilt without --stems. The per-line "
                                    f"and hit numbers may describe an older mix - rebuild with: {rebuild}")
    else:
        rep["stems"] = "absent"
        rep["notes"].append(f"no stems: dialogue-over-bed, music-out and hit checks need: {rebuild}")

    if stems:
        lines = dialogue_over_bed(stems, sr, tl["captions"])
        med = float(np.median([r["db"] for r in lines])) if lines else None
        rep["dialogue"] = {"median_db": med, "worst": sorted(lines, key=lambda r: r["db"])[:5],
                           "warnings": [r for r in lines if r["db"] < DIALOGUE_WARN], "lines": lines}
        check("dialogue over bed", True, med is None or med >= DIALOGUE_MIN,
              "no captions" if med is None else f"median {med:.1f} dB", f">= {DIALOGUE_MIN:g} (aim {DIALOGUE_AIM:g}+)")
        rep["music_out"] = music_out(stems["score"], sr, shots)
        silent = sum(r["silent"] for r in rep["music_out"])
        check("music-out silence", True, silent == len(rep["music_out"]),
              f"{silent}/{len(rep['music_out'])} shots silent" if rep["music_out"] else "no music-out shots",
              f"score < {SILENT:g} dBFS")
        rep["hits"] = hits(stems["effects"], sr, shots, cues(shots))

    # ---- length and tail
    dur = len(mix) / sr
    tail = rms_db(mix[max(0, int((total - TAIL) * sr)): int(total * sr)])
    rep["length"] = {"soundtrack_s": round(dur, 3), "timeline_total_s": total, "tail_dbfs": round(tail, 1),
                     "mix_rms_dbfs": round(rms_db(mix), 1)}
    check("length", True, dur >= total, f"{dur:.2f} s", f">= {total:.2f} s")
    check("tail", False, None, f"{tail:.1f} dBFS", f"last {TAIL * 1000:.0f} ms before {total:.2f} s")

    # ---- phone speaker and mono playback
    rep["presence"] = {"mix_above_250hz": round(above_hz(mix, sr), 3)}
    value = f"mix {rep['presence']['mix_above_250hz']:.0%}"
    if stems:
        rep["presence"]["effects_above_250hz"] = round(above_hz(stems["effects"], sr), 3)
        value = f"effects {rep['presence']['effects_above_250hz']:.0%}, " + value
    check("phone presence", False, None, value, f"energy above {PHONE_HZ} Hz")
    rep["mono"] = mono_check(mix, sr, shots, total) | {
        "mono_lufs": mono["integrated_lufs"], "mono_minus_stereo_lu": round(mono["integrated_lufs"] - loud["integrated_lufs"], 1)}
    check("mono", False, None, f"corr {rep['mono']['correlation']:.2f}, mono sum {rep['mono']['mono_minus_stereo_lu']:+.1f} LU")

    failed = [c["name"] for c in rep["checks"] if c["hard"] and not c["ok"]]
    rep["ok"], rep["failed"] = not failed, failed
    return rep


def clip(text, n=58):
    return text if len(text) <= n else text[: n - 3] + "..."


def print_report(rep):
    L = rep["length"]
    sm = rep.get("stem_match")
    stems = rep["stems"]
    if sm:
        lag = f", soundtrack {sm['soundtrack_lag_ms']:+.1f} ms" if rep["stems"] == "present" else ""
        stems += f" (match {sm['correlation']:.3f}{lag})"
    print(f"MIXCHECK {rep['episode']}")
    print(f"  soundtrack {L['soundtrack_s']:.2f} s | timeline {L['timeline_total_s']:.2f} s | stems: {stems}\n")
    for c in rep["checks"]:
        tag = ("HARD", "PASS" if c["ok"] else "FAIL") if c["hard"] else ("info", "")
        print(f"  {tag[0]}  {tag[1]:4s}  {c['name']:18s} {c['value']:34s} {c['target']}")
    if "dialogue" in rep:
        d = rep["dialogue"]
        print("\nDialogue over bed, 5 worst lines (mono dialogue-stem RMS minus score+effects RMS, caption window)")
        for r in d["worst"]:
            print(f"  {r['db']:5.1f} dB  {r['shot']:10s} {r['start']:6.2f} s  {r['who']:9s} \"{clip(r['text'])}\"")
        warn = ", ".join(f"{r['shot']}@{r['start']:.2f}s {r['db']:.1f} dB" for r in d["warnings"][:8]) or "none"
        if len(d["warnings"]) > 8:
            warn += f" ... (+{len(d['warnings']) - 8} more, all in --json)"
        print(f"  under {DIALOGUE_WARN:g} dB (check it isn't buried): {warn}")
    if rep.get("music_out"):
        print(f"\nMusic-out shots (score stem, {EDGE:g} s trimmed at each edge)")
        for r in rep["music_out"]:
            print(f"  {r['shot']:10s} {r['start']:6.2f}-{r['end']:6.2f} s  loudest 100 ms {r['loudest_100ms_dbfs']:6.1f} dBFS  "
                  f"{'silent' if r['silent'] else 'NOT SILENT'}")
    if "hits" in rep:
        print(f"\nHits: {N_HITS} loudest {HIT_WIN:g} s windows of the effects stem (loudest first)")
        for r in rep["hits"]:
            cue = f"{r['cue']} (peak {r['peak_after_cue']:+.2f} s)" if r["cue"] else "(no placed cue)"
            print(f"  {r['rms_dbfs']:6.1f} dBFS  peak {r['peak_at']:6.2f} s  {r['shot']:10s} +{r['into_shot']:5.2f} s  {cue}")
    m, w = rep["mono"], rep["mono"]["lowest_1s_window"]
    print(f"\nMono: L/R correlation {m['correlation']:.3f}; mono sum {m['mono_lufs']:.1f} LUFS "
          f"({m['mono_minus_stereo_lu']:+.1f} LU vs stereo)"
          + (f"; lowest 1 s window {w['correlation']:.2f} at {w['start']:.1f} s ({w['shot']})" if w else ""))
    print(f"Tail: {L['tail_dbfs']:.1f} dBFS in the last {TAIL * 1000:.0f} ms (mix average {L['mix_rms_dbfs']:.1f} dBFS)")
    for n in rep["notes"]:
        print(f"NOTE: {n}")
    hard = [c for c in rep["checks"] if c["hard"]]
    verdict = "PASS" if rep["ok"] else "FAIL (" + ", ".join(rep["failed"]) + ")"
    print(f"\nRESULT: {verdict} - {sum(c['ok'] for c in hard)}/{len(hard)} hard checks")


def main(argv):
    args = [a for a in argv if not a.startswith("-")]
    if len(args) != 1 or "-h" in argv or "--help" in argv:
        sys.exit(__doc__)
    rep = measure(args[0].rstrip("/"))
    if "--json" in argv:
        print(json.dumps(rep, indent=1))
    else:
        print_report(rep)
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
