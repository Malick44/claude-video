"""Export the show's sounds as WAV files (for CapCut, Confessionals, trailers...).

  python pipeline/sound_kit.py            # -> sound_kit/*.wav (48 kHz stereo, peaks at -1 dBFS)

Each sound comes from the same place the episodes use (soundtrack.py): synthesized by
pipeline/sounds.py, which is deterministic, or the pinned stock asset it points at.
"""
import os

import numpy as np
import soundfile as sf

import sounds as snd
from common import SHOW_DIR, load_sound_sources
from soundbank import Bank

bank = Bank(load_sound_sources(), [SHOW_DIR])

OUT = os.path.join(SHOW_DIR, "sound_kit")


def typing_line(text="Where were you on the night of June 13th?", span=1.44):
    """A typed interviewer question exactly as the question cards play it: keys, then the bell."""
    y = np.zeros((int((span + 1.6) * snd.SR), 2))
    for j, ch in enumerate(text):
        if ch != " ":
            key = bank.get("typewriter", i=j) * 10 ** ((snd.LEVELS["typewriter"] + snd.typewriter_gain(j)) / 20)
            i = int((0.15 + span * j / len(text)) * snd.SR)
            y[i: i + len(key)] += snd.stereo(key)
    ding = bank.get("ding") * 10 ** (snd.LEVELS["ding"] / 20)
    i = int((0.15 + span + 0.05) * snd.SR)
    y[i: i + len(ding)] += snd.stereo(ding)[: len(y) - i]
    return y


def theme(seconds=60.0):
    bed = snd.stereo(bank.get("theme", seconds))
    fade = np.ones(len(bed))
    k = int(3.0 * snd.SR)
    fade[int(seconds * snd.SR) - k: int(seconds * snd.SR)] = np.linspace(1, 0, k)
    fade[int(seconds * snd.SR):] = 0
    return (bed * fade[:, None])[: int(seconds * snd.SR)]


KIT = {
    "theme_60s": lambda: theme(60.0),
    "sting_title": lambda: bank.get("sting"),
    "sting_end": lambda: bank.get("sting_end"),
    "sting_soft": lambda: bank.get("sting_soft"),
    "riser_2s": lambda: bank.get("riser", 2.0),
    "impact": lambda: bank.get("impact"),
    "braam": lambda: bank.get("braam"),
    "whoosh": lambda: bank.get("whoosh"),
    "camera_shutter": lambda: bank.get("shutter"),
    "typewriter_key": lambda: bank.get("typewriter"),
    "typewriter_question": typing_line,
    "typewriter_bell": lambda: bank.get("ding"),
    "wind_20s": lambda: bank.get("wind", 20.0),
    "wind_chimes_20s": lambda: bank.get("chimes", 20.0),
    "night_crickets_20s": lambda: bank.get("crickets", 20.0),
    "doorbell_glitch": lambda: bank.get("glitch"),
    "doorbell_jump": lambda: bank.get("jump"),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, make in KIT.items():
        y = make()
        y = y / (np.max(np.abs(y)) + 1e-9) * 10 ** (-1 / 20)
        path = os.path.join(OUT, f"{name}.wav")
        sf.write(path, y, snd.SR, subtype="PCM_16")
        print(f"{name:22s} {len(y) / snd.SR:5.1f}s")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
