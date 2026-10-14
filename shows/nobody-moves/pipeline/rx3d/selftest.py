"""blender_reenact.py --selftest [--allow-skip] (docs/BLENDER_REENACTMENTS.md §9). pipeline/selftest.py calls it too.

A. Pure Python, always (no bpy): word resolution, render.py's frame grid, content/render keys and asset identity,
   up-to-date rules, validation, Blender discovery errors, engine resolution, --scale and --frames parsing, the
   synthetic-timeline gate, the cut-back mapping, screen geometry and the timing check. Under a second.
B. Rendering (needs Blender; without it the selftest FAILS unless --allow-skip): one worker process for heist,
   action and one showcase cell per proxy (108x192, Cycles CPU, 4 spp, no denoise, no haze), the real filing path
   (clips.py add) on a 31-frame draft clip, determinism across two worker processes, the rigidity and never-touch
   tripwires, the
   BLENDED-glare rule, the GPU device check, `model add` (good GLB, broken GLB), and the emitter calibration
   swatch. No PIL: frame statistics come from the worker's result.json (bpy + numpy).
"""
import argparse
import copy
import glob
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time

EP_TEMPLATE = '''
L = lambda who, text, say=None: ("line", who, text, say or text)
V = lambda img, a, b, look=None: {{"img": img, "kb": (a, b), "look": look}}
DERIVED_STILLS = {{"lorraine_lift": {{"from": "lorraine", "gamma": 1.5}}}}
CLIPS = {{"rx_heist_gnome": "Locked-off camera. The gnome slides sideways, rigid. No people, no text."}}
SHOTS = [
    {{"id": "rx", "kind": "reenactment", "clip": "rx_test_bl", "in": 0.0, "speed": 1.0, "dur": {dur},
     "label": "REENACTMENT · AI", "stamp": "THEORY #1: THE GNOME", "pre": 0.3,
     "blender": {{"template": "heist", "move_on": "Then", "move_at": 1.2{heist_extra}}},
     "items": [L("NARRATOR", "That night, he waited. Then he made his move.")]}},
    {{"id": "rx2", "kind": "reenactment", "clip": "rx_test2_bl", "in": 0.0, "speed": 1.0, "dur": 2.4,
     "label": "REENACTMENT · AI", "stamp": "THEORY #2",
     "blender": {{"template": "action", "move_on": ["One", "goose#2"], "tip_on": "dared",
                 "land_on": {{"word": "dared", "offset": 0.3}}, "move_at": [0.35, 0.95], "tip_at": 1.45,
                 "land_at": 2.05, "options": {{"chime": True, "embers": 6, "dust": 8, "sparks": 6}}}},
     "items": [L("NARRATOR (TRAILER)", "One goose... the goose... dared.")]}},
    {{"id": "deny", "kind": "still", "views": [V("lorraine_lift", (0.5, 0.5, 1.0), (0.5, 0.5, 1.0))],
     "items": [L("LORRAINE", "Kid.")]}},
]
'''


def _timeline(dur, then_at=1.0, s0=0.0, synthetic=False):
    """'Then' at exactly then_at s (shot-local) in a shot starting at s0 (not frame-aligned when s0 isn't); the
    action shot's words placed by hand."""
    a = s0 + dur
    caps = [
        {"shot": "rx", "text": "That night, he waited. Then he made his move.", "start": s0 + 0.3, "end": s0 + dur - 0.3,
         "words": [[w, s0 + x, s0 + y] for w, x, y in
                   [["That", 0.3, 0.45], ["night,", 0.45, 0.6], ["he", 0.62, 0.7], ["waited.", 0.7, 0.95],
                    ["Then", then_at, then_at + 0.1], ["he", then_at + 0.1, then_at + 0.2],
                    ["made", then_at + 0.2, then_at + 0.3], ["his", then_at + 0.3, then_at + 0.4],
                    ["move.", then_at + 0.4, min(then_at + 0.5, dur - 0.3)]]]},
        {"shot": "rx2", "text": "One goose... the goose... dared.", "start": a + 0.35, "end": a + 1.75,
         "words": [["One", a + 0.35, a + 0.5], ["goose...", a + 0.5, a + 0.75], ["the", a + 0.85, a + 0.95],
                   ["goose...", a + 0.95, a + 1.2], ["dared.", a + 1.45, a + 1.75]]},
        {"shot": "deny", "text": "Kid.", "start": a + 2.5, "end": a + 2.8, "words": [["Kid.", a + 2.5, a + 2.8]]},
    ]
    shots = [{"id": "rx", "start": s0, "end": s0 + dur}, {"id": "rx2", "start": a, "end": a + 2.4},
             {"id": "deny", "start": a + 2.4, "end": a + 3.0}]
    tl = {"total": a + 3.0, "shots": shots, "captions": caps}
    if synthetic:
        tl["synthetic"] = True
    return tl


class Report:
    def __init__(self):
        self.fails, self.n = [], 0

    def ok(self, cond, what):
        self.n += 1
        if not cond:
            self.fails.append(what)
        print(("  ok   " if cond else "  FAIL ") + what, flush=True)
        return cond


def _episode(root, dur=1.6, heist_extra="", timeline=True, then_at=1.0, s0=0.0, synthetic=False):
    d = os.path.join(root, "ep_test")
    os.makedirs(os.path.join(d, "build"), exist_ok=True)
    with open(os.path.join(d, "episode.py"), "w") as f:
        f.write(EP_TEMPLATE.format(dur=dur, heist_extra=heist_extra))
    tl = os.path.join(d, "build", "timeline.json")
    if timeline:
        with open(tl, "w") as f:
            json.dump(_timeline(dur, then_at, s0, synthetic), f)
    elif os.path.exists(tl):
        os.remove(tl)
    return d


def _raises(R, fn, needle, what, code=None):
    try:
        fn()
    except Exception as e:      # Fail
        ok = needle in str(e) and (code is None or getattr(e, "code", None) == code)
        return R.ok(ok, what + ("" if ok else f" (got {type(e).__name__} {getattr(e, 'code', '')}: {str(e)[:200]!r})"))
    return R.ok(False, what + " (no error)")


def _drv(D, args, env=None, timeout=600):
    return subprocess.run([sys.executable, os.path.join(D.PIPE, "blender_reenact.py")] + args, capture_output=True,
                          text=True, env=env, timeout=timeout)


