#!/usr/bin/env bash
# Scaffold a new AI TikTok series folder from the NOBODY MOVES pipeline. The script works from any
# directory (it finds the repo itself); the paths below are from the repo root:
#
#   bash .agents/skills/ai-tiktok-series/scripts/new_show.sh <slug> [shows_dir]
#   bash .agents/skills/ai-tiktok-series/scripts/new_show.sh --check shows/<slug>   # re-list leftovers
#
# Copies the pipeline from shows/nobody-moves into <shows_dir>/<slug> (default: the repo's
# shows/): the setup and build scripts, tools/, pipeline/*.py, plus cast.py and soundtrack.py
# as starting points. It writes SERIES.md from the skill's bible template and creates empty
# episodes/ and stills/ folders. It never copies .venv/, assets/, build/, stock/, stills or
# episodes, and it never changes shows/nobody-moves.
#
# Last, it lists the NOBODY MOVES-specific lines a grep can find. The list is a starting
# point: references/new-show-checklist.md covers the rest.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
SKILL=$(dirname "$HERE")

# One pattern for the first listing and for --check, so the two never drift apart.
PATTERN='NOBODY|[Nn]obody[ _-]?[Mm]oves|nm-selftest|[Ff]lamingo|DEB[?"]|Deb[ .,?]|[Gg]arrison|GARRISON|[Ll]orraine|LORRAINE|Birchwood|MR\. BASIN|"CHIME"|"RAY"|INTERVIEWER|FRONT DOOR|06/14|June 13|Follow the case|Reenactments|ep01_three_feet|[Dd]oorbell|"evidence"|"board"|THEME_NOTES =|THEME_TURN =|PAD_CHORDS =|pi \* 55 \*|82\.4|\(81, 88, 93\)|root=33|\(33, 1\.0\)|1318\.5|No\\\.\)|03:11'

leftovers() {
  echo "NOBODY MOVES specifics a grep can find (a starting point, not the whole job):"
  ( cd "$1" && grep -rnE "$PATTERN" --include='*.py' --include='*.sh' . | sed 's|^\./|  |' ) || true
  echo
  echo "Lines for kinds you keep (doorbell, evidence, board) can stay. The grep can't see what a"
  echo "line does: work through $SKILL/references/new-show-checklist.md, section 3"
  echo "(build_audio.py's climax and hush, sound_kit.py, the pitches in sounds.py, the self-test fixture)."
}

if [ "${1:-}" = "--check" ]; then
  [ -d "${2:-}/pipeline" ] || { echo "usage: new_show.sh --check <show_dir>   (e.g. shows/late-humans)" >&2; exit 1; }
  leftovers "$2"
  exit 0
fi

SLUG=${1:-}
case "$SLUG" in
  "" | -* | *[!a-z0-9-]*)
    echo "usage: new_show.sh <slug> [shows_dir]   (slug: lowercase letters, digits and dashes)" >&2
    exit 1 ;;
esac

ROOT=$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null || (cd "$SKILL/../../.." && pwd))
SRC="$ROOT/shows/nobody-moves"
DEST="${2:-$ROOT/shows}/$SLUG"

[ -d "$SRC/pipeline" ] || { echo "template show not found: $SRC" >&2; exit 1; }
[ -e "$DEST" ] && { echo "already exists: $DEST (pick another slug or remove it)" >&2; exit 1; }

mkdir -p "$DEST/pipeline" "$DEST/tools" "$DEST/episodes" "$DEST/stills"
for f in setup.sh make_episode.sh requirements.txt .gitignore .env.example cast.py soundtrack.py; do
  cp "$SRC/$f" "$DEST/$f"
done
cp "$SRC/tools/common.sh" "$SRC/tools/install-kokoro.sh" "$SRC/tools/kokoro_say.py" "$DEST/tools/"
cp "$SRC"/pipeline/*.py "$DEST/pipeline/"
cp "$SKILL/references/series-bible-template.md" "$DEST/SERIES.md"

echo "created $DEST"
echo

leftovers "$DEST"
echo
echo "next (see the skill's stages 2-5):"
echo "  1. cd $DEST   # the commands below run from the show folder"
echo "  2. cp -r $SRC/assets .   # optional: same pinned model and font files, saves the download"
echo "  3. ./setup.sh && .venv/bin/python pipeline/selftest.py"
echo "  4. fill in SERIES.md, rewrite cast.py, then work through references/new-show-checklist.md"
echo "  5. write episodes/ep01_<episode_title>/episode.py (e.g. ep01_three_feet) from"
echo "     $SKILL/references/pilot-template.py"
