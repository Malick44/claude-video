"""Voice the script, lay it on a timeline, and mix the soundtrack.

  python pipeline/build_audio.py episodes/<episode> [--stems]

Each line comes from the first of: a recording in <episode>/recordings/<shot>_<n>.* (any
audio format), a locked Eleven v4 take in <episode>/recordings/<shot>_<n>.v4.* (skipped under
NM_VOICES=kokoro), the character's TTS provider in cast.py (Kokoro by default, or ElevenLabs).
timeline.json records which captions an ElevenLabs voice made ("provider", "voice_id", "model") and
which are locked v4 takes ("generated"), so the end card's AI disclosure and SCRIPT.md follow the
soundtrack, not the cast in force when they run.
Audio tags in a line's spoken text ("[too quickly] I didn't see nothing.") go to ElevenLabs as written;
Kokoro gets the text without them (voiced_text). The captions never show them, the word timing gives
a sound tag ([sighs]) time only when the voice got it (words.py), and timeline.json keeps them so
SCRIPT.md can show them as directions. check_lines() stops before anything is voiced if a tag would
reach the screen or a stray bracket would reach a voice, and validate() if a shot can't be drawn right
(an unknown kind, a reenactment without its "REENACTMENT · AI" label, a tag too wide, and so on).
Music and sound effects come from soundtrack.py (synthesized unless pointed at stock assets).

A reenactment shot (kind "reenactment") plays a clip from clips/ (pipeline/clips.py files them): its
length is "dur" when set, else its lines or its clip, whichever is longer. Its lines are voiced and
captioned as on a still. Its cue is a reversed suck-in into a slowed hit on its first frame and a swell
that peaks into the hard cut, then "cut_silence" seconds of total silence. A missing clip renders its
fallback still, so the episode still builds.

The mix is 48 kHz stereo on three buses: dialogue; the score (theme layers whose intensity
builds toward the last shot marked "climax": True, else the last doorbell shot that flickers; ducked under
dialogue, dipped before each reveal and cut on shots marked "music": "out"); and effects
(stings, impacts, risers, whooshes, foley, ambiences), most of them placed automatically from
the shot kinds. The master
is compressed, limited and loudness-normalized to TikTok's level (-14 LUFS, -1.5 dBTP).

Outputs (in <episode>/build/):
  timeline.json  - shot/caption/sfx timings (+ stock credits) consumed by render.py / script_md.py
  soundtrack.wav - final mix (voice + score + sfx)
  stems/{dialogue,score,effects}.wav - with --stems: the three buses, pre-master, for remixing
"""
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

import numpy as np
import soundfile as sf

import clips as cliptools
import sounds as snd
import words as wordtimes
import stock
from common import (CLIP_FPS, CLIP_KINDS, CTA_DELAY, DISCLOSURE_IN, DISCLOSURE_MIN_S, KINDS, MODELS, REENACT_DEFAULT_S,
                    RX_TAG_MAX_X, RX_TAG_X, SHOW_DIR, clip_info, clip_path, doorbell_clock, file_sha1, fmt_rate,
                    load_episode, rx_tag_width, still_file)
from soundbank import Bank
from sounds import LEVELS, SR, typewriter_gain

AUDIO_EXTS = ("wav", "m4a", "mp3", "aiff", "aif", "flac", "ogg", "caf")
LOCKED = ".v4"     # recordings/<rec>.v4.<ext>: a locked Eleven v4 take (a raw clip from build/voice/), not a human one
VOICE_SR = 24000   # Kokoro's native rate; voice clips are cached at this rate, resampled for the mix
# Cast entry fields that don't change what the voice generates. FX_FIELDS run on the generated clip,
# so changing one re-processes the cached raw clip without voicing (or paying for) the line again;
# TIMING_FIELDS ("lang", the accent words.py phonemizes in) are in neither cache key.
FX_FIELDS = ("pitch", "altered", "fx_on_recordings")
TIMING_FIELDS = ("lang",)
LOUDNESS = -14.0   # integrated LUFS target (TikTok normalizes around here)
# Name cards (render.draw_lower_third): in at 0.35 s (or on the last line, or on the cut), 0.3 s to fade
# in, 0.25 s to fade out before the cut. A card fully legible under LT_MIN_S is too short to read, and on
# a shot with no lines its yellow note is the joke: at most SILENT_CARD_CPS characters a legible second.
LT_IN, LT_FADE_IN, LT_FADE_OUT, LT_MIN_S, SILENT_CARD_CPS = 0.35, 0.3, 0.25, 1.2, 20
HIT_PREROLL = 0.35        # reenact_hit's suck-in, before the reenactment's first frame
LINE_BEFORE_CUT = 0.5     # a reenactment's last line should end this long before its hard cut
RX_SHARE = 0.20           # reenactments past this share of the runtime (or more than RX_MAX) warn
RX_MAX = 2
CONFESSIONAL_S = 30.0     # under this (or EPISODE "CONFESSIONAL: ..."), a Confessional: one reenactment of
CONFESSIONAL_RX_S = 5.0   # at most this long replaces the share rule
KB_LOCKED = (0.03, 0.02)  # a reenactment's camera counts as moving past a 3% zoom or a 0.02 centre move
CLIPS = {}                # shot id -> (clip path or None, clip_info or None), filled by validate()

ep = None  # set in main()
BUILD = CACHE = None
FFMPEG = None


