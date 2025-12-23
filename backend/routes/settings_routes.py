#settings_routes.py
from flask import Blueprint, request, jsonify
from database import get_db

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/<camera_id>', methods=['GET'])
def get_settings(camera_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE camera_id = ?', (camera_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Invalid camera ID'}), 400
    
    cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user['id'],))
    settings = cursor.fetchone()
    
    conn.close()
    
    if settings:
        return jsonify(dict(settings))
    
    return jsonify({})

@settings_bp.route('/<camera_id>', methods=['PUT'])
def update_settings(camera_id):
    data = request.json
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE camera_id = ?', (camera_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Invalid camera ID'}), 400
    
    # Build update query dynamically
    allowed_fields = [
        'do_not_disturb', 'dnd_start_hour', 'dnd_end_hour',
        'camera_enabled', 'email_alerts', 'sound_alerts',
        'auto_arm', 'arm_start_hour', 'arm_end_hour',
        'sensitivity', 'night_mode_auto', 'alert_on_unknown',
        'alert_on_weapon', 'decoy_voice'
    ]
    
    updates = []
    values = []
    
    for field in allowed_fields:
        if field in data:
            updates.append(f"{field} = ?")
            values.append(data[field])
    
    if updates:
        values.append(user['id'])
        query = f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    
    return jsonify({'success': True})

@settings_bp.route('/<camera_id>/dnd', methods=['POST'])
def toggle_dnd(camera_id):
    enabled = request.json.get('enabled', False)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE camera_id = ?', (camera_id,))
    user = cursor.fetchone()
    
    if user:
        cursor.execute('''
            UPDATE user_settings SET do_not_disturb = ? WHERE user_id = ?
        ''', (1 if enabled else 0, user['id']))
        conn.commit()
    
    conn.close()
    
    return jsonify({'success': True, 'do_not_disturb': enabled})

@settings_bp.route('/<camera_id>/arm', methods=['POST'])
def toggle_arm(camera_id):
    armed = request.json.get('armed', True)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE camera_id = ?', (camera_id,))
    user = cursor.fetchone()
    
    if user:
        cursor.execute('''
            UPDATE user_settings SET auto_arm = ? WHERE user_id = ?
        ''', (1 if armed else 0, user['id']))
        conn.commit()
    
    conn.close()
    
    return jsonify({'success': True, 'armed': armed})