from firebase_admin import firestore
from flask import render_template, request, redirect, url_for, session, jsonify, Response
from app.main import main_bp
from app.models.plant import Plant
from app.auth.utils import login_required
from openai import OpenAI
from firebase_admin import db
from datetime import datetime, timedelta
import requests
import cv2
import numpy as np
import pandas as pd
import csv
from io import StringIO
from sklearn.linear_model import LinearRegression
from datetime import datetime
from flask import Blueprint
import os
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI()

# Add this function before your routes
def format_datetime(value):
    """Format a datetime object or timestamp string."""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            try:
                value = datetime.fromtimestamp(int(value))
            except ValueError:
                return value
    return value.strftime('%Y-%m-%d %H:%M')

# Add this after creating the Blueprint
main_bp.add_app_template_filter(format_datetime, 'datetime')

def timeago(value):
    """Format a timestamp to a human-readable time ago string."""
    if not value:
        return ''

    # Convert string timestamp to datetime if needed
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            try:
                value = datetime.fromtimestamp(int(value))
            except ValueError:
                return value

    now = datetime.now(pytz.UTC)
    if isinstance(value, datetime) and value.tzinfo is None:
        value = pytz.UTC.localize(value)

    diff = now - value

    if diff.days > 365:
        years = diff.days // 365
        return f"{years}y ago"
    if diff.days > 30:
        months = diff.days // 30
        return f"{months}mo ago"
    if diff.days > 0:
        return f"{diff.days}d ago"
    if diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    if diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    return "just now"

# Register the filter with the Blueprint
main_bp.add_app_template_filter(timeago, 'timeago')

