import requests
import logging
import os
import time
import re
from datetime import datetime
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
    """Fetch live bus data from NSW Spatial API."""
    try:
        logger.info("Fetching live bus data...")
        
        # Updated endpoints with the correct FeatureServer/0 structure
        endpoints = [
            f"{BUSES_API_URL}/query?f=json&where=1=1&outFields=*&resultRecordCount=1000",
            f"{BUSES_API_URL}/query?f=geojson&where=1=1&outFields=*&resultRecordCount=1000",
            f"{BUSES_API_URL}?f=json&where=1=1&outFields=*"
        ]
        
        for endpoint in endpoints:
            try:
                logger.info(f"Trying bus data endpoint: {endpoint}")
                response = requests.get(endpoint, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Check if we got valid data
                if isinstance(data, dict) and ('features' in data or 'records' in data):
                    logger.info(f"Successfully fetched bus data from: {endpoint}")
                    return data
                    
            except requests.RequestException as e:
                logger.warning(f"Failed to fetch from {endpoint}: {e}")
                continue
        
        logger.error("All bus API endpoints failed")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching bus data: {e}")
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
            
            # Create unique ID for each bus using the field structure you provided
            bus_id = props.get('id') or props.get('vehicle.vehicle.id') or props.get('hashId', str(hash(str(props))))
            
            # Extract coordinates using the specific field names from your API structure
            lat = props.get('vehicle.position.latitude')
            lon = props.get('vehicle.position.longitude')
            
            # Try geometry if coordinates not in properties
            if (not lat or not lon) and 'geometry' in feature and feature['geometry']:
                if feature['geometry']['type'] == 'Point':
                    coords = feature['geometry']['coordinates']
                    lon, lat = coords[0], coords[1]
            
            if not lat or not lon:
                logger.warning(f"Bus {bus_id} missing coordinates, skipping")
                continue
            
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
    
    if not actions:
        logger.warning("No valid bus data to index.")
        return
    
    try:
        # Delete old data (older than 5 minutes)
        five_minutes_ago = datetime.utcnow().isoformat()
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
        
        # Index new data
        helpers.bulk(es, actions)
        logger.info(f"Successfully indexed {len(actions)} bus records")
        
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
