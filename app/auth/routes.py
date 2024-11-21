from flask import render_template, request, redirect, url_for, session, flash
from firebase_admin import auth, firestore
from datetime import datetime
from app.auth import auth_bp
from app.auth.utils import login_required

db = firestore.client()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.get_user_by_email(email)
            session['user'] = user.uid
            session['email'] = email
            return redirect(url_for('main.dashboard'))
        except:
            flash('Invalid credentials', 'error')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        
        try:
            # Create user in Firebase Auth
            user = auth.create_user(
                email=email,
                password=password,
                display_name=name
            )
            
            # Store additional user data in Firestore
            db.collection('users').document(user.uid).set({
                'name': name,
                'email': email,
                'created_at': datetime.now()
            })
            
            flash('Registration successful!', 'success')
            return redirect(url_for('auth.login'))
            
        except auth.EmailAlreadyExistsError:
            flash('Email already exists', 'error')
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
            
    return render_template('auth/register.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login')) 