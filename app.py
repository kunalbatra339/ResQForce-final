from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# MongoDB Configuration (Localhost)
client = MongoClient("mongodb+srv://zero2omegadev:ayushkunal456@cluster0.5rnijnb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['rescue_db']
agencies_collection = db['agencies']
emergencies_collection = db['emergencies']
resources_collection = db['resources']

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Temporary debug route (remove in production)
@app.route('/debug/emergencies')
def debug_emergencies():
    try:
        emergencies = list(emergencies_collection.find())
        for emergency in emergencies:
            emergency['_id'] = str(emergency['_id'])
        return jsonify({
            'count': len(emergencies),
            'emergencies': emergencies
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hash_password(request.form['password'])

        try:
            agency = agencies_collection.find_one({'email': email})
            if agency and agency['password'] == password:
                session['agency_id'] = str(agency['_id'])
                session['role'] = agency.get('role', 'agency')
                return redirect(url_for('dashboard'))
            return render_template('login.html', error="Invalid credentials")
        except Exception as e:
            return render_template('login.html', error="Database error")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        try:
            if agencies_collection.find_one({'email': data['email']}):
                return render_template('register.html', error="Email already registered")

            agency_data = {
                'name': data['name'],
                'email': data['email'],
                'password': hash_password(data['password']),
                'expertise': data['expertise'],
                'latitude': 20.5937,
                'longitude': 78.9629,
                'last_updated': None,
                'role': 'agency',
                'verified': False,
                'agency_type': 'local'
            }
            result = agencies_collection.insert_one(agency_data)
            session['agency_id'] = str(result.inserted_id)
            session['role'] = 'agency'
            return redirect(url_for('dashboard'))
        except Exception as e:
            return render_template('register.html', error=str(e))
    return render_template('register.html')

@app.route('/emergency_map')
def emergency_map():
    if 'agency_id' not in session:
        return redirect(url_for('login'))
    return render_template('emergency_map.html')

@app.route('/api/report_emergency', methods=['POST'])
def report_emergency():
    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    description = data.get('description')
    tag = data.get('tag')

    try:
        emergency_data = {
            'latitude': lat,
            'longitude': lng,
            'description': description,
            'status': 'pending',
            'created_at': datetime.now(),
            'reported_by': 'public',
            'tag': tag
        }
        emergencies_collection.insert_one(emergency_data)
        return jsonify({'message': 'Emergency reported successfully'}), 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': 'Failed to report emergency'}), 500

@app.route('/client')
def client_portal():
    return render_template('client.html')

@app.route('/api/update_location', methods=['POST'])
def update_location():
    if 'agency_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    try:
        agencies_collection.update_one(
            {'_id': ObjectId(session['agency_id'])},
            {'$set': {
                'latitude': data['lat'],
                'longitude': data['lng'],
                'last_updated': datetime.now()
            }}
        )
        session['latitude'] = data['lat']
        session['longitude'] = data['lng']
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"[API ERROR] Location Update: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/emergencies')
def get_emergencies():
    try:
        emergencies = list(emergencies_collection.find({'status': 'pending'}).sort('created_at', -1))
        for emergency in emergencies:
            emergency['_id'] = str(emergency['_id'])
            severity = emergency.get('severity', 'low')
            if severity == 'high':
                emergency['severity_display'] = '🔴 High'
            elif severity == 'medium':
                emergency['severity_display'] = '🟡 Medium'
            else:
                emergency['severity_display'] = '🟢 Low'
        return jsonify(emergencies)
    except Exception as e:
        print(f"[API ERROR] Emergencies: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/emergency_details')
def get_all_emergency_details():
    if 'agency_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        lat = session.get('latitude', 20.5937)
        lng = session.get('longitude', 78.9629)

        emergencies = list(emergencies_collection.find({'status': 'pending'}).sort('created_at', -1))
        for emergency in emergencies:
            emergency['_id'] = str(emergency['_id'])
            elat = float(emergency.get('latitude', 0))
            elng = float(emergency.get('longitude', 0))

            # Haversine formula (meters)
            from math import radians, cos, sin, acos
            distance = 6371000 * acos(
                cos(radians(lat)) * cos(radians(elat)) *
                cos(radians(elng) - radians(lng)) +
                sin(radians(lat)) * sin(radians(elat))
            )
            emergency['distance'] = round(distance, 2)
        return jsonify(emergencies)
    except Exception as e:
        print(f"[ERROR] Emergency details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    if 'agency_id' not in session:
        return redirect(url_for('login'))

    role = session.get('role', 'agency')
    if role == 'ndrf':
        return redirect(url_for('ndrf_dashboard'))
    else:
        return render_template('dashboard.html')

@app.route('/api/agencies')
def get_agencies():
    if 'agency_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        agencies = list(agencies_collection.find({}, {'name':1, 'latitude':1, 'longitude':1, 'expertise':1}))
        for agency in agencies:
            agency['_id'] = str(agency['_id'])
        return jsonify(agencies)
    except Exception as e:
        print(f"[API ERROR] Agencies: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/delete_emergencies', methods=['POST'])
def delete_all_emergencies():
    if 'agency_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        emergencies_collection.delete_many({})
        return jsonify({'status': 'All emergencies deleted'})
    except Exception as e:
        print(f"[DELETE ERROR] Failed to delete emergencies: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/ndrf_dashboard')
def ndrf_dashboard():
    if 'agency_id' not in session or session.get('role') != 'ndrf':
        return redirect(url_for('login'))
    return render_template('ndrf_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
