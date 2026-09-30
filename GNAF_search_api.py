"""Address search API with a separately deployed Celery worker."""
import logging
import os

import psycopg2
from psycopg2 import sql
from celery import Celery
from celery.exceptions import TimeoutError as TaskTimeout
from flask import Flask, jsonify, request, url_for

app = Flask(__name__)
redis_host = os.getenv("REDIS_HOST", "localhost")
celery = Celery(app.import_name,
                broker=f"redis://{redis_host}:6379/0",
                backend=f"redis://{redis_host}:6379/0")
celery.conf.update(task_track_started=True, task_time_limit=35,
                   broker_connection_retry_on_startup=True, result_expires=3600)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
        connect_timeout=5)


@celery.task(name="gnaf.search")
def search_task(address, state):
    parts = address.split()
    number = int(parts[0]) if parts and parts[0].isdigit() else None
    street_parts = parts[1:] if number is not None else parts
    street = " ".join(street_parts).upper() or None
    query = sql.SQL("""
        SELECT DISTINCT latitude, longitude, number_first, street_name, street_type, state
        FROM {}.address_principals
        WHERE (%s IS NULL OR number_first = %s)
          AND (%s IS NULL OR CONCAT_WS(' ', street_name, street_type) ILIKE %s)
          AND (%s IS NULL OR state = %s)
        ORDER BY street_name, number_first
        LIMIT 100
    """).format(sql.Identifier(os.getenv("GNAF_SCHEMA", "gnaf_202502")))
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout TO 25000")
            cur.execute(query, (number, number, street, f"%{street}%" if street else None, state, state))
            rows = cur.fetchall()
    finally:
        conn.close()
    keys = ("latitude", "longitude", "number_first", "street_name", "street_type", "state")
    return [dict(zip(keys, row)) for row in rows]


@app.get("/search")
def search():
    address = request.args.get("address", "").strip()
    state = request.args.get("state", "").strip().upper() or None
    if not address or len(address) > 200:
        return jsonify(error="Provide an address of 1–200 characters"), 400
    if state and state not in {"NSW", "VIC", "QLD", "SA", "WA", "TAS", "ACT", "NT"}:
        return jsonify(error="Invalid Australian state"), 400
    try:
        task = search_task.apply_async(args=[address, state])
        if request.args.get("async", "false").lower() == "true":
            location = url_for("get_results", task_id=task.id)
            return jsonify(task_id=task.id, status="pending", results_url=location), 202, {"Location": location}
        return jsonify(task.get(timeout=30)), 200
    except TaskTimeout:
        return jsonify(error="Address search timed out; retry or use async=true"), 504
    except Exception:
        app.logger.exception("Address search failed")
        return jsonify(error="Address search service unavailable"), 503


@app.get("/results/<task_id>")
def get_results(task_id):
    try:
        task = search_task.AsyncResult(task_id)
        state = task.state
    except Exception:
        app.logger.exception("Result backend unavailable")
        return jsonify(error="Result service unavailable"), 503
    if state == "SUCCESS":
        return jsonify(state=task.state, result=task.result), 200
    if state == "FAILURE":
        return jsonify(state=task.state, error="Address search failed"), 503
    return jsonify(state=task.state, status="Pending or unknown task; results expire after one hour"), 202


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
