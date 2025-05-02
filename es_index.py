import json
import logging
from elasticsearch import Elasticsearch, helpers

# Initialize Elasticsearch client
es = Elasticsearch(hosts=["http://localhost:9200"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Create the index for building_complex_points
es.indices.create(index='building_complex_points', body=building_complex_points_mapping, ignore=400)

# Load data from JSON file for building_complex_points
with open('./BuildingComplexPoint_EPSG4326.json') as f:
    data = json.load(f)

# Prepare the data for bulk indexing
bcp_actions = [
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

# Bulk index the data for building_complex_points
try:
    helpers.bulk(es, bcp_actions)
    logger.info("Building Complex Points data indexed successfully")
except helpers.BulkIndexError as e:
    logger.error(f"Bulk indexing error: {e.errors}")
    for error in e.errors:
        logger.error(error)

# Define the index mapping for height_of_building
height_of_building_mapping = {
    "mappings": {
        "properties": {
            "geometry": {
                "type": "geo_shape"  # Use geo_shape for polygons
            },
            "properties": {
                "type": "object",
                "properties": {
                    "OBJECTID": { "type": "integer" },
                    "EPI_NAME": { "type": "text" },
                    "LGA_NAME": { "type": "text" },
                    "PUBLISHED_DATE": { "type": "date", "format": "yyyyMMddHHmmss" },
                    "COMMENCED_DATE": { "type": "date", "format": "yyyyMMddHHmmss" },
                    "CURRENCY_DATE": { "type": "date", "format": "yyyyMMddHHmmss" },
                    "MAP_TYPE": { "type": "keyword" },
                    "MAP_NAME": { "type": "text" },
                    "LAY_NAME": { "type": "text" },
                    "LAY_CLASS": { "type": "text" },
                    "SYM_CODE": { "type": "integer" },
                    "MAX_B_H": { "type": "float" },
                    "LEGIS_REF_CLAUSE": { "type": "text" },
                    "UNITS": { "type": "keyword" },
                    "PCO_REF_KEY": { "type": "text" },
                    "EPI_TYPE": { "type": "keyword" },
                    "MAX_B_H_M": { "type": "float" }
                }
            }
        }
    }
}

# Create the index for height_of_building
es.indices.create(index='height_of_building', body=height_of_building_mapping, ignore=400)

# Load data from JSON file for height_of_building
with open('./Height of Building_EPSG4326.json') as f:
    hob_data = json.load(f)

# Prepare the data for bulk indexing
hob_bcp_actions = [
    {
        "_index": "height_of_building",
        "_id": feature["properties"]["OBJECTID"],  # Use OBJECTID as the document ID
        "_source": {
            "geometry": feature["geometry"],
            "properties": feature["properties"]
        }
    }
    for feature in hob_data["Height of Building"]["features"]
]

# Bulk index the data for height_of_building
try:
    helpers.bulk(es, hob_bcp_actions)
    logger.info("Height of Building data indexed successfully")
except helpers.BulkIndexError as e:
    logger.error(f"Bulk indexing error: {e.errors}")
    for error in e.errors:
        logger.error(error)

# Define the index mapping for stairs
stairs_mapping = {
    "mappings": {
        "properties": {
            "geometry": {
                "type": "geo_point"  # Use geo_point for point data
            },
            "properties": {
                "type": "object",
                "properties": {
                    "OBJECTID": { "type": "integer" },
                    "ID": { "type": "keyword" },
                    "Name": { "type": "text" },
                    "Address": { "type": "text" },
                    "Suburb": { "type": "text" },
                    "No_Steps": { "type": "integer" },
                    "HandRails": { "type": "keyword" },
                    "TGSI": { "type": "keyword" },
                    "StairNosingConstrastStrip": { "type": "keyword" },
                    "ClosestAlternateRoutes": { "type": "text" },
                    "Photo": { "type": "keyword" }
                }
            }
        }
    }
}

# Create the index for stairs
es.indices.create(index='stairs', body=stairs_mapping, ignore=400)

# Load data from Stairs.geojson
with open('./Stairs.geojson') as f:
    stairs_data = json.load(f)

# Prepare the data for bulk indexing
stairs_actions = [
    {
        "_index": "stairs",
        "_id": feature["properties"]["OBJECTID"],  # Use OBJECTID as the document ID
        "_source": {
            "geometry": {
                "lat": feature["geometry"]["coordinates"][1],
                "lon": feature["geometry"]["coordinates"][0]
            },
            "properties": feature["properties"]
        }
    }
    for feature in stairs_data["features"]
]

# Bulk index the data for stairs
try:
    helpers.bulk(es, stairs_actions)
    logger.info("Stairs data indexed successfully")
except helpers.BulkIndexError as e:
    logger.error(f"Bulk indexing error: {e.errors}")
    for error in e.errors:
        logger.error(error)