"""Speak a line with a Kokoro preset voice. Installed as `kokoro` by tools/install-kokoro.sh.

  kokoro "I didn't see nothing." garrison.wav am_fenrir 1.0
  kokoro --voices
"""
import os
import sys

import soundfile as sf
from kokoro_onnx import Kokoro

args = sys.argv[1:]
if not args or (len(args) < 2 and args[0] != "--voices"):
    sys.exit('usage: kokoro "text" out.wav [voice] [speed]   (list voices: kokoro --voices)')
models = os.path.expanduser("~/.kokoro/models")
k = Kokoro(os.path.join(models, "kokoro.onnx"), os.path.join(models, "voices.bin"))
if args[0] == "--voices":
    print(" ".join(sorted(k.get_voices())))
    sys.exit()
text, out = args[0], args[1]
voice = args[2] if len(args) > 2 else "af_heart"
speed = float(args[3]) if len(args) > 3 else 1.0
# b* voices are British English; everything else is spoken as American English
samples, sr = k.create(text, voice=voice, speed=speed, lang="en-gb" if voice.startswith("b") else "en-us")
sf.write(out, samples, sr)
print("wrote", out)
