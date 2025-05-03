from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch

# Initialize Flask app
app = Flask(__name__)

# Elasticsearch client
es = Elasticsearch(hosts=["http://localhost:9200"])

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





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)