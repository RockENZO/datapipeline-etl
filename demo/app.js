// UI for the static demo. The ETL and search logic lives in pipeline.js.
(function () {
    const P = window.Pipeline;
    const params = new URLSearchParams(location.search);
    const STEP_MS = Number(params.get('speed')) || 140; // pause between datasets so the stages are visible

    const map = L.map('map', { zoomControl: true, preferCanvas: true });
    map.fitBounds([[-33.935, 151.150], [-33.825, 151.275]]);   // the extract's inner-Sydney viewport
    map.createPane('shapes').style.zIndex = 410;
    map.createPane('points').style.zIndex = 450;
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
    const els = { selector: $('datasetSelector'), input: $('searchInput'), stats: $('stats'), legend: $('legendItems'), log: $('log'), rejects: $('rejects'), rejectCount: $('rejectCount'), tableRows: $('tableRows'), tableCount: $('tableCount'), run: $('runBtn') };
    const layers = {}, counts = {}, indexes = {};
    let ready = false;

    Object.entries(P.DATASETS).forEach(([key, cfg]) => {
        layers[key] = L.layerGroup().addTo(map);
        counts[key] = 0;
        els.selector.add(new Option(`${cfg.icon} ${cfg.name}`, key));
    });
    els.selector.insertBefore(new Option('All datasets', ''), els.selector.firstChild);
    els.selector.value = '';

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
        els.rejects.innerHTML = '';
        els.rejectCount.textContent = '0';
        Object.values(layers).forEach(l => l.clearLayers());
        Object.keys(counts).forEach(k => counts[k] = 0);
        ['extract', 'transform', 'load', 'query'].forEach(s => stage(s, null, null, 0));
        stage('query', null, 'Waiting for a search');
        drawLegend();
        els.stats.textContent = 'Pipeline running…';

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
            return L.circleMarker([g.coordinates[1], g.coordinates[0]], { pane: 'points', radius: 5, weight: 1.5, color: '#fff', fillColor: cfg.color, fillOpacity: 1 });
        }
        const style = { pane: 'shapes', fillColor: cfg.color, color: cfg.color, weight: 2, opacity: .9, fillOpacity: .12 };
        if (g.type === 'Polygon') return L.polygon(g.coordinates.map(ring => ring.map(c => [c[1], c[0]])), style);
        if (g.type === 'MultiPolygon') return L.polygon(g.coordinates.map(poly => poly.map(ring => ring.map(c => [c[1], c[0]]))), style);
        return null;
    }

    function popup(feature, cfg) {
        const props = feature.properties;
        let html = `<div class="popup-content"><div class="popup-title">${escapeHtml(cfg.icon)} ${escapeHtml(props._display_name)}</div><div class="popup-info"><div><strong>Dataset:</strong> ${escapeHtml(cfg.name)}</div>`;
        for (const [key, value] of Object.entries(props)) {
            if (key.startsWith('_') || value === null || value === undefined || value === '' || key === cfg.display) continue;
            const label = key.replace(/([a-z\d])([A-Z])/g, '$1 $2').replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());
            html += `<div><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</div>`;
        }
        return html + '</div></div>';
    }

    // `fit` is set for searches the user asked for: they ignore the viewport and then zoom to the hits.
    function search({ fit = false } = {}) {
        if (!ready) return;
        const query = els.input.value.trim();
        const keys = els.selector.value ? [els.selector.value] : Object.keys(P.DATASETS);
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
        const took = Math.max(1, Math.round(performance.now() - started));
        drawLegend();
        total += tableRows.length;
        els.stats.textContent = `Showing ${total} items${tableRows.length ? ` (${tableRows.length} table-only)` : ''}${query ? ` for “${query}”` : ''}${capped ? ' · capped at 1000 per dataset' : ''}`;
        stage('query', 'done', `${total} hits in ${took} ms${query ? ` for “${query}”` : ''}`, 100);
        log(`query      ${query ? '"' + query + '"' : '(all)'} → ${total} hits, ${took} ms`);
    }

    function fitToHits(keys) {
        const bounds = L.latLngBounds([]);
        keys.forEach(key => layers[key].eachLayer(l => bounds.extend(l.getLatLng ? l.getLatLng() : l.getBounds())));
        if (bounds.isValid()) map.fitBounds(bounds.pad(0.15), { maxZoom: 16, animate: false });
    }

    const YEARS = Array.from({ length: 14 }, (_, i) => { const y = 2005 + i; return `F${y}_${String((y + 1) % 100).padStart(2, '0')}`; });

    function sparkline(props) {
        const values = YEARS.map(k => Number(props[k])).filter(v => Number.isFinite(v));
        if (values.length < 2) return '';
        const w = 280, h = 52, max = Math.max(...values), min = Math.min(...values), span = max - min || 1;
        const pts = values.map((v, i) => `${(i / (values.length - 1) * w).toFixed(1)},${(h - 4 - (v - min) / span * (h - 8)).toFixed(1)}`).join(' ');
        return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" role="img" aria-label="Recovery rate over time"><polyline points="${pts}" fill="none" stroke="#a78bfa" stroke-width="2"/></svg>`;
    }

    // Records without coordinates cannot be drawn, so search hits for them are listed instead.
    function renderTable(rows) {
        els.tableCount.textContent = String(rows.length);
        els.tableRows.innerHTML = '';
        if (!rows.length) {
            els.tableRows.innerHTML = '<p class="muted small">Matches from datasets without coordinates appear here.</p>';
            return;
        }
        for (const { cfg, doc } of rows) {
            const p = doc.properties;
            const row = document.createElement('div');
            row.className = 'row';
            if (cfg.name === 'Waste Recovery') {
                const first = Number(p[YEARS[0]]), last = Number(p[YEARS[YEARS.length - 1]]);
                row.innerHTML = `<b>${escapeHtml(cfg.icon)} ${escapeHtml(cfg.name)}</b><span>Recovery rate, 2005-06 to 2018-19: ${(first * 100).toFixed(0)}% → ${(last * 100).toFixed(0)}%</span>${sparkline(p)}`;
            } else {
                const detail = [p.Address, p.Suburb && String(p.Suburb).trim(), p.HoursWeekday].filter(Boolean).join(' · ');
                row.innerHTML = `<b>${escapeHtml(cfg.icon)} ${escapeHtml(String(p[cfg.display] ?? 'Unnamed').trim())}</b><span>${escapeHtml(detail)}</span>`;
            }
            els.tableRows.appendChild(row);
        }
    }

    function drawLegend() {
        els.legend.innerHTML = '';
        Object.entries(P.DATASETS).forEach(([key, cfg]) => {
            const item = document.createElement('div');
            item.className = 'legend-item' + (map.hasLayer(layers[key]) ? '' : ' inactive');
            item.tabIndex = 0;
            item.setAttribute('role', 'button');
            item.setAttribute('aria-pressed', String(map.hasLayer(layers[key])));
            const swatch = document.createElement('span');
            swatch.className = 'swatch' + (cfg.geometryType === 'polygon' ? ' poly' : '');
            swatch.style.background = cfg.color;
            const label = document.createElement('span');
            label.textContent = `${cfg.icon} ${cfg.name}`;
            const count = document.createElement('span');
            count.className = 'legend-count';
            count.textContent = counts[key] || 0;
            item.append(swatch, label, count);
            const toggle = () => {
                if (map.hasLayer(layers[key])) map.removeLayer(layers[key]); else map.addLayer(layers[key]);
                drawLegend();
            };
            item.addEventListener('click', toggle);
            item.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
            els.legend.appendChild(item);
        });
    }

    $('searchBtn').addEventListener('click', () => search({ fit: true }));
    els.input.addEventListener('keydown', e => { if (e.key === 'Enter') search({ fit: true }); });
    els.selector.addEventListener('change', () => search({ fit: true }));
    $('clearBtn').addEventListener('click', () => { els.input.value = ''; els.selector.value = ''; search({ fit: true }); });
    els.run.addEventListener('click', runPipeline);
    // Re-running the search redraws every layer, which would slam shut a popup that has just auto-panned the map.
    let popupOpen = false;
    map.on('popupopen', () => { popupOpen = true; });
    map.on('popupclose', () => { popupOpen = false; });
    map.on('moveend', () => { if (ready && !popupOpen && (els.input.value || els.selector.value)) search(); });

    // Example queries that return hits in the shipped extract.
    ['Redfern', 'hospital', 'King Street', 'library', 'ambulance', 'Business CBD'].forEach(term => {
        const b = document.createElement('button');
        b.type = 'button';
        b.textContent = term;
        b.addEventListener('click', () => { els.input.value = term; els.selector.value = ''; search({ fit: true }); });
        $('chips').appendChild(b);
    });

    // Used by tools/demo/record.mjs to show a popup without hunting for a canvas marker.
    function openFirst(key) {
        const layer = layers[key].getLayers()[0];
        if (layer) layer.openPopup();
    }

    window.__demo = { search, runPipeline, map, openFirst };
    drawLegend();
    runPipeline();
})();
