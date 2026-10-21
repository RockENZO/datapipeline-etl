const assert = require('node:assert/strict');
const path = require('node:path');
const L = require(path.join(__dirname, '../demo/livebus.js'));

// Inline fixtures only exercise the parser; the page itself shows whatever the live feed returns.
const attrs = (id, lat, lon, extra = {}) => ({ id, 'vehicle.position.latitude': lat, 'vehicle.position.longitude': lon, ...extra });
const feed = { features: [
    { attributes: attrs('b1', -33.87, 151.2, { 'vehicle.trip.routeId': '333', 'vehicle.position.speed': '40kmh', 'vehicle.vehicle.label': 'Bus 7' }) },
    { attributes: attrs(0, 0, 0) },                                             // numeric zero id and (0,0) are valid
    { attributes: attrs('', -33.8, 151.1) },                                    // no stable id
    { attributes: attrs('b3', NaN, 151.1) },                                    // not finite
    { attributes: attrs('b4', 95, 151.1) },                                     // out of bounds
    { attributes: { id: 'b5' }, geometry: { x: 151.3, y: -33.9 } },             // ArcGIS x/y
    { attributes: { id: 'b6' }, geometry: { x: 1, y: 2, spatialReference: { wkid: 3857 } } },   // not WGS84
    { properties: { id: 'b7' }, geometry: { type: 'Point', coordinates: [151.4, -33.7] } },     // GeoJSON
] };
const buses = L.parseBuses(feed);
assert.deepEqual(buses.map(b => b.id), ['b1', '0', 'b5', 'b7']);
assert.equal(buses[0].route, '333');
assert.equal(buses[0].speed, 40);
assert.equal(buses[0].label, 'Bus 7');
assert.equal(L.parseBuses({ features: [{ attributes: attrs('t', 1, 2, { 'vehicle.timestamp.low': 1760000000 }) }] })[0].ts, 1760000000);
assert.deepEqual([buses[2].lat, buses[2].lon], [-33.9, 151.3]);
assert.deepEqual(L.parseBuses(null), []);
assert.deepEqual(L.parseBuses({ features: [null, 7, { attributes: attrs('ok', 1, 2) }] }).map(b => b.id), ['ok']);   // bad entries skipped one by one

(async () => {
    const calls = [];
    const ok = async url => { calls.push(url); return calls.length === 1 ? { ok: false, status: 500 } : { ok: true, json: async () => feed }; };
    assert.equal((await L.fetchBuses(ok)).length, 4);
    assert.equal(calls.length, 2, 'falls back to the geojson endpoint');
    await assert.rejects(L.fetchBuses(async () => { throw new TypeError('Failed to fetch'); }), /Failed to fetch/);
    await assert.rejects(L.fetchBuses(async () => ({ ok: true, json: async () => ({ error: { message: 'Invalid query' } }) })), /Invalid query/);
    const seen = [];
    await L.fetchBuses(async url => { seen.push(url); return { ok: true, json: async () => feed }; }, undefined, 123);
    assert(seen[0].endsWith('&_=123'), 'first request carries a cache-busting parameter');
    const order = [];
    await assert.rejects(L.fetchBuses(async url => { order.push(url); throw new TypeError('nope'); }, undefined, 9));
    assert.deepEqual(order.map(u => u.includes('f=geojson') + ':' + u.endsWith('&_=9')), ['false:true', 'false:false', 'true:true', 'true:false'], 'each endpoint is tried cache-busted, then plain');
    // An empty feed is fine; a non-empty feed with nothing usable is a failed refresh.
    assert.deepEqual(await L.fetchBuses(async () => ({ ok: true, json: async () => ({ features: [] }) })), []);
    await assert.rejects(L.fetchBuses(async () => ({ ok: true, json: async () => ({ features: [{ attributes: { id: 'z' } }] }) })), /no usable/);
    console.log('livebus ok');
})();
