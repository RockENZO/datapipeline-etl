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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)