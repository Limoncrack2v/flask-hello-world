from flask import Flask, request, jsonify, render_template
import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# ✅ Usa mayúsculas coherentes con el archivo .env
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
DBNAME = os.getenv("DBNAME")
CONNECTION_STRING = os.getenv("CONNECTION_STRING")

app = Flask(__name__)

# ✅ Si no hay CONNECTION_STRING, crea una desde variables individuales
def get_connection():
    if CONNECTION_STRING:
        return psycopg2.connect(CONNECTION_STRING)
    elif all([USER, PASSWORD, HOST, PORT, DBNAME]):
        return psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
    else:
        raise Exception("Database connection details are missing.")


# ---------- ROUTES ----------

@app.route('/')
def home():
    return '<h2>Flask + PostgreSQL running successfully 🚀</h2>'


@app.route('/about')
def about():
    return '<h3>About page — Flask PostgreSQL API Demo</h3>'


@app.route('/sensor')
def sensor():
    """Simple DB test"""
    try:
        connection = get_connection()
        print("✅ Connection successful!")
        cur = connection.cursor()
        cur.execute("SELECT NOW();")
        result = cur.fetchone()

        cur.close()
        connection.close()
        return f"<h3>Current DB Time: {result[0]}</h3>"

    except Exception as e:
        return f"<h3>❌ Failed to connect: {e}</h3>"


@app.route("/sensor/<int:sensor_id>", methods=["POST"])
def insert_sensor_value(sensor_id):
    """Insert sensor reading"""
    data = request.get_json() or {}
    value = data.get("value", None)

    if value is None:
        return jsonify({"error": "Missing 'value' in JSON body"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO sensors (sensor_id, value) VALUES (%s, %s);",
            (sensor_id, value)
        )
        conn.commit()

        return jsonify({
            "message": "Sensor value inserted successfully ✅",
            "sensor_id": sensor_id,
            "value": value
        }), 201

    except psycopg2.Error as e:
        return jsonify({"error": str(e)}), 500
@app.route("/sensor/<int:sensor_id>")
def get_sensor(sensor_id):
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Get the latest 10 values
        cur.execute("""
            SELECT value, created_at
            FROM sensores
            WHERE sensor_id = %s
            ORDER BY created_at DESC
            LIMIT 10;
        """, (sensor_id,))
        rows = cur.fetchall()

        # Convert to lists for graph
        values = [r[0] for r in rows][::-1]        # reverse for chronological order
        timestamps = [r[1].strftime('%Y-%m-%d %H:%M:%S') for r in rows][::-1]
        
        return render_template("sensor.html", sensor_id=sensor_id, values=values, timestamps=timestamps, rows=rows)

    except Exception as e:
        return f"<h3>Error: {e}</h3>"

    finally:
        if 'conn' in locals():
            conn.close()
