import requests
import logging
import os
from datetime import datetime
from elasticsearch import Elasticsearch, helpers
from apscheduler.schedulers.blocking import BlockingScheduler

# Initialize Elasticsearch client
es_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
es = Elasticsearch(hosts=[f"http://{es_host}:9200"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API URLs
PEDESTRIAN_API_URL = "https://services1.arcgis.com/cNVyNtjGVZybOQWZ/arcgis/rest/services/Automatic_Hourly_Pedestrian_Count/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
BUSES_API_URL = "https://portal.spatial.nsw.gov.au/geoserver/liveTransport/buses/FeatureServer"

def fetch_api_data():
    """Fetch data from the API."""
    try:
        response = requests.get(PEDESTRIAN_API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching data from API: {e}")
        return None

def fetch_bus_data():
    """Fetch live bus data from NSW Spatial API."""
    try:
        # Try different endpoint formats for NSW Spatial API
        endpoints = [
            f"{BUSES_API_URL}/query?f=json&where=1=1&outFields=*",
            f"{BUSES_API_URL}/query?f=geojson&where=1=1&outFields=*",
            f"{BUSES_API_URL}?f=json&where=1=1&outFields=*"
        ]
        
        for endpoint in endpoints:
            try:
                logger.info(f"Trying bus data endpoint: {endpoint}")
                response = requests.get(endpoint, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Check if we got valid data
                if 'features' in data or 'records' in data:
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

def transform_api_data(data):
    """Transform API data into Elasticsearch bulk format."""
    actions = []
    for feature in data.get("features", []):
        properties = feature["properties"]
        doc_id = properties["ObjectId"]  # Use ObjectId as the document ID
        actions.append({
            "_index": "pedestrian_counts",
            "_id": doc_id,
            "_source": {
                "location_code": properties["Location_code"],
                "location_name": properties["Location_Name"],
                "date": datetime.utcfromtimestamp(properties["Date"] / 1000).isoformat(),
                "total_count": properties["TotalCount"],
                "hour": properties["Hour"],
                "day": properties["Day"],
                "day_no": properties["DayNo"],
                "week": properties["Week"],
                "last_week": properties["LastWeek"],
                "previous_4_day_time_avg": properties["Previous4DayTimeAvg"],
                "last_year": properties["LastYear"],
                "previous_52_day_time_avg": properties["Previous52DayTimeAvg"]
            }
        })
    return actions

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
    
    for feature in features:
        try:
            # Extract properties from different possible structures
            if 'properties' in feature:
                props = feature['properties']
            elif 'attributes' in feature:
                props = feature['attributes']
            else:
                props = feature
            
            # Create unique ID for each bus
            bus_id = props.get('id') or props.get('vehicle.vehicle.id') or props.get('vehicleId', str(hash(str(props))))
            
            # Extract coordinates
            lat = None
            lon = None
            
            if 'geometry' in feature and feature['geometry']:
                if feature['geometry']['type'] == 'Point':
                    coords = feature['geometry']['coordinates']
                    lon, lat = coords[0], coords[1]
            
            # Try to get coordinates from properties if not in geometry
            if not lat or not lon:
                lat = props.get('vehicle.position.latitude') or props.get('latitude')
                lon = props.get('vehicle.position.longitude') or props.get('longitude')
            
            if not lat or not lon:
                logger.warning(f"Bus {bus_id} missing coordinates, skipping")
                continue
            
            # Create document
            doc = {
                "geometry": {
                    "lat": float(lat),
                    "lon": float(lon)
                },
                "properties": {
                    "bus_id": str(bus_id),
                    "trip_id": props.get('vehicle.trip.tripId') or props.get('tripId'),
                    "route_id": props.get('vehicle.trip.routeId') or props.get('routeId'),
                    "start_time": props.get('vehicle.trip.startTime') or props.get('startTime'),
                    "start_date": props.get('vehicle.trip.startDate') or props.get('startDate'),
                    "schedule_relationship": props.get('vehicle.trip.scheduleRelationship'),
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "bearing": props.get('vehicle.position.bearing') or props.get('bearing'),
                    "speed": props.get('vehicle.position.speed') or props.get('speed'),
                    "compass": props.get('vehicle.position.compass') or props.get('compass'),
                    "timestamp_low": props.get('vehicle.timestamp.low'),
                    "timestamp_high": props.get('vehicle.timestamp.high'),
                    "timestamp_unsigned": props.get('vehicle.timestamp.unsigned'),
                    "congestion_level": props.get('vehicle.congestionLevel') or props.get('congestionLevel'),
                    "vehicle_id": props.get('vehicle.vehicle.id') or props.get('vehicleId'),
                    "vehicle_label": props.get('vehicle.vehicle.label') or props.get('label'),
                    "license_plate": props.get('vehicle.vehicle.licensePlate') or props.get('licensePlate'),
                    "occupancy_status": props.get('vehicle.occupancyStatus') or props.get('occupancyStatus'),
                    "last_updated": current_time
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
    
    return actions
            "_source": {
                "location_code": properties["Location_code"],
                "location_name": properties["Location_Name"],
                "date": datetime.utcfromtimestamp(properties["Date"] / 1000).isoformat(),
                "total_count": properties["TotalCount"],
                "hour": properties["Hour"],
                "day": properties["Day"],
                "day_no": properties["DayNo"],
                "week": properties["Week"],
                "last_week": properties["LastWeek"],
                "previous_4_day_time_avg": properties["Previous4DayTimeAvg"],
                "last_year": properties["LastYear"],
                "previous_52_day_time_avg": properties["Previous52DayTimeAvg"]
            }
        })
    return actions

def index_api_data():
    """Fetch, transform, and index API data into Elasticsearch."""
    logger.info("Fetching API data...")
    data = fetch_api_data()
    if not data:
        logger.error("No data fetched from API.")
        return

    logger.info("Transforming API data...")
    actions = transform_api_data(data)
    try:
        helpers.bulk(es, actions)
        logger.info("API data indexed successfully")
    except helpers.BulkIndexError as e:
        logger.error(f"Bulk indexing error: {e.errors}")
        for error in e.errors:
            logger.error(error)

def schedule_api_updates():
    """Schedule periodic updates for API data indexing."""
    scheduler = BlockingScheduler()
    # Schedule the job to run every hour
    scheduler.add_job(index_api_data, 'interval', hours=1)
    logger.info("Scheduler started. API data will be updated every hour.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")

if __name__ == "__main__":
    # Index data immediately
    logger.info("Indexing API data immediately...")
    index_api_data()

    # Start the scheduler to keep the API data up to date
    schedule_api_updates()