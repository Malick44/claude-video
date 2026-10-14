"""Fit the remake's takes and clips to each other, from a build's timeline.json.

build_audio.py builds the timeline and validates the shots (the label, the hit's pre-roll, name cards,
lengths). This adds what the pipeline doesn't:
- the pace gate (D1, D2, D7): the runtime against the 50 s ceiling and NOTES.md's trim trigger
  (49.5 s), words/min overall and while someone is speaking, the same timeline projected to 150 and
  165 words/min while speaking, and the speaking pace the takes need;
- with --ref, each line's length against a reference build (the Kokoro scratch build), so a v4 take
  more than 5% longer than its Kokoro take is named;
- for each reenactment, where its move falls in the generated take: the hold time to write into the
  motion prompt (a move on a key word: "For the first X seconds"; a landing after the line: "At about
  Y seconds"), the `in` to set once a clip exists, whether the generated take covers in + dur, the
  dur this take needs, and the longest take a clip fitted to this one can absorb.

Run from shows/nobody-moves after building the audio:
  .venv/bin/python pipeline/build_audio.py episodes/ep01r_three_feet_reenacted
  .venv/bin/python episodes/ep01r_three_feet_reenacted/tools/fit_takes.py [--timeline T] [--ref R]
T defaults to the episode's build/timeline.json; R is another build's timeline.json, e.g. the Kokoro
arm's copy from docs/AUDIO_ELEVENLABS_V4.md's A/B script. Exit 1 when the runtime is 50 s or more, a
clip's source runs past its generated take, or a line runs past its reenactment's dur.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

EP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CEILING = 50.0          # D7: main episodes stay under 50 s
TRIM_AT = 49.5          # NOTES.md, "Pace": the ordered trim list starts over this
HEADROOM_MIN = 1.5      # D2: the headroom the Kokoro scratch timeline must leave for longer takes
FLOOR_WPM = 150         # D1: the floor while someone is speaking
TARGET_WPM = 165        # D1: the target while someone is speaking
OVERALL = (110, 120)    # D1: words/min overall
TAKE_GROWTH = 0.05      # D1: each v4 take no longer than its Kokoro take + 5%
AFTER_LINE = 0.5        # at least this much action after a reenactment's line, before the cut
MAX_DUR = 6.0           # a reenactment is 3-6 s
SHORT_TAKE = 5          # generators make 5 s or 10 s takes
# The word each reenactment's move lands on; None means the move lands after the line ends.
KEY_WORDS = {"heist": "Then", "action": None}
WORD = re.compile(r"[A-Za-z0-9:']+(?:-[A-Za-z]+)?")


def load_episode(ep_dir=EP_DIR):
    spec = importlib.util.spec_from_file_location("episode", os.path.join(ep_dir, "episode.py"))
    ep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ep)
    return ep


def load_timeline(path=None):
    path = path or os.path.join(EP_DIR, "build", "timeline.json")
    if not os.path.exists(path):
        sys.exit(f"{path} not found: build the audio first (pipeline/build_audio.py {os.path.relpath(EP_DIR)})")
    with open(path) as f:
        return json.load(f)


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def tc(x):
    return f"{int(x // 60)}:{x % 60:05.2f}"


def pace(tl):
    """Words, speaking seconds, silence, and the projections D1 and D2 are read against."""
    caps = tl["captions"]
    words = sum(len(WORD.findall(c["text"])) for c in caps)
    speak = sum(c["end"] - c["start"] for c in caps)
    total = tl["total"]
    silence = total - speak
    p = {"total": total, "words": words, "speak": speak, "silence": silence,
         "wpm": words / total * 60, "wpm_speaking": words / speak * 60 if speak else 0.0}
    for wpm in (FLOOR_WPM, TARGET_WPM):
        t = silence + words / wpm * 60
        p[wpm] = {"total": t, "wpm": words / t * 60}
    room = (CEILING - HEADROOM_MIN) - silence
    p["need_head"] = words / room * 60 if room > 0 else float("inf")
    room = words / OVERALL[0] * 60 - silence
    p["need_overall"] = words / room * 60 if room > 0 else float("inf")
    return p


def reenactments(ep, tl):
    """One dict per reenactment shot: its line in the take, the move's place in the generated take,
    and the clip checks."""
    shots = {s["id"]: s for s in tl["shots"]}
    out = []
    for s in ep.SHOTS:
        if s["kind"] != "reenactment":
            continue
        t = shots[s["id"]]
        caps = [c for c in tl["captions"] if c["shot"] == s["id"]]
        r = {"id": s["id"], "clip": s["clip"], "start": t["start"], "end": t["end"],
             "in": s.get("in", 0.0), "speed": s.get("speed", 1.0), "dur": s.get("dur", t["end"] - t["start"]),
             "seconds": getattr(ep, "CLIP_SOURCES", {}).get(s["clip"], {}).get("seconds"), "caps": caps}
        r["src_end"] = r["in"] + r["dur"] * (r["speed"] if isinstance(r["speed"], (int, float)) else 1.0)
        if not caps:
            out.append(r)
            continue
        r["lead"] = caps[0]["start"] - t["start"]                 # pre, as built
        r["take"] = caps[-1]["end"] - caps[0]["start"]            # the line(s), pauses included
        key = KEY_WORDS.get(s["id"])
        r["key"] = key
        if key:
            hits = [w for c in caps for w in c.get("words", []) if norm(w[0]) == norm(key)]
            if not hits:
                sys.exit(f"{s['id']}: the key word {key!r} isn't in its caption words; update KEY_WORDS")
            r["key_t"] = hits[0][1] - caps[0]["start"]
        else:
            r["key_t"] = r["take"]
        r["move"] = r["in"] + r["lead"] + r["key_t"]              # seconds into the generated take
        r["shift"] = r["lead"] + r["key_t"]                       # in = (move time in the take) - shift
        r["after"] = r["dur"] - (r["lead"] + r["take"])           # action after the line, before the cut
        r["dur_needed"] = r["lead"] + r["take"] + AFTER_LINE
        r["max_key"] = r["in"] + r["key_t"]                       # in can fall only to 0
        r["max_take"] = r["take"] * r["max_key"] / r["key_t"] if r["key_t"] else r["take"]
        out.append(r)
    return out


def word_time(caps, word):
    """Seconds into the line where `word` starts (the first caption word that matches)."""
    for c in caps:
        for w in c.get("words", []):
            if norm(w[0]) == norm(word):
                return w[1] - caps[0]["start"]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--timeline", help="timeline.json (default: the episode's build/timeline.json)")
    ap.add_argument("--ref", help="a reference build's timeline.json (the Kokoro scratch build)")
    args = ap.parse_args()
    ep = load_episode()
    tl = load_timeline(args.timeline)
    fail = False

    p = pace(tl)
    head = CEILING - p["total"]
    state = "FAIL" if p["total"] >= CEILING else ("WARN" if p["total"] > TRIM_AT else "OK")
    fail |= state == "FAIL"
    print(f"RUNTIME {p['total']:.2f} s: {state} ({head:.2f} s under {CEILING:.0f} s"
          + ("; over 49.5 s: apply NOTES.md's trim list, in order" if state != "OK" else "") + ")")
    lo, hi = OVERALL
    print(f"PACE {p['words']} words: {p['wpm']:.0f} words/min overall (target {lo}-{hi}: "
          f"{'OK' if p['wpm'] >= lo else 'WARN'}), {p['wpm_speaking']:.0f} while speaking ({p['speak']:.1f} s; "
          f"target ~{TARGET_WPM}, floor {FLOOR_WPM}: {'OK' if p['wpm_speaking'] >= FLOOR_WPM else 'WARN'}); "
          f"silence {p['silence']:.1f} s")
    for wpm in (FLOOR_WPM, TARGET_WPM):
        q = p[wpm]
        ok = q["total"] < CEILING and CEILING - q["total"] >= HEADROOM_MIN and q["wpm"] >= lo
        room = CEILING - q["total"]
        print(f"AT {wpm} WORDS/MIN while speaking: {q['total']:.1f} s, {q['wpm']:.0f} overall, "
              f"{abs(room):.1f} s {'under' if room >= 0 else 'over'} {CEILING:.0f} s: {'OK' if ok else 'WARN'}")
    print(f"NEEDED while speaking: {p['need_head']:.0f} words/min for {HEADROOM_MIN} s of headroom, "
          f"{p['need_overall']:.0f} for {lo} overall")

    if args.ref:
        ref = {c["rec"]: c for c in load_timeline(args.ref)["captions"]}
        grown = 0.0
        for c in tl["captions"]:
            r = ref.get(c["rec"])
            if not r:
                continue
            d, rd = c["end"] - c["start"], r["end"] - r["start"]
            grown += d - rd
            if d > rd * (1 + TAKE_GROWTH):
                print(f"WARN {c['rec']}: {d:.2f} s, {d / rd * 100 - 100:+.0f}% over the reference's {rd:.2f} s "
                      f"(D1: at most +{TAKE_GROWTH * 100:.0f}%; pick a quicker take)")
        print(f"TAKES vs reference: {grown:+.2f} s in total (runtime {tl['total'] - load_timeline(args.ref)['total']:+.2f} s)")

    for r in reenactments(ep, tl):
        secs = r["seconds"]
        print(f"REENACTMENT {r['id']} (clip {r['clip']}): {tc(r['start'])}-{tc(r['end'])}, dur {r['dur']:.2f} s, "
              f"in {r['in']:.2f}")
        if "take" not in r:
            print("  no line over it: nothing to fit")
            continue
        cue = f"{r['key']!r} {r['key_t']:.2f} s into the line" if r["key"] else "the move lands after the line"
        print(f"  line {r['take']:.2f} s, from {r['lead']:.2f} s into the shot; {cue}")
        if r["key"]:
            print(f"  motion prompt: hold still for the first {r['move']:.2f} s of the generated take, then move "
                  f"(\"For the first ... seconds\")")
        else:
            print(f"  motion prompt: land at about {r['move']:.2f} s into the generated take (\"At about ... seconds\")")
        print(f"  once a clip exists: if its move comes at S s into the take, set in = S - {r['shift']:.2f} (0 or more)")
        need = 10 if r["in"] + r["dur"] > SHORT_TAKE else SHORT_TAKE
        if secs is None:
            print(f"  source {r['in']:.2f}-{r['src_end']:.2f} s; no CLIP_SOURCES seconds to check (generate {need} s)")
        else:
            ok = r["src_end"] <= secs + 1e-6
            fail |= not ok
            print(f"  source {r['in']:.2f}-{r['src_end']:.2f} s of a {secs} s take: {'OK' if ok else 'FAIL'}"
                  + ("" if ok else f" (generate {need} s and set CLIP_SOURCES seconds to {need})"))
        over = r["dur_needed"] > r["dur"] + 1e-6
        if r["after"] < -1e-6:
            fail = True
        state = "FAIL" if r["after"] < -1e-6 else ("WARN" if r["after"] < AFTER_LINE - 1e-6 else "OK")
        print(f"  action after the line: {r['after']:.2f} s ({state}, at least {AFTER_LINE}); this take needs dur "
              f"{min(r['dur_needed'], MAX_DUR):.2f}" + (" (over the 6.0 s cap: trim the line)" if r["dur_needed"] > MAX_DUR else "")
              + (" (raise dur, then regenerate the clip against this take)" if over else ""))
        if r["key"]:
            print(f"  a clip fitted to this take absorbs a longer one only while {r['key']!r} comes at most "
                  f"{r['max_key']:.2f} s into the line (about a {r['max_take']:.2f} s take if it slows evenly); "
                  "longer: regenerate the clip against the locked take")
        else:
            print(f"  a clip fitted to this take absorbs a take of up to {r['max_take']:.2f} s; longer: regenerate "
                  "the clip (a 10 s take, landing re-timed); raising dur alone freezes it and lands early")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
