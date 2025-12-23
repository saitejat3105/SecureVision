#face_routes.py
from flask import Blueprint, request, jsonify
from database import get_db
import uuid
import os
import base64
import cv2
import numpy as np
from config import Config

faces_bp = Blueprint('faces', __name__)

@faces_bp.route('/<user_id>', methods=['GET'])
def get_faces(user_id):
    """Get all known faces for a user"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, image_count, created_at as lastUpdated, user_id as userId
        FROM known_faces 
        WHERE user_id = ?
        ORDER BY name
    ''', (user_id,))
    
    faces = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'faces': [{
            'id': f['id'],
            'name': f['name'],
            'imageCount': f['image_count'] or 0,
            'lastUpdated': f['lastUpdated'],
            'userId': f['userId']
        } for f in faces]
    })

@faces_bp.route('/register', methods=['POST'])
def register_face():
    """Register a new known face with images"""
    data = request.json
    
    user_id = data.get('user_id')
    name = data.get('name')
    images = data.get('images', [])  # Base64 encoded images
    
    if not user_id or not name:
        return jsonify({'error': 'user_id and name required'}), 400
    
    if len(images) < 5:
        return jsonify({'error': 'At least 5 images required'}), 400
    
    # Create folder for person
    safe_name = name.lower().replace(' ', '_')
    folder_path = os.path.join(Config.TRAIN_DIR, safe_name)
    os.makedirs(folder_path, exist_ok=True)
    
    # Save images
    saved_count = 0
    for i, img_data in enumerate(images):
        try:
            # Remove data URL prefix if present
            if ',' in img_data:
                img_data = img_data.split(',')[1]
            
            # Decode base64
            img_bytes = base64.b64decode(img_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None:
                filename = f"{safe_name}_{saved_count:03d}.jpg"
                filepath = os.path.join(folder_path, filename)
                cv2.imwrite(filepath, img)
                saved_count += 1
        except Exception as e:
            print(f"Error saving image {i}: {e}")
            continue
    
    # Save to database
    conn = get_db()
    cursor = conn.cursor()
    
    face_id = str(uuid.uuid4())
    
    cursor.execute('''
        INSERT INTO known_faces (id, user_id, name, folder_path, image_count)
        VALUES (?, ?, ?, ?, ?)
    ''', (face_id, user_id, name, folder_path, saved_count))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'face_id': face_id,
        'images_saved': saved_count,
        'folder': folder_path
    })

@faces_bp.route('/<face_id>', methods=['DELETE'])
def delete_face(face_id):
    """Delete a known face"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get folder path first
    cursor.execute('SELECT folder_path FROM known_faces WHERE id = ?', (face_id,))
    face = cursor.fetchone()
    
    if face and face['folder_path']:
        # Delete folder and images
        import shutil
        if os.path.exists(face['folder_path']):
            shutil.rmtree(face['folder_path'])
    
    # Delete from database
    cursor.execute('DELETE FROM known_faces WHERE id = ?', (face_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@faces_bp.route('/<face_id>/images', methods=['POST'])
def add_images(face_id):
    """Add more images to existing face"""
    data = request.json
    images = data.get('images', [])
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT name, folder_path, image_count FROM known_faces WHERE id = ?', (face_id,))
    face = cursor.fetchone()
    
    if not face:
        conn.close()
        return jsonify({'error': 'Face not found'}), 404
    
    folder_path = face['folder_path']
    current_count = face['image_count'] or 0
    safe_name = face['name'].lower().replace(' ', '_')
    
    saved_count = 0
    for i, img_data in enumerate(images):
        try:
            if ',' in img_data:
                img_data = img_data.split(',')[1]
            
            img_bytes = base64.b64decode(img_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None:
                filename = f"{safe_name}_{current_count + saved_count:03d}.jpg"
                filepath = os.path.join(folder_path, filename)
                cv2.imwrite(filepath, img)
                saved_count += 1
        except Exception as e:
            continue
    
    # Update count
    cursor.execute('''
        UPDATE known_faces SET image_count = ? WHERE id = ?
    ''', (current_count + saved_count, face_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'images_added': saved_count,
        'total_images': current_count + saved_count
    })