def _no_bpy_python():
    """An interpreter that can't import bpy (for the no-Blender exit)."""
    for c in (sys.executable, shutil.which("python3"), "/usr/bin/python3"):
        if c and os.path.exists(c):
            r = subprocess.run([c, "-c", "import importlib.util as u; print(u.find_spec('bpy') is None)"],
                               capture_output=True, text=True)
            if r.stdout.strip() == "True":
                return c
    return None


def part_a(D, R, root):
    print("A. pure Python", flush=True)
    os.environ["NM_RX_SELFTEST"] = "1"
    # 1. words
    R.ok(D.norm_word("dared.") == "dared" and D.norm_word("moves...") == "moves" and D.norm_word("I'm") == "i'm"
         and D.norm_word("‘Then,") == "then", "normalize: punctuation, ellipses, inner apostrophes")
    b = D.parse_beat("goose#2", "start")
    R.ok(b["word"] == "goose" and b["nth"] == 2 and b["edge"] == "start", "parse 'goose#2'")
    ep = D.load_episode(_episode(root))
    tl, _ = D.load_timeline(ep)
    rx, rx2 = ep.SHOTS[0], ep.SHOTS[1]
    t, src, _, notes, wt = D.resolve_beat(tl, rx, "Then", 1.2, "move")
    R.ok(abs(t - 1.0) < 1e-9 and src == "timeline" and not notes and wt == [1.0, 1.1],
         f"'Then' resolves to 1.000 s from the timeline, with its word times ({t}, {wt})")
    t, _, _, _, _ = D.resolve_beat(tl, rx2, "goose#2", None, "move")
    R.ok(abs(t - 0.95) < 1e-9, f"'goose#2' is the second goose (0.95 s, got {t:.3f})")
    t, _, _, _, _ = D.resolve_beat(tl, rx2, {"word": "dared", "offset": 0.3}, None, "land")
    R.ok(abs(t - 2.05) < 1e-9, f"land: end of 'dared.' + 0.30 s = 2.05 s (got {t:.3f})")
    _raises(R, lambda: D.resolve_beat(tl, rx, "Thenn", None, "move"), "move_on 'Thenn' not in rx",
            "a missing word fails and lists the shot's words")
    t, src, _, notes, _ = D.resolve_beat(tl, rx, "Thenn", 1.2, "move")
    R.ok(src == "move_at" and t == 1.2 and notes, "a missing word falls back to move_at with a warning")
    t, src, _, notes, _ = D.resolve_beat(tl, rx, "Then", 0.5, "move")
    R.ok(any("drift" in n for n in notes) and t == 1.0, "move_on vs move_at drift over 0.4 s warns; the word wins")
    stale = copy.deepcopy(rx)
    stale["items"] = [("line", "NARRATOR", "That night. Then he moved.", "That night. Then he moved.")]
    R.ok("changed" in (D.stale_reason(tl, stale) or ""), "stale timeline: the shot's lines changed")
    stale = copy.deepcopy(rx)
    stale["dur"] = 2.0
    R.ok("dur" in (D.stale_reason(tl, stale) or ""), "stale timeline: dur differs by more than a frame")
    t, src, _, _, _ = D.resolve_beat(None, rx, "Then", 1.2, "move")
    R.ok(src == "move_at" and t == 1.2, "no timeline: move_at")
    # 2. frames: render.py's grid
    R.ok(D.frames_for({"dur": 4.05}) == (123, 121) and D.frames_for({"dur": 4.0}) == (121, 119)
         and D.frames_for({"dur": 5.0}) == (151, 149), "frames = ceil((in + dur) * 30) + 1; last shown frame")
    R.ok(D.beat_frame({"in": 0.0}, 2.26, 0.0, "event") == 68 and D.beat_frame({"in": 0.0}, 2.26, 0.0, "start") == 67,
         "beat on a frame-aligned shot: event k = ceil(30 t), a start beat's last still frame is k - 1")
    R.ok(D.beat_frame({"in": 0.0}, 2.26, 10.734, "start") == 66,
         "the prototype heist ('Then' 12.994 s, shot at 10.734 s): the first moving frame is clip frame 67, shown at "
         "global frame 390, the first frame after the word")
    rng = random.Random(7)
    bad = 0
    for _ in range(400):      # render.py shows clip frame floor(30*in + fi - 30*S + 1e-6) on global frame fi
        S, t, cin = rng.uniform(0, 40), rng.uniform(0.3, 4.0), rng.choice([0.0, 0.0, 0.25])
        k = D.beat_frame({"in": cin}, t, S, "start") + 1
        fi = math.ceil(30 * (S + t) - 1e-6)
        shown = lambda f: math.floor(30 * cin + f - 30 * S + 1e-6)       # noqa: E731
        if not (shown(fi) >= k and shown(fi - 1) < k and fi / 30 >= S + t - 1e-6 and (fi - 1) / 30 < S + t):
            bad += 1
    R.ok(bad == 0, f"400 random shot starts and beats: the first moving frame is on screen from the first global "
                   f"frame at or after the word, never before or later ({bad} misses)")
    # 3. keys
    render = D.render_settings("preview", "cycles", "cpu", None)
    args = argparse.Namespace(require_models=False)

    def job(at=None, opts=None, subject=None, props=None, models=None, quality="preview", rend=None):
        s = copy.deepcopy(rx)
        s["blender"].pop("move_on")
        s["blender"]["move_at"] = 1.26 if at is None else at
        if opts:
            s["blender"]["options"] = opts
        if subject:
            s["blender"]["subject"] = subject
        if props is not None:
            s["blender"]["props"] = props
        j, _ = D.resolve_shot(ep, s, args, None, None, quality, rend or render, "5.0.1")
        return j
    k1, k2, k3 = job(1.240)["content_key"], job(1.260)["content_key"], job(1.300)["content_key"]
    R.ok(k1 == k2, "content key: 1.240 s and 1.260 s are the same frame: same key")
    R.ok(k1 != k3, "content key: 1.300 s (the next frame) changes it")
    R.ok(job(opts={"travel": 0.3})["content_key"] != k1, "content key: an option change changes it")
    R.ok(job(subject="basin")["content_key"] != k1, "content key: swapping the subject (garrison -> basin) changes it")
    R.ok(job(props=["deb"])["content_key"] != job(props=["basin"])["content_key"],
         "content key: swapping a prop (deb -> basin) changes it")
    pv, fin = job(), job(quality="final", rend=D.render_settings("final", "cycles", "cpu", None))
    R.ok(pv["content_key"] == fin["content_key"] and pv["cache_key"] != fin["cache_key"],
         "a preview and a final share the content key; the frame folders (full key) differ")
    eg = job(rend=D.render_settings("preview", "eevee", "gpu", None))
    R.ok(eg["content_key"] == pv["content_key"], "engine and device are not in the content key (a GPU final stays "
                                                 "current on a CPU machine)")
    src = open(os.path.join(D.PIPE, "blender_reenact.py")).read()
    R.ok("git_info()" not in src.split("def content_key_of")[1].split("def render_key_of")[0],
         "content key: the git commit is not in it")
    # GLB identity: forward, bytes
    mdir = os.path.join(root, "models_a")
    os.makedirs(mdir, exist_ok=True)
    glb = os.path.join(mdir, "garrison.glb")
    with open(glb, "wb") as f:
        f.write(b"glTF-fixture-1")
    ent = {"file": "garrison.glb", "sha1": D.file_sha1(glb), "height_m": 0.406, "forward": "+z", "ai_generated": True}
    old = D.MODELS_DIR
    D.MODELS_DIR = mdir
    try:
        def write(e):
            with open(os.path.join(mdir, "models.json"), "w") as f:
                json.dump({"garrison": e}, f)
        write(ent)
        g1 = job()["content_key"]
        write(dict(ent, forward="+x"))
        R.ok(job()["content_key"] != g1, "content key: editing a GLB's forward in models.json changes it")
        write(ent)
        time.sleep(0.01)
        with open(glb, "wb") as f:
            f.write(b"glTF-fixture-2")
        _raises(R, job, "rerun model add", "a GLB whose bytes differ from models.json fails ('rerun model add')")
        write(dict(ent, sha1=D.file_sha1(glb)))
        R.ok(job()["content_key"] != g1, "content key: new GLB bytes (re-filed) change it")
        j = job()
        R.ok(j["subject"]["sha1"] == D.file_sha1(glb), "the job carries the MEASURED sha1 of the GLB")
    finally:
        D.MODELS_DIR = old
    # up to date
    mp4 = os.path.join(root, "clip.mp4")
    with open(mp4, "wb") as f:
        f.write(b"mp4")
    sc = {"mp4_sha1": D.file_sha1(mp4), "content_key": "C", "quality": "final"}
    R.ok(D.up_to_date(sc, mp4, "C", "draft")[0] and D.up_to_date(sc, mp4, "C", "final")[0],
         "up to date: a filed final satisfies --build at draft and at final")
    R.ok(not D.up_to_date(dict(sc, quality="draft"), mp4, "C", "final")[0], "a filed draft doesn't satisfy a final")
    R.ok(not D.up_to_date(sc, mp4, "D", "draft")[0], "changed content is never up to date")
    # 4. validation
    def errs(mut):
        s = copy.deepcopy(rx)
        mut(s)
        return " | ".join(D.validate_shot(ep, s)[0])

    def fails(mut, needle, what):
        e = errs(mut)
        R.ok(needle in e, f"validate: {what}" + ("" if needle in e else f" (got {e!r})"))
    fails(lambda s: s.pop("dur"), "dur is required", "dur missing")
    fails(lambda s: s.update(speed=0.5), "speed must be 1.0", "speed 0.5")
    fails(lambda s: s.update(speed="fit"), "speed must be 1.0", 'speed "fit"')
    fails(lambda s: s["blender"].update(template="caper"), "unknown template", "unknown template")
    fails(lambda s: s["blender"].update(options={"travl": 0.3}), "unknown option", "unknown option key")
    fails(lambda s: s["blender"].update(subject="deb"), "canon never shows how Deb was moved", "deb as the subject")
    fails(lambda s: s["blender"].update(template="action", options={"outfit": "pirate"}), "isn't designed",
          "Lorraine with outfit 'pirate'")
    fails(lambda s: s["blender"].update(template="showcase"), "CLI only", "showcase in an episode")
    fails(lambda s: s["blender"].update(camera="drone"), "unknown camera preset", "unknown camera preset")
    fails(lambda s: s.update(label="REENACTMENT (DIRECTOR'S CUT) · AI"), "label must be", "a third label")
    fails(lambda s: s.update(label="REENACTMENT"), "label must be", "a plain REENACTMENT label (D4: always · AI)")
    fails(lambda s: s.update(clip="rx_heist_gnome"), "AI clip's key", "a Blender clip on an AI clip's key (CLIPS)")
    s = copy.deepcopy(rx)
    s["clip"] = "rx_heist_gnome_render"
    R.ok(any("end a Blender clip's key with _bl" in w for w in D.validate_shot(ep, s)[1]),
         "validate: a Blender clip key without _bl warns")
    fails(lambda s: s["blender"].update(tip_on="Then"), "has no tip beat", "tip_on on the heist")
    fails(lambda s: s["blender"].update(move_on=["Then", "made"]), "has one move", "a list move_on on the heist")
    s = copy.deepcopy(rx2)
    s["blender"]["move_on"] = ["One", "goose", "the", "dared"]
    R.ok("1-3 words" in " ".join(D.validate_shot(ep, s)[0]), "validate: at most 3 rock words")
    os.environ.pop("NM_RX_SELFTEST", None)
    s = copy.deepcopy(rx)
    s["blender"].pop("move_on")
    s["blender"]["move_at"] = 0.1
    _raises(R, lambda: D.resolve_shot(ep, s, args, None, None, "preview", render, "5.0.1"), "outside [0.3",
            "validate: a beat at 0.1 s fails")
    s = copy.deepcopy(rx)
    s["blender"].pop("move_on")
    s["blender"].update(move_at=0.7, options={"toward": 0.6})
    _, warns = D.validate_shot(ep, s)
    j, notes = D.resolve_shot(ep, s, args, None, None, "preview", render, "5.0.1")
    R.ok(any("toward 0.6" in w for w in warns) and any("stillness first" in n for n in notes),
         "toward 0.6 and a move at 0.7 s print warnings")
    os.environ["NM_RX_SELFTEST"] = "1"
    # synthetic timeline: fine for a preview, never for a filed final
    ep_s = D.load_episode(_episode(os.path.join(root, "syn"), synthetic=True))
    tl_s, sha_s = D.load_timeline(ep_s)
    j, notes = D.resolve_shot(ep_s, ep_s.SHOTS[0], args, tl_s, sha_s, "preview", render, "5.0.1")
    R.ok(any("synthetic" in n for n in notes) and j["beats"]["move"]["source"] == "synthetic",
         "a synthetic timeline: WARN at preview, the source recorded as 'synthetic'")
    _raises(R, lambda: D.resolve_shot(ep_s, ep_s.SHOTS[0], args, tl_s, sha_s, "final",
                                      D.render_settings("final", "cycles", "cpu", None), "5.0.1", filed=True),
            "run build_audio.py", "a synthetic timeline fails a filed final")
    # 5. Blender discovery errors
    env = dict(os.environ, NM_BLENDER="/nonexistent/blender")
    r = _drv(D, [os.path.join(root, "ep_test"), "--dry-run"], env=env)
    R.ok(r.returncode == 2 and "not an executable" in r.stderr, f"NM_BLENDER=/nonexistent: exit 2, 'not an "
                                                                 f"executable', no fall-through (exit {r.returncode})")
    env = {k: v for k, v in os.environ.items() if k != "NM_BLENDER"}
    r = _drv(D, [os.path.join(root, "ep_test"), "--dry-run", "--blender", "/opt/blender-4.1/blender"], env=env)
    R.ok(r.returncode == 2 and "--blender /opt/blender-4.1/blender: not an executable" in r.stderr,
         f"--blender with a missing path: exit 2, no fall-through (exit {r.returncode})")
    py = _no_bpy_python()
    if py:
        env = dict({k: v for k, v in os.environ.items() if k != "NM_BLENDER"}, NM_BLENDER_DISCOVER="0")
        r = subprocess.run([py, os.path.join(D.PIPE, "blender_reenact.py"), os.path.join(root, "ep_test"), "--dry-run"],
                           capture_output=True, text=True, env=env)
        R.ok(r.returncode == 2 and "pip install bpy==5.0.1" in r.stderr,
             f"no Blender: exit 2 with the install hint (exit {r.returncode})")
    else:
        print("  skip no-Blender exit: every interpreter here has bpy", flush=True)
    # 6. engine resolution (fake probe results)
    A = lambda e="auto", d="auto": argparse.Namespace(engine=e, device=d)       # noqa: E731
    R.ok(D.resolve_engine(A(), {"eevee": True, "gpu": {}}, "final")[:3] == ("eevee", "gpu", None),
         "engine auto with Eevee: eevee on the GPU")
    R.ok(D.resolve_engine(A(), {"eevee": False, "gpu": {"CUDA": ["x"], "OPTIX": ["x"]}}, "final")[:3] ==
         ("cycles", "gpu", "OPTIX"), "engine auto, no Eevee, OptiX and CUDA found: Cycles on OptiX")
    _raises(R, lambda: D.resolve_engine(A("auto", "gpu"), {"eevee": False, "gpu": {}}, "final"), "no Cycles GPU",
            "--device gpu with no GPU device: exit 2", code=2)
    _raises(R, lambda: D.resolve_engine(A("eevee", "cpu"), {"eevee": True, "gpu": {}}, "final"), "GPU only",
            "--engine eevee --device cpu: exit 2 (not silently turned into gpu)", code=2)
    R.ok(D.resolve_engine(A("auto", "cpu"), {"eevee": True, "gpu": {"OPTIX": ["x"]}}, "final")[:2] == ("cycles", "cpu"),
         "--device cpu with Eevee available: Cycles on the CPU")
    # 7. --scale, --frames, --shot
    _raises(R, lambda: D.check_scale(33), "356x633", "--scale 33 (356x633) fails before rendering: yuv420p needs even "
                                                       "sizes")
    R.ok(all(s in D.VALID_SCALES for s in (10, 25, 50, 100)) and 33 not in D.VALID_SCALES, "--scale 10/25/50/100 are valid")
    _raises(R, lambda: D.parse_frames("every:0", 10), "accepted", "--frames every:0 names the accepted forms")
    _raises(R, lambda: D.parse_frames("5-", 10), "accepted", "--frames 5- names the accepted forms")
    r = _drv(D, [os.path.join(root, "ep_test"), "--shot", "nope", "--dry-run"])
    R.ok(r.returncode != 0 and "rx, rx2" in r.stderr, "a mistyped --shot lists the shots with a blender dict")
    # 8. cut-back mapping and screen geometry
    b = D.kb_box([0.305, 0.325, 0.765, 0.77], [941, 1672], (0.52, 0.53, 1.35))
    R.ok(abs(b[0] - 0.21) < 0.01 and abs(b[2] - 0.83) < 0.01, f"cut-back: lorraine under kb (0.52, 0.53, 1.35) spans x "
                                                              f"0.21-0.83 ({[round(x, 3) for x in b]})")
    b = D.kb_box([0.287, 0.286, 0.676, 0.807], [941, 1672], (0.47, 0.49, 1.37))
    R.ok(abs(b[1] - 0.221) < 0.006 and abs(b[3] - 0.934) < 0.006 and abs((b[0] + b[2]) / 2 - 0.515) < 0.006,
         "cut-back: garrison under g_deny's kb: cap 0.22, boots 0.93, centre x 0.515")
    k = D.suggest_kb([0.305, 0.325, 0.765, 0.77], [941, 1672],
                     D.kb_box([0.305, 0.325, 0.765, 0.77], [941, 1672], (0.52, 0.53, 1.35)))
    R.ok(k == [0.52, 0.53, 1.35], f"cut-back: suggest_kb inverts kb_box (back to (0.52, 0.53, 1.35), got {k})")
    k = D.suggest_kb([0.305, 0.325, 0.765, 0.77], [941, 1672], [0.384, 0.36, 0.797, 0.766])
    R.ok(k[2] == 1.0, f"cut-back: a reenactment showing her smaller than the uncropped still suggests zoom 1.0 ({k})")
    sq = [(0, 0), (100, 0), (100, 100), (0, 100)]
    R.ok(abs(D.poly_area(D.clip_poly_rect(sq, (50, 50, 200, 200))) - 2500) < 1e-6 and
         D.hull_in_rect(sq, (150, 150, 200, 200)) == 0.0, "screen geometry: polygon clipped to a rectangle")
    circle = [(885 + 230 * math.cos(a / 32 * 2 * math.pi), 590 + 230 * math.sin(a / 32 * 2 * math.pi)) for a in range(32)]
    R.ok(D.hull_in_rect(circle, (44, 170, 758, 340)) == 0.0, "a round fireball whose bounding box touches the tag zone's "
                                                              "corner but whose silhouette doesn't is clear")
    # 9. the timing check: the drop starts on its word and lands after it
    jb = {"last_shown": 60, "props": [], "subject": {"name": "lorraine"},
          "beats": {"move": {"frame": 10}, "tip": {"word": "dared", "word_t": [1.45, 1.75], "frame": 43},
                    "land": {"word": "dared", "word_t": [1.45, 1.75], "frame": 61}}}
    mo = {"screen": {"subject": [[400, 600, 700, 1300]] * 62}, "hull": {}, "camera": [[1]] * 62, "objects": {},
          "heading_deg": {"lorraine": [0] * 62}, "keep_clear": []}
    _, w = D.screen_checks(jb, mo, {"id": "x"}, facts={"phases": {"t_tip": 1.70, "t_fall": 1.9, "t_land": 1.80}})
    R.ok(any("miss 'dared'" in x for x in w) and any("lands 0.05 s after" in x for x in w),
         "timing check: a tip 0.25 s late and a landing 0.05 s after the word both warn")
    os.environ.pop("NM_RX_SELFTEST", None)