@main_bp.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('main/landing.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    plants = Plant.get_user_plants(session['user'])
    return render_template('main/dashboard.html', plants=plants)


@main_bp.route('/plants')
@login_required
def plants():
    # Get reference to sensor_data node
    ref = db.reference('sensor_data')
    sensor_readings = ref.get()
    
    # Process the latest readings
    latest_readings = {
        'soil_moisture': '0',
        'temperature': '0',
        'humidity': '0',
        'ultrasonic': '0'
    }
    
    if sensor_readings:
        for reading_id, data in sensor_readings.items():
            sensor_type = data.get('sensor', '')
            value = data.get('value', '0')
            
            if 'Soil Moisture' in sensor_type:
                latest_readings['soil_moisture'] = value
            elif 'Temperature' in sensor_type:
                latest_readings['temperature'] = value
            elif 'Humidity' in sensor_type:
                latest_readings['humidity'] = value
            elif 'Ultrasonic Distance' in sensor_type:
                latest_readings['ultrasonic'] = value

    # Mock plant data structure with real sensor values
    plants = [
        {
            'id': '1',
            'name': 'Field Section A',
            'type': 'Potato',
            'moisture': latest_readings['soil_moisture'],
            'temperature': latest_readings['temperature'],
            'humidity': latest_readings['humidity'],
            'light': latest_readings['ultrasonic'],
            'health_status': get_health_status(latest_readings),
            'last_updated': 'Just now'
        }
        # Add more fields as needed
    ]
    
    return render_template('main/plants.html', plants=plants)

def get_health_status(readings):
    # Simple logic to determine plant health based on sensor readings
    try:
        moisture = float(readings['soil_moisture'])
        temp = float(readings['temperature'])
        humidity = float(readings['humidity'])
        
        if (20 <= moisture <= 60 and 
            20 <= temp <= 30 and 
            40 <= humidity <= 80):
            return 'Healthy'
        elif (10 <= moisture <= 70 and 
              15 <= temp <= 35 and 
              30 <= humidity <= 90):
            return 'Warning'
        else:
            return 'Critical'
    except:
        return 'Unknown'


@main_bp.route('/statistics')
@login_required
def statistics():
    # Get reference to sensor_data node
    ref = db.reference('sensor_data')
    sensor_readings = ref.get()
    
    # Initialize data structures for historical data
    historical_data = {
        'moisture': [],
        'temperature': [],
        'humidity': [],
        'dates': []
    }
    
    if sensor_readings:
        # Sort readings by timestamp
        sorted_readings = sorted(
            sensor_readings.items(),
            key=lambda x: x[1].get('timestamp', ''),
            reverse=True
        )
        
        # Group readings by date
        readings_by_date = {}
        for _, reading in sorted_readings:
            timestamp = reading.get('timestamp', '')
            date = timestamp.split('T')[0]
            
            if date not in readings_by_date:
                readings_by_date[date] = {
                    'moisture': [],
                    'temperature': [],
                    'humidity': []
                }
            
            # Handle case where value might be a dict or string
            value_data = reading.get('value', {})
            if isinstance(value_data, dict):
                value = float(value_data.get('value', 0))
            else:
                value = float(value_data)
                
            sensor_type = reading.get('sensor', '')
            
            if 'Soil Moisture' in sensor_type:
                readings_by_date[date]['moisture'].append(value)
            elif 'Temperature' in sensor_type:
                readings_by_date[date]['temperature'].append(value)
            elif 'Humidity' in sensor_type:
                readings_by_date[date]['humidity'].append(value)
        
        # Calculate daily averages
        for date, values in readings_by_date.items():
            historical_data['dates'].append(date)
            historical_data['moisture'].append(
                sum(values['moisture']) / len(values['moisture']) if values['moisture'] else 0
            )
            historical_data['temperature'].append(
                sum(values['temperature']) / len(values['temperature']) if values['temperature'] else 0
            )
            historical_data['humidity'].append(
                sum(values['humidity']) / len(values['humidity']) if values['humidity'] else 0
            )
    
    return render_template('main/statistics.html',
                         moisture_data=historical_data['moisture'],
                         temperature_data=historical_data['temperature'],
                         growth_data=historical_data['humidity'],
                         date_labels=historical_data['dates'],
                         historical_data=historical_data)


@main_bp.route('/settings')
@login_required
def settings():
    return render_template('main/settings.html')


@main_bp.route('/chatbot')
@login_required
def chatbot():
    return render_template('main/chatbot.html')


@main_bp.route('/add_plant', methods=['POST'])
@login_required
def add_plant():
    name = request.form['plant_name']
    type = request.form['plant_type']
    plant = Plant(name=name, type=type, user_id=session['user'])
    plant.save()
    return redirect(url_for('main.dashboard'))


@main_bp.route('/chatbot/send', methods=['POST'])
@login_required
def chatbot_send():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400
            
        user_message = data.get('message')
        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        print(f"Received message: {user_message}")  # Debug log
        
        # Initialize conversation with context about potato growing
        messages = [
            {
                "role": "system", 
                "content": "You are a potato growing expert. Provide helpful advice about growing potatoes, dealing with common issues, and maximizing yield."
            },
            {"role": "user", "content": user_message}
        ]
        
        print("Sending request to OpenAI...")  # Debug log
        
        # Get response from OpenAI using GPT-4 (updated API call)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        bot_response = response.choices[0].message.content
        print(f"Received response: {bot_response}")  # Debug log
        
        return jsonify({"response": bot_response})
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@main_bp.route('/alerts/settings', methods=['GET', 'POST'])
@login_required
def alert_settings():
    if request.method == 'POST':
        thresholds = {
            'moisture_min': request.form.get('moisture_min'),
            'moisture_max': request.form.get('moisture_max'),
            'temperature_min': request.form.get('temperature_min'),
            'temperature_max': request.form.get('temperature_max'),
            'humidity_min': request.form.get('humidity_min'),
            'humidity_max': request.form.get('humidity_max')
        }
        # Store in Firebase under user's settings
        db.reference(f'users/{session["user"]}/alert_thresholds').set(thresholds)
    return render_template('main/alert_settings.html')

@main_bp.route('/weather')
@login_required
def weather():
    API_KEY = os.getenv('OPENWEATHER_API_KEY')  # Get API key from environment variable
    
    if not API_KEY:
        return render_template('main/weather.html', 
                             forecast={'list': [], 'city': {'name': 'Unknown'}},
                             error="OpenWeatherMap API key not configured")
    
    lat = request.args.get('lat', '0')
    lon = request.args.get('lon', '0')
    
    url = f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        forecast = response.json()
        
        return render_template('main/weather.html', forecast=forecast)
    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return render_template('main/weather.html', 
                             forecast={'list': [], 'city': {'name': 'Unknown'}},
                             error="Unable to fetch weather data")

@main_bp.route('/detect-disease', methods=['POST'])
@login_required
def detect_disease():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
        
    image = request.files['image']
    img = cv2.imdecode(np.frombuffer(image.read(), np.uint8), cv2.IMREAD_COLOR)
    
    # Basic image processing for disease detection
    # Convert to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Define color ranges for common plant diseases
    # Yellow/brown spots (common in many plant diseases)
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([30, 255, 255])
    
    # Dark spots (potential fungal infections)
    lower_dark = np.array([0, 0, 0])
    upper_dark = np.array([180, 255, 30])
    
    # Create masks
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    dark_mask = cv2.inRange(hsv, lower_dark, upper_dark)
    
    # Calculate percentage of affected areas
    yellow_percent = (np.sum(yellow_mask > 0) / yellow_mask.size) * 100
    dark_percent = (np.sum(dark_mask > 0) / dark_mask.size) * 100
    
    # Simple decision logic
    diagnosis = {
        'status': 'healthy',
        'confidence': 0,
        'details': []
    }
    
    if yellow_percent > 5:
        diagnosis['status'] = 'warning'
        diagnosis['details'].append(f'Detected {yellow_percent:.1f}% yellow/brown spots - possible nutrient deficiency')
        diagnosis['confidence'] = min(yellow_percent * 2, 100)
    
    if dark_percent > 10:
        diagnosis['status'] = 'danger'
        diagnosis['details'].append(f'Detected {dark_percent:.1f}% dark spots - possible fungal infection')
        diagnosis['confidence'] = min(dark_percent * 2, 100)
    
    return jsonify(diagnosis)

@main_bp.route('/irrigation/control', methods=['POST'])
@login_required
def control_irrigation():
    action = request.json.get('action')
    zone = request.json.get('zone')
    
    if action == 'start':
        # Send command to IoT device
        db.reference(f'irrigation_control/{zone}').set({
            'status': 'active',
            'start_time': datetime.now().isoformat(),
            'duration': request.json.get('duration', 30)  # minutes
        })
    elif action == 'stop':
        db.reference(f'irrigation_control/{zone}').set({
            'status': 'inactive'
        })
    
    return jsonify({'status': 'success'})

def get_historical_data():
    """Fetch historical sensor data from Firebase"""
    ref = db.reference('sensor_data')
    sensor_readings = ref.get()
    
    if not sensor_readings:
        return []
    
    historical_data = []
    for reading_id, data in sensor_readings.items():
        historical_data.append({
            'timestamp': data.get('timestamp', ''),
            'sensor': data.get('sensor', ''),
            'value': float(data.get('value', 0))
        })
    
    # Sort by timestamp
    historical_data.sort(key=lambda x: x['timestamp'])
    return historical_data

def get_current_conditions():
    """Get current sensor readings"""
    ref = db.reference('sensor_data')
    latest_readings = ref.order_by_child('timestamp').limit_to_last(1).get()
    
    if not latest_readings:
        return [0, 0, 0]  # Default values if no readings
    
    # Process the latest reading
    current_conditions = {
        'moisture': 0,
        'temperature': 0,
        'humidity': 0
    }
    
    for reading_id, data in latest_readings.items():
        sensor_type = data.get('sensor', '')
        value = float(data.get('value', 0))
        
        if 'Soil Moisture' in sensor_type:
            current_conditions['moisture'] = value
        elif 'Temperature' in sensor_type:
            current_conditions['temperature'] = value
        elif 'Humidity' in sensor_type:
            current_conditions['humidity'] = value
    
    return [
        current_conditions['moisture'],
        current_conditions['temperature'],
        current_conditions['humidity']
    ]

@main_bp.route('/predictions')
@login_required
def get_predictions():
    try:
        # Fetch historical data
        historical_data = get_historical_data()
        
        if not historical_data:
            return render_template('main/predictions.html', 
                                error="No historical data available")
        
        # Prepare data for model
        df = pd.DataFrame(historical_data)
        df_pivot = df.pivot(columns='sensor', values='value')
        
        # Ensure we have all required columns
        required_columns = ['Soil Moisture', 'Temperature', 'Humidity']
        for col in required_columns:
            if col not in df_pivot.columns:
                df_pivot[col] = 0
        
        # Create target variable (simple example using moisture as yield indicator)
        df_pivot['yield'] = df_pivot['Soil Moisture'].rolling(window=3).mean()
        
        # Drop rows with NaN values
        df_pivot = df_pivot.dropna()
        
        if len(df_pivot) < 2:
            return render_template('main/predictions.html', 
                                error="Insufficient data for prediction")
        
        # Create and train model
        model = LinearRegression()
        X = df_pivot[required_columns]
        y = df_pivot['yield']
        model.fit(X, y)
        
        # Make prediction for current conditions
        current = get_current_conditions()
        predicted_yield = model.predict([current])[0]
        
        return render_template('main/predictions.html', 
                             predicted_yield=round(predicted_yield, 2))
                             
    except Exception as e:
        return render_template('main/predictions.html', 
                             error=f"Error making prediction: {str(e)}")

@main_bp.route('/timelapse')
@login_required
def timelapse():
    # Fetch all plant images from storage
    plant_images = db.reference(f'plant_images/{session["user"]}').get()
    
    # Sort by timestamp
    sorted_images = sorted(plant_images.items(), 
                         key=lambda x: x[1]['timestamp'])
    
    return render_template('main/timelapse.html', 
                         images=sorted_images)

@main_bp.route('/community')
@login_required
def community():
    # Fetch community posts
    posts = db.reference('community_posts').get() or []  # Initialize empty list if None
    
    # Convert posts dictionary to list if it exists
    if isinstance(posts, dict):
        posts = [
            {
                'id': post_id,
                **post_data,
                'comments': post_data.get('comments', [])
                if isinstance(post_data.get('comments'), list)
                else []
            }
            for post_id, post_data in posts.items()
        ]
    
    # Get user's following list
    following = db.reference(f'users/{session["user"]}/following').get() or []
    
    # Add some sample posts if none exist
    if not posts:
        posts = [
            {
                'id': '1',
                'user_id': 'system',
                'user_name': 'System',
                'user_avatar': '/static/images/default-avatar.png',
                'content': 'Welcome to the farming community! Share your experiences and learn from others.',
                'timestamp': datetime.now().isoformat(),
                'likes': 0,
                'comments': []
            }
        ]
    
    return render_template('main/community.html', 
                         posts=posts,
                         following=following)

@main_bp.route('/share-tips', methods=['POST'])
@login_required
def share_tips():
    # Get user info
    user_ref = db.reference(f'users/{session["user"]}').get()
    user_name = user_ref.get('name', 'Anonymous') if user_ref else 'Anonymous'
    
    tip = {
        'user_id': session['user'],
        'user_name': user_name,
        'user_avatar': user_ref.get('avatar', '/static/images/default-avatar.png') if user_ref else '/static/images/default-avatar.png',
        'content': request.form.get('content'),
        'timestamp': datetime.now().isoformat(),
        'likes': 0,
        'comments': []
    }
    
    # Create posts node if it doesn't exist
    posts_ref = db.reference('community_posts')
    posts_ref.push(tip)
    
    return redirect(url_for('main.community'))

@main_bp.route('/export-data')
@login_required
def export_data():
    # Fetch all sensor data
    sensor_data = get_historical_data()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Sensor', 'Value'])
    
    for reading in sensor_data:
        writer.writerow([
            reading['timestamp'],
            reading['sensor'],
            reading['value']
        ])
    
    # Return CSV file
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=sensor_data.csv'}
    )