def has_filter(exe, name):
    out = subprocess.run([exe, "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return re.search(rf"^\s*\S+\s+{name}\s", out, re.M) is not None


def ffmpeg():
    # The bundled imageio-ffmpeg build has no rubberband, which the pitched voices need, so prefer
    # a system ffmpeg that does (brew install ffmpeg) and fall back to the bundled one.
    global FFMPEG
    if FFMPEG is None:
        import imageio_ffmpeg
        FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
        if not has_filter(FFMPEG, "rubberband"):
            system = shutil.which("ffmpeg")
            if system and has_filter(system, "rubberband"):
                FFMPEG = system
    return FFMPEG


def db(x):
    return 10 ** (x / 20)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- voice

_kokoro = None


def kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(MODELS, "kokoro.onnx"), os.path.join(MODELS, "voices.bin"))
    return _kokoro


def trim(y, thresh=db(-45), pad=0.03):
    idx = np.where(np.abs(y) > thresh)[0]
    if not len(idx):
        return y
    a = max(0, idx[0] - int(pad * VOICE_SR))
    b = min(len(y), idx[-1] + int(pad * VOICE_SR))
    return y[a:b]


def fx(path_in, path_out, cast):
    filters = []
    if cast.get("pitch", 1.0) != 1.0:
        filters.append(f"rubberband=pitch={cast['pitch']}")
    if cast.get("altered"):
        # documentary "voice altered": pitch-down (above) + a little grit and phone-ish band.
        filters += ["highpass=f=120", "lowpass=f=5200", "acrusher=bits=10:mix=0.25:mode=log", "vibrato=f=5.5:d=0.08"]
    if not filters:
        return path_in
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", path_in, "-af", ",".join(filters),
                    "-ar", str(VOICE_SR), path_out], check=True)
    return path_out


def recording(rec):
    """The take that replaces a line's TTS, if <episode>/recordings/ has one: your own take (hook_1.m4a)
    first, else a locked v4 take (hook_1.v4.wav, the line's raw clip copied from build/voice/). Under
    NM_VOICES=kokoro a locked v4 take is skipped, so a Kokoro build stays Kokoro after takes are locked;
    a human take wins over every cast."""
    names = [rec] if os.environ.get("NM_VOICES") == "kokoro" else [rec, rec + LOCKED]
    for name in names:
        for ext in AUDIO_EXTS:
            path = os.path.join(ep.DIR, "recordings", f"{name}.{ext}")
            if os.path.exists(path):
                return path
    return None


def locked_take(path):
    """True for a locked v4 take (recordings/<rec>.v4.<ext>): an ElevenLabs voice, not a human, so the end
    card and SCRIPT.md still count it as an AI voice."""
    return bool(path) and os.path.splitext(os.path.basename(path))[0].endswith(LOCKED)


def check_lines():
    """Stop before voicing anything if a line would go wrong: an audio tag (words.TAG) that would be
    shown on screen and also sent to the voice, a bracket that isn't a whole tag, a Kokoro line that
    is only tags, or a speaker missing from the cast. Warn, once per character, when tags go to a
    voice that won't act on them. A line with a recording sends nothing to a voice, so it's skipped."""
    warned = set()
    for shot in ep.SHOTS:
        n = 0
        for item in shot["items"]:
            if item[0] == "pause":
                continue
            _, who, text, say = item
            n += 1
            where = f"shot {shot['id']}, line {n} ({who})"
            if who not in ep.CAST:
                sys.exit(f"{where}: {who} is not in the cast - add them to cast.py (or this episode's CAST)")
            if recording(f"{shot['id']}_{n}"):
                continue
            vid = ep.CAST[who].get("voice_id") if ep.CAST[who].get("provider") == "elevenlabs" else None
            if vid is not None and (not vid or str(vid).startswith("<")):
                sys.exit(f"{where}: {who} has no ElevenLabs voice yet: the voice_id is the placeholder {vid!r}. Design "
                         "the voice and fill in its id (CAST_V4 in cast.py), or build on the Kokoro scratch cast "
                         "(leave NM_VOICES unset, or NM_VOICES=kokoro)")
            plain = re.sub(r"[\[\]]", "", text)
            # a bracket in the caption is on-screen text ("[REDACTED]") unless it also goes to the voice
            tag = next((t for t in wordtimes.TAG.findall(text) if t in say), None)
            if tag and say == text:
                sys.exit(f"{where}: the caption {text!r} has {tag}, and with no separate spoken text it would "
                         "be both shown on screen and sent to the voice as an audio tag. For a delivery "
                         f"direction, put it only in the spoken text, L()'s third argument: L({who!r}, "
                         f"{wordtimes.strip_tags(text)!r}, {text!r}). For on-screen text, give L() a third "
                         f"argument without brackets: L({who!r}, {text!r}, {plain!r})")
            if tag:
                sys.exit(f"{where}: the caption {text!r} shows the audio tag {tag}, which the spoken text "
                         f"also sends to the voice. Keep the tag only in the spoken text: L({who!r}, "
                         f"{wordtimes.strip_tags(text)!r}, {say!r})")
            if re.search(r"[\[\]]", wordtimes.strip_tags(say)):
                if say == text:
                    sys.exit(f"{where}: the caption {text!r} has square brackets, and with no separate spoken "
                             "text they would also go to the voice, where brackets mean audio tags. Give L() "
                             f"a third argument without brackets: L({who!r}, {text!r}, {plain!r})")
                sys.exit(f"{where}: the spoken text {say!r} has a square bracket that isn't part of a whole "
                         "audio tag (a word or phrase in brackets that starts with a letter, like [deadpan]); "
                         "fix the tag or take the bracket out")
            tags = wordtimes.TAG.findall(say)
            if not tags:
                continue
            cast = ep.CAST[who]
            model = cast.get("model", stock.TTS_MODEL)
            if cast.get("provider", "kokoro") != "elevenlabs":
                if not wordtimes.strip_tags(say).strip():
                    sys.exit(f"{where}: the spoken text {say!r} is only audio tags, which a Kokoro voice "
                             "leaves out, so there is nothing to say")
                if who not in warned:
                    warned.add(who)
                    print(f"warning: {where}: {who} is a Kokoro voice, which leaves audio tags ({tags[0]}) out; "
                          'give them an ElevenLabs voice with "model": "eleven_v4" in cast.py to use them',
                          file=sys.stderr)
            elif model not in stock.TAG_MODELS and who not in warned:
                warned.add(who)
                print(f"warning: {where}: {who}'s ElevenLabs model {model} may read audio tags out loud; "
                      'give them "model": "eleven_v4" in cast.py', file=sys.stderr)


