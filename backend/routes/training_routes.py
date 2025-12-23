#training_routes.py
from flask import Blueprint, request, jsonify
from services.training_service import TrainingService
from services.camera_service import CameraService
import threading

training_bp = Blueprint('training', __name__)

training_service = TrainingService()
camera_service = CameraService()

training_status = {
    'is_training': False,
    'progress': 0,
    'message': ''
}

@training_bp.route('/start', methods=['POST'])
def start_training():
    if training_status['is_training']:
        return jsonify({
            'success': False,
            'error': 'Training already in progress'
        })
    
    def train_callback(status):
        training_status['progress'] = status.get('progress', 0)
        training_status['message'] = status.get('status', '')
    
    def train_thread():
        training_status['is_training'] = True
        success, results = training_service.train_models(callback=train_callback)
        training_status['is_training'] = False
        training_status['results'] = results
    
    thread = threading.Thread(target=train_thread)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Training started'
    })

@training_bp.route('/status', methods=['GET'])
def get_training_status():
    return jsonify(training_status)

@training_bp.route('/collect/<camera_id>', methods=['POST'])
def collect_images(camera_id):
    data = request.json
    person_name = data.get('name')
    num_images = data.get('num_images', 20)
    interval = data.get('interval', 2)
    
    if not person_name:
        return jsonify({'error': 'Person name required'}), 400
    
    # Start collection in background
    def collect():
        count = training_service.auto_capture(
            camera_service, camera_id, person_name, 
            duration=num_images * interval, interval=interval
        )
        return count
    
    thread = threading.Thread(target=collect)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': f'Started collecting images for {person_name}'
    })

@training_bp.route('/people', methods=['GET'])
def get_people():
    people = training_service.get_people_list()
    return jsonify({'people': people})

@training_bp.route('/people/<name>', methods=['DELETE'])
def delete_person(name):
    success = training_service.delete_person(name)
    return jsonify({'success': success})

@training_bp.route('/capture-single/<camera_id>', methods=['POST'])
def capture_single(camera_id):
    """Capture single image for training"""
    data = request.json
    person_name = data.get('name')
    
    if not person_name:
        return jsonify({'error': 'Person name required'}), 400
    
    import cv2
    import os
    from config import Config
    
    # Get frame
    frame = camera_service.get_frame(camera_id)
    if frame is None:
        return jsonify({'error': 'Camera not active'}), 400
    
    # Detect face
    haar = cv2.CascadeClassifier(
        os.path.join(Config.HAARCASCADES_DIR, 'haarcascade_frontalface_default.xml')
    )
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = haar.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) == 0:
        return jsonify({'error': 'No face detected'}), 400
    
    # Save face
    x, y, w, h = faces[0]
    face = frame[y:y+h, x:x+w]
    
    person_dir = os.path.join(Config.TRAIN_DIR, person_name)
    os.makedirs(person_dir, exist_ok=True)
    
    existing = len(os.listdir(person_dir))
    filename = f"{person_name}_{existing:03d}.jpg"
    filepath = os.path.join(person_dir, filename)
    cv2.imwrite(filepath, face)
    
    return jsonify({
        'success': True,
        'path': filepath,
        'count': existing + 1
    })