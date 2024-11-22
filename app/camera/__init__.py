# app/camera/__init__.py
from flask import Blueprint

camera_bp = Blueprint('camera', __name__)

from . import routes
