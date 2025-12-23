#detection_routes.py
from flask import Blueprint, request, jsonify, send_file
from database import get_db
from services.storage_service import StorageService
import uuid
import os

detection_bp = Blueprint('detection', __name__)
storage_service = StorageService()

@detection_bp.route('/intruders/<camera_id>', methods=['GET'])
def get_intruders(camera_id):
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM intruder_logs 
        WHERE camera_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ? OFFSET ?
    ''', (camera_id, limit, offset))
    
    logs = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'logs': [dict(log) for log in logs],
        'count': len(logs)
    })

@detection_bp.route('/intruders/<camera_id>', methods=['POST'])
def add_intruder_log(camera_id):
    data = request.json
    
    conn = get_db()
    cursor = conn.cursor()
    
    log_id = str(uuid.uuid4())
    
    cursor.execute('''
        INSERT INTO intruder_logs 
        (id, camera_id, image_path, confidence, severity, type, details, weapon_detected, mask_detected)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        log_id,
        camera_id,
        data.get('image_path'),
        data.get('confidence', 0),
        data.get('severity', 5),
        data.get('type', 'unknown_person'),
        data.get('details', ''),
        data.get('weapon_detected', 0),
        data.get('mask_detected', 0)
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'log_id': log_id
    })

@detection_bp.route('/intruders/image/<path:filename>', methods=['GET'])
def get_intruder_image(filename):
    from config import Config
    filepath = os.path.join(Config.INTRUDERS_DIR, filename)
    
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='image/jpeg')
    
    return jsonify({'error': 'Image not found'}), 404

@detection_bp.route('/intruders/<log_id>/resolve', methods=['POST'])
def resolve_intruder(log_id):
    conn = get_db()
    cursor = conn.cursor()
    
    from datetime import datetime
    cursor.execute('''
        UPDATE intruder_logs 
        SET is_resolved = 1, resolved_at = ?
        WHERE id = ?
    ''', (datetime.now(), log_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@detection_bp.route('/faces/<camera_id>', methods=['GET'])
def get_known_faces(camera_id):
    # Get user_id from camera_id
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE camera_id = ?', (camera_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'faces': []})
    
    cursor.execute('''
        SELECT * FROM known_faces 
        WHERE user_id = ?
        ORDER BY name
    ''', (user['id'],))
    
    faces = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'faces': [dict(f) for f in faces]
    })

@detection_bp.route('/faces/<camera_id>', methods=['POST'])
def add_known_face(camera_id):
    data = request.json
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE camera_id = ?', (camera_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Invalid camera ID'}), 400
    
    face_id = str(uuid.uuid4())
    from config import Config
    folder_path = os.path.join(Config.TRAIN_DIR, data['name'])
    
    cursor.execute('''
        INSERT INTO known_faces (id, user_id, name, folder_path, is_authorized)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        face_id,
        user['id'],
        data['name'],
        folder_path,
        data.get('is_authorized', 1)
    ))
    
    conn.commit()
    conn.close()
    
    # Create folder
    os.makedirs(folder_path, exist_ok=True)
    
    return jsonify({
        'success': True,
        'face_id': face_id
    })

@detection_bp.route('/faces/<face_id>', methods=['DELETE'])
def delete_known_face(face_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT folder_path FROM known_faces WHERE id = ?', (face_id,))
    face = cursor.fetchone()
    
    if face:
        # Delete folder
        import shutil
        if os.path.exists(face['folder_path']):
            shutil.rmtree(face['folder_path'])
        
        cursor.execute('DELETE FROM known_faces WHERE id = ?', (face_id,))
        conn.commit()
    
    conn.close()
    
    return jsonify({'success': True})

@detection_bp.route('/stats/<camera_id>', methods=['GET'])
def get_stats(camera_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user info
    cursor.execute('SELECT id FROM users WHERE camera_id = ?', (camera_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Invalid camera ID'}), 400
    
    # Count intruders today
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT COUNT(*) as count FROM intruder_logs 
        WHERE camera_id = ? AND date(timestamp) = ?
    ''', (camera_id, today))
    alerts_today = cursor.fetchone()['count']
    
    # Count known faces
    cursor.execute('SELECT COUNT(*) as count FROM known_faces WHERE user_id = ?', (user['id'],))
    known_faces = cursor.fetchone()['count']
    
    # Recent alerts
    cursor.execute('''
        SELECT * FROM intruder_logs 
        WHERE camera_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 5
    ''', (camera_id,))
    recent_alerts = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'stats': {
            'alertsToday': alerts_today,
            'totalVisitors': known_faces,
            'uptime': 99.8,
            'modelsActive': 8,
            'totalIntruders': 0
        },
        'recentAlerts': [dict(a) for a in recent_alerts]
    })

@detection_bp.route('/storage/stats', methods=['GET'])
def get_storage_stats():
    stats = storage_service.get_storage_stats()
    return jsonify(stats)

@detection_bp.route('/storage/cleanup', methods=['POST'])
def cleanup_storage():
    deleted = storage_service.cleanup_old_files()
    return jsonify({
        'success': True,
        'deleted_count': deleted
    })