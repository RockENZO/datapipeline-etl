import requests
import logging
from datetime import datetime
from elasticsearch import Elasticsearch, helpers
from apscheduler.schedulers.blocking import BlockingScheduler

# Initialize Elasticsearch client
es = Elasticsearch(hosts=["http://localhost:9200"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API URL
API_URL = "https://services1.arcgis.com/cNVyNtjGVZybOQWZ/arcgis/rest/services/Automatic_Hourly_Pedestrian_Count/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"

def fetch_api_data():
    """Fetch data from the API."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching data from API: {e}")
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