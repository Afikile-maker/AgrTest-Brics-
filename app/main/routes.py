from firebase_admin import firestore
from flask import render_template, request, redirect, url_for, session, jsonify
from app.main import main_bp
from app.models.plant import Plant
from app.auth.utils import login_required
from openai import OpenAI  # Updated import
from firebase_admin import db
from datetime import datetime, timedelta

# Initialize OpenAI client
client = OpenAI()

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
    
    # Initialize data arrays
    moisture_data = []
    temperature_data = []
    humidity_data = []
    date_labels = []
    
    if sensor_readings:
        # Sort readings by timestamp
        sorted_readings = sorted(
            sensor_readings.items(),
            key=lambda x: x[1].get('timestamp', ''),
            reverse=True
        )[:7]  # Get last 7 days of readings
        
        # Process each type of sensor reading
        for _, reading in sorted_readings:
            timestamp = reading.get('timestamp', '')
            date_labels.append(timestamp.split('T')[0])  # Get just the date part
            
            sensor_type = reading.get('sensor', '')
            value = float(reading.get('value', 0))
            
            if 'Soil Moisture' in sensor_type:
                moisture_data.append(value)
            elif 'Temperature' in sensor_type:
                temperature_data.append(value)
            elif 'Humidity' in sensor_type:
                humidity_data.append(value)
    
    # Reverse the arrays so oldest data comes first
    moisture_data.reverse()
    temperature_data.reverse()
    humidity_data.reverse()
    date_labels.reverse()
    
    return render_template('main/statistics.html',
                         moisture_data=moisture_data,
                         temperature_data=temperature_data,
                         growth_data=humidity_data,  # Using humidity as growth indicator for now
                         date_labels=date_labels)


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
