import requests
import logging
import os
import time
import re
import math
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch, helpers
import schedule
import threading

# Initialize Elasticsearch client
es_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
es = Elasticsearch(hosts=[f"http://{es_host}:9200"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_speed_value(speed_data):
    """Extract numeric speed value from various formats."""
    if isinstance(speed_data, (int, float)):
        return float(speed_data)
    
    if isinstance(speed_data, str):
        # Extract digits from speed string like "80kmh"
        speed_match = re.search(r'(\d+)', speed_data)
        if speed_match:
            return float(speed_match.group(1))
    
    return 0.0

# API URLs
BUSES_API_URL = "https://portal.spatial.nsw.gov.au/geoserver/liveTransport/buses/FeatureServer/0"

def wait_for_elasticsearch():
    """Wait for Elasticsearch to be ready."""
    for i in range(30):
        try:
            if es.ping():
                logger.info("Elasticsearch is ready!")
                return True
        except:
            pass
        logger.info(f"Waiting for Elasticsearch... ({i+1}/30)")
        time.sleep(10)
    
    raise Exception("Elasticsearch is not available after 5 minutes")

def create_bus_index():
    """Create the live_buses index with proper mapping."""
    index_mapping = {
        "mappings": {
            "properties": {
                "geometry": {"type": "geo_point"},
                "properties": {
                    "type": "object",
                    "properties": {
                        "bus_id": {"type": "keyword"},
                        "trip_id": {"type": "keyword"},
                        "route_id": {"type": "keyword"},
                        "start_time": {"type": "keyword"},
                        "start_date": {"type": "keyword"},
                        "schedule_relationship": {"type": "keyword"},
                        "latitude": {"type": "float"},
                        "longitude": {"type": "float"},
                        "bearing": {"type": "float"},
                        "speed": {"type": "float"},
                        "compass": {"type": "keyword"},
                        "timestamp_low": {"type": "long"},
                        "timestamp_high": {"type": "long"},
                        "timestamp_unsigned": {"type": "boolean"},
                        "congestion_level": {"type": "keyword"},
                        "vehicle_id": {"type": "keyword"},
                        "vehicle_label": {"type": "keyword"},
                        "license_plate": {"type": "keyword"},
                        "occupancy_status": {"type": "keyword"},
                        "last_updated": {"type": "date"}
                    }
                }
            }
        }
    }
    
    try:
        es.indices.create(index='live_buses', body=index_mapping, ignore=400)
        logger.info("Created live_buses index")
    except Exception as e:
        logger.info(f"Index might already exist: {e}")

def fetch_bus_data():
    """Fetch every enumerated object ID, or discard the entire refresh.

    Membership is fixed by the initial ID query; moving vehicles are not a
    transactionally frozen time snapshot. Departing IDs cause a safe retry on
    the next scheduled refresh rather than publication of a partial feed.
    """
    deadline = time.monotonic() + 120

    def query(params):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("Bus refresh exceeded its 120-second request budget")
        response = requests.get(f"{BUSES_API_URL}/query", params=params,
                                timeout=min(30, remaining))
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict) or 'error' in result:
            raise ValueError("Invalid bus API response or upstream error")
        if result.get('exceededTransferLimit', False) is not False:
            raise ValueError("Bus API truncated the requested results")
        return result

    try:
        enumeration = query({'f': 'json', 'where': '1=1', 'returnIdsOnly': True})
        field = enumeration.get('objectIdFieldName')
        ids = enumeration.get('objectIds')
        if (not isinstance(field, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', field)
                or not isinstance(ids, list) or len(ids) > 10000
                or any(type(value) is not int for value in ids)
                or len(set(ids)) != len(ids)):
            raise ValueError("Invalid or oversized bus object ID enumeration")
        features = []
        for start in range(0, len(ids), 250):
            requested = ids[start:start + 250]
            # This ArcGIS-compatible GeoServer ignores objectIds; use its
            # supported SQL filter and still verify exact returned membership.
            page = query({'f': 'json', 'where': f"{field} IN ({','.join(map(str, requested))})",
                          'outFields': '*', 'outSR': 4326,
                          'resultRecordCount': len(requested)})
            reference = page.get('spatialReference')
            if reference is not None and (not isinstance(reference, dict)
                    or reference.get('latestWkid', reference.get('wkid')) != 4326):
                raise ValueError("Unexpected bus page spatial reference")
            rows = page.get('features')
            if not isinstance(rows, list):
                raise ValueError("Bus API features must be a list")
            returned = []
            for feature in rows:
                if not isinstance(feature, dict):
                    raise ValueError("Malformed bus feature")
                properties = feature.get('attributes', feature.get('properties'))
                value = properties.get(field) if isinstance(properties, dict) else None
                if type(value) is not int:
                    raise ValueError("Bus feature has no valid enumerated object ID")
                returned.append(value)
            if len(returned) != len(requested) or set(returned) != set(requested):
                raise ValueError("Bus page contains missing, duplicate or unexpected IDs")
            features.extend(rows)
        logger.info("Fetched all %d enumerated bus records", len(features))
        return {'features': features, 'spatialReference': {'wkid': 4326}}
    except (requests.RequestException, ValueError, TypeError) as error:
        logger.error("Discarding incomplete bus refresh: %s", error)
        return None

def transform_bus_data(data):
    """Transform bus data into Elasticsearch bulk format."""
    actions = []
    current_time = datetime.utcnow().isoformat()
    
    # Handle different data formats
    features = []
    if 'features' in data:
        features = data['features']
    elif 'records' in data:
        features = data['records']
    elif isinstance(data, list):
        features = data
    
    logger.info(f"Processing {len(features)} bus records")
    
    for feature in features:
        try:
            # Extract properties from different possible structures
            if 'properties' in feature:
                props = feature['properties']
            elif 'attributes' in feature:
                props = feature['attributes']
            else:
                props = feature
            
            # Only stable upstream identities may overwrite an existing vehicle.
            bus_id = next((str(props[key]).strip() for key in
                           ('id', 'vehicle.vehicle.id', 'hashId')
                           if isinstance(props.get(key), (str, int))
                           and not isinstance(props.get(key), bool)
                           and str(props[key]).strip()), None)
            if bus_id is None:
                logger.warning("Bus record missing a stable identity, skipping")
                continue

            lat = props.get('vehicle.position.latitude')
            lon = props.get('vehicle.position.longitude')
            # Missing is distinct from zero. ArcGIS x/y is WGS84 only when
            # requested with outSR=4326; explicit unsupported CRS is rejected.
            geometry = feature.get('geometry') or {}
            if lat is None or lon is None:
                reference = geometry.get('spatialReference') or (data.get('spatialReference') if isinstance(data, dict) else None)
                wkid = reference.get('latestWkid', reference.get('wkid')) if reference is not None else 4326
                if wkid != 4326:
                    raise ValueError('Unsupported point spatial reference')
                if geometry.get('type') == 'Point':
                    lon, lat = geometry['coordinates'][:2]
                elif 'x' in geometry and 'y' in geometry:
                    lon, lat = geometry['x'], geometry['y']
            if isinstance(lat, bool) or isinstance(lon, bool):
                raise ValueError('Boolean coordinates are invalid')
            lat, lon = float(lat), float(lon)
            if not (math.isfinite(lat) and math.isfinite(lon)
                    and -90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError('Coordinates must be finite WGS84 latitude/longitude')

            # Create document with the field structure from your API
            doc = {
                "geometry": {
                    "lat": float(lat),
                    "lon": float(lon)
                },
                "properties": {
                    "bus_id": str(bus_id),
                    "trip_id": props.get('vehicle.trip.tripId', ''),
                    "route_id": props.get('vehicle.trip.routeId', ''),
                    "start_time": props.get('vehicle.trip.startTime', ''),
                    "start_date": props.get('vehicle.trip.startDate', ''),
                    "schedule_relationship": props.get('vehicle.trip.scheduleRelationship', 0),
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "bearing": props.get('vehicle.position.bearing', 0),
                    "speed": extract_speed_value(props.get('vehicle.position.speed', 0)),
                    "compass": props.get('vehicle.position.compass', ''),
                    "timestamp_low": props.get('vehicle.timestamp.low', 0),
                    "timestamp_high": props.get('vehicle.timestamp.high', 0),
                    "timestamp_unsigned": props.get('vehicle.timestamp.unsigned', ''),
                    "congestion_level": props.get('vehicle.congestionLevel', 0),
                    "vehicle_id": props.get('vehicle.vehicle.id', ''),
                    "vehicle_label": props.get('vehicle.vehicle.label', ''),
                    "license_plate": props.get('vehicle.vehicle.licensePlate', ''),
                    "occupancy_status": props.get('vehicle.occupancyStatus', 0),
                    "last_updated": current_time,
                    "timestamp": int(time.time())
                }
            }
            
            actions.append({
                "_index": "live_buses",
                "_id": bus_id,
                "_source": doc
            })
            
        except Exception as e:
            logger.warning(f"Error processing bus feature: {e}")
            continue
    
    logger.info(f"Transformed {len(actions)} bus records for indexing")
    return actions

def index_bus_data():
    """Fetch, transform, and index bus data into Elasticsearch."""
    logger.info("Fetching live bus data...")
    data = fetch_bus_data()
    if not data:
        logger.error("No bus data fetched from API.")
        return

    logger.info("Transforming bus data...")
    actions = transform_bus_data(data)
    
    features = data.get('features') if isinstance(data, dict) else None
    if (not isinstance(features, list) or not actions
            or len(actions) != len(features)
            or len({action['_id'] for action in actions}) != len(actions)):
        logger.warning("Discarding refresh: every fetched record must transform to a distinct vehicle")
        return
    
    try:
        # Preserve the last usable snapshot if this refresh fails or is partial.
        helpers.bulk(es, actions)
        logger.info(f"Successfully indexed {len(actions)} bus records")

        # Expire only genuinely stale records after a successful refresh.
        five_minutes_ago = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        delete_query = {
            "query": {
                "range": {
                    "properties.last_updated": {
                        "lt": five_minutes_ago
                    }
                }
            }
        }
        es.delete_by_query(index="live_buses", body=delete_query, ignore=[404])

        
    except helpers.BulkIndexError as e:
        logger.error(f"Error during bulk indexing: {e}")
        for error in e.errors:
            logger.error(f"Bulk error: {error}")
    except Exception as e:
        logger.error(f"Unexpected error during indexing: {e}")

def schedule_bus_updates():
    """Schedule periodic updates for bus data indexing."""
    # Schedule job to run every 30 seconds
    schedule.every(30).seconds.do(index_bus_data)
    logger.info("Scheduler started. Bus data will be updated every 30 seconds.")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Wait for Elasticsearch
    wait_for_elasticsearch()
    
    # Create index
    create_bus_index()
    
    # Index data immediately
    logger.info("Indexing bus data immediately...")
    index_bus_data()

    # Start the scheduler to keep the bus data up to date
    try:
        schedule_bus_updates()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
