// Browser port of the ETL path in es_index_multi_docker.py and the query path in web_map/app.py,
// run against the synthetic files in data/. Kept free of DOM code so Node can test it.
(function (root, factory) {
    if (typeof module !== 'undefined' && module.exports) module.exports = factory();
    else root.Pipeline = factory();
})(typeof self !== 'undefined' ? self : this, function () {
    // Same indices, source files, id fields and map styling as the Docker application.
    // `search` lists the multi_match fields with their Elasticsearch mapping type.
    const DATASETS = {
        building_complex_points: { name: 'Building Complex Points', file: 'BuildingComplexPoint_EPSG4326.json', idField: 'topoid', dataPath: 'BuildingComplexPoint', geometryType: 'point', display: 'generalname', color: '#f87171', icon: '🏢', search: [['generalname', 'text'], ['alternativelabel', 'text']] },
        stairs: { name: 'Stairs', file: 'Stairs.geojson', idField: 'OBJECTID', geometryType: 'point', display: 'Name', color: '#c084fc', icon: '🚶', search: [['Name', 'text'], ['Address', 'text'], ['Suburb', 'text']] },
        recreation_centres: { name: 'Recreation Centres', file: 'Recreation_centres.geojson', idField: 'OBJECTID', geometryType: 'point', display: 'Name', color: '#4ade80', icon: '🏃', search: [['Name', 'text'], ['Address', 'text'], ['Suburb', 'text']] },
        library_details: { name: 'Libraries', file: 'Library_details.geojson', idField: 'FacilityID', geometryType: 'point', nonSpatial: true, display: 'Name', color: '#60a5fa', icon: '📚', search: [['Name', 'text'], ['Address', 'text'], ['Suburb', 'text']] },
        information_kiosks: { name: 'Information Kiosks', file: 'Information_kiosks.geojson', idField: 'OBJECTID', geometryType: 'point', display: 'CentreName', color: '#fbbf24', icon: 'ℹ️', search: [['CentreName', 'text'], ['StreetAddress', 'text'], ['Suburb', 'text']] },
        nsw_ambulance_stations: { name: 'Ambulance Stations', file: 'NSW Ambulance Station_EPSG4326.json', idField: 'topoid', dataPath: 'NSW Ambulance Station', geometryType: 'point', display: 'generalname', color: '#fb923c', icon: '🚑', search: [['generalname', 'text']] },
        business_rate_category: { name: 'Business Rate Categories', file: 'Business_rate_category.geojson', idField: 'OBJECTID', geometryType: 'polygon', display: 'BUS_VALUE', color: '#2dd4bf', icon: '🏪', search: [['BUS_VALUE', 'keyword']] },
        free_15_minute_parking: { name: 'Free 15 Minute Parking', file: 'Free_15_minute_parking.geojson', idField: 'OBJECTID', geometryType: 'polygon', display: 'Street', color: '#86efac', icon: '🅿️', search: [['Street', 'text'], ['Section', 'text'], ['Suburb', 'text']] },
        residential_waste_recovery: { name: 'Waste Recovery', file: 'Residential_waste_recovery.geojson', idField: 'OBJECTID', geometryType: 'polygon', nonSpatial: true, display: 'All_', color: '#94a3b8', icon: '♻️', search: [['All_', 'text']] },
        ticket_parking_rates: { name: 'Ticket Parking', file: 'Ticket_parking_rates.geojson', idField: 'OBJECTID', geometryType: 'polygon', display: 'PlanYear', color: '#a78bfa', icon: '🎫', search: [['PlanYear', 'text'], ['Tariff1', 'text'], ['Tariff2', 'text']] },
    };

    // Mirrors process_geometry(): points become {lat, lon}; shapes pass through; anything else is rejected.
    function processGeometry(geometry) {
        if (!geometry || !geometry.coordinates || !geometry.coordinates.length) return null;
        const type = String(geometry.type || '').toLowerCase();
        const coords = geometry.coordinates;
        if (type === 'point') {
            if (coords.length >= 2) return { lat: coords[1], lon: coords[0] };
        } else if (['polygon', 'multipolygon', 'linestring'].includes(type)) {
            return geometry;
        }
        return null;
    }

    // Mirrors the data_path walk in index_dataset(): nested wrapper keys, then `features`.
    function extractFeatures(raw, dataPath) {
        let data = raw;
        if (dataPath) for (const part of dataPath.split('.')) data = (data && data[part]) || {};
        return Array.isArray(data.features) ? data.features : [];
    }

    // Transform one extracted file into index-ready documents and a list of rejected records.
    function transform(indexName, raw) {
        const cfg = DATASETS[indexName];
        const features = extractFeatures(raw, cfg.dataPath);
        const docs = [];
        const rejected = [];
        features.forEach((feature, i) => {
            const geometry = processGeometry(feature.geometry);
            const properties = feature.properties || {};
            if (!geometry && cfg.nonSpatial && !feature.geometry) {
                // Mirrors NON_SPATIAL_DATASETS in the indexer: council tables without coordinates are kept
                // for search and listed, but never drawn.
                docs.push({ _id: properties[cfg.idField] || i + 1, geometry: null, properties: { ...properties } });
                return;
            }
            if (!geometry) {
                rejected.push({ dataset: indexName, row: i + 1, name: properties[cfg.display] || properties.Name || null, reason: feature.geometry ? 'unusable geometry' : 'no geometry' });
                return;
            }
            const id = properties[cfg.idField] ? properties[cfg.idField] : i + 1;
            docs.push({ _id: id, geometry, properties: { ...properties } });
        });
        return { docs, rejected, extracted: features.length };
    }

    // Standard-analyzer-style tokens: lowercase, split on anything that is not a letter or digit.
    function tokenize(value) {
        return String(value ?? '').toLowerCase().split(/[^\p{L}\p{N}]+/u).filter(Boolean);
    }

    // Load: build the searchable structure (the in-browser stand-in for the Elasticsearch index).
    function buildIndex(indexName, docs) {
        const cfg = DATASETS[indexName];
        const entries = docs.map(doc => {
            const fields = cfg.search.map(([field, type]) => {
                const value = doc.properties[field];
                return { type, exact: value == null ? null : String(value), tokens: type === 'text' ? tokenize(value) : [] };
            });
            return { doc, fields, bbox: doc.geometry ? boundsOf(doc.geometry) : null };
        });
        return { name: indexName, entries };
    }

    function boundsOf(geometry) {
        if (geometry && typeof geometry.lat === 'number') return [geometry.lon, geometry.lat, geometry.lon, geometry.lat];
        const b = [Infinity, Infinity, -Infinity, -Infinity];
        (function walk(c) {
            if (typeof c[0] === 'number') {
                b[0] = Math.min(b[0], c[0]); b[1] = Math.min(b[1], c[1]);
                b[2] = Math.max(b[2], c[0]); b[3] = Math.max(b[3], c[1]);
            } else c.forEach(walk);
        })(geometry.coordinates);
        return b;
    }

    // multi_match semantics: any query term may hit any field. Text fields compare analysed tokens;
    // keyword fields need an exact, case-sensitive value. bbox is [west, south, east, north].
    function search(index, query, bbox, size = 1000) {
        const terms = tokenize(query);
        const needle = String(query || '').trim();
        const hits = [];
        for (const entry of index.entries) {
            if (bbox && entry.bbox) {
                const [w, s, e, n] = bbox, b = entry.bbox;
                if (b[2] < w || b[0] > e || b[3] < s || b[1] > n) continue;
            }
            let score = 0;
            if (!terms.length) score = 1;
            else for (const f of entry.fields) {
                if (f.type === 'text') score += terms.filter(t => f.tokens.includes(t)).length;
                else if (f.exact !== null && f.exact === needle) score += 1;
            }
            if (score > 0) hits.push({ entry, score });
        }
        hits.sort((a, b) => b.score - a.score);
        return { total: hits.length, docs: hits.slice(0, size).map(h => h.entry.doc) };
    }

    // GeoJSON feature in the shape /api/search/<dataset> returns, with the display name resolved.
    function toFeature(indexName, doc) {
        const cfg = DATASETS[indexName];
        const g = doc.geometry;
        const geometry = !g ? null : typeof g.lat === 'number' ? { type: 'Point', coordinates: [g.lon, g.lat] } : g;
        return { type: 'Feature', geometry, properties: { ...doc.properties, _display_name: doc.properties[cfg.display] ?? 'Unnamed' } };
    }

    return { DATASETS, processGeometry, extractFeatures, transform, tokenize, buildIndex, search, toFeature };
});
