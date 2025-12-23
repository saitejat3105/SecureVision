#database.py
import sqlite3
import hashlib
import uuid
from datetime import datetime
from config import Config

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with all tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            camera_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Known faces table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS known_faces (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            folder_path TEXT NOT NULL,
            image_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP,
            is_authorized INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Intruder logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intruder_logs (
            id TEXT PRIMARY KEY,
            camera_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image_path TEXT,
            full_image_path TEXT,
            cropped_face_path TEXT,
            confidence REAL,
            severity INTEGER DEFAULT 5,
            type TEXT DEFAULT 'unknown_person',
            details TEXT,
            is_recurring INTEGER DEFAULT 0,
            visit_count INTEGER DEFAULT 1,
            weapon_detected INTEGER DEFAULT 0,
            mask_detected INTEGER DEFAULT 0,
            is_resolved INTEGER DEFAULT 0,
            resolved_at TIMESTAMP,
            FOREIGN KEY (camera_id) REFERENCES users(camera_id)
        )
    ''')
    
    # User settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY,
            do_not_disturb INTEGER DEFAULT 0,
            dnd_start_hour INTEGER DEFAULT 22,
            dnd_end_hour INTEGER DEFAULT 7,
            camera_enabled INTEGER DEFAULT 1,
            email_alerts INTEGER DEFAULT 1,
            sound_alerts INTEGER DEFAULT 1,
            auto_arm INTEGER DEFAULT 1,
            arm_start_hour INTEGER DEFAULT 22,
            arm_end_hour INTEGER DEFAULT 6,
            sensitivity TEXT DEFAULT 'medium',
            night_mode_auto INTEGER DEFAULT 1,
            alert_on_unknown INTEGER DEFAULT 1,
            alert_on_weapon INTEGER DEFAULT 1,
            decoy_voice INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Face embeddings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS face_embeddings (
            id TEXT PRIMARY KEY,
            known_face_id TEXT NOT NULL,
            embedding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (known_face_id) REFERENCES known_faces(id)
        )
    ''')
    
    # Activity logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id TEXT PRIMARY KEY,
            camera_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            description TEXT,
            severity TEXT DEFAULT 'info'
        )
    ''')
    
    # Vehicle plates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicle_plates (
            id TEXT PRIMARY KEY,
            camera_id TEXT NOT NULL,
            plate_number TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image_path TEXT,
            is_known INTEGER DEFAULT 0,
            owner_name TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def hash_password(password):
    """Hash password with salt"""
    salt = uuid.uuid4().hex
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(stored_hash, password):
    """Verify password against stored hash"""
    salt, hashed = stored_hash.split(':')
    return hashed == hashlib.sha256((password + salt).encode()).hexdigest()

def create_user(username, email, password):
    """Create new user"""
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = str(uuid.uuid4())
    camera_id = f"CAM_{uuid.uuid4().hex[:8].upper()}"
    password_hash = hash_password(password)
    
    try:
        cursor.execute('''
            INSERT INTO users (id, username, email, password_hash, camera_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, email, password_hash, camera_id))
        
        # Create default settings
        cursor.execute('''
            INSERT INTO user_settings (user_id)
            VALUES (?)
        ''', (user_id,))
        
        conn.commit()
        return {'id': user_id, 'username': username, 'camera_id': camera_id}
    except sqlite3.IntegrityError as e:
        return None
    finally:
        conn.close()

def authenticate_user(username, password):
    """Authenticate user"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    if user and verify_password(user['password_hash'], password):
        cursor.execute('''
            UPDATE users SET last_login = ? WHERE id = ?
        ''', (datetime.now(), user['id']))
        conn.commit()
        conn.close()
        return {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'camera_id': user['camera_id']
        }
    
    conn.close()
    return None

if __name__ == '__main__':
    init_db()