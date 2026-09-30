"""Create clearly labelled synthetic Sydney fixtures; never overwrite user data."""
import json
from pathlib import Path

FILES = [
    ('BuildingComplexPoint_EPSG4326.json', 'point', 'BuildingComplexPoint'),
    ('Stairs.geojson', 'point', None),
    ('Recreation_centres.geojson', 'point', None),
    ('Library_details.geojson', 'point', None),
    ('Information_kiosks.geojson', 'point', None),
    ('NSW Ambulance Station_EPSG4326.json', 'point', None),
    ('Height of Building_EPSG4326.json', 'polygon', None),
    ('Business_rate_category.geojson', 'polygon', None),
    ('Free_15_minute_parking.geojson', 'polygon', None),
    ('Residential_waste_recovery.geojson', 'polygon', None),
    ('Ticket_parking_rates.geojson', 'polygon', None),
]

def generate(directory=Path('data')):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if any((directory / name).exists() for name, _, _ in FILES):
        raise FileExistsError('Demo inputs already exist. Use a fresh directory or retain your real data.')
    for name, kind, wrapper in FILES:
        geometry = {'type': 'Point', 'coordinates': [151.20, -33.86]} if kind == 'point' else {'type': 'Polygon', 'coordinates': [[[151.20,-33.86],[151.21,-33.86],[151.21,-33.85],[151.20,-33.85],[151.20,-33.86]]]}
        collection = {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'geometry': geometry, 'properties': {
            'OBJECTID': 1, 'topoid': 1, 'FacilityID': 1, 'Name': 'SYNTHETIC DEMO',
            'generalname': 'SYNTHETIC DEMO', 'All_': 'SYNTHETIC DEMO', 'BUS_VALUE': 'SYNTHETIC DEMO',
            'Street': 'SYNTHETIC DEMO', 'PlanYear': 'SYNTHETIC DEMO', 'source': 'synthetic fixture; not real infrastructure'}}]}
        payload = {wrapper: collection} if wrapper else collection
        (directory / name).write_text(json.dumps(payload, sort_keys=True) + '\n')
    print('Generated 11 synthetic demo records; these are not real city datasets.')

if __name__ == '__main__':
    generate()