def warn(msg):
    print(f"warning: {msg}", file=sys.stderr)


def has_lines(shot):
    return any(item[0] != "pause" for item in shot["items"])


def static_length(shot):
    """A shot's pre, P() pauses and post: its length before lines and "min", as main() lays it out."""
    return shot.get("pre", 0.0) + sum(it[1] for it in shot["items"] if it[0] == "pause") + shot.get("post", 0.0)


def validate():
    """Stop before anything is voiced on a shot the renderer can't draw right, naming the shot and the fix,
    and warn about the mistakes a machine can catch. Every check is on a kind or field the published
    episodes don't use (or misuse), so they build as before."""
    shots = ep.SHOTS
    ids = [s.get("id") for s in shots]
    dup = sorted({str(x) for x in ids if ids.count(x) > 1})
    if dup:
        sys.exit(f"shot ids must be unique (recordings, clips and captions are keyed by them): {', '.join(dup)}")
    for i, s in enumerate(shots):
        sid, kind = s.get("id"), s.get("kind")
        where = f"shot {sid}"
        if kind not in KINDS:
            close = difflib.get_close_matches(str(kind), KINDS, 1)
            sys.exit(f"{where}: unknown kind {kind!r}" + (f" (did you mean {close[0]!r}?)" if close else "")
                     + f"; the kinds are {', '.join(KINDS)}")
        if kind == "doorbell":
            if not isinstance(s.get("flicker", True), bool):
                sys.exit(f"{where}: \"flicker\" must be True or False, not {s['flicker']!r}")
            ja = s.get("jump_after", 0)
            if isinstance(ja, bool) or not isinstance(ja, int):
                sys.exit(f"{where}: \"jump_after\" must be a whole number of seconds, not {ja!r} "
                         "(the doorbell clock ticks in whole seconds)")
        at = s.get("lower_third_at")
        if at not in (None, "last", "cut"):
            sys.exit(f"{where}: \"lower_third_at\" is \"last\" (in on the last line) or \"cut\" (on from the "
                     f"first frame to the cut), not {at!r}")
        if at == "last" and not has_lines(s):
            sys.exit(f"{where}: \"lower_third_at\": \"last\" needs a line to come in on; this shot has none. "
                     "For a silent cutaway use \"lower_third_at\": \"cut\"")
        if kind in CLIP_KINDS:
            validate_clip(i, s)
    rx = [s for s in shots if s["kind"] == "reenactment"]
    if rx:
        ends = [s for s in shots if s["kind"] == "end"]
        if not ends:
            sys.exit("this episode has a reenactment but no end shot: the AI disclosure is on the end card, so "
                     "add {\"id\": \"end\", \"kind\": \"end\", \"items\": [], \"min\": 2.6}")
        for e in ends:
            if not has_lines(e):     # an end card with lines is checked once they are voiced
                check_disclosure(e, max(static_length(e), e.get("min", 0.0)))
        if len(rx) > RX_MAX:
            warn(f"{len(rx)} reenactments: more than {RX_MAX} spends the move; keep one or two, each a theory")
    for key, spec in getattr(ep, "DERIVED_STILLS", {}).items():
        unknown = set(spec) - {"from", "gamma", "blur", "tint", "gain"}
        if not spec.get("from") or unknown:
            sys.exit(f"DERIVED_STILLS[{key!r}]: needs \"from\" (the still it lifts) and takes only gamma, blur, tint "
                     f"and gain" + (f"; unknown: {', '.join(sorted(unknown))}" if unknown else ""))
        if spec["from"] != key and spec["from"] in ep.DERIVED_STILLS:
            sys.exit(f"DERIVED_STILLS[{key!r}]: derive from a still file, not from another derived key ({spec['from']!r})")
        if not still_file(ep, spec["from"]):
            warn(f"DERIVED_STILLS[{key!r}]: its source still {spec['from']!r} doesn't exist")
    for key, kind, errors, warnings in cliptools.lint_episode(ep):
        what = "CLIPS" if kind == "motion" else "STILLS"
        for e in errors:
            warn(f"{what}[{key!r}]: the {kind} prompt {e} (pipeline/clips.py add refuses it)")
        for w in warnings:
            warn(f"{what}[{key!r}]: the {kind} prompt {w}")


