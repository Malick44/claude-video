#!/usr/bin/env bash
# Install Kokoro TTS for your user account, usable outside this project:
#   ~/.kokoro/            its own Python environment + the model files
#   ~/.local/bin/kokoro   kokoro "text" out.wav [voice] [speed]   (kokoro --voices lists all 54)
# Same pinned versions and model files as the show, so the voices match cast.py.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/common.sh"

PY=$(find_python)
K="$HOME/.kokoro"
"$PY" -m venv "$K"
"$K/bin/pip" install -q --upgrade pip
"$K/bin/pip" install -q kokoro-onnx==0.6.1 espeakng-loader==0.2.4 soundfile
check_espeak_path "$K/bin/python"
fetch_models "$K/models" "$K/bin/python"
cp "$HERE/kokoro_say.py" "$K/say.py"

mkdir -p "$HOME/.local/bin"
printf '#!/bin/sh\nexec "$HOME/.kokoro/bin/python" "$HOME/.kokoro/say.py" "$@"\n' > "$HOME/.local/bin/kokoro"
chmod +x "$HOME/.local/bin/kokoro"

echo "installed: ~/.local/bin/kokoro (Python: $("$K/bin/python" -V))"
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo "~/.local/bin is not on your PATH yet. Run:"
     echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc && source ~/.zshrc" ;;
esac
echo 'try: kokoro "Next question." lorraine.wav af_bella && afplay lorraine.wav'
