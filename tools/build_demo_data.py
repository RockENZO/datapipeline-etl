"""Extract the inner-Sydney subset of the open datasets used by the static Pages demo.

Source: https://github.com/RockENZO/Knia-data-repo ("data files/", stored with Git LFS). The files there
cover all of NSW and total over 700 MB, which a Pages site cannot ship, so this keeps only records inside
the demo viewport, drops bulky bookkeeping attributes and rounds coordinates to 6 decimal places. Record
values are otherwise untouched. File names, wrapper keys and property names match the originals.

usage: python tools/build_demo_data.py "<path to Knia-data-repo>/data files" [output-dir]
"""
import json
import sys
from pathlib import Path

WEST, EAST, SOUTH, NORTH = 151.14, 151.28, -33.94, -33.82   # inner Sydney: CBD to Newtown, Glebe to Bondi Junction
OUT = Path(__file__).resolve().parent.parent / 'demo' / 'data'

KEEP = {
    'BuildingComplexPoint_EPSG4326.json': ['topoid', 'generalname', 'alternativelabel', 'buildingcomplextype', 'operationalstatus', 'urbanity'],
    'NSW Ambulance Station_EPSG4326.json': ['OBJECTID', 'topoid', 'generalname', 'alternativelabel', 'operationalstatus', 'urbanity'],
}
DROP = {'Stairs.geojson': ['Photo']}
# (file, wrapper key path or None)
FILES = [
    ('BuildingComplexPoint_EPSG4326.json', 'BuildingComplexPoint'),
    ('Stairs.geojson', None),
    ('Recreation_centres.geojson', None),
    ('Library_details.geojson', None),
    ('Information_kiosks.geojson', None),
    ('NSW Ambulance Station_EPSG4326.json', 'NSW Ambulance Station'),
    ('Business_rate_category.geojson', None),
    ('Free_15_minute_parking.geojson', None),
    ('Residential_waste_recovery.geojson', None),
    ('Ticket_parking_rates.geojson', None),
]


def rounded(coords):
    if isinstance(coords[0], (int, float)):
        return [round(c, 6) for c in coords[:2]]
    return [rounded(c) for c in coords]


def spans(coords):
    flat = []
    def walk(c):
        if isinstance(c[0], (int, float)):
            flat.append(c)
        else:
            for x in c:
                walk(x)
    walk(coords)
    xs, ys = [p[0] for p in flat], [p[1] for p in flat]
    return min(xs), min(ys), max(xs), max(ys)


def inside(geometry):
    """True when a feature has no geometry (kept: non-spatial rows) or its extent meets the viewport."""
    if not geometry or not geometry.get('coordinates'):
        return True
    x0, y0, x1, y1 = spans(geometry['coordinates'])
    return not (x1 < WEST or x0 > EAST or y1 < SOUTH or y0 > NORTH)


def build(source, name, wrapper):
    raw = json.loads((source / name).read_text())
    node = raw[wrapper] if wrapper else raw
    kept = []
    for feature in node.get('features', []):
        geometry = feature.get('geometry')
        if not inside(geometry):
            continue
        props = feature.get('properties') or {}
        if name in KEEP:
            props = {k: props.get(k) for k in KEEP[name]}
        else:
            props = {k: v for k, v in props.items() if k not in DROP.get(name, [])}
        if geometry and geometry.get('coordinates'):
            geometry = {'type': geometry['type'], 'coordinates': rounded(geometry['coordinates'])}
        kept.append({'type': 'Feature', 'properties': props, 'geometry': geometry})
    collection = {'type': 'FeatureCollection', 'features': kept}
    return {wrapper: collection} if wrapper else collection, len(node.get('features', [])), len(kept)


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    source = Path(argv[1])
    out = Path(argv[2]) if len(argv) > 2 else OUT
    out.mkdir(parents=True, exist_ok=True)
    for name, wrapper in FILES:
        payload, before, after = build(source, name, wrapper)
        (out / name).write_text(json.dumps(payload, separators=(',', ':'), ensure_ascii=False) + '\n')
        print(f'{name}: {before} -> {after} features, {(out / name).stat().st_size / 1024:.0f} KB')


if __name__ == '__main__':
    main(sys.argv)
