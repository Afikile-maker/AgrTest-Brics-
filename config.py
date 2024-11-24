import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    FIREBASE_CONFIG = {
        "apiKey": "AIzaSyBYAuhIUbAK7ACty7PdWvHOBbAe4TPDf7g",
        "authDomain": "agritest-10701.firebaseapp.com",
        "databaseURL": "https://agritest-10701-default-rtdb.firebaseio.com",
        "projectId": "agritest-10701",
        "storageBucket": "agritest-10701.firebasestorage.app",
        "messagingSenderId": "1055187803843",
        "appId": "1:1055187803843:web:2886440c136f8e4953cc76",
        "measurementId": "G-VWQFRLBGTC"
    }
    # Get Firebase credentials path from environment variable
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH')
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

