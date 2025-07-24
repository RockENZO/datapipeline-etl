import os
import logging
from flask import Flask, render_template, request, jsonify
from elasticsearch import Elasticsearch

app = Flask(__name__)

# Elasticsearch client
es_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
es = Elasticsearch(hosts=[f"http://{es_host}:9200"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dataset configurations
DATASETS = {
    'building_complex_points': {
        'name': 'Building Complex Points',
        'geometry_type': 'point',
        'search_fields': ['properties.generalname', 'properties.alternativelabel'],
        'display_field': 'generalname',
        'color': '#e74c3c',
        'icon': '🏢'
    },
    'stairs': {
        'name': 'Stairs',
        'geometry_type': 'point',
        'search_fields': ['properties.Name', 'properties.Address'],
        'display_field': 'Name',
        'color': '#9b59b6',
        'icon': '🚶'
    },
    'recreation_centres': {
        'name': 'Recreation Centres',
        'geometry_type': 'point',
        'search_fields': ['properties.Name', 'properties.Address'],
        'display_field': 'Name',
        'color': '#27ae60',
        'icon': '🏃'
    },
    'library_details': {
        'name': 'Libraries',
        'geometry_type': 'point',
        'search_fields': ['properties.Name', 'properties.Address'],
        'display_field': 'Name',
        'color': '#3498db',
        'icon': '📚'
    },
    'information_kiosks': {
        'name': 'Information Kiosks',
        'geometry_type': 'point',
        'search_fields': ['properties.Name', 'properties.Address'],
        'display_field': 'Name',
        'color': '#f39c12',
        'icon': 'ℹ️'
    },
    'nsw_ambulance_stations': {
        'name': 'Ambulance Stations',
        'geometry_type': 'point',
        'search_fields': ['properties.generalname'],
        'display_field': 'generalname',
        'color': '#e67e22',
        'icon': '🚑'
    },
    'business_rate_category': {
        'name': 'Business Rate Categories',
        'geometry_type': 'polygon',
        'search_fields': ['properties.BUS_VALUE'],
        'display_field': 'BUS_VALUE',
        'color': '#1abc9c',
        'icon': '🏪'
    },
    'free_15_minute_parking': {
        'name': 'Free 15 Minute Parking',
        'geometry_type': 'polygon',
        'search_fields': ['properties.Street', 'properties.Section', 'properties.Suburb'],
        'display_field': 'Street',
        'color': '#2ecc71',
        'icon': '🅿️'
    },
    'residential_waste_recovery': {
        'name': 'Waste Recovery',
        'geometry_type': 'point',
        'search_fields': ['properties.All_', 'properties.F2018_19'],
        'display_field': 'All_',
        'color': '#95a5a6',
        'icon': '♻️'
    },
    'ticket_parking_rates': {
        'name': 'Ticket Parking',
        'geometry_type': 'polygon',
        'search_fields': ['properties.PlanYear', 'properties.Tariff1', 'properties.Tariff2'],
        'display_field': 'PlanYear',
        'color': '#34495e',
        'icon': '🎫'
    }
}

@app.route('/')
def index():
    """Render the main map interface."""
    return render_template('index.html', datasets=DATASETS)

@app.route('/api/datasets')
def get_datasets():
    """Get available datasets."""
    return jsonify(DATASETS)

@app.route('/api/search/<dataset>')
def search_dataset(dataset):
    """Search and return data for map visualization."""
    if dataset not in DATASETS:
        return jsonify({"success": False, "error": "Dataset not found"}), 404
    
    query = request.args.get('query', '')
    bbox = request.args.get('bbox')  # Bounding box for map extent
    size = int(request.args.get('size', 1000))  # Default to 1000 results
    
    dataset_config = DATASETS[dataset]
    
    # Base search body
    search_body = {
        "size": size,
        "_source": ["geometry", "properties"]
    }
    
    # Add query if provided
    if query:
        search_body["query"] = {
            "multi_match": {
                "query": query,
                "fields": dataset_config['search_fields']
            }
        }
    else:
        search_body["query"] = {"match_all": {}}
    
    # Add bounding box filter if provided
    if bbox:
        try:
            # bbox format: "west,south,east,north"
            west, south, east, north = map(float, bbox.split(','))
            
            if dataset_config['geometry_type'] == 'point':
                geo_filter = {
                    "geo_bounding_box": {
                        "geometry": {
                            "top_left": {"lat": north, "lon": west},
                            "bottom_right": {"lat": south, "lon": east}
                        }
                    }
                }
            else:
                geo_filter = {
                    "geo_shape": {
                        "geometry": {
                            "shape": {
                                "type": "envelope",
                                "coordinates": [[west, north], [east, south]]
                            },
                            "relation": "intersects"
                        }
                    }
                }
            
            if "query" in search_body and search_body["query"] != {"match_all": {}}:
                search_body["query"] = {
                    "bool": {
                        "must": search_body["query"],
                        "filter": geo_filter
                    }
                }
            else:
                search_body["query"] = {
                    "bool": {
                        "filter": geo_filter
                    }
                }
        except (ValueError, IndexError):
            return jsonify({"success": False, "error": "Invalid bbox format"}), 400
    
    try:
        response = es.search(index=dataset, body=search_body)
        
        # Convert to GeoJSON format
        features = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            geometry = source.get('geometry')
            properties = source.get('properties', {})
            
            # Process geometry based on type
            if dataset_config['geometry_type'] == 'point' and isinstance(geometry, dict) and 'lat' in geometry:
                # Point stored as {lat, lon}
                geojson_geometry = {
                    "type": "Point",
                    "coordinates": [geometry['lon'], geometry['lat']]
                }
            elif dataset_config['geometry_type'] == 'point' and isinstance(geometry, list):
                # Point stored as [lon, lat]
                geojson_geometry = {
                    "type": "Point",
                    "coordinates": geometry
                }
            else:
                # Polygon, LineString, etc. - already in correct format
                geojson_geometry = geometry
            
            feature = {
                "type": "Feature",
                "geometry": geojson_geometry,
                "properties": {
                    **properties,
                    "_dataset": dataset,
                    "_color": dataset_config['color'],
                    "_icon": dataset_config['icon'],
                    "_display_name": properties.get(dataset_config['display_field'], 'Unnamed')
                }
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return jsonify({
            "success": True,
            "data": geojson,
            "total": response['hits']['total']['value'] if isinstance(response['hits']['total'], dict) else response['hits']['total'],
            "dataset": dataset_config
        })
        
    except Exception as e:
        logger.error(f"Search error for {dataset}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/<dataset>/<doc_id>')
def get_detail(dataset, doc_id):
    """Get detailed information for a specific item."""
    if dataset not in DATASETS:
        return jsonify({"success": False, "error": "Dataset not found"}), 404
    
    try:
        response = es.get(index=dataset, id=doc_id)
        return jsonify({
            "success": True,
            "data": response['_source'],
            "dataset": DATASETS[dataset]
        })
    except Exception as e:
        logger.error(f"Error fetching {dataset} detail: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        # Check Elasticsearch connection
        if es.ping():
            return jsonify({"status": "healthy", "elasticsearch": "connected"})
        else:
            return jsonify({"status": "healthy", "elasticsearch": "disconnected", "message": "Web app is running, Elasticsearch not ready yet"})
    except Exception as e:
        return jsonify({"status": "healthy", "elasticsearch": "error", "message": "Web app is running", "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
