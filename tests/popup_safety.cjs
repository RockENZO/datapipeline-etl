const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const { escapeHtml } = require(path.join(root, 'web_map/static/popup_safety.js'));
const html = fs.readFileSync(path.join(root, 'web_map/templates/index.html'), 'utf8');
const context = vm.createContext({ escapeHtml });
for (const [name, end] of [['createPopupContent', '// Live data management'],
                          ['createLivePopupContent', '// Stop live data updates']]) {
    const start = html.indexOf('function ' + name + '(');
    assert(start >= 0);
    const stop = html.indexOf(end, start);
    assert(stop > start);
    vm.runInContext(html.slice(start, stop), context);
}
const payload = '<img src=x onerror="alert(1)">';
const dataset = { icon: payload, name: payload, display_field: 'Name' };
const ordinary = context.createPopupContent({ properties: {
    _display_name: payload, [payload]: payload, Name: payload,
    Count: 0, Available: false,
}}, dataset);
assert(!ordinary.includes('<img'), 'Source properties must not create HTML elements');
assert(ordinary.includes('&lt;img'), 'Unsafe source text must remain visible as text');
assert(ordinary.includes('Count:</strong> 0'), 'Zero-valued properties must remain visible');
assert(ordinary.includes('Available:</strong> false'), 'False-valued properties must remain visible');
const live = context.createLivePopupContent({ properties: {
    route_id: payload, vehicle_label: payload, trip_id: payload,
    speed: payload, occupancy_status: payload,
}}, { name: 'Live Buses' });
assert(!live.includes('<img'), 'Live bus properties must not create HTML elements');
assert(live.includes('&lt;img'));
assert.equal(escapeHtml('&<>"\''), '&amp;&lt;&gt;&quot;&#39;');
assert.equal(escapeHtml(0), '0');
const stationary = context.createLivePopupContent({ properties: { speed: 0 } }, { name: 'Live Buses' });
assert(stationary.includes('0 km/h'), 'Stationary bus speed must remain visible');
console.log('Map and live-bus popup injection/zero-value checks passed.');
const acronym = context.createPopupContent({ properties: { _display_name: 'x', URL: 'u', HoursWeekday: 'h', No_Steps: 3 } }, { icon: '', name: 'n', display_field: 'Name' });
assert(acronym.includes('URL:</strong>'), 'Acronym property names must not be split into letters');
assert(acronym.includes('Hours Weekday:</strong>'), 'camelCase property names are split into words');
assert(acronym.includes('No Steps:</strong>'), 'snake_case property names lose underscores');
console.log('Popup label formatting checks passed.');
