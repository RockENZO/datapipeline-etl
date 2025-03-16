from flask import Flask, request, jsonify
import psycopg2
from celery import Celery
import logging

app = Flask(__name__)

# Celery configuration
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'
)

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    celery.autodiscover_tasks(['search_api'])
    return celery

celery = make_celery(app)

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

@celery.task(name='search_api.search_task')
def search_task(address, state):
    # Split the address into components
    address_parts = address.split()
    number_first = address_parts[0] if len(address_parts) > 0 else None
    street_name = address_parts[1].upper() if len(address_parts) > 1 else None
    street_type = address_parts[2].upper() if len(address_parts) > 2 else None

    logging.info(f"Searching for address: {address}, state: {state}")
    logging.info(f"Parsed address parts - number_first: {number_first}, street_name: {street_name}, street_type: {street_type}")

    conn = get_db_connection()
    cur = conn.cursor()
    
    # Build the query dynamically based on available parts
    query = """
    SET search_path TO gnaf_202502, public;
    SELECT DISTINCT latitude, longitude, number_first, street_name, street_type, state
    FROM address_principals
    WHERE (%s IS NULL OR number_first = %s)
    AND (%s IS NULL OR street_name ILIKE %s)
    AND (%s IS NULL OR street_type ILIKE %s)
    AND (%s IS NULL OR state = %s);
    """
    cur.execute(query, (number_first, number_first, street_name, f"%{street_name}%", street_type, f"%{street_type}%", state, state))
    results = cur.fetchall()
    cur.close()
    conn.close()
    
    logging.info(f"Query results: {results}")

    return [{
        "latitude": result[0],
        "longitude": result[1],
        "number_first": result[2],
        "street_name": result[3],
        "street_type": result[4],
        "state": result[5]
    } for result in results]

@app.route('/search', methods=['GET'])
def search():
    address = request.args.get('address')
    state = request.args.get('state')
    if not address:
        return jsonify({"error": "Address parameter is required"}), 400

    task = search_task.apply_async(args=[address, state])
    result = task.get(timeout=30)  # Wait for the task to complete with a timeout
    return jsonify(result), 200

@app.route('/results/<task_id>', methods=['GET'])
def get_results(task_id):
    task = search_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'result': task.result
        }
    else:
        response = {
            'state': task.state,
            'status': str(task.info)  # this is the exception raised
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)