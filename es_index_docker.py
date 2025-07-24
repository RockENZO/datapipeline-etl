import json
import logging
import os
import time
from elasticsearch import Elasticsearch, helpers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Wait for Elasticsearch to be ready
def wait_for_elasticsearch():
    es_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
    es = Elasticsearch(hosts=[f"http://{es_host}:9200"], timeout=60)
    
    for i in range(30):  # Wait up to 5 minutes
        try:
            if es.ping():
                logger.info("Elasticsearch is ready!")
                return es
        except Exception as e:
            logger.info(f"Waiting for Elasticsearch... ({i+1}/30)")
            time.sleep(10)
    
    raise Exception("Elasticsearch is not available after 5 minutes")

# Initialize Elasticsearch client
es = wait_for_elasticsearch()

# Define the index mapping for building_complex_points
building_complex_points_mapping = {
    "mappings": {
        "properties": {
            "geometry": {
                "type": "geo_point"
            },
            "properties": {
                "type": "object",
                "properties": {
                    "topoid": { "type": "integer" },
                    "objectmoddate": { "type": "date", "format": "yyyyMMddHHmmss" },
                    "featuremoddate": { "type": "date", "format": "yyyyMMddHHmmss" },
                    "classsubtype": { "type": "integer" },
                    "featurereliabilitydate": { "type": "date", "format": "yyyyMMddHHmmss" },
                    "attributereliabilitydate": { "type": "date", "format": "yyyyMMddHHmmss" },
                    "capturesourcecode": { "type": "integer" },
                    "capturemethodcode": { "type": "integer" },
                    "planimetricaccuracy": { "type": "integer" },
                    "verticalaccuracy": { "type": "integer" },
                    "operationalstatus": { "type": "integer" },
                    "generalnameoid": { "type": "integer" },
                    "generalname": { "type": "text" },
                    "alternativelabel": { "type": "text" },
                    "buildingcomplextype": { "type": "integer" },
                    "relevance": { "type": "integer" },
                    "startdate": { "type": "date", "format": "yyyyMMddHHmmss" },
                    "enddate": { "type": "date", "format": "yyyyMMddHHmmss" },
                    "lastupdate": { "type": "date", "format": "yyyyMMddHHmmss" },
                    "msoid": { "type": "integer" },
                    "centroidid": { "type": "integer" },
                    "shapeuuid": { "type": "keyword" },
                    "changetype": { "type": "text" },
                    "processstate": { "type": "text" },
                    "urbanity": { "type": "text" },
                    "createdate": { "type": "date", "format": "yyyyMMddHHmmss" }
                }
            }
        }
    }
}

def index_building_complex_points():
    """Index building complex points data."""
    logger.info("Creating building_complex_points index...")
    
    # Delete existing index if it exists
    if es.indices.exists(index='building_complex_points'):
        es.indices.delete(index='building_complex_points')
        logger.info("Deleted existing building_complex_points index")
    
    # Create the index
    es.indices.create(index='building_complex_points', body=building_complex_points_mapping)
    logger.info("Created building_complex_points index")
    
    # Load data from JSON file
    data_file = './data/BuildingComplexPoint_EPSG4326.json'
    if not os.path.exists(data_file):
        logger.error(f"Data file not found: {data_file}")
        return
    
    with open(data_file) as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data['BuildingComplexPoint']['features'])} building complex points")
    
    # Prepare the data for bulk indexing
    actions = []
    for feature in data["BuildingComplexPoint"]["features"]:
        try:
            # Handle lastupdate field properly
            lastupdate = feature["properties"].get("lastupdate", "")
            if lastupdate and '.' in lastupdate:
                lastupdate = lastupdate.split('.')[0]
            
            action = {
                "_index": "building_complex_points",
                "_id": feature["properties"]["topoid"],
                "_source": {
                    "geometry": feature["geometry"]["coordinates"][:2],  # Keep only [lon, lat]
                    "properties": {
                        **feature["properties"],
                        "lastupdate": lastupdate
                    }
                }
            }
            actions.append(action)
        except Exception as e:
            logger.warning(f"Skipping feature due to error: {e}")
            continue
    
    # Bulk index the data
    try:
        logger.info(f"Indexing {len(actions)} building complex points...")
        helpers.bulk(es, actions, chunk_size=1000)
        logger.info("Building Complex Points data indexed successfully")
        
        # Verify indexing
        count = es.count(index='building_complex_points')
        logger.info(f"Indexed {count['count']} documents in building_complex_points index")
        
    except helpers.BulkIndexError as e:
        logger.error(f"Bulk indexing error: {e.errors}")
        for error in e.errors:
            logger.error(error)
    except Exception as e:
        logger.error(f"Error during indexing: {e}")

if __name__ == "__main__":
    logger.info("Starting data indexing process...")
    index_building_complex_points()
    logger.info("Data indexing complete!")
