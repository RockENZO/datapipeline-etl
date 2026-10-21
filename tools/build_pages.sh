#!/bin/sh
# Assemble the static GitHub Pages site into _site/: the demo plus the popup escape helper
# shared with the Flask map. usage: tools/build_pages.sh [output-dir]
set -e
cd "$(dirname "$0")/.."
OUT="${1:-_site}"
rm -rf "$OUT"
mkdir -p "$OUT"
cp -R demo/. "$OUT"/
cp web_map/static/popup_safety.js "$OUT"/popup_safety.js
touch "$OUT"/.nojekyll
echo "Built $OUT ($(find "$OUT" -type f | wc -l) files)"
