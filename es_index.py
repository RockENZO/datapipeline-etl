import json
import logging
from elasticsearch import Elasticsearch, helpers

# Initialize Elasticsearch client
es = Elasticsearch(hosts=["http://localhost:9200"], timeout=60)

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


# Define the index mapping for recreation_centres
recreation_centres_mapping = {
    "mappings": {
        "properties": {
            "geometry": {
                "type": "geo_point"  # Use geo_point for point data
            },
            "properties": {
                "type": "object",
                "properties": {
                    "OBJECTID": { "type": "integer" },
                    "Name": { "type": "text" },
                    "Address": { "type": "text" },
                    "Address2": { "type": "text" },
                    "Suburb": { "type": "text" },
                    "Postcode": { "type": "integer" },
                    "PhoneNumber": { "type": "text" },
                    "URL": { "type": "text" },
                    "OpeningHours": { "type": "text" },
                    "Lat": { "type": "float" },
                    "Long": { "type": "float" }
                }
            }
        }
    }
}

# Create the index for recreation_centres
es.indices.create(index='recreation_centres', body=recreation_centres_mapping, ignore=400)

# Load data from Recreation_centres.geojson
with open('./Recreation_centres.geojson') as f:
    recreation_centres_data = json.load(f)

# Prepare the data for bulk indexing
recreation_centres_actions = [
    {
        "_index": "recreation_centres",
        "_id": feature["properties"]["OBJECTID"],  # Use OBJECTID as the document ID
        "_source": {
            "geometry": {
                "lat": feature["geometry"]["coordinates"][1],
                "lon": feature["geometry"]["coordinates"][0]
            },
            "properties": feature["properties"]
        }
    }
    for feature in recreation_centres_data["features"]
]

# Bulk index the data for recreation_centres
try:
    helpers.bulk(es, recreation_centres_actions)
    logger.info("Recreation Centres data indexed successfully")
except helpers.BulkIndexError as e:
    logger.error(f"Bulk indexing error: {e.errors}")
    for error in e.errors:
        logger.error(error)

# Define the index mapping for information_kiosks
information_kiosks_mapping = {
    "mappings": {
        "properties": {
            "geometry": {
                "type": "geo_point"  # Use geo_point for point data
            },
            "properties": {
                "type": "object",
                "properties": {
                    "OBJECTID": { "type": "integer" },
                    "CentreName": { "type": "text" },
                    "StreetAddress": { "type": "text" },
                    "Suburb": { "type": "text" },
                    "Phone": { "type": "text" }
                }
            }
        }
    }
}

# Create the index for information_kiosks
es.indices.create(index='information_kiosks', body=information_kiosks_mapping, ignore=400)

# Load data from Information_kiosks.geojson
with open('./Information_kiosks.geojson') as f:
    information_kiosks_data = json.load(f)

# Prepare the data for bulk indexing
information_kiosks_actions = [
    {
        "_index": "information_kiosks",
        "_id": feature["properties"]["OBJECTID"],  # Use OBJECTID as the document ID
        "_source": {
            "geometry": {
                "lat": feature["geometry"]["coordinates"][1],
                "lon": feature["geometry"]["coordinates"][0]
            },
            "properties": feature["properties"]
        }
    }
    for feature in information_kiosks_data["features"]
]

# Bulk index the data for information_kiosks
try:
    helpers.bulk(es, information_kiosks_actions)
    logger.info("Information Kiosks data indexed successfully")
except helpers.BulkIndexError as e:
    logger.error(f"Bulk indexing error: {e.errors}")
    for error in e.errors:
        logger.error(error)

# Define the index mapping for ambulance_stations
ambulance_stations_mapping = {
    "mappings": {
        "properties": {
            "geometry": {
                "type": "geo_point"  # Use geo_point for point data
            },
            "properties": {
                "type": "object",
                "properties": {
                    "OBJECTID": { "type": "integer" },
                    "topoid": { "type": "integer" },
                    "generalname": { "type": "text" },
                    "classsubtype": { "type": "integer" },
                    "operationalstatus": { "type": "integer" },
                    "urbanity": { "type": "text" },
                    "planimetricaccuracy": { "type": "integer" },
                    "createdate": { "type": "date", "format": "yyyyMMddHHmmss" },
                    "lastupdate": { "type": "date", "format": "yyyyMMddHHmmss" }
                }
            }
        }
    }
}

