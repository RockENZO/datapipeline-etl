// UI for the static demo. The ETL and search logic lives in pipeline.js.
(function () {
    const P = window.Pipeline;
    const params = new URLSearchParams(location.search);
    const STEP_MS = Number(params.get('speed')) || 140; // pause between datasets so the stages are visible

    const map = L.map('map', { zoomControl: false, preferCanvas: true });
    L.control.zoom({ position: 'topright' }).addTo(map);
    // The sidebar floats over the left of the map on wide screens, so keep content clear of it.
    const fitPad = () => (window.innerWidth > 900 ? { paddingTopLeft: [340, 70], paddingBottomRight: [70, 80] } : { paddingTopLeft: [20, 130], paddingBottomRight: [20, 90] });
    map.fitBounds([[-33.935, 151.150], [-33.825, 151.275]], fitPad());   // the extract's inner-Sydney viewport
    map.createPane('shapes').style.zIndex = 410;
    map.createPane('points').style.zIndex = 450;
    map.createPane('live').style.zIndex = 460;
    const mapEl = document.getElementById('map');
    if (params.get('tiles') === 'off') {
        mapEl.classList.add('no-tiles');
    } else {
        let failures = 0;
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap contributors', maxZoom: 19 })
            .on('tileerror', () => { if (++failures > 3) mapEl.classList.add('no-tiles'); })
            .addTo(map);
    }

    const $ = id => document.getElementById(id);
    const els = { form: $('searchForm'), clear: $('clearBtn'), sidebar: $('sidebar'), sheetBtn: $('sheetBtn'), tableSection: $('tableSection'), input: $('searchInput'), stats: $('stats'), legend: $('legendItems'), log: $('log'), rejects: $('rejects'), rejectCount: $('rejectCount'), tableRows: $('tableRows'), tableCount: $('tableCount'), run: $('runBtn') };
    const layers = {}, counts = {}, indexes = {};
    let ready = false;

    Object.entries(P.DATASETS).forEach(([key, cfg]) => {
        layers[key] = L.layerGroup().addTo(map);
        counts[key] = 0;
    });

    // Live buses: polled straight from Spatial NSW in the browser (see livebus.js). No backend, so it only
    // works while the feed answers cross-origin requests; otherwise the pill says so and the rest still works.
    const LIVE_MS = Number(params.get('livems')) || 30000, LIVE_COLOR = '#5e5ce6';
    const busesOn = params.get('buses') !== 'off';
    const busLayer = L.layerGroup();
    if (busesOn) busLayer.addTo(map);
    const busEntries = new Set();   // { m: marker, b: last bus record, missed: polls it was absent, anim: frame id }
    const live = { state: 'connecting', count: 0, updated: null, newest: 0, timer: null, busy: false };

    function busPopup(b) {
        const rows = [['Route', b.route], ['Vehicle', b.label || b.plate], ['Speed', b.speed ? b.speed + ' km/h' : ''], ['Position time', b.ts ? new Date(b.ts * 1000).toLocaleTimeString() : '']]
            .filter(([, v]) => v).map(([k, v]) => `<dt>${escapeHtml(k)}</dt><dd>${escapeHtml(String(v))}</dd>`).join('');
        return `<div class="popup-kicker" style="color:${LIVE_COLOR}">Live bus</div><div class="popup-title">${escapeHtml(b.route ? 'Route ' + b.route : 'Bus ' + b.id)}</div><dl class="popup-info">${rows}</dl>`;
    }

    // Glide a marker to its new position so a refresh reads as movement. The popup follows via the marker's move event.
    function glide(entry, lat, lon) {
        cancelAnimationFrame(entry.anim);
        const from = entry.m.getLatLng(), t0 = performance.now(), DUR = 1200;
        if (from.lat === lat && from.lng === lon) return;
        const step = now => {
            const k = Math.min(1, (now - t0) / DUR), e = 1 - Math.pow(1 - k, 3);
            entry.m.setLatLng([from.lat + (lat - from.lat) * e, from.lng + (lon - from.lng) * e]);
            if (k < 1) entry.anim = requestAnimationFrame(step);
        };
        entry.anim = requestAnimationFrame(step);
    }

    // Each new record is matched to an existing marker by vehicle id (stable), then record id, then trip, so a selected bus keeps its popup
    // even if the feed re-labels it. A bus that misses a poll or two stays (dimmed) rather than vanishing under the user.
    function showBuses(buses) {
        const keys = [['vid', b => b.vid], ['id', b => b.id], ['trip', b => b.trip && b.route && b.trip + '|' + b.route]];
        const index = keys.map(([, f]) => new Map([...busEntries].map(e => [f(e.b), e]).filter(([k]) => k)));
        const claimed = new Set();
        for (const b of buses) {
            let entry = null;
            keys.forEach(([, f], i) => { const k = f(b); const e = !entry && k ? index[i].get(k) : null; if (e && !claimed.has(e)) entry = e; });
            if (entry) {
                claimed.add(entry); entry.missed = 0; entry.b = b;
                entry.m.setStyle({ fillOpacity: 1 });
                glide(entry, b.lat, b.lon);
                const html = busPopup(b);
                if (html !== entry.html) { entry.html = html; entry.m.setPopupContent(html); }
            } else {
                const m = L.circleMarker([b.lat, b.lon], { pane: 'live', radius: 5, weight: 1.5, color: '#fff', fillColor: LIVE_COLOR, fillOpacity: 1 }).bindPopup(busPopup(b));
                entry = { m, b, missed: 0, html: busPopup(b), anim: 0 };
                claimed.add(entry);
                busEntries.add(entry);
                busLayer.addLayer(m);
            }
        }
        for (const e of [...busEntries]) {
            if (claimed.has(e)) continue;
            if (++e.missed > 3) { cancelAnimationFrame(e.anim); busLayer.removeLayer(e.m); busEntries.delete(e); } else e.m.setStyle({ fillOpacity: .45 });
        }
    }

    async function pollBuses() {
        if (live.busy || !map.hasLayer(busLayer) || document.hidden) return;
        live.busy = true;
        const ctl = new AbortController(), timeout = setTimeout(() => ctl.abort(), 15000);
        try {
            const buses = await window.LiveBus.fetchBuses(fetch, ctl.signal);
            live.updated = new Date();
            live.count = buses.length;
            live.newest = Math.max(0, ...buses.map(b => b.ts));
            const age = live.newest ? Date.now() / 1000 - live.newest : 0;
            live.state = !buses.length ? 'empty' : age > 180 ? 'old' : 'live';
            showBuses(buses);
        } catch (e) {
            // Keep the last snapshot visible if we had one; only a first-ever failure marks the feed unavailable.
            live.state = live.updated ? 'stale' : 'offline';
        } finally { clearTimeout(timeout); live.busy = false; updateLivePill(); }
    }
    function startBuses() {
        if (!busesOn) return;
        pollBuses();
        live.timer = setInterval(pollBuses, LIVE_MS);
        document.addEventListener('visibilitychange', () => { if (!document.hidden) pollBuses(); });
    }

    const sleep = ms => new Promise(r => setTimeout(r, ms));
    function log(line) { els.log.textContent += line + '\n'; els.log.scrollTop = els.log.scrollHeight; }
    function stage(name, state, detail, pct) {
        const li = document.querySelector(`[data-stage="${name}"]`);
        li.classList.remove('active', 'done');
        if (state) li.classList.add(state);
        if (detail) li.querySelector('.detail').textContent = detail;
        if (pct != null) li.querySelector('.bar i').style.width = pct + '%';
    }

    async function runPipeline() {
        ready = false;
        els.run.disabled = true;
        els.log.textContent = '';
        els.rejects.innerHTML = '<li class="muted">Nothing yet</li>';
        els.rejectCount.textContent = '0';
        renderTable([]);
        Object.values(layers).forEach(l => l.clearLayers());
        Object.keys(counts).forEach(k => counts[k] = 0);
        ['extract', 'transform', 'load', 'query'].forEach(s => stage(s, null, null, 0));
        stage('query', null, 'Search to see results');
        drawLegend();
        els.stats.textContent = 'Running pipeline…';

        const entries = Object.entries(P.DATASETS);
        const raw = {}, transformed = {};
        let extracted = 0, valid = 0;
        const allRejected = [];

        stage('extract', 'active', 'Reading files…');
        for (const [i, [key, cfg]] of entries.entries()) {
            try {
                const res = await fetch('data/' + encodeURIComponent(cfg.file));
                if (!res.ok) throw new Error('HTTP ' + res.status);
                raw[key] = await res.json();
            } catch (e) {
                log(`✗ extract ${cfg.file}: ${e.message}`);
                stage('extract', null, 'Failed to read ' + cfg.file);
                els.stats.textContent = 'Could not read the demo data';
                els.run.disabled = false;
                return;
            }
            log(`extract    ${cfg.file}`);
            stage('extract', 'active', `${i + 1}/${entries.length} files`, ((i + 1) / entries.length) * 100);
            await sleep(STEP_MS / 2);
        }
        stage('extract', 'done', `${entries.length} files read`);

        stage('transform', 'active', 'Normalising…');
        for (const [i, [key, cfg]] of entries.entries()) {
            const out = P.transform(key, raw[key]);
            transformed[key] = out;
            extracted += out.extracted;
            valid += out.docs.length;
            allRejected.push(...out.rejected);
            log(`transform  ${key}: ${out.docs.length} ok` + (out.rejected.length ? `, ${out.rejected.length} rejected` : ''));
            stage('transform', 'active', `${valid} valid · ${allRejected.length} rejected`, ((i + 1) / entries.length) * 100);
            await sleep(STEP_MS);
        }
        stage('transform', 'done', `${valid} of ${extracted} records valid`);
        els.rejectCount.textContent = String(allRejected.length);
        els.rejects.innerHTML = allRejected.length ? '' : '<li class="muted">None</li>';
        allRejected.forEach(r => {
            const li = document.createElement('li');
            li.textContent = `${r.dataset} #${r.row}${r.name ? ' (' + r.name + ')' : ''}: ${r.reason}`;
            els.rejects.appendChild(li);
        });

        stage('load', 'active', 'Indexing…');
        for (const [i, [key]] of entries.entries()) {
            indexes[key] = P.buildIndex(key, transformed[key].docs);
            log(`load       ${key}: ${transformed[key].docs.length} docs`);
            stage('load', 'active', `${i + 1}/${entries.length} indices`, ((i + 1) / entries.length) * 100);
            await sleep(STEP_MS / 2);
        }
        stage('load', 'done', `${entries.length} indices, ${valid} documents`);

        ready = true;
        els.run.disabled = false;
        search();
    }

    function layerFor(feature, cfg) {
        const g = feature.geometry;
        if (cfg.geometryType === 'point') {
            return L.circleMarker([g.coordinates[1], g.coordinates[0]], { pane: 'points', radius: 6, weight: 2, color: '#fff', fillColor: cfg.color, fillOpacity: 1 });
        }
        const style = { pane: 'shapes', fillColor: cfg.color, color: cfg.color, weight: 1.5, opacity: .85, fillOpacity: .14 };
        if (g.type === 'Polygon') return L.polygon(g.coordinates.map(ring => ring.map(c => [c[1], c[0]])), style);
        if (g.type === 'MultiPolygon') return L.polygon(g.coordinates.map(poly => poly.map(ring => ring.map(c => [c[1], c[0]]))), style);
        return null;
    }

    function popup(feature, cfg) {
        const props = feature.properties;
        let rows = '';
        for (const [key, value] of Object.entries(props)) {
            if (key.startsWith('_') || value === null || value === undefined || value === '' || key === cfg.display) continue;
            const label = key.replace(/([a-z\d])([A-Z])/g, '$1 $2').replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());
            rows += `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(String(value).trim())}</dd>`;
        }
        return `<div class="popup-kicker" style="color:${escapeHtml(cfg.color)}">${escapeHtml(cfg.name)}</div>` +
            `<div class="popup-title">${escapeHtml(String(props._display_name).trim())}</div><dl class="popup-info">${rows}</dl>`;
    }

    // `fit` is set for searches the user asked for: they ignore the viewport and then zoom to the hits.
    function search({ fit = false } = {}) {
        if (!ready) return;
        const query = els.input.value.trim();
        const keys = Object.keys(P.DATASETS);
        const b = map.getBounds();
        const bbox = fit ? null : [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()];
        const started = performance.now();
        Object.values(layers).forEach(l => l.clearLayers());
        Object.keys(counts).forEach(k => counts[k] = 0);
        let total = 0, capped = false;
        const tableRows = [];
        for (const key of keys) {
            const cfg = P.DATASETS[key];
            const result = P.search(indexes[key], query, bbox, 1000);
            for (const doc of result.docs) {
                if (!doc.geometry) { tableRows.push({ key, cfg, doc }); continue; }
                const feature = P.toFeature(key, doc);
                const layer = layerFor(feature, cfg);
                if (layer) { layer.bindPopup(popup(feature, cfg)); layers[key].addLayer(layer); }
            }
            counts[key] = result.docs.length;
            total += result.docs.length;
            if (result.total > result.docs.length) capped = true;
        }
        renderTable(tableRows);
        if (fit) fitToHits(keys);
        els.clear.hidden = !query;
        const took = Math.max(1, Math.round(performance.now() - started));
        drawLegend();
        els.stats.textContent = `${total.toLocaleString()} ${total === 1 ? 'result' : 'results'}${query ? ` for “${query}”` : ''}${capped ? ' · 1,000 per layer max' : ''}`;
        stage('query', 'done', `${total.toLocaleString()} hits in ${took} ms${query ? ` for “${query}”` : ''}`, 100);
        log(`query      ${query ? '"' + query + '"' : '(all)'} → ${total} hits, ${took} ms`);
    }

    function fitToHits(keys) {
        const bounds = L.latLngBounds([]);
        keys.forEach(key => layers[key].eachLayer(l => bounds.extend(l.getLatLng ? l.getLatLng() : l.getBounds())));
        if (bounds.isValid()) map.fitBounds(bounds, { ...fitPad(), maxZoom: 16, animate: false });
    }

    const YEARS = Array.from({ length: 14 }, (_, i) => { const y = 2005 + i; return `F${y}_${String((y + 1) % 100).padStart(2, '0')}`; });

    function sparkline(props) {
        const values = YEARS.map(k => Number(props[k])).filter(v => Number.isFinite(v));
        if (values.length < 2) return '';
        const w = 280, h = 52, max = Math.max(...values), min = Math.min(...values), span = max - min || 1;
        const pts = values.map((v, i) => `${(i / (values.length - 1) * w).toFixed(1)},${(h - 4 - (v - min) / span * (h - 8)).toFixed(1)}`).join(' ');
        return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" role="img" aria-label="Recovery rate over time"><polyline points="${pts}" fill="none" stroke="#007aff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    }

    // Records without coordinates cannot be drawn, so search hits for them are listed instead.
    function renderTable(rows) {
        els.tableCount.textContent = String(rows.length);
        els.tableRows.innerHTML = '';
        els.tableSection.hidden = !rows.length;
        if (!rows.length) return;
        for (const { cfg, doc } of rows) {
            const p = doc.properties;
            const row = document.createElement('div');
            row.className = 'row';
            if (cfg.name === 'Waste Recovery') {
                const first = Number(p[YEARS[0]]), last = Number(p[YEARS[YEARS.length - 1]]);
                row.innerHTML = `<b>${escapeHtml(cfg.name)}</b><span>Recovery rate, 2005-06 to 2018-19: ${(first * 100).toFixed(0)}% → ${(last * 100).toFixed(0)}%</span>${sparkline(p)}`;
            } else {
                const detail = [p.Address, p.Suburb && String(p.Suburb).trim(), p.HoursWeekday].filter(Boolean).join(' · ');
                row.innerHTML = `<b>${escapeHtml(String(p[cfg.display] ?? 'Unnamed').trim())}</b><span>${escapeHtml(detail)}</span>`;
            }
            els.tableRows.appendChild(row);
        }
    }

    const LIVE_LABEL = { connecting: 'Live buses · connecting', live: 'Live buses', empty: 'Live buses · none now', old: 'Live buses · feed not updating', stale: 'Live buses · paused', offline: 'Live buses · unavailable' };
    const SHORT = { building_complex_points: 'Buildings', stairs: 'Stairs', recreation_centres: 'Recreation', information_kiosks: 'Kiosks', nsw_ambulance_stations: 'Ambulance', business_rate_category: 'Business rates', free_15_minute_parking: 'Free parking', ticket_parking_rates: 'Ticket parking' };

    // The live pill changes every poll, so it is updated in place rather than rebuilding the dock (which would drop keyboard focus).
    let livePill = null;
    function updateLivePill() {
        if (!livePill) return;
        const on = map.hasLayer(busLayer) && live.state !== 'offline';
        livePill.classList.toggle('off', !on);
        livePill.setAttribute('aria-pressed', String(on));
        livePill.dataset.live = live.state;
        let n = livePill.querySelector('.n');
        if (live.state === 'live' || live.state === 'old') {
            if (!n) { n = document.createElement('span'); n.className = 'n'; livePill.append(n); }
            n.textContent = live.count.toLocaleString();
        } else if (n) n.remove();
        livePill.firstChild.nextSibling.textContent = LIVE_LABEL[live.state];
        livePill.title = live.updated ? `Fetched ${live.updated.toLocaleTimeString()}` + (live.newest ? `; newest bus position ${new Date(live.newest * 1000).toLocaleTimeString()}` : '') : '';
    }

    function drawLegend() {
        els.legend.innerHTML = '';
        const entries = Object.entries(P.DATASETS).filter(([, cfg]) => !cfg.nonSpatial);   // table-only datasets have no layer
        const allOn = entries.every(([key]) => map.hasLayer(layers[key])) && (!busesOn || map.hasLayer(busLayer));
        const make = (label, on, dotColor, poly, n, toggle) => {
            const b = document.createElement('button');
            b.type = 'button';
            b.className = 'layer' + (on ? '' : ' off');
            b.setAttribute('aria-pressed', String(on));
            if (dotColor) {
                const dot = document.createElement('span');
                dot.className = 'dot' + (poly ? ' poly' : '');
                dot.style.background = dotColor;
                b.append(dot);
            }
            b.append(label);
            if (n != null) {
                const c = document.createElement('span');
                c.className = 'n';
                c.textContent = n.toLocaleString();
                b.append(c);
            }
            b.addEventListener('click', toggle);
            els.legend.appendChild(b);
        };
        make('All', allOn, null, false, null, () => {
            entries.forEach(([key]) => (allOn ? map.removeLayer(layers[key]) : map.addLayer(layers[key])));
            if (busesOn) { if (allOn) map.removeLayer(busLayer); else { map.addLayer(busLayer); pollBuses(); } }
            drawLegend();
        });
        entries.forEach(([key, cfg]) => {
            make(SHORT[key] || cfg.name, map.hasLayer(layers[key]), cfg.color, cfg.geometryType === 'polygon', counts[key] || 0, () => {
                if (map.hasLayer(layers[key])) map.removeLayer(layers[key]); else map.addLayer(layers[key]);
                drawLegend();
            });
        });
        if (busesOn) {
            make('', true, LIVE_COLOR, false, null, () => {
                if (map.hasLayer(busLayer)) map.removeLayer(busLayer); else { map.addLayer(busLayer); pollBuses(); }
                drawLegend();
            });
            livePill = els.legend.lastChild;
            updateLivePill();
        }
    }

    els.form.addEventListener('submit', e => { e.preventDefault(); search({ fit: true }); els.input.blur(); });
    els.input.addEventListener('input', () => { els.clear.hidden = !els.input.value; });
    els.clear.addEventListener('click', () => { els.input.value = ''; els.clear.hidden = true; search({ fit: true }); els.input.focus(); });
    els.run.addEventListener('click', runPipeline);
    els.sheetBtn.addEventListener('click', () => {
        const open = els.sidebar.classList.toggle('open');
        els.sheetBtn.setAttribute('aria-expanded', String(open));
    });
    // Re-running the search redraws every layer, which would slam shut a popup that has just auto-panned the map.
    let popupOpen = false;
    map.on('popupopen', () => { popupOpen = true; });
    map.on('popupclose', () => { popupOpen = false; });
    map.on('click', () => els.sidebar.classList.remove('open'));
    map.on('moveend', () => { if (ready && !popupOpen && els.input.value) search(); });

    // Example queries that return hits in the shipped extract.
    ['Redfern', 'hospital', 'King Street', 'library', 'ambulance'].forEach(term => {
        const b = document.createElement('button');
        b.type = 'button';
        b.textContent = term;
        b.addEventListener('click', () => { els.input.value = term; els.clear.hidden = false; search({ fit: true }); });
        $('chips').appendChild(b);
    });

    // Used by tools/demo/record.mjs to show a popup without hunting for a canvas marker.
    function openFirst(key) {
        const layer = layers[key].getLayers()[0];
        if (layer) layer.openPopup();
    }

    // Opens the popup of the live bus nearest the middle of the current view (never one off-screen: that would pan the map away).
    function openBus() {
        const view = map.getBounds(), c = view.getCenter();
        const e = [...busEntries].filter(e => view.contains(e.m.getLatLng())).sort((a, b) => c.distanceTo(a.m.getLatLng()) - c.distanceTo(b.m.getLatLng()))[0];
        if (e) e.m.openPopup();
        return !!e;
    }

    window.__demo = { search, runPipeline, map, openFirst, pollBuses, openBus };
    drawLegend();
    runPipeline();
    startBuses();
})();
