#!/usr/bin/env bash
# One-time setup: Python venv + Kokoro TTS model + fonts (all fetched from PyPI / GitHub).
set -euo pipefail
cd "$(dirname "$0")"
. tools/common.sh

PY=$(find_python)
"$PY" -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
check_espeak_path .venv/bin/python

# The cast (cast.py) only sounds the same across episodes with these exact model files.
fetch_models assets/models .venv/bin/python

mkdir -p assets/fonts
G=https://raw.githubusercontent.com/google/fonts/main
download "$G/ofl/oswald/Oswald%5Bwght%5D.ttf" assets/fonts/Oswald.ttf
download "$G/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf" assets/fonts/Inter.ttf
download "$G/ofl/ibmplexmono/IBMPlexMono-Medium.ttf" assets/fonts/PlexMono.ttf
download "$G/apache/permanentmarker/PermanentMarker-Regular.ttf" assets/fonts/PermanentMarker.ttf
download "$G/apache/specialelite/SpecialElite-Regular.ttf" assets/fonts/SpecialElite.ttf

echo "setup done ($(.venv/bin/python -V)) - now: ./make_episode.sh episodes/ep01_three_feet"