# Create the index for ambulance_stations
es.indices.create(index='ambulance_stations', body=ambulance_stations_mapping, ignore=400)

# Load data from NSW Ambulance Station_EPSG4326.json
with open('./NSW Ambulance Station_EPSG4326.json') as f:
    ambulance_stations_data = json.load(f)

# Prepare the data for bulk indexing
ambulance_stations_actions = [
    {
        "_index": "ambulance_stations",
        "_id": feature["properties"]["OBJECTID"],  # Use OBJECTID as the document ID
        "_source": {
            "geometry": {
                "lat": feature["geometry"]["coordinates"][1],
                "lon": feature["geometry"]["coordinates"][0]
            },
            "properties": feature["properties"]
        }
    }
    for feature in ambulance_stations_data["Hospital"]["features"]
]

# Bulk index the data for ambulance_stations
try:
    helpers.bulk(es, ambulance_stations_actions)
    logger.info("Ambulance Stations data indexed successfully")
except helpers.BulkIndexError as e:
    logger.error(f"Bulk indexing error: {e.errors}")
    for error in e.errors:
        logger.error(error)

# Define the index mapping for bicycle_network
bicycle_network_mapping = {
    "mappings": {
        "properties": {
            "geometry": {
                "type": "geo_shape"  # Use geo_shape for line or polygon data
            },
            "properties": {
                "type": "object",
                "properties": {
                    "fid": { "type": "integer" },
                    "roadclass": { "type": "text" },
                    "region": { "type": "text" },
                    "lga": { "type": "text" },
                    "name": { "type": "text" },
                    "facility": { "type": "text" },
                    "infra": { "type": "text" },
                    "oneway": { "type": "text" },
                    "width": { "type": "float" },
                    "length_km": { "type": "float" },
                    "edit_dt": { "type": "date", "format": "yyyyMMdd" },
                    "SHAPE__Length": { "type": "float" },
                    "portal_last_updated": { "type": "date", "format": "yyyy-MM-dd" },
                    "globalid": { "type": "keyword" }
                }
            }
        }
    }
}

# Create the index for bicycle_network
es.indices.create(index='bicycle_network', body=bicycle_network_mapping, ignore=400)

# Load data from Existing_Bicycle_Network_SPHERICAL_MERCATOR.json
with open('./Existing_Bicycle_Network_SPHERICAL_MERCATOR.json') as f:
    bicycle_network_data = json.load(f)

# Check if the 'Existing_Bicycle_Network' key exists
if "Existing_Bicycle_Network" not in bicycle_network_data:
    logger.error("The 'Existing_Bicycle_Network' key is missing in the bicycle network JSON file.")
    exit(1)

# Check if the 'features' key exists under 'Existing_Bicycle_Network'
if "features" not in bicycle_network_data["Existing_Bicycle_Network"]:
    logger.error("The 'features' key is missing under 'Existing_Bicycle_Network' in the JSON file.")
    exit(1)

# Prepare the data for bulk indexing
bicycle_network_actions = [
    {
        "_index": "bicycle_network",
        "_id": feature["properties"]["fid"],  # Use fid as the document ID
        "_source": {
            "geometry": feature["geometry"],  # GeoJSON geometry
            "properties": feature["properties"]
        }
    }
    for feature in bicycle_network_data["Existing_Bicycle_Network"]["features"]
]

# Bulk index the data for bicycle_network
try:
    helpers.bulk(es, bicycle_network_actions)
    logger.info("Bicycle Network data indexed successfully")
except helpers.BulkIndexError as e:
    logger.error(f"Bulk indexing error: {e.errors}")
    for error in e.errors:
        logger.error(error)

# Define the index mapping for free_15_minute_parking
free_15_minute_parking_mapping = {
    "mappings": {
        "properties": {
            "geometry": {
                "type": "geo_shape"  # Use geo_shape for polygon data
            },
            "properties": {
                "type": "object",
                "properties": {
                    "OBJECTID": { "type": "integer" },
                    "Street": { "type": "text" },
                    "Section": { "type": "text" },
                    "Suburb": { "type": "text" },
                    "ID": { "type": "integer" },
                    "Shape__Area": { "type": "float" },
                    "Shape__Length": { "type": "float" }
                }
            }
        }
    }
}

