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

    conn = get_db_connection()
    cur = conn.cursor()
    query = """
    SELECT latitude, longitude
    FROM gnaf_202411.addresses
    WHERE address LIKE %s
    LIMIT 1;
    """
    cur.execute(query, (f"%{address}%",))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return jsonify({"latitude": result[0], "longitude": result[1]})
    else:
        return jsonify({"error": "Address not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)