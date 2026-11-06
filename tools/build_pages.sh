#!/bin/sh
# Assemble the static GitHub Pages site into _site/: the demo plus the popup escape helper
# shared with the Flask map. usage: tools/build_pages.sh [output-dir]
set -e
cd "$(dirname "$0")/.."
OUT="${1:-_site}"
# Never remove a caller-supplied path. mkdir also rejects an existing symlink
# and prevents simultaneous builds from both claiming the same destination.
mkdir -p -- "$(dirname -- "$OUT")"
if ! mkdir -- "$OUT"; then
    printf 'Cannot create Pages output at %s. Choose a new directory.\n' "$OUT" >&2
    exit 1
fi
cp -R demo/. "$OUT"/
cp web_map/static/popup_safety.js "$OUT"/popup_safety.js
touch "$OUT"/.nojekyll
echo "Built $OUT ($(find "$OUT" -type f | wc -l) files)"