# Create the index for free_15_minute_parking
es.indices.create(index='free_15_minute_parking', body=free_15_minute_parking_mapping, ignore=400)

# Load data from Free_15_minute_parking.geojson
with open('./Free_15_minute_parking.geojson') as f:
    free_15_minute_parking_data = json.load(f)

# Prepare the data for bulk indexing
free_15_minute_parking_actions = [
    {
        "_index": "free_15_minute_parking",
        "_id": feature["properties"]["OBJECTID"],  # Use OBJECTID as the document ID
        "_source": {
            "geometry": feature["geometry"],  # GeoJSON geometry
            "properties": feature["properties"]
        }
    }
    for feature in free_15_minute_parking_data["features"]
]

# Bulk index the data for free_15_minute_parking
try:
    helpers.bulk(es, free_15_minute_parking_actions)
    logger.info("Free 15-Minute Parking data indexed successfully")
except helpers.BulkIndexError as e:
    logger.error(f"Bulk indexing error: {e.errors}")
    for error in e.errors:
        logger.error(error)


# Define the index mapping for residential_waste_recovery
residential_waste_recovery_mapping = {
    "mappings": {
        "properties": {
            "geometry": {
                "type": "geo_shape"  # Use geo_shape for spatial data (if geometry is not null)
            },
            "properties": {
                "type": "object",
                "properties": {
                    "id": { "type": "integer" },
                    "All_": { "type": "text" },
                    "F2005_06": { "type": "float" },
                    "F2006_07": { "type": "float" },
                    "F2007_08": { "type": "float" },
                    "F2008_09": { "type": "float" },
                    "F2009_10": { "type": "float" },
                    "F2010_11": { "type": "float" },
                    "F2011_12": { "type": "float" },
                    "F2012_13": { "type": "float" },
                    "F2013_14": { "type": "float" },
                    "F2014_15": { "type": "float" },
                    "F2015_16": { "type": "float" },
                    "F2016_17": { "type": "float" },
                    "F2017_18": { "type": "float" },
                    "F2018_19": { "type": "float" },
                    "ObjectId": { "type": "integer" }
                }
            }
        }
    }
}

# Create the index for residential_waste_recovery
es.indices.create(index='residential_waste_recovery', body=residential_waste_recovery_mapping, ignore=400)

# Load data from Residential_waste_recovery.geojson
with open('./Residential_waste_recovery.geojson') as f:
    residential_waste_recovery_data = json.load(f)

# Prepare the data for bulk indexing
residential_waste_recovery_actions = [
    {
        "_index": "residential_waste_recovery",
        "_id": feature["id"],  # Use id from the top level of the Feature object
        "_source": {
            "geometry": feature["geometry"],  # GeoJSON geometry (can be null)
            "properties": feature["properties"]
        }
    }
    for feature in residential_waste_recovery_data["features"]
]

# Bulk index the data for residential_waste_recovery
try:
    helpers.bulk(es, residential_waste_recovery_actions)
    logger.info("Residential Waste Recovery data indexed successfully")
except helpers.BulkIndexError as e:
    logger.error(f"Bulk indexing error: {e.errors}")
    for error in e.errors:
        logger.error(error)

# Define the index mapping for business_rate_category
business_rate_category_mapping = {
    "mappings": {
        "properties": {
            "geometry": {
                "type": "geo_shape"  # Use geo_shape for spatial data
            },
            "properties": {
                "type": "object",
                "properties": {
                    "id": { "type": "integer" },
                    "category": { "type": "text" },
                    "description": { "type": "text" },
                    "rate": { "type": "float" }
                }
            }
        }
    }
}

# Create the index for business_rate_category
es.indices.create(index='business_rate_category', body=business_rate_category_mapping, ignore=400)

# Load data from Business_rate_category.geojson
with open('./Business_rate_category.geojson') as f:
    business_rate_category_data = json.load(f)

