// Records docs/demo.gif (and docs/demo.mp4) of the static demo with Playwright screenshots + ffmpeg.
//   npm i playwright && npx playwright install chromium   (once)
//   node tools/demo/record.mjs
// Env: TILES=off          skip OpenStreetMap tiles (use when the network blocks them)
//      LEAFLET_DIR=path   serve Leaflet from a local dist/ folder instead of unpkg
//      CHROMIUM=path      use an existing Chromium binary
//      BUSES=off          leave the live bus layer out of the recording (default: included, needs network)
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const site = path.join(root, '_site');
const work = fs.mkdtempSync(path.join(process.env.TMPDIR || '/tmp', 'demo-rec-'));
execFileSync(path.join(root, 'tools/build_pages.sh'), [site], { stdio: 'inherit' });

const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.geojson': 'application/json' };
const server = http.createServer((req, res) => {
    let p = decodeURIComponent(req.url.split('?')[0]);
    if (p === '/') p = '/index.html';
    const file = path.join(site, p);
    if (!file.startsWith(site) || !fs.existsSync(file)) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'content-type': types[path.extname(file)] || 'application/octet-stream' });
    res.end(fs.readFileSync(file));
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {});
const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
const page = await context.newPage();
if (process.env.LEAFLET_DIR) {
    await page.route('https://unpkg.com/leaflet@1.9.4/dist/*', route => {
        const name = route.request().url().split('/').pop();
        route.fulfill({ path: path.join(process.env.LEAFLET_DIR, name), contentType: name.endsWith('.css') ? 'text/css' : 'text/javascript' });
    });
}
// Screenshots are taken in a loop rather than with Playwright's video recorder, which needs its own ffmpeg build.
let capturing = true, frames = 0;
const started = Date.now();
const capture = (async () => {
    while (capturing) {
        // The first shots can run before the page has navigated, and newer Playwright/Node combinations reject those: skip the frame.
        try { await page.screenshot({ path: path.join(work, String(frames).padStart(5, '0') + '.jpg'), type: 'jpeg', quality: 80 }); frames++; }
        catch { await new Promise(r => setTimeout(r, 100)); }
    }
})();
// BUSES=off keeps the live feed out (offline machines, repeatable shots); otherwise the recording includes it and needs network.
const buses = process.env.BUSES !== 'off';
const q = '?' + [process.env.TILES === 'off' && 'tiles=off', buses ? 'livems=5000' : 'buses=off'].filter(Boolean).join('&');
await page.goto(`http://localhost:${port}/${q}`);
await page.waitForFunction(() => document.querySelector('[data-stage="query"]').classList.contains('done'), null, { timeout: 30000 });
if (process.env.TILES !== 'off') await page.waitForSelector('.leaflet-tile-loaded', { timeout: 30000 });  // fail loudly instead of recording a blank map
await page.waitForTimeout(1500);

const type = async text => { await page.fill('#searchInput', ''); await page.type('#searchInput', text, { delay: 90 }); await page.press('#searchInput', 'Enter'); };
const pill = name => page.getByRole('button', { name: new RegExp('^' + name) });
await page.click('#chips button:nth-of-type(1)');   // Redfern
await page.waitForTimeout(1800);
await page.evaluate(() => window.__demo.openFirst('stairs'));
await page.waitForTimeout(2400);
await type('King Street');
await page.waitForTimeout(2000);
await type('hospital');
await page.waitForTimeout(1800);
await page.click('#clearBtn');
await pill('All').click();                           // hide every layer...
await pill('Ambulance').click();                     // ...then show just one
await page.waitForTimeout(1800);
await pill('All').click();
await type('library');                               // libraries have no coordinates: listed under "Not on the map"
await page.waitForTimeout(2400);
await page.click('#clearBtn');
await page.waitForTimeout(800);
if (buses) {                                   // live buses: open one and let a refresh pass; the popup must stay open
    await page.waitForSelector('.layer[data-live="live"], .layer[data-live="old"]', { timeout: 30000 });   // fail loudly if the feed is unreachable
    await page.waitForTimeout(1200);
    if (!(await page.evaluate(() => window.__demo.openBus()))) throw new Error('no live bus in view to open');
    await page.waitForTimeout(7000);
    if (!(await page.evaluate(() => !!document.querySelector('.leaflet-popup')))) throw new Error('live bus popup closed on refresh');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(600);
}
await page.click('#runBtn');                   // replay the pipeline
await page.waitForFunction(() => document.querySelector('[data-stage="query"]').classList.contains('done'), null, { timeout: 30000 });
await page.waitForTimeout(1500);

capturing = false;
await capture;
const fps = (frames / ((Date.now() - started) / 1000)).toFixed(2);
await context.close();
await browser.close();
server.close();

fs.mkdirSync(path.join(root, 'docs'), { recursive: true });
execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', fps, '-i', path.join(work, '%05d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '26', '-vf', 'scale=1024:-2', '-movflags', '+faststart', path.join(root, 'docs/demo.mp4')]);
execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', fps, '-i', path.join(work, '%05d.jpg'), '-vf', 'fps=10,scale=800:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle', '-loop', '0', path.join(root, 'docs/demo.gif')]);
fs.rmSync(work, { recursive: true, force: true });
console.log('Wrote docs/demo.gif and docs/demo.mp4');
