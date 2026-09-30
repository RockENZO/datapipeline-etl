"""Exercise Flask -> Redis -> separate Celery worker -> real PostgreSQL."""
import sys
sys.path.insert(0, '/app')
from GNAF_search_api import app
client = app.test_client()
response = client.get('/search?address=95%20Balo%20Street&state=NSW')
assert response.status_code == 200, response.json
assert len(response.json) == 1, response.json
assert response.json[0]['street_name'] == 'BALO', response.json
response = client.get('/search?address=unknown')
assert response.status_code == 200 and response.json == [], response.json
print('PASS: real broker, worker, database and API round trip')
