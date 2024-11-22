# app/camera/routes.py
from flask import Response
from . import camera_bp
from .camera import Camera

def gen_frames(camera):
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@camera_bp.route('/video_feed')
def video_feed():
    return Response(gen_frames(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
