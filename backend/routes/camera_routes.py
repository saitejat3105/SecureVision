#camera_routes.py
from flask import Blueprint, Response, request, jsonify
from services.camera_service import CameraService
from services.night_vision import NightVisionService

camera_bp = Blueprint('camera', __name__)

# Initialize services
camera_service = CameraService()
night_vision = NightVisionService()

@camera_bp.route('/start/<camera_id>', methods=['POST'])
def start_camera(camera_id):
    device_index = request.json.get('device_index', 0) if request.json else 0
    success = camera_service.start_camera(camera_id, device_index)
    
    return jsonify({
        'success': success,
        'camera_id': camera_id,
        'message': 'Camera started' if success else 'Failed to start camera'
    })

@camera_bp.route('/stop/<camera_id>', methods=['POST'])
def stop_camera(camera_id):
    camera_service.stop_camera(camera_id)
    return jsonify({
        'success': True,
        'message': 'Camera stopped'
    })

@camera_bp.route('/feed/<camera_id>')
def video_feed(camera_id):
    return Response(
        camera_service.generate_frames(camera_id),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@camera_bp.route('/status/<camera_id>', methods=['GET'])
def camera_status(camera_id):
    status = camera_service.get_status(camera_id)
    return jsonify(status)

@camera_bp.route('/night-mode/<camera_id>', methods=['POST'])
def set_night_mode(camera_id):
    enabled = request.json.get('enabled', False)
    camera_service.set_night_mode(camera_id, enabled)
    
    return jsonify({
        'success': True,
        'night_mode': enabled
    })

@camera_bp.route('/capture/<camera_id>', methods=['POST'])
def capture_image(camera_id):
    frame = camera_service.capture_image(camera_id)
    
    if frame is not None:
        import cv2
        import os
        from datetime import datetime
        from config import Config
        
        filename = f"capture_{camera_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(Config.DATA_DIR, filename)
        cv2.imwrite(filepath, frame)
        
        return jsonify({
            'success': True,
            'path': filepath,
            'filename': filename
        })
    
    return jsonify({
        'success': False,
        'error': 'Could not capture image'
    }), 500