import json
import logging
from elasticsearch import Elasticsearch, helpers

# Initialize Elasticsearch client
es = Elasticsearch(hosts=["http://localhost:9200"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the index mapping
mapping = {
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

# Create the index with the mapping
es.indices.create(index='building_complex_points', body=mapping, ignore=400)

# Load data from JSON file
with open('./BuildingComplexPoint_EPSG4326.json') as f:
    data = json.load(f)

# Prepare the data for bulk indexing
actions = [
    {
        "_index": "building_complex_points",
        "_id": feature["properties"]["topoid"],  # Use topoid as the document ID
        "_source": {
            "geometry": feature["geometry"]["coordinates"][:2],  # Keep only [lon, lat]
            "properties": {
                **feature["properties"],
                "lastupdate": feature["properties"]["lastupdate"].split('.')[0]  # Remove fractional seconds
            }
        }
    }
    for feature in data["BuildingComplexPoint"]["features"]
]

# Bulk index the data with detailed logging
try:
    helpers.bulk(es, actions)
    logger.info("Data indexed successfully")
except helpers.BulkIndexError as e:
    logger.error(f"Bulk indexing error: {e.errors}")
    for error in e.errors:
        logger.error(error)