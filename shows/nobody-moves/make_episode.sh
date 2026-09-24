#!/usr/bin/env bash
# Build one episode end to end:
#   ./make_episode.sh episodes/ep01_three_feet
# -> <episode>/build/<episode>.mp4 (master), <episode>_tiktok.mp4 (<29 MB), <episode>/SCRIPT.md
set -euo pipefail
EP=$(cd "${1:?usage: ./make_episode.sh episodes/<episode>}" && pwd)
cd "$(dirname "$0")"
PY=.venv/bin/python
[ -x "$PY" ] || { echo "run ./setup.sh first" >&2; exit 1; }

"$PY" pipeline/build_audio.py "$EP"
"$PY" pipeline/script_md.py "$EP"
"$PY" pipeline/render.py "$EP"
"$PY" pipeline/deliver.py "$EP"
