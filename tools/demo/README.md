# Demo recorder

`record.mjs` drives the static Pages demo in headless Chromium and writes `docs/demo.gif` and `docs/demo.mp4`.
Needs Node 18+, ffmpeg and Playwright (`npm i playwright && npx playwright install chromium`). See the header of
the script for the `TILES`, `LEAFLET_DIR` and `CHROMIUM` environment options.
