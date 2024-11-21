from flask import render_template, request, redirect, url_for, session
from app.main import main_bp
from app.models.plant import Plant
from app.auth.utils import login_required

@main_bp.route('/')
def home():
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    plants = Plant.get_user_plants(session['user'])
    return render_template('main/dashboard.html', plants=plants)

@main_bp.route('/add_plant', methods=['POST'])
@login_required
def add_plant():
    name = request.form['plant_name']
    type = request.form['plant_type']
    
    plant = Plant(name=name, type=type, user_id=session['user'])
    plant.save()
    
    return redirect(url_for('main.dashboard')) 