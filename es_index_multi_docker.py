import os
import json
import time
import logging
from elasticsearch import Elasticsearch, helpers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Wait for Elasticsearch to be ready
def wait_for_elasticsearch():
    es_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
    es = Elasticsearch(hosts=[f"http://{es_host}:9200"], timeout=60)
    
    for i in range(30):
        try:
            if es.ping():
                logger.info("Elasticsearch is ready!")
                return es
        except Exception as e:
            logger.info(f"Waiting for Elasticsearch... (attempt {i+1}/30)")
            time.sleep(10)
    
    raise Exception("Elasticsearch is not available after 5 minutes")

# Initialize Elasticsearch client
es = wait_for_elasticsearch()

# Define index mappings for different data types
index_mappings = {
    "building_complex_points": {
        "mappings": {
            "properties": {
                "geometry": {"type": "geo_point"},
                "properties": {
                    "type": "object",
                    "properties": {
                        "topoid": {"type": "integer"},
                        "generalname": {"type": "text"},
                        "alternativelabel": {"type": "text"},
                        "buildingcomplextype": {"type": "integer"},
                        "operationalstatus": {"type": "integer"},
                        "urbanity": {"type": "text"}
                    }
                }
            }
        }
    },
    "stairs": {
        "mappings": {
            "properties": {
                "geometry": {"type": "geo_point"},
                "properties": {
                    "type": "object",
                    "properties": {
                        "OBJECTID": {"type": "integer"},
                        "ID": {"type": "keyword"},
                        "Name": {"type": "text"},
                        "Address": {"type": "text"},
                        "Suburb": {"type": "text"},
                        "No_Steps": {"type": "integer"},
                        "HandRails": {"type": "keyword"},
                        "TGSI": {"type": "keyword"},
                        "StairNosingConstrastStrip": {"type": "keyword"},
                        "ClosestAlternateRoutes": {"type": "text"}
                    }
                }
            }
        }
    },
    "recreation_centres": {
        "mappings": {
            "properties": {
                "geometry": {"type": "geo_point"},
                "properties": {
                    "type": "object",
                    "properties": {
                        "FacilityID": {"type": "integer"},
                        "Name": {"type": "text"},
                        "Address": {"type": "text"},
                        "Suburb": {"type": "text"},
                        "URL": {"type": "keyword"},
                        "Hours": {"type": "text"},
                        "Transport": {"type": "text"}
                    }
                }
            }
        }
    },
    "library_details": {
        "mappings": {
            "properties": {
                "geometry": {"type": "geo_point"},
                "properties": {
                    "type": "object",
                    "properties": {
                        "FacilityID": {"type": "integer"},
                        "Name": {"type": "text"},
                        "Address": {"type": "text"},
                        "Suburb": {"type": "text"},
                        "URL": {"type": "keyword"},
                        "HoursWeekday": {"type": "text"},
                        "HoursWeekends": {"type": "text"},
                        "Transport": {"type": "text"},
                        "WheelchairAccess": {"type": "keyword"}
                    }
                }
            }
        }
    },
    "information_kiosks": {
        "mappings": {
            "properties": {
                "geometry": {"type": "geo_point"},
                "properties": {
                    "type": "object",
                    "properties": {
                        "OBJECTID": {"type": "integer"},
                        "Name": {"type": "text"},
                        "Address": {"type": "text"},
                        "Suburb": {"type": "text"},
                        "Type": {"type": "keyword"},
                        "Status": {"type": "keyword"}
                    }
                }
            }
        }
    },
    "nsw_ambulance_stations": {
        "mappings": {
            "properties": {
                "geometry": {"type": "geo_point"},
                "properties": {
                    "type": "object",
                    "properties": {
                        "topoid": {"type": "integer"},
                        "generalname": {"type": "text"},
                        "operationalstatus": {"type": "integer"},
                        "urbanity": {"type": "text"}
                    }
                }
            }
        }
    },
    "height_of_building": {
        "mappings": {
            "properties": {
                "geometry": {"type": "geo_point"},
                "properties": {
                    "type": "object",
                    "properties": {
                        "topoid": {"type": "integer"},
                        "generalname": {"type": "text"},
                        "height": {"type": "float"},
                        "buildingcomplextype": {"type": "integer"}
                    }
                }
            }
        }
    },
    "business_rate_category": {
        "mappings": {
            "properties": {
                "geometry": {"type": "geo_shape"},
                "properties": {
                    "type": "object",
                    "properties": {
                        "OBJECTID": {"type": "integer"},
                        "BUS_VALUE": {"type": "keyword"},
                        "Shape__Area": {"type": "float"},
                        "Shape__Length": {"type": "float"}
                    }
                }
            }
        }
    },
    "free_15_minute_parking": {
        "mappings": {
            "properties": {
                "geometry": {"type": "geo_point"},
                "properties": {
                    "type": "object",
                    "properties": {
                        "OBJECTID": {"type": "integer"},
                        "Name": {"type": "text"},
                        "Address": {"type": "text"},
                        "Suburb": {"type": "text"},
                        "Type": {"type": "keyword"},
                        "Spaces": {"type": "integer"}
                    }
                }
            }
        }
    },
    "residential_waste_recovery": {
        "mappings": {
            "properties": {
                "geometry": {"type": "geo_point"},
                "properties": {
                    "type": "object",
                    "properties": {
                        "OBJECTID": {"type": "integer"},
                        "Name": {"type": "text"},
                        "Address": {"type": "text"},
                        "Suburb": {"type": "text"},
                        "Type": {"type": "keyword"},
                        "Status": {"type": "keyword"}
                    }
                }
            }
        }
    },
    "ticket_parking_rates": {
        "mappings": {
            "properties": {
                "geometry": {"type": "geo_point"},
                "properties": {
                    "type": "object",
                    "properties": {
                        "OBJECTID": {"type": "integer"},
                        "Name": {"type": "text"},
                        "Address": {"type": "text"},
                        "Rate": {"type": "text"},
                        "Hours": {"type": "text"}
                    }
                }
            }
        }
    }
}

