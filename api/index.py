from flask import Flask, request, jsonify
import psycopg2
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener cadena de conexión
CONNECTION_STRING = os.getenv("CONNECTION_STRING")

app = Flask(__name__)

# Función auxiliar para conectar a la base
def get_connection():
    return psycopg2.connect(CONNECTION_STRING)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about')
def about():
    return 'About'

@app.route('/sensor')
def sensor():
    """Lee el primer registro de la tabla 'sensores'."""
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM sensores LIMIT 1;")
        result = cur.fetchone()

        cur.close()
        conn.close()
        return jsonify({"data": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/sensor/<int:sensor_id>", methods=["POST"])
def insert_sensor_value(sensor_id):
    """Inserta un nuevo valor del sensor."""
    value = request.args.get("value", type=float)
    if value is None:
        return jsonify({"error": "Missing 'value' query parameter"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()

        # Insertar registro
        cur.execute(
            "INSERT INTO sensores (sensor_id, value) VALUES (%s, %s)",
            (sensor_id, value)
        )
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({
            "message": "Sensor value inserted successfully",
            "sensor_id": sensor_id,
            "value": value
        }), 201

    except psycopg2.Error as e:
        return jsonify({"error": str(e)}), 500


# Punto de entrada local
if __name__ == '__main__':
    app.run(debug=True)
