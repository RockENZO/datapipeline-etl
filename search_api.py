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
    state = request.args.get('state')
    if not address:
        return jsonify({"error": "Address parameter is required"}), 400

    # Split the address into components
    address_parts = address.split()
    number_first = address_parts[0] if len(address_parts) > 0 else None
    street_name = address_parts[1].upper() if len(address_parts) > 1 else None
    street_type = address_parts[2].upper() if len(address_parts) > 2 else None

    conn = get_db_connection()
    cur = conn.cursor()
    
    # Build the query dynamically based on available parts
    query = """
    SET search_path TO gnaf_202502, public;
    SELECT DISTINCT latitude, longitude, number_first, street_name, street_type, state
    FROM address_principals
    WHERE (%s IS NULL OR number_first = %s)
    AND (%s IS NULL OR street_name LIKE %s)
    AND (%s IS NULL OR street_type LIKE %s)
    AND (%s IS NULL OR state = %s);
    """
    cur.execute(query, (number_first, number_first, street_name, f"%{street_name}%", street_type, f"%{street_type}%", state, state))
    results = cur.fetchall()
    cur.close()
    conn.close()

    if results:
        return jsonify([{
            "latitude": result[0],
            "longitude": result[1],
            "number_first": result[2],
            "street_name": result[3],
            "street_type": result[4],
            "state": result[5]
        } for result in results])
    else:
        return jsonify({"error": "Address not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)