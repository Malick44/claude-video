"""Voice the script, lay it on a timeline, and mix the soundtrack.

  python pipeline/build_audio.py episodes/<episode> [--stems]

Each line comes from the first of: a recording in <episode>/recordings/<shot>_<n>.* (any
audio format), the character's TTS provider in cast.py (Kokoro by default, or ElevenLabs).
Music and sound effects come from soundtrack.py (synthesized unless pointed at stock assets).

The mix is 48 kHz stereo on three buses: dialogue; the score (theme layers whose intensity
builds toward the last shot marked "climax": True, else the last doorbell shot; ducked under
dialogue, dipped before each reveal and cut on shots marked "music": "out"); and effects
(stings, impacts, risers, whooshes, foley, ambiences), most of them placed automatically from
the shot kinds. The master
is compressed, limited and loudness-normalized to TikTok's level (-14 LUFS, -1.5 dBTP).

Outputs (in <episode>/build/):
  timeline.json  - shot/caption/sfx timings (+ stock credits) consumed by render.py / script_md.py
  soundtrack.wav - final mix (voice + score + sfx)
  stems/{dialogue,score,effects}.wav - with --stems: the three buses, pre-master, for remixing
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

import numpy as np
import soundfile as sf

import sounds as snd
import words as wordtimes
import stock
from common import CTA_DELAY, MODELS, SHOW_DIR, doorbell_clock, load_episode
from soundbank import Bank
from sounds import LEVELS, SR, typewriter_gain

AUDIO_EXTS = ("wav", "m4a", "mp3", "aiff", "aif", "flac", "ogg", "caf")
VOICE_SR = 24000   # Kokoro's native rate; voice clips are cached at this rate, resampled for the mix
LOUDNESS = -14.0   # integrated LUFS target (TikTok normalizes around here)

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
    """Your own take for a line, if you dropped one in <episode>/recordings/ (e.g. hook_1.m4a)."""
    for ext in AUDIO_EXTS:
        path = os.path.join(ep.DIR, "recordings", f"{rec}.{ext}")
        if os.path.exists(path):
            return path
    return None


def voice_line(who, say, rec):
    if who not in ep.CAST:
        sys.exit(f"{who} is not in the cast - add them to cast.py (or this episode's CAST)")
    cast = ep.CAST[who]
    take = recording(rec)
    if take:
        st = os.stat(take)
        key = hashlib.sha1(json.dumps([cast, take, st.st_size, st.st_mtime]).encode()).hexdigest()[:12]
    else:
        key = hashlib.sha1(json.dumps([cast, say]).encode()).hexdigest()[:12]
    raw = os.path.join(CACHE, f"{who}_{key}_raw.wav")
    out = os.path.join(CACHE, f"{who}_{key}.wav")
    if not os.path.exists(out):
        provider = cast.get("provider", "kokoro")
        apply_fx = True
        if take:
            samples = stock.decode_audio(take, VOICE_SR)
            apply_fx = cast.get("fx_on_recordings", False)
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
    """Word -> phonemes in the speaker's accent, for word timing (any provider's audio).
    One function per accent, so words.weight's cache (keyed by it) is shared across lines."""
    voice = ep.CAST[who].get("voice", "a")
    lang = "en-us" if voice[0] == "a" else "en-gb"
    if lang not in _phonemizers:
        _phonemizers[lang] = lambda w: kokoro().tokenizer.phonemize(w, lang)
    return _phonemizers[lang]


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
            spoken = [[w, round(t + a, 3), round(t + b, 3)] for w, a, b in wordtimes.caption_times(y, SR, say, text, phonemizer(who))]
            captions.append({"start": round(t, 3), "end": round(t + dur, 3), "who": who, "text": text, "shot": shot["id"],
                             "rec": rec, "recorded": bool(recording(rec)), "words": spoken})
            lines.append({"start": round(t, 3), "end": round(t + dur, 3), "text": text})
            t += dur
        t += shot.get("post", 0.0)
        t = max(t, start + shot.get("min", 0.0))
        shots.append({k: v for k, v in shot.items() if k != "items"} | {"start": round(start, 3), "end": round(t, 3), "lines": lines})
        print(f"{shot['id']:10s} {start:6.2f} -> {t:6.2f}  ({t - start:4.2f}s)")
    total = t
    print(f"TOTAL {total:.2f}s")

    n = int((total + 0.5) * SR)
    vox = np.zeros(n)
    for s, y in voice:
        i = int(s * SR)
        vox[i: i + len(y)] += y[: n - i]
    score = np.zeros((n, 2))     # theme: ducked, shaped by intensity, gated
    under = np.zeros((n, 2))     # risers + soft swells: ducked under dialogue only
    fxbus = np.zeros((n, 2))     # stings, hits, foley, ambiences

    def put(buf, at, y, gain_db):
        i = int(round(at * SR))
        if i < 0:
            y, i = y[-i:], 0
        if i >= n or not len(y):
            return
        seg = snd.stereo(y)[: n - i]
        buf[i: i + len(seg)] += seg * db(gain_db)

    bank = Bank(ep.SOUNDS, [ep.DIR, SHOW_DIR])

    # ---- doorbell timings (used by both the mix and the renderer)
    for s in shots:
        if s["kind"] == "doorbell":
            s["flicker_at"] = round(s["lines"][-1]["end"] + 0.15, 3)

    # ---- score: theme from the title card (first "sting") to the end card
    bed_start = next((s["start"] for s in shots if "sting" in s.get("sfx", [])), 0.0)
    bed_end = next((s["start"] for s in shots if s["kind"] == "end"), total) + 0.4
    # the score builds to the last shot marked "climax": True, else to the last doorbell shot
    marked = [s["start"] for s in shots if s.get("climax")]
    doorbells = [s["start"] for s in shots if s["kind"] == "doorbell"]
    climax = (marked or doorbells or [bed_end])[-1]
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

    for s in shots:
        if s.get("music") == "out":
            dip(s["start"], s["end"], 0.0)
        if s["kind"] == "doorbell":  # hush under the flicker so the reveal hit lands
            dip(s["flicker_at"], s["flicker_at"] + CTA_DELAY, 0.3, 0.3, 0.6)
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
        for name in s.get("sfx", []):
            if name == "sting":
                # a riser sweeps into the title, then braam + impact + piano cluster
                rs = min(2.0, s["start"])
                put(under, s["start"] - rs, bank.get("riser", rs), LEVELS["riser"])
                put(fxbus, s["start"], bank.get("sting"), LEVELS["sting"])
            elif name == "sting_end":
                put(fxbus, s["start"], bank.get("sting_end"), LEVELS["sting_end"])
            elif name == "sting_soft":
                # a low swell under the shot's last line (the question the episode asks)
                put(under, s["lines"][-1]["start"] - 0.1, bank.get(name), LEVELS[name])
            elif name == "shutter":
                put(fxbus, s["start"], bank.get("shutter"), LEVELS["shutter"])
                put(fxbus, s["start"], bank.get("impact"), LEVELS["impact"] - 4)
            elif name in ("wind", "chimes", "crickets"):
                put(fxbus, s["start"], bank.get(name, s["end"] - s["start"]), LEVELS[name])
            else:
                sys.exit(f"shot {s['id']}: unknown sfx {name!r}")
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
            flick = s["flicker_at"]
            for j in range(6):
                put(fxbus, flick + j * 0.3, bank.get("glitch"), LEVELS["glitch"])
            # the jump cut to frame B
            put(fxbus, s["start"] + doorbell_clock(s)[1], bank.get("jump"), LEVELS["jump"])
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
