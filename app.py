from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from flask_jwt_extended import set_access_cookies

from datetime import timedelta

#from flask_bcrypt import Bcrypt

#from flask_wtf.csrf import CSRFProtect

import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
import os
import joblib
import pandas as pd

app = Flask(__name__)
# Load environment variables
load_dotenv()
app.config['JWT_SECRET_KEY'] = 'super-secret'
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_TOKEN_LOCATION'] = ['cookies']  # <-- Important!
app.config['JWT_COOKIE_SECURE'] = False  # Set to True in production (HTTPS)
app.config['JWT_COOKIE_HTTPONLY'] = True  # Can't be accessed via JS
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'  # Path where cookie is valid
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'  # Mitigates CSRF

jwt = JWTManager(app)
app.secret_key = os.getenv('SECRET_KEY')  # Make sure to use a secure secret key

#csrf=CSRFProtect(app)
#bcrypt = Bcrypt(app)

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

@app.route('/get-brands', methods=['GET'])
@jwt_required()
def get_brands():
    """Fetch unique car brands."""
    if 'user' not in session:
        flash("You need to log in first!", "warning")
        return render_templete("landing_page.html")
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
@jwt_required()
def get_models_and_body():
    """Fetch car models and body types based on selected brand."""
    if 'user' not in session:
        flash("You need to log in first!", "warning")
        return render_templete("landing_page.html")
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
@jwt_required()
def get_area():
    """Fetch unique area information."""
    if 'user' not in session:
        flash("You need to log in first!", "warning")
        return render_templete("landing_page.html")
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
@jwt_required()
def submit_entry():
    """Insert a new car entry into the database."""
    data = request.get_json()
    if 'user' not in session:
        flash("You need to log in first!", "warning")
        return render_templete("landing_page.html")
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

preprocessor = joblib.load(r'web-project-models/preprocessor.pk1')

@app.route('/predict-price', methods=['POST'])
@jwt_required()
def predict_price():
    current_user = get_jwt_identity()
    if 'user' not in session:
        flash("You need to log in first!", "warning")
        return render_templete("landing_page.html")
    try:
        # Extract input data from request
        data = request.get_json();
        required_fields = ['kilometers-run', 'engine-cc', 'manufacture-year', 'registration-year']
        if not all(data[field] for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        # Create DataFrame from dictionary
        df_new_data = pd.DataFrame([{
            "Brand": data["brand"],
            "Model": data["model"],
            "Body Type": data["body"],
            "Condition": data["condition"],
            "Area_info": data["area"],
            "Kilometers Run": int(data["kilometers-run"]),
            "Engine Capacity": int(data["engine-cc"]),
            "Negotiable or not": data["negotiation"],
            "Registration age": 2025 - int(data["registration-year"]),
            "car_age": 2025 - int(data["manufacture-year"]),
            "Transmission": data["transmission"],
            "Other fuel type": "1" if "Other" in data["fuel-types"] else "0"
        }])

        # Add fuel type columns
        fuel_columns = {'CNG', 'Diesel', 'Electric', 'Hybrid', 'LPG', 'Octane', 'Petrol'}
        for col in fuel_columns:
            df_new_data[col] = "1" if col in data["fuel-types"] else "0"

        # Preprocess the input data using the preprocessor (one-hot encoding, scaling)
        x_trans = preprocessor.transform(df_new_data)
        # If the result is sparse, convert it to dense array
        x_transformed_dense = x_trans.toarray()
        # Load all models
        models = load_models()
        predictions = {}
        # Make predictions
        for model_name, model in models.items():
            try:
                price = model.predict(x_transformed_dense)[0]
                predictions[model_name.split(".")[0]] = f"{int(price):,}"  # Format with commas
            except Exception as e:
                predictions[model_name] = f"Error: {str(e)}"
        return jsonify(predictions)
 
    except Exception as e:
        # If an error occurs, return an error message
        return jsonify({'error': str(e)}), 500

def load_models():
    """Load all model files from the directory except 'preprocessor.pk1'"""
    model_dir = "web-project-models"
    model_files = [f for f in os.listdir(model_dir) if f.endswith(".pk1") and f != "preprocessor.pk1"]
    models = {}

    for model_file in model_files:
        try:
            model_path = os.path.join(model_dir, model_file)
            models[model_file] = joblib.load(model_path)  
        except Exception as e:
            print(f"Error loading {model_file}: {e}")

    return models

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        data = request.get_json(); 
        email = data.get('email'); 
        #password = check_password_hash(data.get('password')); password=bcrypt.check_password_hash(password, data['password'])
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('''SELECT name, password FROM users WHERE email = %s''', (email,))
            names = [row for row in cursor.fetchall()]
            print(names)
            if len(names)>0 and check_password_hash(names[0][1], data.get('password')):
                session['user'] = names[0][0]  # Store user in session
                release_db_connection(conn)
                access_token = create_access_token(identity=names[0][0], expires_delta=timedelta(hours=1))
                print(access_token)
                resp = jsonify({'success':True,'msg':'sign in successful'})  # Redirect to index after successful login
                set_access_cookies(resp, access_token)
                print(resp)
                return resp 
            else:
                release_db_connection(conn)
                return jsonify({'success': False,'msg':'Wrong email password'})
 
    except Exception as e:
        release_db_connection(conn)
        return jsonify({'success': False, 'msg': "Some during fetching from database, Error"})

# Logout Route
@app.route('/signout')
@jwt_required()
def signout():
    session.pop('user', None)  # Remove user from session
    resp=jsonify({'success':True,'msg':'successful'})
    resp.delete_cookie('access_token_cookie')

    flash("You have been logged out.", "info")
    return resp

@app.route('/customer-register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        username = request.get_json()['username']
        email = request.get_json()['email']
        password = generate_password_hash(request.get_json()['password'])
        #password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('''SELECT name FROM users WHERE email = %s''', (email,))
            names = [row[0] for row in cursor.fetchall()]
            if len(names)>0: 
                release_db_connection(conn); 
                return jsonify({'success': False,'msg': 'enter new email'})
            else:
                cursor.execute('''INSERT INTO "users" ("name", "password", "email") VALUES (%s, %s, %s)''', ( username, password, email))
                conn.commit()
                session['user'] = username  # Store user in session
                access_token = create_access_token(identity=username, expires_delta=timedelta(hours=1))
                resp=jsonify({'success':True,'msg':'registration successful'})
                set_access_cookies(resp, access_token)
                return resp
    except Exception as e:
        release_db_connection(conn)
        return jsonify({'success': False,'msg': str(e)})

# Protect Routes - Example of protecting a route that requires login
@app.route('/')
def index():
    if 'user' not in session:
        flash("You need to log in first!", "warning")
        return render_template("landing_page.html")
    else:
        return render_template('index.html', user=session['user'])  # Load main HTML form



if __name__ == '__main__':
    app.run(debug=True)
