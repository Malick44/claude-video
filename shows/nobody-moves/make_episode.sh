#!/usr/bin/env bash
# Build one episode end to end:
#   ./make_episode.sh episodes/ep01_three_feet
# -> <episode>/build/<episode>.mp4 (master), <episode>_tiktok.mp4 (<29 MB), <episode>/SCRIPT.md
#
# An episode whose reenactments carry a "blender" dict gets a Blender pass between two audio builds:
# build_audio (word times) -> blender_reenact --build (files each clip, or reports it up to date) ->
# build_audio (records the clips) -> render. Episodes without one build exactly as before.
#   NM_RX_QUALITY=draft|final  the clips' quality (default draft; final under NM_FINAL=1)
#   NM_FINAL=1                 the release build: no Blender, a missing model or a render over the time
#                              budget is an error, and deliver.py refuses a proxy or draft clip
#   NM_BLENDER=/path           a blender binary or a python with bpy; NM_BLENDER_FLAGS: extra flags
set -euo pipefail
EP=$(cd "${1:?usage: ./make_episode.sh episodes/<episode>}" && pwd)
cd "$(dirname "$0")"
PY=.venv/bin/python
[ -x "$PY" ] || { echo "run ./setup.sh first" >&2; exit 1; }

"$PY" pipeline/build_audio.py "$EP"
DELIVER=()
if [ "$("$PY" pipeline/blender_reenact.py "$EP" --has-shots)" = yes ]; then
  FINAL=${NM_FINAL:-}
  QUALITY=${NM_RX_QUALITY:-$([ "$FINAL" = 1 ] && echo final || echo draft)}
  FLAGS=(--build --quality "$QUALITY")
  [ "$FINAL" = 1 ] && FLAGS+=(--require-models)
  rc=0
  # shellcheck disable=SC2086  # NM_BLENDER_FLAGS is a list of flags
  "$PY" pipeline/blender_reenact.py "$EP" "${FLAGS[@]}" ${NM_BLENDER_FLAGS:-} || rc=$?
  if [ "$rc" = 2 ] || [ "$rc" = 3 ]; then     # 2: no Blender (or engine, device, ffmpeg); 3: over the time budget
    [ "$FINAL" = 1 ] && { echo "NM_FINAL=1: blender_reenact.py exited $rc" >&2; exit "$rc"; }
    echo "WARN blender_reenact.py exited $rc: the reenactments play their fallback stills (see above)" >&2
  elif [ "$rc" != 0 ]; then
    exit "$rc"
  fi
  "$PY" pipeline/build_audio.py "$EP"          # records each filed clip (its voices come from the cache)
  [ "$FINAL" = 1 ] || DELIVER=(--allow-draft)  # a working build delivers a draft clip, with a warning
fi
"$PY" pipeline/script_md.py "$EP"
"$PY" pipeline/render.py "$EP"
"$PY" pipeline/deliver.py "$EP" ${DELIVER[@]+"${DELIVER[@]}"}   # (bash 3.2: an empty array under set -u)
