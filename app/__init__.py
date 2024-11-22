from flask import Flask
from firebase_admin import credentials, initialize_app
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Firebase
    cred = credentials.Certificate(app.config['FIREBASE_CREDENTIALS_PATH'])
    firebase_app = initialize_app(cred)

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    # app/__init__.py
    from .camera import camera_bp
    app.register_blueprint(camera_bp, url_prefix='/camera')

    return app
