from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import hashlib
import os
from datetime import datetime, timezone # <--- NEW: Import timezone

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# MongoDB Configuration (Localhost)
# IMPORTANT: For production, replace "mongodb://localhost:27017/" with your MongoDB Atlas URI
# It's better to load this from an environment variable (e.g., os.environ.get('MONGO_URI'))
client = MongoClient("mongodb+srv://zero2omegadev:ayushkunal456@cluster0.5rnijnb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0") # Consider using os.environ.get('MONGO_URI') here
db = client['rescue_db']
agencies_collection = db['agencies']
emergencies_collection = db['emergencies']
resources_collection = db['resources']

def hash_password(password):
    """Hashes a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

# Temporary debug route (remove in production)
@app.route('/debug/emergencies')
def debug_emergencies():
    """Returns all emergencies for debugging purposes."""
    try:
        emergencies = list(emergencies_collection.find())
        for emergency in emergencies:
            emergency['_id'] = str(emergency['_id'])
        return jsonify({
            'count': len(emergencies),
            'emergencies': emergencies
        })
    except Exception as e:
        print(f"[DEBUG ERROR] Failed to fetch debug emergencies: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    """Renders the main index page."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if request.method == 'POST':
        email = request.form['email']
        password = hash_password(request.form['password'])

        try:
            agency = agencies_collection.find_one({'email': email})
            if agency and agency['password'] == password:
                session['agency_id'] = str(agency['_id'])
                session['role'] = agency.get('role', 'agency')
                # Store current location in session (default if not set)
                session['latitude'] = agency.get('latitude', 20.5937)
                session['longitude'] = agency.get('longitude', 78.9629)
                return redirect(url_for('dashboard'))
            return render_template('login.html', error="Invalid credentials")
        except Exception as e:
            print(f"[LOGIN ERROR] {str(e)}")
            return render_template('login.html', error="Database error during login")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles new agency registration."""
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
                'latitude': 20.5937, # Default latitude for new registrations
                'longitude': 78.9629, # Default longitude for new registrations
                'last_updated': None,
                'role': 'agency', # Default role for new registrations
                'verified': False,
                'agency_type': 'local'
            }
            result = agencies_collection.insert_one(agency_data)
            session['agency_id'] = str(result.inserted_id)
            session['role'] = 'agency'
            session['latitude'] = agency_data['latitude']
            session['longitude'] = agency_data['longitude']
            return redirect(url_for('dashboard'))
        except Exception as e:
            print(f"[REGISTER ERROR] {str(e)}")
            return render_template('register.html', error=f"Registration failed: {str(e)}")
    return render_template('register.html')

@app.route('/emergency_map')
def emergency_map():
    """Renders the emergency map page, requires login."""
    if 'agency_id' not in session:
        return redirect(url_for('login'))
    return render_template('emergency_map.html')

@app.route('/api/report_emergency', methods=['POST'])
def report_emergency():
    """API endpoint to report a new emergency."""
    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    description = data.get('description')
    tag = data.get('tag')
    severity = data.get('severity', 'low')

    # Basic validation
    if not all([lat, lng, description, tag]):
        return jsonify({'error': 'Missing required emergency data'}), 400

    try:
        emergency_data = {
            'latitude': lat,
            'longitude': lng,
            'description': description,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc), # <--- CHANGED: Use timezone-aware UTC datetime
            'reported_by': 'public',
            'tag': tag,
            'severity': severity
        }
        emergencies_collection.insert_one(emergency_data)
        return jsonify({'message': 'Emergency reported successfully'}), 200
    except Exception as e:
        print(f"[API ERROR] Report Emergency: {e}")
        return jsonify({'error': 'Failed to report emergency'}), 500

@app.route('/client')
def client_portal():
    """Renders the client portal page."""
    return render_template('client.html')

@app.route('/api/update_location', methods=['POST'])
def update_location():
    """API endpoint for agencies to update their location."""
    if 'agency_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    try:
        # Ensure lat and lng are floats
        lat = float(data['lat'])
        lng = float(data['lng'])

        agencies_collection.update_one(
            {'_id': ObjectId(session['agency_id'])},
            {'$set': {
                'latitude': lat,
                'longitude': lng,
                'last_updated': datetime.now()
            }}
        )
        # Update session with new location
        session['latitude'] = lat
        session['longitude'] = lng
        return jsonify({'status': 'success'})
    except ValueError:
        return jsonify({'error': 'Invalid latitude or longitude format'}), 400
    except Exception as e:
        print(f"[API ERROR] Location Update: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/emergencies')
def get_emergencies():
    """API endpoint to get pending emergencies for the dashboard list."""
    # No session check here, as it's used by dashboard.html which already has a redirect
    try:
        emergencies = list(emergencies_collection.find({'status': 'pending'}).sort('created_at', -1))
        for emergency in emergencies:
            emergency['_id'] = str(emergency['_id'])
            # Add display text for severity
            severity = emergency.get('severity', 'low')
            if severity == 'high':
                emergency['severity_display'] = '🔴 High'
            elif severity == 'medium':
                emergency['severity_display'] = '🟡 Medium'
            else:
                emergency['severity_display'] = '🟢 Low'
        return jsonify(emergencies)
    except Exception as e:
        print(f"[API ERROR] Get Emergencies: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/emergency_details')
def get_all_emergency_details():
    """API endpoint to get all pending emergencies with distance for map display."""
    if 'agency_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get agency's current location from session
        lat = session.get('latitude')
        lng = session.get('longitude')

        # If session location is not set, try to fetch from DB or use default
        if lat is None or lng is None:
            agency = agencies_collection.find_one({'_id': ObjectId(session['agency_id'])})
            if agency:
                lat = agency.get('latitude', 20.5937)
                lng = agency.get('longitude', 78.9629)
            else:
                lat = 20.5937
                lng = 78.9629
            session['latitude'] = lat
            session['longitude'] = lng

        emergencies = list(emergencies_collection.find({'status': 'pending'}).sort('created_at', -1))
        for emergency in emergencies:
            emergency['_id'] = str(emergency['_id'])
            elat = float(emergency.get('latitude', 0))
            elng = float(emergency.get('longitude', 0))

            # Haversine formula (meters) for distance calculation
            from math import radians, cos, sin, acos # Ensure these are imported for Haversine
            distance = 6371000 * acos(
                cos(radians(lat)) * cos(radians(elat)) *
                cos(radians(elng) - radians(lng)) +
                sin(radians(lat)) * sin(radians(elat))
            )
            emergency['distance'] = round(distance, 2)

            # Add display text for severity (same as /api/emergencies)
            severity = emergency.get('severity', 'low')
            if severity == 'high':
                emergency['severity_display'] = '🔴 High'
            elif severity == 'medium':
                emergency['severity_display'] = '🟡 Medium'
            else:
                emergency['severity_display'] = '🟢 Low'

        return jsonify(emergencies)
    except Exception as e:
        print(f"[ERROR] Emergency details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    """Renders the dashboard page, redirects based on role."""
    if 'agency_id' not in session:
        return redirect(url_for('login'))

    role = session.get('role', 'agency')
    if role == 'ndrf':
        return redirect(url_for('ndrf_dashboard'))
    else:
        return render_template('dashboard.html')

@app.route('/api/agencies')
def get_agencies():
    """API endpoint to get agency details (for map display)."""
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

# New route to render the NDRF confirmation page
@app.route('/confirm_ndrf_delete', methods=['GET'])
def confirm_ndrf_delete_page():
    """Renders the page to confirm NDRF credentials before deletion."""
    if 'agency_id' not in session:
        return redirect(url_for('login'))
    # Optional: You might want to check if the current user is an NDRF here too
    # if session.get('role') != 'ndrf':
    #     return jsonify({'error': 'Access Denied'}), 403
    return render_template('confirm_ndrf_delete.html')


@app.route('/api/delete_emergencies', methods=['POST'])
def delete_all_emergencies():
    """
    API endpoint to delete all emergencies.
    Requires NDRF email and password from form data for authentication.
    """
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    try:
        hashed_password = hash_password(password)
        ndrf_agency = agencies_collection.find_one({
            'email': email,
            'password': hashed_password
        })

        if not ndrf_agency:
            return jsonify({'error': 'Invalid email or password'}), 401

        if ndrf_agency.get('role') != 'ndrf':
            return jsonify({'error': 'Only NDRF agencies can perform this action'}), 403

        # If authenticated as NDRF, proceed with deletion
        result = emergencies_collection.delete_many({})
        print(f"[DELETE SUCCESS] Deleted {result.deleted_count} emergencies by NDRF: {email}")
        # Return a success message that the frontend can interpret for redirection
        return jsonify({'status': f'Successfully deleted {result.deleted_count} emergencies.'}), 200

    except Exception as e:
        print(f"[DELETE ERROR] Failed to delete emergencies: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/logout')
def logout():
    """Logs out the current user."""
    session.clear()
    return redirect(url_for('index'))

@app.route('/ndrf_dashboard')
def ndrf_dashboard():
    """Renders the NDRF specific dashboard."""
    if 'agency_id' not in session or session.get('role') != 'ndrf':
        return redirect(url_for('login'))
    return render_template('ndrf_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