def validate_clip(i, s):
    """A clip shot's own checks (validate()). Resolves its clip into CLIPS."""
    shots = ep.SHOTS
    d = CLIP_KINDS[s["kind"]]
    where = f"shot {s['id']}"
    if not s.get("clip"):
        sys.exit(f"{where}: a {s['kind']} needs \"clip\": the key of episodes/<ep>/clips/<key>.mp4 or the "
                 "series clips/ (and a \"fallback\" list of views to render until the clip exists)")
    label = s.get("label", d["label"])
    if label != d["label"]:
        sys.exit(f"{where}: the label must read exactly {d['label']!r}: every reenactment is marked AI on screen. "
                 f"Put the theory and any escalation in the stamp (\"stamp\": \"THEORY #2: ... (DIRECTOR'S CUT)\"), "
                 f"not {label!r}")
    stamp = s.get("stamp")
    if RX_TAG_X + rx_tag_width(label, stamp) > RX_TAG_MAX_X:
        sys.exit(f"{where}: the tag would end at x {RX_TAG_X + rx_tag_width(label, stamp)}, past x {RX_TAG_MAX_X} "
                 "(the apps' buttons): shorten the label or the stamp")
    speed = s.get("speed", 1.0)
    if speed != "fit" and (isinstance(speed, bool) or not isinstance(speed, (int, float)) or not 0.25 <= speed <= 2.0):
        sys.exit(f"{where}: \"speed\" is a playback rate from 0.25 to 2.0, or \"fit\", not {speed!r}")
    if speed == "fit" and "dur" not in s and not has_lines(s) and max(static_length(s), s.get("min", 0.0)) <= 0:
        sys.exit(f"{where}: \"speed\": \"fit\" stretches the clip over the shot, and a shot with no lines, pauses, "
                 "\"pre\", \"post\" or \"min\" has no length to stretch it over: set \"dur\"")
    if s.get("interp", "nearest") not in ("nearest", "blend"):
        sys.exit(f"{where}: \"interp\" is \"nearest\" or \"blend\", not {s['interp']!r}")
    if s.get("look", d["look"]) not in (d["look"], None):
        sys.exit(f"{where}: \"look\" is {d['look']!r} or None, not {s['look']!r}")
    for field, why in (("lower_third", "no name card on a reenactment: the cut-back's real ornament gets it"),
                       ("climax", "the score is cut under a reenactment; mark the shot after it")):
        if s.get(field):
            sys.exit(f"{where}: {field!r} isn't allowed on a reenactment ({why})")
    if s.get("music") == "out":
        sys.exit(f"{where}: \"music\": \"out\" isn't allowed on a reenactment: its swell plays on the score bus, "
                 "and the score is already cut under it and silent after the cut")
    if i == len(shots) - 1:
        sys.exit(f"{where}: a reenactment can't be the last shot: it needs a hard cut back to the real ornament")
    if "dur" in s and not (isinstance(s["dur"], (int, float)) and s["dur"] > 0):
        sys.exit(f"{where}: \"dur\" is the shot length in seconds, not {s['dur']!r}")
    cin, cout = s.get("in", 0.0), s.get("out")
    number = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)   # noqa: E731
    if not number(cin) or cin < 0 or (cout is not None and (not number(cout) or cout <= cin)):
        sys.exit(f"{where}: \"in\" and \"out\" are seconds of the clip, 0 <= in < out (got in {cin!r}, out {cout!r})")
    path = clip_path(ep.DIR, s["clip"])
    info = clip_info(path) if path else None
    if path and not info:
        sys.exit(f"{where}: {path} has no video stream; file the clip with pipeline/clips.py add")
    if info:
        add = f"pipeline/clips.py add {os.path.relpath(ep.DIR, SHOW_DIR)} {s['clip']} <file> --generator ..."
        if abs(info["fps"] - CLIP_FPS) > 0.01:
            sys.exit(f"{where}: {os.path.basename(path)} is {info['fps']:g} fps, not {CLIP_FPS}: file it with {add}")
        if info["rotation"] or info["sar"] != (1, 1):
            sys.exit(f"{where}: {os.path.basename(path)} has " + (f"a {info['rotation']:g}° rotation" if info["rotation"]
                     else f"non-square pixels (SAR {info['sar'][0]}:{info['sar'][1]})") + ", which the renderer "
                     f"doesn't apply, so it would play garbled or stretched: file it with {add}")
        if cin >= info["seconds"] or (cout is not None and cout > info["seconds"] + 0.5 / CLIP_FPS):
            sys.exit(f"{where}: \"in\" {cin:g} / \"out\" {cout} fall outside the clip ({info['seconds']:.2f} s)")
    CLIPS[s["id"]] = (path, info)
    # warnings: each a mistake a draft made
    if stamp and re.search(r"\d:\d\d", stamp):
        warn(f"{where}: the stamp {stamp!r} has a clock time; a theory must not be readable against the doorbell table")
    (cx0, cy0, z0), (cx1, cy1, z1) = s.get("kb", ((0.5, 0.5, 1.0), (0.5, 0.5, 1.0)))
    if abs(z1 / z0 - 1) > KB_LOCKED[0] or max(abs(cx1 - cx0), abs(cy1 - cy0)) > KB_LOCKED[1]:
        warn(f"{where}: the camera moves (\"kb\"); lock it, since a push-in on a rigid figure reads as a zoom on a still")
    if speed != 1.0:
        warn(f"{where}: \"speed\" {speed!r}: keep 1.0 and tune \"in\"; slow motion belongs in the generated take "
             "(or a one-time retime with pipeline/clips.py add --retime)")
    if s.get("interp") == "blend":
        warn(f"{where}: \"interp\": \"blend\" ghosts the frames; retime at intake instead (clips.py add --retime)")
    nxt = shots[i + 1]
    if nxt["kind"] not in ("still", "evidence"):
        warn(f"{where}: the next shot ({nxt['id']}, {nxt['kind']}) isn't a still or evidence shot; cut back to the "
             "real ornament, unmoved, for the denial")
    if i and "sting_soft" in shots[i - 1].get("sfx", []):
        warn(f"shot {shots[i - 1]['id']}: its sting_soft swell peaks on the reenactment's first frame, on top of "
             "reenact_hit; drop it")


def check_disclosure(shot, length):
    if length - DISCLOSURE_IN < DISCLOSURE_MIN_S:
        sys.exit(f"shot {shot['id']}: on an episode with a reenactment the end card's AI disclosure is fully visible "
                 f"from {DISCLOSURE_IN} s, so a {length:.2f} s card shows it for {length - DISCLOSURE_IN:.2f} s, under "
                 f"{DISCLOSURE_MIN_S} s: give the end card \"min\": {DISCLOSURE_IN + DISCLOSURE_MIN_S:.2f} or more")


