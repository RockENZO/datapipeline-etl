from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch

# Initialize Flask app
app = Flask(__name__)

# Elasticsearch client
es = Elasticsearch(hosts=["http://localhost:9200"])

@app.route('/es_search', methods=['GET'])
def es_search():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    response = es.search(index="building_complex_points", body={
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["properties.generalname", "properties.street_name"]
            }
        }
    })

    return jsonify(response['hits']['hits']), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)