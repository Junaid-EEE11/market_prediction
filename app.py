from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database Connection Pooling
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
except Exception as e:
    print("Error: Unable to connect to the database", e)
    exit(1)

def get_db_connection():
    """Get a database connection from the pool."""
    return db_pool.getconn()

def release_db_connection(conn):
    """Release the database connection back to the pool."""
    if conn:
        db_pool.putconn(conn)

@app.route('/')
def index():
    return render_template('index.html')  # Load main HTML form

@app.route('/get-brands', methods=['GET'])
def get_brands():
    """Fetch unique car brands."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT DISTINCT "Brand" FROM "CarData"')
            brands = [row[0] for row in cursor.fetchall()]
        return jsonify({'brands': brands})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        release_db_connection(conn)

@app.route('/get-models-body', methods=['GET'])
def get_models_and_body():
    """Fetch car models and body types based on selected brand."""
    brand = request.args.get('brand')
    if not brand:
        return jsonify({'error': 'Brand parameter is required'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT DISTINCT "Model" FROM "CarData" WHERE "Brand" = %s', (brand,))
            models = [row[0] for row in cursor.fetchall()]

            cursor.execute('SELECT DISTINCT "Body Type" FROM "CarData" WHERE "Brand" = %s', (brand,))
            body_types = [row[0] for row in cursor.fetchall()]

        return jsonify({'models': models, 'body_types': body_types})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        release_db_connection(conn)

@app.route('/get-area', methods=['GET'])
def get_area():
    """Fetch unique area information."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT DISTINCT "Area_info" FROM "CarData"')
            areas = [row[0] for row in cursor.fetchall()]
        return jsonify({'areas': areas})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        release_db_connection(conn)

@app.route('/submit-entry', methods=['POST'])
def submit_entry():
    """Insert a new car entry into the database."""
    data = request.get_json()
    petrol = "Petrol" in data["fuel-types"] # data['fuel-types'].get('petrol', False)  # Default to False if not provided
    diesel = "Diesel" in data["fuel-types"] # data['fuel-types'].get('diesel', False)
    electric = "Electric" in data["fuel-types"] #  data['fuel-types'].get('electric', False)
    hybrid ="Hybrid" in data["fuel-types"] # data['fuel-types'].get('hybrid', False)
    cng = "CNG" in data["fuel-types"] #data['fuel-types'].get('cng', False)
    lpg = "LPG" in data["fuel-types"] #data['fuel-types'].get('lpg', False)
    octane ="Octane" in data["fuel-types"] # data['fuel-types'].get('octane', False)
    other = "Other" in data["fuel-types"] #data['fuel-types'].get('other-fuel-type', False)

    required_fields = ['brand', 'model', 'price', 'condition', 'area', 
                       'kilometers-run', 'engine-cc', 'negotiation', 
                       'manufacture-year', 'registration-year', 'transmission']

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('''INSERT INTO "CarData" ("Brand", "Model", "Body Type", "Price", "Condition", "Area_info", "Petrol", "Diesel", "Electric", "Hybrid", "CNG", "LPG", "Octane", "Other fuel type", "Kilometers Run", "Engine Capacity", "Negotiable or not", "Registration Year", "Year of Manufacture","Transmission") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', (data['brand'], data['model'], data['body'], data['price'], data['condition'], data['area'], petrol, diesel, electric, hybrid, cng, lpg, octane, other, data['kilometers-run'], data['engine-cc'], data['negotiation'], data['registration-year'], data['manufacture-year'], data['transmission']))
        conn.commit()
        return jsonify({'message': 'Entry successfully added!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        release_db_connection(conn)

if __name__ == '__main__':
    app.run(debug=True)
