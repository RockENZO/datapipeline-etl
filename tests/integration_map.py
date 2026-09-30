"""Verify indexed fixtures through the actual Flask/Elasticsearch integration."""
import sys
sys.path.insert(0, '/app')
from app import app, DATASETS
client = app.test_client()
assert client.get('/health').status_code == 200
assert client.get('/').status_code == 200
for dataset in DATASETS:
    if dataset == 'live_buses':
        continue
    response = client.get('/api/search/' + dataset + '?query=SYNTHETIC%20DEMO')
    assert response.status_code == 200, (dataset, response.json)
    assert response.json['total'] == 1, (dataset, response.json)
    feature = response.json['data']['features'][0]
    assert feature['geometry']['type'] in ('Point', 'Polygon'), feature
print('PASS: dependency health, rendered map and all 10 visible synthetic dataset searches')
