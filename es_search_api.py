from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import os

# Initialize Flask app
app = Flask(__name__)

# Elasticsearch client
es_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
es = Elasticsearch(hosts=[f"http://{es_host}:9200"])

@app.route('/es_search/building_complex_points', methods=['GET'])
def search_building_complex_points():
    """Search in the building_complex_points index."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Define the search query
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["properties.generalname", "properties.street_name"]
            }
        }
    }

    try:
        # Perform the search
        response = es.search(index="building_complex_points", body=search_body)
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/pedestrian_counts', methods=['GET'])
def search_pedestrian_counts():
    """Search in the pedestrian_counts index."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Define the search query
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["location_name", "location_code"]
            }
        }
    }

    try:
        # Perform the search
        response = es.search(index="pedestrian_counts", body=search_body)
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/height_of_building', methods=['GET'])
def search_height_of_building():
    """Search in the height_of_building index."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Define the search query
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["properties.EPI_NAME", "properties.LGA_NAME", "properties.MAP_NAME"]
            }
        }
    }

    try:
        # Perform the search
        response = es.search(index="height_of_building", body=search_body)
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/stairs', methods=['GET'])
def search_stairs():
    """Search in the stairs index."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Define the search query
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["properties.Name", "properties.Address", "properties.Suburb"]
            }
        }
    }

    try:
        # Perform the search
        response = es.search(index="stairs", body=search_body)
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/recreation_centres', methods=['GET'])
def search_recreation_centres():
    """Search in the recreation_centres index."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Define the search query
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["properties.Name", "properties.Address", "properties.Suburb"]
            }
        }
    }

    try:
        # Perform the search
        response = es.search(index="recreation_centres", body=search_body)
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/information_kiosks', methods=['GET'])
def search_information_kiosks():
    """Search in the information_kiosks index."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Define the search query
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["properties.CentreName", "properties.StreetAddress", "properties.Suburb"]
            }
        }
    }

    try:
        # Perform the search
        response = es.search(index="information_kiosks", body=search_body)
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/ambulance_stations', methods=['GET'])
def search_ambulance_stations():
    """Search in the ambulance_stations index."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Define the search query
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["properties.generalname", "properties.urbanity"]
            }
        }
    }

    try:
        # Perform the search
        response = es.search(index="ambulance_stations", body=search_body)
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/bicycle_network', methods=['GET'])
def search_bicycle_network():
    """Search in the bicycle_network index."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Define the search query
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["properties.name", "properties.region", "properties.lga", "properties.facility"]
            }
        }
    }

    try:
        # Perform the search
        response = es.search(index="bicycle_network", body=search_body)
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/free_15_minute_parking', methods=['GET'])
def search_free_15_minute_parking():
    """Search in the free_15_minute_parking index."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Define the search query
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["properties.Street", "properties.Section", "properties.Suburb"]
            }
        }
    }

    try:
        # Perform the search
        response = es.search(index="free_15_minute_parking", body=search_body)
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/residential_waste_recovery', methods=['GET'])
def search_residential_waste_recovery():
    """Search in the residential_waste_recovery index."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Define the search query
    search_body = {
        "query": {
            "match": {
                "properties.All_": query  # Match the query against the All_ field
            }
        }
    }

    try:
        # Perform the search
        response = es.search(index="residential_waste_recovery", body=search_body)
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/business_rate_category', methods=['GET'])
def search_business_rate_category():
    """Search in the business_rate_category index."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Define the search query
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["properties.BUS_VALUE"]  # Match the correct field name
            }
        }
    }

    try:
        # Perform the search
        response = es.search(index="business_rate_category", body=search_body)
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/ucl', methods=['GET'])
def search_ucl():
    """Search in the UCL index and return geometry data."""
    query = request.args.get('query')

    # Define the search query
    if not query:
        search_body = {
            "_source": ["geometry"],  # Include only the geometry field
            "query": {
                "match_all": {}
            }
        }
    else:
        search_body = {
            "_source": ["geometry"],  # Include only the geometry field
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["properties.ucl_name_2021", "properties.state_name_2021"]
                }
            }
        }

    try:
        # Perform the search
        response = es.search(index="ucl", body=search_body, size=10000)  # Adjust size as needed
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/es_search/ticket_parking_rates', methods=['GET'])
def search_ticket_parking_rates():
    """Search in the ticket_parking_rates index."""
    query = request.args.get('query')

    # Define the search query
    if not query:
        search_body = {
            "query": {
                "match_all": {}
            }
        }
    else:
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["properties.PlanYear", "properties.Tariff1", "properties.Tariff2"]
                }
            }
        }

    try:
        # Perform the search
        response = es.search(index="ticket_parking_rates", body=search_body, size=10000)  # Adjust size as needed
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/es_search/parking_permits_areas', methods=['GET'])
def search_parking_permits_areas():
    """Search in the parking_permits_areas index."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": [
                    "properties.Label",
                    "properties.Label_2",
                    "properties.Precinct",
                    "properties.BusinessEligible",
                    "properties.VisitorEligible",
                    "properties.ResidentialEligible"
                ]
            }
        }
    }

    try:
        response = es.search(index="parking_permits_areas", body=search_body)
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/lga_ndd_total', methods=['GET'])
def search_lga_ndd_total():
    geom_type = request.args.get('type')
    query = request.args.get('query')

    # Build the search query
    if geom_type:
        search_body = {
            "query": {
                "term": {
                    "geometry.type.keyword": geom_type  # Filter by geometry type
                }
            }
        }
    elif not query:
        search_body = { "query": { "match_all": {} } }
    else:
        # Example: search by fid if you want to support property queries
        search_body = {
            "query": {
                "match": {
                    "properties.fid": query
                }
            }
        }

    try:
        response = es.search(index="lga_ndd_total", body=search_body, size=1000)
        # Return only geometry type and coordinates
        results = []
        for hit in response['hits']['hits']:
            geom = hit['_source']['geometry']
            results.append({
                "type": geom.get("type"),
                "coordinates": geom.get("coordinates")
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/dzn', methods=['GET'])
def search_dzn():
    geom_type = request.args.get('type')
    query = request.args.get('query')

    if geom_type:
        search_body = {
            "query": {
                "match": {
                    "geometry.type": geom_type
                }
            }
        }
    elif not query:
        search_body = { "query": { "match_all": {} } }
    else:
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "properties.dzn_code",
                        "properties.sa2_name_2021" 
                    ]
                }
            }
        }

    try:
        response = es.search(index="dzn", body=search_body, size=1000)
        results = []
        for hit in response['hits']['hits']:
            geom = hit['_source']['geometry']
            results.append({
                "type": geom.get("type"),
                "coordinates": geom.get("coordinates")
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/es_search/library_details/has_feature', methods=['GET'])
def search_library_details_has_feature():
    field = request.args.get('field')
    if not field:
        return jsonify({"error": "Field parameter is required"}), 400

    search_body = {
        "query": {
            "exists": {
                "field": f"properties.{field}"
            }
        }
    }

    try:
        response = es.search(index="library_details", body=search_body)
        return jsonify(response['hits']['hits']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)