def clip_timing(shot, start, t):
    """(end time, timeline fields) for a clip shot whose pre, lines and post end at t."""
    sid = shot["id"]
    d = CLIP_KINDS[shot["kind"]]
    path, info = CLIPS[sid]
    content = t - start
    cin = float(shot.get("in", 0.0))
    cout = float(shot["out"]) if "out" in shot else (info["seconds"] if info else None)
    speed = shot.get("speed", 1.0)
    note = ""
    if "dur" in shot:
        length = float(shot["dur"])
        if content > length + 1e-6:
            sys.exit(f"shot {sid}: its pre, lines and post run {content:.2f} s, longer than \"dur\" {length:g}: raise "
                     f"\"dur\" (to at most {d['length'][1]:g}) or shorten the line")
    elif speed == "fit" or cout is None:
        length = max(content, shot.get("min", 0.0), 0.0 if cout is not None else REENACT_DEFAULT_S)
        if cout is None:
            note = (f"; its clip is missing, so it runs {length:.2f} s until the clip lands and then changes length: "
                    "set \"dur\"")
    else:
        length = max(content, (cout - cin) / speed, shot.get("min", 0.0))
    if length <= 0:     # validate_clip() stops a "fit" shot with nothing to give it a length; this is the guard
        sys.exit(f"shot {sid}: the shot has no length (no lines, pauses, \"pre\", \"post\", \"min\" or clip): set \"dur\"")
    if speed == "fit":
        speed = (cout - cin) / length if cout is not None else 1.0
        if not 0.25 <= speed <= 2.0:
            sys.exit(f"shot {sid}: \"speed\": \"fit\" plays {cout - cin:.2f} s of clip in {length:.2f} s, a rate of "
                     f"{speed:.2f}, outside 0.25-2.0: trim the clip with \"in\"/\"out\" or change the lines")
    play = (cout - cin) / speed if cout is not None else None
    freeze = round(play, 3) if play is not None and length > play + 1e-6 else None
    fallback = next((v["img"] for v in shot.get("fallback", []) if still_file(ep, v["img"])), None)
    if path is None:
        warn(f"shot {sid}: clip {shot['clip']} is missing, so it renders "
             + (f"its fallback still {fallback}" if fallback else "a placeholder (no fallback still exists either)")
             + f" under the label; file the clip with pipeline/clips.py add {os.path.relpath(ep.DIR, SHOW_DIR)} "
             f"{shot['clip']} <file>" + note)
    else:
        index = os.path.join(os.path.dirname(path), "clips.json")
        if shot["clip"] not in (json.load(open(index)) if os.path.exists(index) else {}):
            warn(f"shot {sid}: clip {shot['clip']} has no clips.json entry (no prompt or generator on record); "
                 "file it with pipeline/clips.py add")
    fields = {
        "clip_file": os.path.relpath(path, SHOW_DIR) if path else None,
        "clip_sha1": file_sha1(path)[:12] if path else None,
        "clip_in": round(cin, 4), "clip_out": round(cout, 4) if cout is not None else None,
        "clip_speed": round(speed, 6), "clip_fps": info["fps"] if info else None,
        "clip_w": info["w"] if info else None, "clip_h": info["h"] if info else None,
        "clip_frames": info["frames"] if info else None, "clip_freeze_at": freeze,
        "clip_missing": path is None, "clip_fallback": fallback,
        "label": shot.get("label", d["label"]), "look": shot.get("look", d["look"]), "cue": shot.get("cue", d["cue"]),
        "interp": shot.get("interp", "nearest"), "cut_silence": shot.get("cut_silence", d["cut_silence"]),
        "kb": shot.get("kb", ((0.5, 0.5, 1.0), (0.5, 0.5, 1.0))),
    }
    return start + length, fields


def clip_note(s):
    if s["clip_missing"]:
        return f"  clip {s['clip']} [MISSING -> fallback {s['clip_fallback'] or 'placeholder'}]"
    used = min(s["clip_out"], s["clip_in"] + (s["end"] - s["start"]) * s["clip_speed"])   # cut there by "dur"
    return f"  clip {s['clip']} {s['clip_in']:.2f}-{used:.2f}s @{fmt_rate(s['clip_speed'])}x"


def legible(s):
    """Seconds a shot's name card is fully on screen (render.draw_lower_third's timing)."""
    dur = s["end"] - s["start"]
    if s.get("lower_third_at") == "cut":
        return dur
    t0 = s["lines"][-1]["start"] - s["start"] if s.get("lower_third_at") == "last" else LT_IN
    return dur - LT_FADE_OUT - (t0 + LT_FADE_IN)


def check_timeline(shots, total):
    """Checks that need the voiced timeline: warnings, plus the end card's disclosure when it has lines."""
    rx = [s for s in shots if s["kind"] in CLIP_KINDS]
    for i, s in enumerate(shots):
        where = f"shot {s['id']}"
        dur = s["end"] - s["start"]
        if s.get("lower_third"):
            got = legible(s)
            if got < LT_MIN_S:
                warn(f"{where}: its name card is fully legible for {max(0.0, got):.2f} s (under {LT_MIN_S} s); give a "
                     "short or silent shot \"lower_third_at\": \"cut\", or more time")
            note = s["lower_third"][2] if len(s["lower_third"]) > 2 else ""
            if not s["lines"] and got > 0 and len(note) > SILENT_CARD_CPS * got:
                warn(f"{where}: on a silent shot the name card is the joke, and its note {note!r} ({len(note)} characters) "
                     f"is more than {SILENT_CARD_CPS} characters a second of its {got:.2f} s; keep the punch short "
                     "(about 15 characters) and put the setup in the subtitle")
        if s["kind"] == "end" and rx and s["lines"]:
            check_disclosure(s, dur)
        if s["kind"] not in CLIP_KINDS:
            continue
        lo, hi = CLIP_KINDS[s["kind"]]["length"]
        if not lo <= dur <= hi:
            warn(f"{where}: {dur:.2f} s long, outside {lo:g}-{hi:g} s")
        if s.get("clip_freeze_at") is not None and dur - s["clip_freeze_at"] > 1.0:
            warn(f"{where}: the clip ends {dur - s['clip_freeze_at']:.2f} s before the cut and freezes on its last frame "
                 "(over 1 s); set \"dur\", or trim the line")
        if s["lines"] and s["end"] - s["lines"][-1]["end"] < LINE_BEFORE_CUT:
            warn(f"{where}: its last line ends {s['end'] - s['lines'][-1]['end']:.2f} s before the cut (under "
                 f"{LINE_BEFORE_CUT} s): leave the action time under the swell's peak")
        prev = shots[i - 1] if i else None
        # timeline times are rounded to the millisecond, so a "post" of exactly HIT_PREROLL can measure a hair under it
        if prev is not None and s.get("cue") and prev["lines"] and s["start"] - prev["lines"][-1]["end"] < HIT_PREROLL - 0.001:
            warn(f"shot {prev['id']}: its last line ends {s['start'] - prev['lines'][-1]['end']:.2f} s before {s['id']}, "
                 f"under reenact_hit's {HIT_PREROLL} s suck-in, which would play over it; give it \"post\"")
    if not rx:
        return
    if str(getattr(ep, "EPISODE", "")).upper().startswith("CONFESSIONAL") or total < CONFESSIONAL_S:
        # a Confessional's rule (SERIES.md): at most one reenactment, 5 s or shorter. Its share of a 15-25 s
        # short is always over 20%, so the share rule doesn't apply.
        long = [s["id"] for s in rx if s["end"] - s["start"] > CONFESSIONAL_RX_S + 1e-6]
        if len(rx) > 1 or long:
            warn(f"a Confessional has at most one reenactment, {CONFESSIONAL_RX_S:g} s or shorter; this one has "
                 f"{len(rx)}" + (f", and {', '.join(long)} runs longer" if long else ""))
        return
    share = sum(s["end"] - s["start"] for s in rx) / total if total else 0
    if share > RX_SHARE:
        warn(f"reenactments are {share:.0%} of the runtime (over {RX_SHARE:.0%}); they are the punch, not the episode")


