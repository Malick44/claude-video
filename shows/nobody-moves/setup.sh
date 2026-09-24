#!/usr/bin/env bash
# One-time setup: Python venv + Kokoro TTS model + fonts (all fetched from PyPI / GitHub).
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

mkdir -p assets/models assets/fonts
dl() { [ -s "$2" ] || { echo "downloading $(basename "$2")"; curl -fsSL -o "$2" "$1"; }; }

K=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
dl "$K/kokoro-v1.0.int8.onnx" assets/models/kokoro.onnx
dl "$K/voices-v1.0.bin" assets/models/voices.bin

G=https://raw.githubusercontent.com/google/fonts/main
dl "$G/ofl/oswald/Oswald%5Bwght%5D.ttf" assets/fonts/Oswald.ttf
dl "$G/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf" assets/fonts/Inter.ttf
dl "$G/ofl/ibmplexmono/IBMPlexMono-Medium.ttf" assets/fonts/PlexMono.ttf
dl "$G/apache/permanentmarker/PermanentMarker-Regular.ttf" assets/fonts/PermanentMarker.ttf
dl "$G/apache/specialelite/SpecialElite-Regular.ttf" assets/fonts/SpecialElite.ttf

echo "setup done - now: ./make_episode.sh episodes/ep01_three_feet"
