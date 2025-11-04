from flask import Flask
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
CONNECTION_STRING = os.getenv("CONNECTION_STRING")

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about')
def about():
    return 'About'
    
print(f"Connection string: {CONNECTION_STRING}")

@app.route('/sensor')
def sensor():
    connection = None
    try:
        connection = psycopg2.connect(CONNECTION_STRING)
        app.logger.info("Connection successful!")

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM sensor_readings;")
        result = cursor.fetchone()

        return f"Connection successful! {result}"

    except Exception as e:
        app.logger.error(f"Failed to connect: {e}")
        return f"Failed to connect: {e}"

    finally:
        if connection:
            cursor.close()
            connection.close()
            app.logger.info("Connection closed.")