def voiced_text(who, say):
    """The text a character's voice is given: as written for ElevenLabs, without its audio tags for
    Kokoro, which would read them out. The word timing uses the same text, so a tag the voice never
    got ([sighs] on a Kokoro line, or on your own take of one) has no time of its own in the captions."""
    return say if ep.CAST[who].get("provider") == "elevenlabs" else wordtimes.strip_tags(say)


def voice_line(who, say, rec):
    if who not in ep.CAST:
        sys.exit(f"{who} is not in the cast - add them to cast.py (or this episode's CAST)")
    cast = ep.CAST[who]
    provider = cast.get("provider", "kokoro")
    say = voiced_text(who, say)
    take = recording(rec)
    keyed = {k: v for k, v in cast.items() if k not in TIMING_FIELDS}
    if take:
        st = os.stat(take)
        key = gen = hashlib.sha1(json.dumps([keyed, take, st.st_size, st.st_mtime]).encode()).hexdigest()[:12]
    else:
        key = hashlib.sha1(json.dumps([keyed, say]).encode()).hexdigest()[:12]
        voice = {k: v for k, v in keyed.items() if k not in FX_FIELDS}
        gen = hashlib.sha1(json.dumps([voice, say]).encode()).hexdigest()[:12]
    raw = os.path.join(CACHE, f"{who}_{gen}_raw.wav")   # the clip as voiced: same voice and text, same file
    out = os.path.join(CACHE, f"{who}_{key}.wav")        # after FX, trim and loudness
    if not os.path.exists(out):
        apply_fx = not take or cast.get("fx_on_recordings", False)
        if take or not os.path.exists(raw):   # only the FX changed: re-process the raw clip, don't re-voice
            if take:
                samples = stock.decode_audio(take, VOICE_SR)
            elif provider == "elevenlabs":
                samples = stock.decode_audio_bytes(stock.elevenlabs_tts(say, cast), VOICE_SR)
            elif provider == "kokoro":
                samples, sr = kokoro().create(say, voice=cast["voice"], speed=cast["speed"], lang="en-us" if cast["voice"][0] == "a" else "en-gb")
                assert sr == VOICE_SR, sr
            else:
                sys.exit(f"{who}: unknown voice provider {provider!r} (kokoro or elevenlabs)")
            sf.write(raw, samples, VOICE_SR)
        processed = fx(raw, out + ".fx.wav", cast) if apply_fx else raw
        y, _ = sf.read(processed)
        y = trim(y)
        # loudness-match every line: RMS target, peak-capped
        rms = np.sqrt(np.mean(y ** 2)) + 1e-9
        y = y * (db(-17) / rms)
        peak = np.max(np.abs(y))
        if peak > db(-1.5):
            y = y * (db(-1.5) / peak)
        sf.write(out, y, VOICE_SR)
    return stock.decode_audio(out, SR)  # resampled to the mix rate


_phonemizers = {}


def phonemizer(who):
    """Word -> phonemes in the speaker's accent, for word timing (any provider's audio): the cast
    entry's "lang" ("en-us" or "en-gb"), else the Kokoro preset's (a... is US), else US English.
    One function per accent, so words.weight's cache (keyed by it) is shared across lines."""
    cast = ep.CAST[who]
    lang = cast.get("lang") or ("en-us" if cast.get("voice", "a")[0] == "a" else "en-gb")
    if lang not in _phonemizers:
        _phonemizers[lang] = lambda w: kokoro().tokenizer.phonemize(w, lang)
    return _phonemizers[lang]


def climax_at(shots, end):
    """When the score peaks: the last shot marked "climax": True, else the last doorbell shot that flickers
    (a "flicker": False doorbell is a cold open, before the title: never the peak), else `end`."""
    marked = [s["start"] for s in shots if s.get("climax")]
    doorbells = [s["start"] for s in shots if s["kind"] == "doorbell" and s.get("flicker", True)]
    return (marked or doorbells or [end])[-1]


# ---------------------------------------------------------------- mastering

