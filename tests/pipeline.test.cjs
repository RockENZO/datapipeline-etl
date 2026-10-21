const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const P = require(path.join(root, 'demo/pipeline.js'));

// Geometry handling matches process_geometry() in es_index_multi_docker.py.
assert.deepEqual(P.processGeometry({ type: 'Point', coordinates: [151.2, -33.8, 12] }), { lat: -33.8, lon: 151.2 });
assert.equal(P.processGeometry({ type: 'Point', coordinates: [] }), null);
assert.equal(P.processGeometry({ type: 'Point', coordinates: [1] }), null);
assert.equal(P.processGeometry(null), null);
assert.equal(P.processGeometry({ type: 'GeometryCollection', coordinates: [[0, 0]] }), null);
const poly = { type: 'Polygon', coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]] };
assert.equal(P.processGeometry(poly), poly);

// Every shipped demo file goes through the pipeline. Council tables without coordinates are kept as
// table-only rows (libraries, waste recovery); everything else must have usable geometry.
const indexes = {};
let docs = 0, rejected = 0;
for (const [name, cfg] of Object.entries(P.DATASETS)) {
    const out = P.transform(name, JSON.parse(fs.readFileSync(path.join(root, 'demo/data', cfg.file), 'utf8')));
    assert(out.docs.length > 0, name + ' has no documents');
    assert.equal(out.docs.length + out.rejected.length, out.extracted);
    const spatial = out.docs.filter(d => d.geometry).length;
    if (cfg.nonSpatial) assert.equal(spatial, 0, name + ' is expected to carry no coordinates');
    if (!cfg.nonSpatial) assert.equal(spatial, out.docs.length, name + ' must be fully spatial');
    indexes[name] = P.buildIndex(name, out.docs);
    docs += out.docs.length; rejected += out.rejected.length;
}
assert.equal(rejected, 0, 'the shipped extract has no malformed records');
assert(docs > 2000);
// A malformed record (coordinates present but unusable, or missing geometry on a spatial dataset) is rejected.
const bad = P.transform('stairs', { features: [
    { geometry: { type: 'Point', coordinates: [] }, properties: { Name: 'a' } },
    { geometry: null, properties: { Name: 'b' } },
    { geometry: { type: 'Point', coordinates: [151.2, -33.8, 0] }, properties: { OBJECTID: 7, Name: 'c' } },
] });
assert.equal(bad.docs.length, 1);
assert.equal(bad.rejected.length, 2);
assert.equal(bad.docs[0]._id, 7);

// Search: text fields match whole analysed tokens, case-insensitively, with OR semantics.
const stairs = indexes.stairs;
const all = [-180, -90, 180, 90];
assert.equal(P.search(stairs, 'STAIRS').total > 100, true);
assert.equal(P.search(stairs, 'stai').total, 0, 'text search is token based, not prefix based');
const suburb = stairs.entries[0].doc.properties.Suburb.trim();
const best = P.search(stairs, suburb + ' stairs').docs[0];
assert.equal(String(best.properties.Suburb).trim(), suburb, 'documents matching more terms rank first');
// Kiosks use CentreName/StreetAddress in the real export, not Name/Address.
assert(P.search(indexes.information_kiosks, 'Customs').total >= 1);
assert.equal(P.toFeature('information_kiosks', indexes.information_kiosks.entries[0].doc).properties._display_name, 'Customs House');
// Ambulance stations sit under the "NSW Ambulance Station" wrapper key.
assert(P.search(indexes.nsw_ambulance_stations, 'ambulance').total >= 5);
// Keyword fields are exact and case-sensitive.
assert.equal(P.search(indexes.business_rate_category, 'Business CBD').total, 1);
assert.equal(P.search(indexes.business_rate_category, 'business cbd').total, 0);
// Non-spatial rows are searchable and always pass the bbox filter.
const libs = indexes.library_details;
assert.equal(P.search(libs, 'library', [0, 0, 1, 1]).total >= 8, true);
assert.equal(P.toFeature('library_details', libs.entries[0].doc).geometry, null);
// bbox filter keeps only what intersects the viewport, for points and polygons.
assert.equal(P.search(stairs, '', [0, 0, 1, 1]).total, 0);
assert.equal(P.search(stairs, '', all).total, stairs.entries.length);
const park = indexes.free_15_minute_parking;
assert.equal(P.search(park, '', all).total, park.entries.length);
assert.equal(P.search(park, '', [10, 10, 11, 11]).total, 0);
// The example-search chips in the UI must all return something.
for (const term of ['Redfern', 'hospital', 'King Street', 'library', 'ambulance']) {
    const hits = Object.values(indexes).reduce((n, ix) => n + P.search(ix, term).total, 0);
    assert(hits > 0, 'example search "' + term + '" returns nothing');
}
console.log('Static demo pipeline checks passed.');
