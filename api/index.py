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
        
def get_all_sensors():
    """Obtiene una lista de todos los IDs de sensor únicos desde la tabla 'sensores'."""
    sensors = []
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Consulta para obtener los IDs únicos.
        # Asumimos que tienes una columna llamada 'sensor_id' en la tabla 'sensores'.
        cur.execute("SELECT DISTINCT sensor_id FROM sensores ORDER BY sensor_id ASC;")
        
        # Mapeamos los IDs a una lista de diccionarios para Jinja2
        rows = cur.fetchall()
        sensors = [{'id': row[0], 'name': f'Sensor {row[0]}'} for row in rows]
        
        return sensors

    except Exception as e:
        print(f"Error al obtener la lista de sensores: {e}")
        return []
    finally:
        if conn:
            conn.close()

# ---------- ROUTES ----------

@app.route('/')
def home():
    return render_template("index.html")


@app.route('/about')
def about():
    """Ruta principal que muestra la lista de IDs de sensor disponibles."""
    
    # 1. Ejecutar la consulta a la DB
    sensor_list = get_all_sensors()
    
    # 2. Renderizar el template, pasando la lista de IDs
    return render_template(
        "index.html", 
        title="Dashboard Principal", 
        sensor_list=sensor_list
    )


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
