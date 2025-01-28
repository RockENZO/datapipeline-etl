from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5433"  # Use the port mapped to the host
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "password"

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

@app.route('/search', methods=['GET'])
def search():
    address = request.args.get('address')
    if not address:
        return jsonify({"error": "Address parameter is required"}), 400

    # Split the address into components
    address_parts = address.split()
    if len(address_parts) < 3:
        return jsonify({"error": "Address format should be 'number street_name street_type'"}), 400

    number_first = address_parts[0]
    street_name = address_parts[1]
    street_type = address_parts[2]

    conn = get_db_connection()
    cur = conn.cursor()
    query = """
    SELECT latitude, longitude
    FROM gnaf_202411.address_principals
    WHERE number_first = %s AND street_name = %s AND street_type = %s
    LIMIT 1;
    """
    cur.execute(query, (number_first, street_name, street_type))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return jsonify({"latitude": result[0], "longitude": result[1]})
    else:
        return jsonify({"error": "Address not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)