def process_geometry(geometry):
    """Process geometry based on type for Elasticsearch indexing."""
    if not geometry or not geometry.get('coordinates'):
        return None
    
    geom_type = geometry.get('type', '').lower()
    coords = geometry['coordinates']
    
    if geom_type == 'point':
        # Point geometry: [lon, lat] or [lon, lat, elevation]
        if len(coords) >= 2:
            return {
                'lat': coords[1],
                'lon': coords[0]
            }
    elif geom_type in ['polygon', 'multipolygon', 'linestring']:
        # Shape geometry: return as-is for geo_shape
        return geometry
    
    return None

def index_dataset(index_name, file_path, id_field=None, data_path=None):
    """Index a dataset into Elasticsearch."""
    try:
        logger.info(f"Processing {index_name} from {file_path}")
        
        # Create index with mapping
        if index_name in index_mappings:
            es.indices.create(index=index_name, body=index_mappings[index_name], ignore=400)
        else:
            # Default mapping for unknown datasets
            default_mapping = {
                "mappings": {
                    "properties": {
                        "geometry": {"type": "geo_point"},
                        "properties": {"type": "object"}
                    }
                }
            }
            es.indices.create(index=index_name, body=default_mapping, ignore=400)
        
        # Load data
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extract features from the data structure
        if data_path:
            # Handle nested data structures like BuildingComplexPoint_EPSG4326.json
            for path_part in data_path.split('.'):
                data = data.get(path_part, {})
            features = data.get('features', [])
        else:
            # Handle standard GeoJSON
            features = data.get('features', [])
        
        # Prepare documents for bulk indexing
        actions = []
        for i, feature in enumerate(features):
            geometry = process_geometry(feature.get('geometry'))
            if geometry:
                # Use specified ID field or fallback to auto-generated
                doc_id = None
                if id_field and feature.get('properties', {}).get(id_field):
                    doc_id = feature['properties'][id_field]
                else:
                    doc_id = i + 1
                
                # Clean up properties for date fields if needed
                properties = feature.get('properties', {})
                for key, value in properties.items():
                    if isinstance(value, str) and '.' in value and key.endswith('date'):
                        properties[key] = value.split('.')[0]
                
                doc = {
                    '_index': index_name,
                    '_id': doc_id,
                    '_source': {
                        'geometry': geometry,
                        'properties': properties
                    }
                }
                actions.append(doc)
        
        if actions:
            # Bulk index
            helpers.bulk(es, actions, chunk_size=1000)
            logger.info(f"Successfully indexed {len(actions)} documents to {index_name}")
        else:
            logger.warning(f"No valid documents found for {index_name}")
            
    except Exception as e:
        logger.error(f"Error indexing {index_name}: {e}")

def index_all_datasets():
    """Index all available datasets."""
    datasets = [
        ('building_complex_points', '/app/data/BuildingComplexPoint_EPSG4326.json', 'topoid', 'BuildingComplexPoint'),
        ('stairs', '/app/data/Stairs.geojson', 'OBJECTID', None),
        ('recreation_centres', '/app/data/Recreation_centres.geojson', 'FacilityID', None),
        ('library_details', '/app/data/Library_details.geojson', 'FacilityID', None),
        ('information_kiosks', '/app/data/Information_kiosks.geojson', 'OBJECTID', None),
        ('nsw_ambulance_stations', '/app/data/NSW Ambulance Station_EPSG4326.json', 'topoid', None),
        ('height_of_building', '/app/data/Height of Building_EPSG4326.json', 'topoid', None),
        ('business_rate_category', '/app/data/Business_rate_category.geojson', 'OBJECTID', None),
        ('free_15_minute_parking', '/app/data/Free_15_minute_parking.geojson', 'OBJECTID', None),
        ('residential_waste_recovery', '/app/data/Residential_waste_recovery.geojson', 'OBJECTID', None),
        ('ticket_parking_rates', '/app/data/Ticket_parking_rates.geojson', 'OBJECTID', None)
    ]
    
    for index_name, file_path, id_field, data_path in datasets:
        if os.path.exists(file_path):
            index_dataset(index_name, file_path, id_field, data_path)
        else:
            logger.warning(f"File not found: {file_path}")

if __name__ == "__main__":
    logger.info("Starting multi-dataset indexing process...")
    index_all_datasets()
    logger.info("Multi-dataset indexing complete!")