# Prepare the data for bulk indexing
business_rate_category_actions = [
    {
        "_index": "business_rate_category",
        "_id": feature["properties"]["OBJECTID"],  # Use OBJECTID as the document ID
        "_source": {
            "geometry": feature["geometry"],  # GeoJSON geometry
            "properties": feature["properties"]
        }
    }
    for feature in business_rate_category_data["features"]
]

# Bulk index the data for business_rate_category
try:
    helpers.bulk(es, business_rate_category_actions)
    logger.info("Business Rate Category data indexed successfully")
except helpers.BulkIndexError as e:
    logger.error(f"Bulk indexing error: {e.errors}")
    for error in e.errors:
        logger.error(error)

# Define the index mapping for UCL (Urban Centres and Localities)
ucl_mapping = {
    "mappings": {
        "properties": {
            "geometry": {
                "type": "geo_shape"  # Use geo_shape for spatial data
            },
            "properties": {
                "type": "object",
                "properties": {
                    "UCL_CODE": { "type": "keyword" },
                    "UCL_NAME": { "type": "text" },
                    "STATE_CODE": { "type": "integer" },
                    "STATE_NAME": { "type": "text" },
                    "AREA_SQKM": { "type": "float" },
                    "Shape__Area": { "type": "float" },
                    "Shape__Length": { "type": "float" }
                }
            }
        }
    }
}

# Create the index for UCL
es.indices.create(index='ucl', body=ucl_mapping, ignore=400)

# Load data from UCL_SPHERICAL_MERCATOR.json
with open('./UCL_SPHERICAL_MERCATOR.json') as f:
    ucl_data = json.load(f)

# Prepare the data for bulk indexing without specifying _id
ucl_actions = [
    {
        "_index": "ucl",
        "_source": {
            "geometry": feature["geometry"],  # GeoJSON geometry
            "properties": feature["properties"]
        }
    }
    for feature in ucl_data["UCL"]["features"]
]

# Bulk index the data for UCL
try:
    helpers.bulk(es, ucl_actions)
    logger.info("UCL data indexed successfully")
except helpers.BulkIndexError as e:
    logger.error(f"Bulk indexing error: {e.errors}")
    for error in e.errors:
        logger.error(error)


# Define the index mapping for ticket_parking_rates
ticket_parking_rates_mapping = {
    "mappings": {
        "properties": {
            "geometry": {
                "type": "geo_shape"  # Use geo_shape for spatial data
            },
            "properties": {
                "type": "object",
                "properties": {
                    "OBJECTID": { "type": "integer" },
                    "ID": { "type": "keyword" },
                    "PlanYear": { "type": "text" },
                    "Tariff1": { "type": "text" },
                    "Tariff2": { "type": "text" },
                    "Shape__Area": { "type": "float" },
                    "Shape__Length": { "type": "float" }
                }
            }
        }
    }
}

# Create the index for ticket_parking_rates
es.indices.create(index='ticket_parking_rates', body=ticket_parking_rates_mapping, ignore=400)

# Load data from Ticket_parking_rates.geojson
with open('./Ticket_parking_rates.geojson') as f:
    ticket_parking_rates_data = json.load(f)

# Prepare the data for bulk indexing
ticket_parking_rates_actions = []

for feature in ticket_parking_rates_data["features"]:
    geometry = feature.get("geometry")
    properties = feature.get("properties")

    # Validate geometry
    if geometry and geometry.get("type") in ["Polygon", "MultiPolygon"] and "coordinates" in geometry:
        ticket_parking_rates_actions.append({
            "_index": "ticket_parking_rates",
            "_id": properties.get("OBJECTID"),  # Use OBJECTID as the document ID
            "_source": {
                "geometry": geometry,  # GeoJSON geometry
                "properties": properties
            }
        })
    else:
        logger.warning(f"Invalid geometry for OBJECTID {properties.get('OBJECTID')} - Skipping")

# Bulk index the data for ticket_parking_rates
try:
    helpers.bulk(es, ticket_parking_rates_actions)
    logger.info("Ticket Parking Rates data indexed successfully")
except helpers.BulkIndexError as e:
    logger.error(f"Bulk indexing error: {e.errors}")
    for error in e.errors:
        logger.error(error)




