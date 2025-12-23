#auth_routes.py
from flask import Blueprint, request, jsonify
from database import create_user, authenticate_user, get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    user = create_user(username, email, password)
    
    if user:
        return jsonify({
            'success': True,
            'user': user
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Username or email already exists'
        }), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    user = authenticate_user(username, password)
    
    if user:
        return jsonify({
            'success': True,
            'user': user
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401

@auth_bp.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, camera_id, created_at FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'camera_id': user['camera_id'],
            'created_at': user['created_at']
        })
    
    return jsonify({'error': 'User not found'}), 404