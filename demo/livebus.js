// Live buses for the static demo: the same Spatial NSW feed and record rules as live_bus_indexer.py,
// polled from the browser instead of an indexer writing to Elasticsearch. DOM-free so Node can test it.
(function (root, factory) {
    if (typeof module !== 'undefined' && module.exports) module.exports = factory();
    else root.LiveBus = factory();
})(typeof self !== 'undefined' ? self : this, function () {
    const API = 'https://portal.spatial.nsw.gov.au/geoserver/liveTransport/buses/FeatureServer/0';
    const URLS = [
        API + '/query?f=json&where=1=1&outFields=*&outSR=4326&resultRecordCount=1000',
        API + '/query?f=geojson&where=1=1&outFields=*&outSR=4326&resultRecordCount=1000',
    ];

    const speedValue = s => typeof s === 'number' ? s : typeof s === 'string' && /\d+/.test(s) ? Number(s.match(/\d+/)[0]) : 0;

    // Stable upstream id only (numeric zero counts); finite WGS84 coordinates only. Anything else is skipped.
    function parseBuses(data) {
        const features = data && (data.features || data.records) || (Array.isArray(data) ? data : []);
        const buses = [];
        for (const f of features) {
            if (!f || typeof f !== 'object') continue;
            const p = f.properties || f.attributes || f;
            const id = ['id', 'vehicle.vehicle.id', 'hashId'].map(k => p[k]).find(v => (typeof v === 'string' || typeof v === 'number') && String(v).trim());
            if (id === undefined) continue;
            const g = f.geometry || {};
            let lat = p['vehicle.position.latitude'], lon = p['vehicle.position.longitude'];
            if (lat == null || lon == null) {
                const ref = g.spatialReference || (data && data.spatialReference);
                if (ref && (ref.latestWkid ?? ref.wkid) !== 4326) continue;
                if (g.type === 'Point' && Array.isArray(g.coordinates)) [lon, lat] = g.coordinates;
                else if ('x' in g && 'y' in g) [lon, lat] = [g.x, g.y];
            }
            if (typeof lat !== 'number' || typeof lon !== 'number' || !Number.isFinite(lat) || !Number.isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) continue;
            buses.push({
                id: String(id).trim(), lat, lon,
                vid: String(p['vehicle.vehicle.id'] ?? '').trim(),   // fallback identities in case `id` is not stable between refreshes
                route: p['vehicle.trip.routeId'] || '', trip: p['vehicle.trip.tripId'] || '',
                label: p['vehicle.vehicle.label'] || '', plate: p['vehicle.vehicle.licensePlate'] || '',
                ts: Number(p['vehicle.timestamp.low']) || 0,   // GTFS-realtime position time, epoch seconds
                bearing: Number(p['vehicle.position.bearing']) || 0, speed: speedValue(p['vehicle.position.speed']),
            });
        }
        return buses;
    }

    // Returns the parsed buses, or throws if every endpoint failed (typically CORS or the feed being down).
    async function fetchBuses(fetchFn, signal, now = Date.now()) {
        let last;
        // Every request carries a changing query string so neither the browser nor the portal's CDN answers with a cached copy.
        // There is deliberately no plain-URL fallback: the CDN holds that copy for hours, and showing it as live is worse than
        // failing. A failed attempt is simply retried once with a new value.
        const bust = (u, n) => u + '&_=' + n;
        for (const url of URLS.flatMap(u => [bust(u, now), bust(u, now + 1)])) {
            try {
                const res = await fetchFn(url, { signal });
                if (!res.ok) throw new Error('HTTP ' + res.status);
                const data = await res.json();
                if (data && (data.features || data.records)) {
                    const buses = parseBuses(data), sent = (data.features || data.records).length;
                    // Records came back but none were usable (schema change, wrong CRS): a failed refresh, not an empty feed.
                    if (sent && !buses.length) throw new Error('no usable bus records');
                    return buses;
                }
                throw new Error(data && data.error && data.error.message || 'unexpected response');
            } catch (e) { last = e; }
        }
        throw last;
    }

    return { API, URLS, parseBuses, fetchBuses };
});