def master(raw_path, out_path):
    """Glue compression + limiter + two-pass EBU R128 loudness normalization."""
    chain = "highpass=f=30,acompressor=threshold=0.125:ratio=2.5:attack=15:release=250:makeup=1.5,alimiter=limit=0.9:attack=5:release=60"
    target = f"I={LOUDNESS}:TP=-1.5:LRA=11"
    probe = subprocess.run([ffmpeg(), "-hide_banner", "-i", raw_path, "-af", f"{chain},loudnorm={target}:print_format=json",
                            "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(re.findall(r"\{[^{}]*\}", probe.stderr)[-1])
    measured = (f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
                f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", raw_path, "-af", f"{chain},loudnorm={target}:{measured}",
                    "-ar", str(SR), "-c:a", "pcm_s16le", out_path], check=True)


# ---------------------------------------------------------------- timeline + mix


def main():
    global ep, BUILD, CACHE
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        sys.exit("usage: build_audio.py episodes/<episode> [--stems]")
    ep = load_episode(args[0])
    validate()
    check_lines()
    BUILD = ep.BUILD
    CACHE = os.path.join(BUILD, "voice")
    os.makedirs(CACHE, exist_ok=True)
    t = 0.0
    shots, captions, voice = [], [], []
    for shot in ep.SHOTS:
        start = t
        t += shot.get("pre", 0.0)
        lines = []
        for item in shot["items"]:
            if item[0] == "pause":
                t += item[1]
                continue
            _, who, text, say = item
            rec = f"{shot['id']}_{len(lines) + 1}"
            y = voice_line(who, say, rec)
            dur = len(y) / SR
            voice.append((t, y))
            # when each caption word is spoken, for the renderer's word highlight
            timed = wordtimes.caption_times(y, SR, voiced_text(who, say), text, phonemizer(who))
            spoken = [[w, round(t + a, 3), round(t + b, 3)] for w, a, b in timed]
            take = recording(rec)
            captions.append({"start": round(t, 3), "end": round(t + dur, 3), "who": who, "text": text, "shot": shot["id"],
                             "rec": rec, "recorded": bool(take), "words": spoken})
            # Who voiced it, for the end card's disclosure and SCRIPT.md's Voices table, which read the timeline
            # rather than the cast in force when they run (NM_VOICES may differ). Written only for an AI voice
            # the end card names (left out on Kokoro and human lines, so their timelines don't change).
            cast = ep.CAST[who]
            if locked_take(take):
                captions[-1]["generated"] = True
            elif not take and cast.get("provider") == "elevenlabs":
                captions[-1] |= {"provider": "elevenlabs", "voice_id": cast["voice_id"],
                                 "model": cast.get("model", stock.TTS_MODEL)}
            tags = wordtimes.TAG.findall(say)
            if tags:   # the line's delivery directions, for SCRIPT.md (left out when there are none)
                captions[-1]["tags"] = tags
            lines.append({"start": round(t, 3), "end": round(t + dur, 3), "text": text})
            t += dur
        t += shot.get("post", 0.0)
        extra = {}
        if shot["kind"] in CLIP_KINDS:
            t, extra = clip_timing(shot, start, t)
        else:
            t = max(t, start + shot.get("min", 0.0))
        shots.append({k: v for k, v in shot.items() if k != "items"} | extra
                     | {"start": round(start, 3), "end": round(t, 3), "lines": lines})
        print(f"{shot['id']:10s} {start:6.2f} -> {t:6.2f}  ({t - start:4.2f}s)" + (clip_note(shots[-1]) if extra else ""))
    total = t
    print(f"TOTAL {total:.2f}s")
    check_timeline(shots, total)

    n = int((total + 0.5) * SR)
    vox = np.zeros(n)
    for s, y in voice:
        i = int(s * SR)
        vox[i: i + len(y)] += y[: n - i]
    score = np.zeros((n, 2))     # theme: ducked, shaped by intensity, gated
    under = np.zeros((n, 2))     # risers + soft swells: ducked under dialogue only
    fxbus = np.zeros((n, 2))     # stings, hits, foley, ambiences

    def put(buf, at, y, gain_db, until=None):
        """Add sound y at time `at`; with `until`, cut it there (a hard cut), with an 8 ms declick."""
        i = int(round(at * SR))
        if i < 0:
            y, i = y[-i:], 0
        if i >= n or not len(y):
            return
        seg = snd.stereo(y)[: n - i]
        if until is not None:
            stop = int(round(until * SR)) - i
            if stop <= 0:
                return
            if stop < len(seg):
                k = min(stop, int(0.008 * SR))
                seg = seg[:stop] * np.r_[np.ones(stop - k), np.linspace(1, 0, k)][:, None]
        buf[i: i + len(seg)] += seg * db(gain_db)

    bank = Bank(ep.SOUNDS, [ep.DIR, SHOW_DIR])

    # ---- doorbell timings (used by both the mix and the renderer)
    for s in shots:
        if s["kind"] == "doorbell" and s.get("flicker", True):   # "flicker": False shows only the jump (a cold open)
            s["flicker_at"] = round(s["lines"][-1]["end"] + 0.15, 3)

    # ---- score: theme from the title card (first "sting") to the end card
    bed_start = next((s["start"] for s in shots if "sting" in s.get("sfx", [])), 0.0)
    bed_end = next((s["start"] for s in shots if s["kind"] == "end"), total) + 0.4
    climax = climax_at(shots, bed_end)
    length = bed_end - bed_start
    tt = np.arange(int(length * SR)) / SR + bed_start
    intensity = 0.3 + 0.7 * np.clip((tt - bed_start) / max(1e-3, climax - bed_start), 0, 1) ** 1.3
    gate = np.ones(len(tt))

    def dip(a, b, level, fade_out=0.2, fade_in=0.4):
        m = (tt >= a) & (tt < b)
        gate[m] = np.minimum(gate[m], level)
        for x0, x1, v0, v1 in ((a - fade_out, a, 1, level), (b, b + fade_in, level, 1)):
            m = (tt >= x0) & (tt < x1)
            ramp = v0 + (v1 - v0) * (tt[m] - x0) / max(1e-3, x1 - x0)
            gate[m] = np.minimum(gate[m], ramp)

    for j, s in enumerate(shots):
        if s.get("music") == "out":
            dip(s["start"], s["end"], 0.0)
        if s["kind"] == "doorbell" and "flicker_at" in s:  # hush under the flicker so the reveal hit lands
            dip(s["flicker_at"], s["flicker_at"] + CTA_DELAY, 0.3, 0.3, 0.6)
        if s["kind"] in CLIP_KINDS:   # the score is out under the clip and for cut_silence after the hard cut
            nxt = shots[j + 1] if j + 1 < len(shots) else None
            silence = 0.0 if nxt and nxt["kind"] in CLIP_KINDS else s["cut_silence"]
            dip(s["start"], s["end"] + silence, 0.0, fade_out=0.08, fade_in=0.6)
    fade = np.ones(len(tt))
    k = int(1.5 * SR)
    fade[-k:] = np.linspace(1, 0, k)
    shape = (gate * fade)[:, None]
    if not ep.SOUNDS.get("theme") or ep.SOUNDS.get("theme") == "synth":
        L = snd.theme_layers(length)
        bed = (L["piano"] * 0.85 + L["drone"] * 0.25
               + L["pad"] * (0.35 + 0.55 * intensity)[:, None]
               + L["pulse"] * (0.7 * smooth((intensity - 0.5) / 0.3))[:, None]
               + L["shimmer"] * (0.3 * smooth((intensity - 0.8) / 0.2))[:, None])
    else:
        bed = snd.stereo(bank.get("theme", length)) * (0.7 + 0.3 * intensity)[:, None]
    bed = np.stack([snd.highpass(bed[:, ch], 45, 2) for ch in (0, 1)], axis=1)  # no mud under dialogue
    put(score, bed_start, bed[: len(tt)] * shape, LEVELS["bed"])

    # ---- effects, mostly placed from the shot kinds
    for s in shots:
        until = s["end"] if s["kind"] in CLIP_KINDS else None   # a clip shot's sounds stop dead on its hard cut
        for name in s.get("sfx", []):
            if name == "sting":
                # a riser sweeps into the title, then braam + impact + piano cluster
                rs = min(2.0, s["start"])
                put(under, s["start"] - rs, bank.get("riser", rs), LEVELS["riser"], until)
                put(fxbus, s["start"], bank.get("sting"), LEVELS["sting"], until)
            elif name == "sting_end":
                put(fxbus, s["start"], bank.get("sting_end"), LEVELS["sting_end"], until)
            elif name == "sting_soft":
                # a low swell under the shot's last line (the question the episode asks)
                put(under, s["lines"][-1]["start"] - 0.1, bank.get(name), LEVELS[name], until)
            elif name == "shutter":
                put(fxbus, s["start"], bank.get("shutter"), LEVELS["shutter"], until)
                put(fxbus, s["start"], bank.get("impact"), LEVELS["impact"] - 4, until)
            elif name in ("wind", "chimes", "crickets"):
                put(fxbus, s["start"], bank.get(name, s["end"] - s["start"]), LEVELS[name], until)
            else:
                sys.exit(f"shot {s['id']}: unknown sfx {name!r}")
        if s["kind"] in CLIP_KINDS and s["cue"]:
            # the downbeat on the first frame (its suck-in plays over the previous shot's last 0.35 s), and
            # a swell under the lines that ramps to full on the cut, then stops dead
            put(fxbus, s["start"] - HIT_PREROLL, bank.get("reenact_hit"), LEVELS["reenact_hit"], until)
            sec = s["end"] - s["start"]
            swell = snd.stereo(bank.get("reenact_swell", sec))
            lt = np.arange(len(swell)) / SR
            last = s["lines"][-1]["end"] - s["start"] if s["lines"] else 0.0
            peak = max(last + 0.05, sec - 0.05)
            env = 0.35 + 0.65 * smooth((lt - last) / (peak - last))
            put(under, s["start"], swell * env[:, None], LEVELS["reenact_swell"], until)
        if s["kind"] == "qcard":
            put(fxbus, s["start"] - 0.45, bank.get("whoosh"), LEVELS["whoosh"])
            # typing: one click per character across the first 60% of the card
            txt = s["text"]
            span = (s["end"] - s["start"]) * 0.6
            for j, ch in enumerate(txt):
                if ch != " ":
                    put(fxbus, s["start"] + 0.15 + span * j / len(txt), bank.get("typewriter", i=j), LEVELS["typewriter"] + typewriter_gain(j))
            put(fxbus, s["start"] + 0.15 + span + 0.05, bank.get("ding"), LEVELS["ding"])
        if s["kind"] == "doorbell":
            flick = s.get("flicker_at")
            if flick is not None:
                for j in range(6):
                    put(fxbus, flick + j * 0.3, bank.get("glitch"), LEVELS["glitch"])
            # the jump cut to frame B
            put(fxbus, s["start"] + doorbell_clock(s)[1], bank.get("jump"), LEVELS["jump"])
            if flick is not None:
                # riser across the flicker, landing on the call to action with a hit
                put(under, flick, bank.get("riser", CTA_DELAY), LEVELS["riser"])
                put(fxbus, flick + CTA_DELAY, bank.get("impact"), LEVELS["impact"])
                put(fxbus, flick + CTA_DELAY, bank.get("braam"), LEVELS["braam"])

    # ---- duck the score and the risers under dialogue (smoothed voice envelope)
    env = np.abs(vox)
    w = int(0.25 * SR)
    env = np.convolve(env, np.ones(w) / w, mode="same")
    duck = (1 - 0.6 * np.clip(env / db(-26), 0, 1))[:, None]
    buses = {"dialogue": snd.stereo(vox), "score": (score + under) * duck, "effects": fxbus}
    mix = sum(buses.values())
    norm = db(-1.0) / (np.max(np.abs(mix)) + 1e-9)
    mix *= norm
    if "--stems" in sys.argv:
        os.makedirs(os.path.join(BUILD, "stems"), exist_ok=True)
        for name, bus in buses.items():
            sf.write(os.path.join(BUILD, "stems", f"{name}.wav"), (bus * norm).astype(np.float32), SR, subtype="FLOAT")
    raw = os.path.join(BUILD, "mix_raw.wav")
    sf.write(raw, mix.astype(np.float32), SR, subtype="FLOAT")
    out = os.path.join(BUILD, "soundtrack.wav")
    master(raw, out)
    os.remove(raw)

    with open(os.path.join(BUILD, "timeline.json"), "w") as f:
        json.dump({"total": round(total, 3), "shots": shots, "captions": captions,
                   "credits": list(bank.credits.values())}, f, indent=1)
    print("wrote", out)


if __name__ == "__main__":
    sys.exit(main())
