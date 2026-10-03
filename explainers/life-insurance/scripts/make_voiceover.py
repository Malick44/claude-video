#!/usr/bin/env python3
"""Synthesize the narration with Kokoro -> public/vo.mp3 (+ src/vo.json duck cues).

Cues are anchored to scene-relative frames from src/timeline.json, so retiming a scene
only needs a re-run. Each line is auto-sped (max 1.15x) to fit before the next cue.

  KOKORO_MODELS=/path/to/dir python3 scripts/make_voiceover.py
The dir must hold kokoro.onnx + voices.bin (see shows/nobody-moves/tools/common.sh for the pinned
files). Needs kokoro-onnx==0.6.1, espeakng-loader==0.2.4, soundfile, numpy and ffmpeg."""
import json, os, subprocess, wave
from pathlib import Path
import numpy as np
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parent.parent
tl = json.loads((ROOT / "src/timeline.json").read_text())
FPS, TR = tl["fps"], tl["transition"]
VOICE = "af_heart"
SR = 24000

starts, acc = {}, 0
for s in tl["scenes"]:
    starts[s["id"]] = acc
    acc += s["frames"] - TR
TOTAL = acc + TR  # last scene keeps its full length

# (scene, local_frame, text)
LINES = [
    ("hook", 105, "You're the load-bearing wall."),
    ("hook", 185, "Life insurance is the backup beam."),
    ("squeeze", 25, "If you're a millennial homeowner, you're probably in the sandwich generation. Aging parents on one side. Young kids on the other."),
    ("squeeze", 255, "That's about forty-eight hundred dollars a month, riding on one income."),
    ("paycheck", 20, "Now imagine that paycheck stops."),
    ("paycheck", 150, "The mortgage doesn't pause. Neither does daycare."),
    ("paycheck", 255, "Savings buy months. Your family needs decades."),
    ("dime", 20, "How much coverage? Start with DIME."),
    ("dime", 72, "Debt: car loans, credit cards, student loans."),
    ("dime", 162, "Income: replace your salary for ten years."),
    ("dime", 252, "Mortgage: pay off what's left."),
    ("dime", 342, "Education: tuition for both kids."),
    ("dime", 432, "That's about one point three million. Fifteen times your income."),
    ("cost", 70, "And here's the surprise. It's cheap."),
    ("cost", 150, "A healthy thirty-two-year-old can get a million dollars of cover for about fifty dollars a month."),
    ("cost", 330, "Wait until fifty, and the same cover costs five times more."),
    ("match", 35, "Your mortgage, your kids, your parents' care years. All at once."),
    ("match", 170, "So buy level term that outlasts every obligation."),
    ("match", 285, "For most families, term is the lowest-cost protection."),
    ("myths", 12, "Four myths, busted."),
    ("myths", 66, "Group coverage is small, and it leaves when you do."),
    ("myths", 161, "Young and healthy is when it's cheapest."),
    ("myths", 256, "Replacing a full-time parent costs tens of thousands yearly."),
    ("myths", 350, "Death benefits are generally income-tax-free."),
    ("steps", 50, "Here's how: one, size it with DIME."),
    ("steps", 120, "Two: compare term quotes."),
    ("steps", 190, "Three: add the right riders."),
    ("steps", 260, "Four: name beneficiaries, and a guardian for your kids."),
    ("close", 25, "Life insurance isn't really for you. It's for them."),
    ("close", 125, "The best time was before the mortgage."),
    ("close", 208, "The next best time? This week."),
]

models = Path(os.environ.get("KOKORO_MODELS", Path.home() / ".kokoro/models"))
k = Kokoro(str(models / "kokoro.onnx"), str(models / "voices.bin"))

def say(text, speed):
    x, sr = k.create(text, voice=VOICE, speed=speed, lang="en-us")
    assert sr == SR
    # trim leading/trailing silence
    idx = np.where(np.abs(x) > 0.01)[0]
    return x[idx[0] : idx[-1] + 1] if len(idx) else x

abs_starts = [starts[s] + f for s, f, _ in LINES]
out = np.zeros(int((TOTAL / FPS + 1) * SR), dtype=np.float32)
cues, overflow = [], []
for i, ((scene, f, text), a) in enumerate(zip(LINES, abs_starts)):
    nxt = abs_starts[i + 1] if i + 1 < len(LINES) else TOTAL
    slot = (nxt - a) / FPS - 0.12
    x = say(text, 1.0)
    if len(x) / SR > slot:
        sp = min(1.15, 1.0 * (len(x) / SR) / slot)
        x = say(text, sp)
    dur = len(x) / SR
    if dur > slot + 0.05:
        overflow.append((scene, f, round(dur - slot, 2)))
    i0 = int(a / FPS * SR)
    out[i0 : i0 + len(x)] += x[: len(out) - i0]
    cues.append({"start": a, "end": a + int(dur * FPS) + 1})
if overflow:
    print("overflow (scene, frame, seconds):", overflow)

wav = ROOT / "public/vo.wav"
pcm = (np.clip(out, -1, 1) * 32767).astype("<i2")
with wave.open(str(wav), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-af",
                "highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=7", "-ar", "44100", "-b:a", "160k",
                str(ROOT / "public/vo.mp3")], check=True)
wav.unlink()
(ROOT / "src/vo.json").write_text(json.dumps(cues))
print(f"vo.mp3: {len(cues)} lines, ends at {cues[-1]['end'] / FPS:.1f}s of {TOTAL / FPS:.1f}s")
