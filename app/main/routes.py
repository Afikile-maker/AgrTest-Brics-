from firebase_admin import firestore
from flask import render_template, request, redirect, url_for, session, jsonify
from app.main import main_bp
from app.models.plant import Plant
from app.auth.utils import login_required
from openai import OpenAI  # Updated import

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
    db = firestore.client()
    plants_ref = db.collection('plants').where('user_id', '==', session['user']).stream()
    plants_data = []

    for plant in plants_ref:
        data = plant.to_dict()
        # Get real-time sensor data
        sensor_ref = db.collection('sensor_data').document(plant.id).get()
        sensor_data = sensor_ref.to_dict() if sensor_ref.exists else {}

        plants_data.append({
            'id': plant.id,
            'name': data.get('name'),
            'type': data.get('type'),
            'moisture': sensor_data.get('moisture', 0),
            'temperature': sensor_data.get('temperature', 0),
            'humidity': sensor_data.get('humidity', 0),
            'light': sensor_data.get('light', 0),
            'health_status': sensor_data.get('health_status', 'Unknown'),
            'last_updated': sensor_data.get('timestamp', 'No data')
        })

    return render_template('main/plants.html', plants=plants_data)


@main_bp.route('/statistics')
@login_required
def statistics():
    # Fetch data from Firebase
    db = firestore.client()
    sensor_ref = db.collection('sensor_data').where('user_id', '==', session['user']).stream()

    moisture_data = []
    temperature_data = []
    growth_data = []
    date_labels = []

    for doc in sensor_ref:
        data = doc.to_dict()
        moisture_data.append(data.get('moisture', 0))
        temperature_data.append(data.get('temperature', 0))
        growth_data.append(data.get('growth_rate', 0))
        date_labels.append(data.get('timestamp').strftime('%Y-%m-%d'))

    return render_template('main/statistics.html',
                           moisture_data=moisture_data,
                           temperature_data=temperature_data,
                           growth_data=growth_data,
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