def part_b(D, R, root, bl):
    print(f"B. rendering with {bl[1]}", flush=True)
    os.environ["NM_RX_SELFTEST"] = "1"
    info = D.probe_blender(bl)
    R.ok(info.get("version") and tuple(info["version_tuple"][:2]) >= (5, 0), f"probe: Blender {info.get('version')}")
    ep = D.load_episode(_episode(root, s0=0.0123))
    tl, tl_sha = D.load_timeline(ep)
    args = argparse.Namespace(require_models=False)
    render = D.render_settings("selftest", "cycles", "cpu", None)
    jobs = []
    out = os.path.join(root, "b")
    heist, _ = D.resolve_shot(ep, ep.SHOTS[0], args, tl, tl_sha, "selftest", render, info["version"])
    action, _ = D.resolve_shot(ep, ep.SHOTS[1], args, tl, tl_sha, "selftest", render, info["version"])
    mv = heist["beats"]["move"]["frame"]
    # B4 timing on render.py's grid, with a shot start that isn't frame-aligned (0.0123 s)
    S, w = 0.0123, 0.0123 + 1.0
    fi = math.ceil(30 * w - 1e-6)
    shown = math.floor(fi - 30 * S + 1e-6)
    R.ok(mv + 1 == shown and math.floor(fi - 1 - 30 * S + 1e-6) == mv,
         f"timing: 'Then' at 1.000 s in a shot starting at 0.0123 s: the first moving clip frame {mv + 1} is the one "
         f"render.py shows on global frame {fi}, the first after the word")

    def place(job, name, frames, extra=None):
        d = os.path.join(out, name)
        job = copy.deepcopy(job)
        job.update(frames_dir=os.path.join(d, "frames"), render_frames=frames, motion_path=os.path.join(d, "motion.json"),
                   result_path=os.path.join(d, "result.json"))
        job.update(extra or {})
        jobs.append(job)
        return job
    k_after = min(mv + 15, heist["last_shown"])
    hj = place(heist, "heist", [max(0, mv - 10), k_after])
    land = action["beats"]["land"]["frame"]
    k_land = min(land + 3, action["last_shown"])
    aj = place(action, "action", [0, k_land])
    for name in ("garrison", "lorraine", "deb", "basin"):
        sj, _, _ = D.showcase_job(name, "sheet", render, out_dir=os.path.join(out, f"show_{name}"), frames=[0])
        jobs.append(sj)
    jp = os.path.join(out, "jobs.json")
    os.makedirs(out, exist_ok=True)
    with open(jp, "w") as f:
        json.dump({"jobs": jobs}, f)
    t0 = time.time()
    try:
        D.run_worker(bl, jp, os.path.join(out, "worker.log"), quiet=True, timeout=1200)
        R.ok(True, f"one worker for {len(jobs)} jobs ({time.time() - t0:.1f} s)")
    except D.Fail as e:
        R.ok(False, f"worker batch: {str(e)[:600]}")
    res = {}
    for j in jobs:
        try:
            with open(j["result_path"]) as f:
                res[j["result_path"]] = json.load(f)
        except FileNotFoundError:
            res[j["result_path"]] = {"ok": False, "errors": ["no result"]}

    def motion(job):
        with open(job["motion_path"]) as f:
            return json.load(f)
    # B1 heist
    r = res[hj["result_path"]]
    if R.ok(r["ok"], "heist renders" + ("" if r["ok"] else f": {r['errors']}")):
        R.ok(r.get("blender", {}).get("version") == info["version"], "result.json carries the worker's Blender version")
        for k in hj["render_frames"]:
            st = r["frame_stats"][str(k)]
            R.ok((st["w"], st["h"]) == (108, 192) and st["mean"] > 40 and st["std"] > 5,
                 f"heist frame {k}: 108x192, mean {st['mean']:.0f} > 40, std {st['std']:.0f} > 5 (bpy stats, no PIL)")
        m = motion(hj)
        g = m["objects"]["garrison"]
        R.ok(all(x == g[0] for x in g[: mv + 1]), f"heist: Garrison's root identical through the last still frame ({mv})")
        R.ok(g[mv + 1] != g[0], f"heist: and different from frame {mv + 1}")
        dx = g[k_after][3] - g[0][3]
        R.ok(dx <= -0.02, f"heist: moved {-dx * 100:.1f} cm left by move + 0.5 s (>= 2 cm)")
        R.ok(all(c == m["camera"][0] for c in m["camera"]), "heist: the camera never moves")
        hd = m["heading_deg"]["garrison"]
        R.ok(all(abs(h - hd[0]) < 1e-6 for h in hd), "heist: his yaw never changes")
        R.ok(len(set(m["mesh_hash"]["garrison"])) == 1, "heist: no evaluated mesh vertex changes (rigid)")
        R.ok(m["cast_count"] == {"garrison": 1}, f"heist: exactly one gnome, no flamingo in the frame ({m['cast_count']})")
        bc = [c for c in m["beam_clearance_m"][: heist["last_shown"] + 1] if c is not None]
        R.ok(bc and min(bc) >= 0.25 * 0.0254 - 1e-5 and bc[0] > bc[-1],
             f"heist: no beam within a quarter inch on any frame (min {min(bc) / 0.0254:.2f} in), and the low beam "
             f"closes in ({bc[0] / 0.0254:.2f} -> {bc[-1] / 0.0254:.2f} in)")
        chk, _ = D.screen_checks(hj, m, ep.SHOTS[0])
        R.ok(chk["tag_zone_clear"], f"heist: subject and beams stay out of the tag zone ({chk['tag_zone']})")
    # B2 action
    r = res[aj["result_path"]]
    if R.ok(r["ok"], "action renders" + ("" if r["ok"] else f": {r['errors']}")):
        m = motion(aj)
        lo = m["objects"]["lorraine"]
        dz = lo[k_land][11] - lo[0][11]
        R.ok(abs(dz + 0.18) < 0.006, f"action: one step lower after landing (dz {dz:+.3f} m, want -0.18)")
        hd = m["heading_deg"]["lorraine"]
        R.ok(all(abs(h - hd[0]) < 1e-6 for h in hd), "action: her yaw never changes (rolls and the tip are rigid)")
        f = m["facing"]["lorraine"]
        R.ok(all(15 <= a <= 60 and s < 0 for a, s in f), f"action: beak to frame left at {f[0][0]:.1f} deg to the "
                                                         f"image plane (15-60) on every frame")
        ch = m["objects"]["chime_root"]
        R.ok(ch[0] != ch[k_land], "action: the chime sways")
        chk, _ = D.screen_checks(aj, m, ep.SHOTS[1], facts=r.get("facts"))
        R.ok(chk["tag_zone"].get("fireball") is True and chk["tag_zone"].get("subject") is True,
             f"action: the fireball and Lorraine stay out of the tag zone ({chk['tag_zone']})")
        R.ok("fireball_coverage" in chk and "feet_hidden_by_fx" in chk, "action: fireball coverage and feet visibility "
                                                                         "are measured")
        ph = r["facts"]["phases"]
        R.ok(len(ph["rocks"]) == 2 and abs(ph["t_tip"] - action["beats"]["tip"]["frame"] / 30) < 1e-6,
             f"action: two rocks (on 'One' and 'goose#2') and the tip on 'dared' ({ph})")
    # B3 showcase
    for j in jobs[2:]:
        r = res[j["result_path"]]
        name = j["subject"]["name"]
        if R.ok(r["ok"] and os.path.exists(os.path.join(j["frames_dir"], "0000.png")), f"showcase {name}: one sheet cell"):
            h = r["facts"]["height_m"]
            R.ok(abs(h - D.HEIGHTS[name]) <= 0.001, f"showcase {name}: height {h:.4f} m (bible {D.HEIGHTS[name]})")
    # B6 determinism: the same job in two separate worker processes
    dj = []
    for name in ("det_a", "det_b"):
        jj = copy.deepcopy(hj)
        d = os.path.join(out, name)
        jj.update(frames_dir=os.path.join(d, "frames"), render_frames=[k_after],
                  motion_path=os.path.join(d, "motion.json"), result_path=os.path.join(d, "result.json"))
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "job.json")
        with open(p, "w") as f:
            json.dump(jj, f)
        try:
            D.run_worker(bl, p, os.path.join(d, "worker.log"), quiet=True, timeout=600)
        except D.Fail as e:
            R.ok(False, f"determinism run {name}: {str(e)[:300]}")
        dj.append(jj)
    a, b = (j["motion_path"] for j in dj)
    if os.path.exists(a) and os.path.exists(b):
        R.ok(open(a, "rb").read() == open(b, "rb").read(), "determinism: two worker processes give byte-identical "
                                                           "motion.json")
        ta, tb = (json.load(open(j["result_path"]))["frame_stats"][str(k_after)]["thumb"] for j in dj)
        d = max(abs(x - y) for x, y in zip(ta, tb))
        pa, pb = (os.path.join(j["frames_dir"], f"{k_after:04d}.png") for j in dj)
        same = open(pa, "rb").read() == open(pb, "rb").read()
        R.ok(d <= 1.0, f"determinism: the same frame from two processes matches within 1/255 (9x16 luma grid max diff "
                       f"{d:.2f}; byte-identical: {same}. Cycles' threaded sampling can flip a last bit)")
    # B4b timing without the timeline
    ep2 = D.load_episode(_episode(os.path.join(root, "nt"), timeline=False))
    j2, _ = D.resolve_shot(ep2, ep2.SHOTS[0], args, None, None, "selftest", render, info["version"])
    R.ok(j2["beats"]["move"]["frame"] == 35 and j2["beats"]["move"]["source"] == "move_at",
         f"timing: without timeline.json, move_at 1.2 s takes over (last still frame 35, got "
         f"{j2['beats']['move']['frame']})")
    # B5 the real filing path: a 31-frame (1.03 s, clips.py add's minimum is 1 s) draft clip at 108x192, then
    # cached reruns. First, a clip filed by clips.py add from a generator holds the key: --build refuses it.
    fd = _episode(os.path.join(root, "file"), dur=1.0, then_at=0.5)
    env = dict(os.environ, NM_RX_SELFTEST="1", NM_BLENDER=bl[1])
    cmd = [fd, "--shot", "rx", "--build", "--scale", "10", "--samples", "4", "--engine", "cycles", "--device", "cpu"]
    os.makedirs(os.path.join(fd, "clips"), exist_ok=True)
    with open(os.path.join(fd, "clips", "clips.json"), "w") as f:
        json.dump({"rx_test_bl": {"file": "rx_test_bl.mp4", "generator": "Kling 2.5"}}, f)
    r0 = _drv(D, cmd, env=dict(env, NM_RX_QUALITY="draft"))
    R.ok(r0.returncode == 1 and "not rendered here" in r0.stderr and "RX frame" not in r0.stdout,
         "--build refuses a key that clips.py add filed from a generator, before rendering anything")
    os.remove(os.path.join(fd, "clips", "clips.json"))
    r1 = _drv(D, cmd, env=dict(env, NM_RX_QUALITY="draft"))
    mp4 = os.path.join(fd, "clips", "rx_test_bl.mp4")
    if R.ok(r1.returncode == 0 and os.path.exists(mp4), "--build files a draft clip through clips.py add" +
            ("" if r1.returncode == 0 else f": {r1.stderr[-600:]}")):
        p = D.probe_mp4(mp4)
        R.ok(p["fps"] == 30 and p["pix_fmt"] == "yuv420p" and not p["audio"] and (p["w"], p["h"]) == (108, 192),
             f"mp4: 30 fps, yuv420p, no audio, 108x192 ({p})")
        with open(os.path.join(fd, "clips", "rx_test_bl.blender.json")) as f:
            sc = json.load(f)
        need = ("blender_version", "blender_hash", "device_used", "template", "seed", "git", "content_key", "render_key",
                "cache_key", "episode", "shot", "dur", "in", "render", "ffmpeg", "script_sha1", "picture_sha1")
        R.ok(sc["frames"] == 31 and all(k in sc for k in need) and sc["proxy"] is True and sc["ai_generated"] is False
             and sc["quality"] == "draft" and sc["mp4_sha1"] == D.file_sha1(mp4),
             "sidecar: worker-reported Blender version and device, both keys, episode, shot, dur, in, render, ffmpeg; "
             "frames 31, proxy, not AI, the filed MP4's sha1")
        R.ok(not [n for n in os.listdir(os.path.join(fd, "clips")) if n.startswith(".") or n.endswith(".tmp")
                  or n.endswith(".tmp.mp4")] and not glob.glob(os.path.join(fd, "build", "blender", "*", "*", "*.mkv")),
             "filing leaves no temp file in clips/ and no lossless intermediate in build/")
        with open(os.path.join(fd, "clips", "clips.json")) as f:
            ent = json.load(f).get("rx_test_bl", {})
        R.ok(ent.get("sha1") == sc["mp4_sha1"] and ent.get("generator", "").startswith("Blender ")
             and ent.get("sidecar") == "rx_test_bl.blender.json" and ent.get("quality") == "draft"
             and ent.get("proxy") is True and ent.get("ai_generated") is False and ent.get("prompt", "").startswith("heist:")
             and (ent.get("w"), ent.get("h")) == (108, 192),
             f"clips.json has clips.py add's entry plus the Blender provenance ({ent})")
        t0 = time.time()
        r2 = _drv(D, cmd, env=dict(env, NM_RX_QUALITY="draft"))
        dt = time.time() - t0
        R.ok(r2.returncode == 0 and "up to date" in r2.stdout and "RX frame" not in r2.stdout and dt < 3.0,
             f"a second --build is 'up to date' and starts no worker ({dt:.2f} s)")
        r3 = _drv(D, [fd, "--shot", "rx", "--quality", "final", "--dry-run", "--scale", "10"], env=env)
        R.ok(r3.returncode == 0 and "(up to date)" not in r3.stdout, "a filed draft is not up to date for --quality final")
        r4 = _drv(D, [fd, "--shot", "rx"], env=env)
        R.ok(r4.returncode == 0 and "nothing rendered" in r4.stdout and "RX frame" not in r4.stdout,
             "no mode flag: the run only prints its plan (never a throwaway preview)")
    # B7 tripwires: yaw, a beam through the subject, a BLENDED glare source
    for tname, needle, what in (("_test_yaw", "yaw changed: garrison never turns", "keying a yaw"),
                                ("_test_touch", "never-touch", "a beam through the cap"),
                                ("_test_blended", "BLENDED but it feeds the glare", "a BLENDED emitter")):
        tj = copy.deepcopy(heist)
        d = os.path.join(out, tname)
        tj.update(template=tname, props=[], options={}, frames_dir=os.path.join(d, "frames"), render_frames=[],
                  motion_path=os.path.join(d, "motion.json"), result_path=os.path.join(d, "result.json"))
        os.makedirs(d, exist_ok=True)
        tp = os.path.join(d, "job.json")
        with open(tp, "w") as f:
            json.dump(tj, f)
        try:
            D.run_worker(bl, tp, os.path.join(d, "worker.log"), quiet=True, timeout=300)
            R.ok(False, f"tripwire: {what} must fail")
        except D.Fail as e:
            R.ok(needle in str(e) and str(e).index(needle) < 400, f"tripwire: {what} fails with '{needle}', at the head "
                                                                  f"of the error")
    # B9 the GPU check: a gpu job on a machine without that device fails instead of rendering on the CPU
    if not info.get("gpu"):
        gj = copy.deepcopy(heist)
        d = os.path.join(out, "gpu")
        gj["render"] = dict(gj["render"], device="gpu", gpu_type="OPTIX")
        gj.update(frames_dir=os.path.join(d, "frames"), render_frames=[], motion_path=os.path.join(d, "motion.json"),
                  result_path=os.path.join(d, "result.json"))
        os.makedirs(d, exist_ok=True)
        gp = os.path.join(d, "job.json")
        with open(gp, "w") as f:
            json.dump(gj, f)
        try:
            D.run_worker(bl, gp, os.path.join(d, "worker.log"), quiet=True, timeout=300)
            R.ok(False, "--device gpu without an OptiX device must fail")
        except D.Fail as e:
            R.ok("found no OPTIX device" in str(e), "--device gpu without an OptiX device fails in the worker "
                                                    "(no silent CPU render)")
    else:
        print("  skip the no-GPU check: this machine has a GPU", flush=True)
    # B10 emitter calibration under AgX - Punchy
    sw = os.path.join(out, "swatch")
    os.makedirs(sw, exist_ok=True)
    r = subprocess.run(D.worker_cmd(bl, ["--worker-swatch", sw]), capture_output=True, text=True, timeout=600)
    try:
        with open(os.path.join(sw, "swatch.json")) as f:
            s = json.load(f)
        R.ok(s["laser_sheath_sat"] >= 0.6 and s["laser_core_luma"] > s["laser_sheath_luma"],
             f"laser: sheath saturation {s['laser_sheath_sat']} >= 0.6 (rgb {s['laser_sheath_rgb']}), hotter core")
        R.ok(s["fire_mid_sat"] >= 0.6, f"fire: mid-tone saturation {s['fire_mid_sat']} >= 0.6 (rgb {s['fire_mid_rgb']})")
    except FileNotFoundError:
        R.ok(False, f"emitter swatch: {r.stdout[-300:]} {r.stderr[-300:]}")
    # B11 Eevee: the flare's AOV survives (GPU only)
    if info.get("eevee"):
        ej = copy.deepcopy(heist)
        d = os.path.join(out, "eevee")
        ej["render"] = D.render_settings("selftest", "eevee", "gpu", None)
        ej.update(frames_dir=os.path.join(d, "frames"), render_frames=[], motion_path=os.path.join(d, "motion.json"),
                  result_path=os.path.join(d, "result.json"), save_blend=os.path.join(d, "scene.blend"))
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "job.json"), "w") as f:
            json.dump(ej, f)
        try:
            D.run_worker(bl, os.path.join(d, "job.json"), os.path.join(d, "worker.log"), quiet=True, timeout=600)
            R.ok(True, "Eevee builds the heist with an opaque glint (writes its AOV)")
        except D.Fail as e:
            R.ok(False, f"Eevee heist: {str(e)[:300]}")
    else:
        print("  skip Eevee glint AOV: no GPU/EGL here (GPU-only check)", flush=True)
    # B8 GLB from another tool -> model add (into a temp models dir and sheet dir) -> normalized on import
    mdir = os.path.join(root, "models")
    glb = os.path.join(root, "garrison_test.glb")
    r = subprocess.run(D.worker_cmd(bl, ["--worker-export-proxy", "garrison", glb, "90", "2.5"]), capture_output=True,
                       text=True)
    if R.ok(r.returncode == 0 and os.path.exists(glb), "GLB fixture exported (front +X, 2.5x scale)"):
        env = dict(os.environ, NM_MODELS_DIR=mdir, NM_BLENDER=bl[1], NM_RX_CHECK_QUALITY="selftest")
        r = _drv(D, ["model", "add", "garrison", glb, "--source", "selftest fixture", "--no-ai", "--forward", "+x",
                     "--out-dir", os.path.join(root, "sheet_garrison")], env=env)
        ok = R.ok(r.returncode == 0, "model add checks it in a worker, then files it" +
                  ("" if r.returncode == 0 else f": {r.stderr[-400:]}"))
        r2 = _drv(D, ["model", "add", "gardener", glb, "--source", "x", "--no-ai"], env=env)
        R.ok(r2.returncode != 0 and "cast list" in r2.stderr, "model add refuses a name outside the cast list")
        if ok:
            with open(os.path.join(mdir, "models.json")) as f:
                ent = json.load(f)["garrison"]
            R.ok(ent["ai_generated"] is False and ent["forward"] == "+x" and ent["sha1"] and ent.get("tris"),
                 "models.json entry written (after the check)")
            good = D.file_sha1(os.path.join(mdir, "garrison.glb"))
            bad = os.path.join(root, "broken.glb")
            with open(bad, "wb") as f:
                f.write(b"glTF")
            r3 = _drv(D, ["model", "add", "garrison", bad, "--source", "broken", "--no-ai",
                          "--out-dir", os.path.join(root, "sheet_broken")], env=env)
            with open(os.path.join(mdir, "models.json")) as f:
                ent2 = json.load(f)["garrison"]
            R.ok(r3.returncode == 1 and "import check failed, nothing filed" in r3.stderr and
                 D.file_sha1(os.path.join(mdir, "garrison.glb")) == good and ent2["sha1"] == good and
                 "Traceback" not in r3.stderr.split("the Blender worker")[0],
                 "a broken GLB fails with the importer's error first, and the good model stays filed")
            r4 = _drv(D, ["model", "add", "dale", glb, "--source", "x", "--no-ai", "--out-dir",
                          os.path.join(root, "sheet_dale")], env=env)
            R.ok(r4.returncode == 0, "model add dale works (the bible's 8 ft)" + ("" if r4.returncode == 0 else
                                                                                   f": {r4.stderr[-300:]}"))
            old_dir = D.MODELS_DIR
            D.MODELS_DIR = mdir
            try:
                sj, notes, sdir = D.showcase_job("garrison", "sheet", render, out_dir=os.path.join(out, "glb"), frames=[0])
                jp2 = os.path.join(sdir, "job.json")
                os.makedirs(sdir, exist_ok=True)
                with open(jp2, "w") as f:
                    json.dump(sj, f)
                D.run_worker(bl, jp2, os.path.join(sdir, "worker.log"), quiet=True, timeout=600)
                with open(sj["result_path"]) as f:
                    fr = json.load(f)["facts"]
                R.ok(sj["subject"]["kind"] == "glb" and abs(fr["height_m"] - 0.406) <= 0.001,
                     f"GLB normalized to the bible's height ({fr['height_m']:.4f} m from 2.5x)")
                ft = fr["foot"]
                R.ok(ft["front"] - ft["back"] > 0.01, f"GLB front turned to -Y (feet reach {ft['front']:.3f} m forward, "
                                                       f"{ft['back']:.3f} m back)")
            finally:
                D.MODELS_DIR = old_dir
        R.ok(not os.path.exists(os.path.join(D.SHOW, "build", "models", "garrison_sheet_" + D.file_sha1(glb)[:8])),
             "the selftest leaves nothing in the show's build/models")
    os.environ.pop("NM_RX_SELFTEST", None)


def run(D, args):
    R = Report()
    root = tempfile.mkdtemp(prefix="rx_selftest_")
    t0 = time.time()
    skipped = False
    try:
        part_a(D, R, root)
        try:
            bl = D.find_blender(getattr(args, "blender", None))
        except D.Fail as e:
            bl = None
            print(f"  {e}", flush=True)
        if bl is None:
            skipped = True
            print("SKIP blender: bpy not found (pip install bpy==5.0.1 on Python 3.11, or the Blender app)", flush=True)
        else:
            part_b(D, R, root, bl)
    finally:
        if not R.fails:
            shutil.rmtree(root, ignore_errors=True)
    allow = getattr(args, "allow_skip", False)
    print(f"selftest: {R.n - len(R.fails)}/{R.n} passed in {time.time() - t0:.1f} s" +
          (" (rendering half SKIPPED" + (", allowed)" if allow else ": pass --allow-skip to accept)") if skipped else "") +
          ("" if not R.fails else f"; kept {root}\nFAILED:\n  " + "\n  ".join(R.fails)), flush=True)
    if R.fails:
        return 1
    return 0 if (not skipped or allow) else 4
