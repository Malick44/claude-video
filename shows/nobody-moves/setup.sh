#!/usr/bin/env bash
# One-time setup: Python venv + Kokoro TTS model + fonts (all fetched from PyPI / GitHub).
#   ./setup.sh --blender   only adds .venv-bpy, Blender as a Python module (bpy 5.0.1, Python 3.11), for the
#                          Blender reenactments (docs/BLENDER_REENACTMENTS.md). The Blender 5.0 app works too:
#                          export NM_BLENDER=/path/to/blender instead.
set -euo pipefail
cd "$(dirname "$0")"
. tools/common.sh

if [ "${1:-}" = --blender ]; then
  PY311=$(command -v python3.11 || true)
  [ -n "$PY311" ] || { echo "bpy 5.0.1 is on PyPI for Python 3.11 only: install python3.11 (brew install python@3.11," \
                            "apt install python3.11), or the Blender 5.0 app and export NM_BLENDER=/path/to/blender" >&2; exit 1; }
  "$PY311" -m venv .venv-bpy
  .venv-bpy/bin/pip install -q --upgrade pip
  .venv-bpy/bin/pip install -q bpy==5.0.1
  .venv-bpy/bin/python -c "import bpy; print('bpy', bpy.app.version_string)"
  echo "blender setup done - now: .venv/bin/python pipeline/blender_reenact.py --selftest"
  exit 0
fi

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
