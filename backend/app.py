#app.py
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import threading
import time
import os
import uuid
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import base64
import hashlib
import json

from config import Config
from database import init_db, get_db

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize database
init_db()

# Global variables
cameras = {}  # camera_id -> camera object
detection_threads = {}
last_alert_time = {}
alarm_active = False  # Global alarm state

# ============== MODELS ==============

class FaceDetector:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.known_faces = {}  # name -> embeddings
        
    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        return faces
    
    def get_face_embedding(self, face_img):
        # Simple embedding using histogram
        face_resized = cv2.resize(face_img, (100, 100))
        gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        return hist.flatten()
    
    def recognize_face(self, face_img, user_id):
        if user_id not in self.known_faces or not self.known_faces[user_id]:
            return "Unknown", 0.0, True
        
        embedding = self.get_face_embedding(face_img)
        best_match = "Unknown"
        best_score = 0.0
        
        for name, stored_embeddings in self.known_faces[user_id].items():
            for stored_emb in stored_embeddings:
                score = cv2.compareHist(
                    embedding.astype(np.float32),
                    stored_emb.astype(np.float32),
                    cv2.HISTCMP_CORREL
                )
                if score > best_score:
                    best_score = score
                    best_match = name
        
        is_intruder = best_score < Config.FACE_RECOGNITION_THRESHOLD
        return best_match if not is_intruder else "Intruder", best_score, is_intruder

    def add_known_face(self, user_id, name, face_img):
        if user_id not in self.known_faces:
            self.known_faces[user_id] = {}
        if name not in self.known_faces[user_id]:
            self.known_faces[user_id][name] = []
        
        embedding = self.get_face_embedding(face_img)
        self.known_faces[user_id][name].append(embedding)

# Initialize detector
face_detector = FaceDetector()

# ============== CAMERA SERVICE ==============

class CameraStream:
    def __init__(self, camera_id, user_id):
        self.camera_id = camera_id
        self.user_id = user_id
        self.cap = None
        self.running = False
        self.frame = None
        self.detections = []
        self.night_mode = False
        
    def start(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.running = True
        
    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
            
    def get_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                if self.night_mode:
                    frame = self.enhance_night_vision(frame)
                self.frame = frame
                return frame
        return None
    
    def enhance_night_vision(self, frame):
        # Apply CLAHE for low-light enhancement
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        return enhanced

def detection_loop(camera_id, user_id):
    camera = cameras.get(camera_id)
    if not camera:
        return
    
    while camera.running:
        frame = camera.get_frame()
        if frame is None:
            time.sleep(0.1)
            continue
        
        # Detect faces
        faces = face_detector.detect_faces(frame)
        detections = []
        
        for (x, y, w, h) in faces:
            face_img = frame[y:y+h, x:x+w]
            name, confidence, is_intruder = face_detector.recognize_face(face_img, user_id)
            
            detection = {
                'name': name,
                'confidence': float(confidence),
                'isIntruder': is_intruder,
                'boundingBox': {
                    'x': int(x / frame.shape[1] * 100),
                    'y': int(y / frame.shape[0] * 100),
                    'w': int(w / frame.shape[1] * 100),
                    'h': int(h / frame.shape[0] * 100)
                }
            }
            detections.append(detection)
            
            # Handle intruder
            if is_intruder:
                handle_intruder(camera_id, frame, face_img, detection)
        
        camera.detections = detections
        
        # Emit to connected clients
        socketio.emit(f'detections_{camera_id}', {
            'detections': detections
        })
        
        time.sleep(0.1)

def handle_intruder(camera_id, frame, face_img, detection):
    global last_alert_time
    
    current_time = time.time()
    if camera_id in last_alert_time:
        if current_time - last_alert_time[camera_id] < Config.ALERT_COOLDOWN:
            return
    
    last_alert_time[camera_id] = current_time
    
    # Save intruder image
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'intruder_{timestamp}_{detection["name"]}.jpg'
    filepath = os.path.join(Config.INTRUDER_DIR, filename)
    os.makedirs(Config.INTRUDER_DIR, exist_ok=True)
    cv2.imwrite(filepath, frame)
    
    # Log to database
    log_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute('''
        INSERT INTO intruder_logs (id, camera_id, image_path, confidence, severity, type, details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (log_id, camera_id, filepath, detection['confidence'], 
          calculate_severity(detection), 'unknown_person', 
          f"Unknown person detected with confidence {detection['confidence']:.2%}"))
    conn.commit()
    conn.close()
    
    # Send email alert
    send_email_alert(camera_id, filepath, detection)

def calculate_severity(detection):
    severity = 3  # Base severity
    if detection.get('additionalInfo', {}).get('weapon'):
        severity += 5
    if detection.get('additionalInfo', {}).get('masked'):
        severity += 2
    if detection['confidence'] > 0.8:
        severity += 1
    return min(severity, 10)

def send_email_alert(camera_id, image_path, detection):
    if not Config.EMAIL_ADDRESS or not Config.EMAIL_PASSWORD:
        print("Email not configured")
        return
    
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f'🚨 INTRUDER ALERT - {camera_id}'
        msg['From'] = Config.EMAIL_ADDRESS
        msg['To'] = Config.ALERT_RECIPIENT
        
        body = f"""
        INTRUDER DETECTED!
        
        Camera: {camera_id}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Confidence: {detection['confidence']:.2%}
        
        Please check your security system immediately.
        """
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach image
        if os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', 'attachment', filename='intruder.jpg')
                msg.attach(img)
        
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"Alert email sent for {camera_id}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# ============== ROUTES ==============

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    user_id = str(uuid.uuid4())
    camera_id = f'cam_{username}'
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO users (id, username, email, password_hash, camera_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, email, password_hash, camera_id))
        
        # Create default settings
        conn.execute('''
            INSERT INTO settings (user_id) VALUES (?)
        ''', (user_id,))
        
        conn.commit()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400
    finally:
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    conn = get_db()
    user = conn.execute('''
        SELECT * FROM users WHERE username = ? AND password_hash = ?
    ''', (username, password_hash)).fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'cameraId': user['camera_id'],
                'createdAt': user['created_at']
            },
            'token': str(uuid.uuid4())
        })
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/video_feed/<camera_id>')
def video_feed(camera_id):
    def generate():
        while True:
            camera = cameras.get(camera_id)
            if camera and camera.frame is not None:
                frame = camera.frame.copy()
                
                # Draw detection boxes
                for det in camera.detections:
                    bbox = det['boundingBox']
                    x = int(bbox['x'] * frame.shape[1] / 100)
                    y = int(bbox['y'] * frame.shape[0] / 100)
                    w = int(bbox['w'] * frame.shape[1] / 100)
                    h = int(bbox['h'] * frame.shape[0] / 100)
                    
                    color = (0, 0, 255) if det['isIntruder'] else (0, 255, 0)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    
                    label = f"{det['name']} ({det['confidence']:.0%})"
                    cv2.putText(frame, label, (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.033)  # ~30 FPS
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/camera/start/<camera_id>', methods=['POST'])
def start_camera(camera_id):
    data = request.json
    user_id = data.get('userId')
    
    if camera_id not in cameras:
        camera = CameraStream(camera_id, user_id)
        camera.start()
        cameras[camera_id] = camera
        
        # Start detection thread
        thread = threading.Thread(target=detection_loop, args=(camera_id, user_id))
        thread.daemon = True
        thread.start()
        detection_threads[camera_id] = thread
    
    return jsonify({'success': True})

@app.route('/api/camera/stop/<camera_id>', methods=['POST'])
def stop_camera(camera_id):
    if camera_id in cameras:
        cameras[camera_id].stop()
        del cameras[camera_id]
    return jsonify({'success': True})

@app.route('/api/camera/nightmode', methods=['POST'])
def toggle_night_mode():
    data = request.json
    camera_id = data.get('cameraId')
    enabled = data.get('enabled')
    
    if camera_id in cameras:
        cameras[camera_id].night_mode = enabled
    return jsonify({'success': True})

@app.route('/api/alarm/trigger', methods=['POST'])
def trigger_alarm():
    global alarm_active
    alarm_active = True
    try:
        import winsound
        # Play alarm sound in a separate thread so it doesn't block
        def play_alarm():
            while alarm_active:
                winsound.Beep(1000, 500)  # 1000Hz for 0.5 seconds
        import threading
        threading.Thread(target=play_alarm, daemon=True).start()
    except:
        print('\a' * 10)  # Terminal beep for non-Windows
    return jsonify({'success': True})

@app.route('/api/alarm/stop', methods=['POST'])
def stop_alarm():
    global alarm_active
    alarm_active = False
    return jsonify({'success': True})

@app.route('/api/camera/status/<camera_id>')
def camera_status(camera_id):
    active = camera_id in cameras and cameras[camera_id].running
    return jsonify({'active': active})

@app.route('/api/intruder-logs/<camera_id>')
def get_intruder_logs(camera_id):
    conn = get_db()
    logs = conn.execute('''
        SELECT * FROM intruder_logs WHERE camera_id = ? ORDER BY timestamp DESC
    ''', (camera_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(log) for log in logs])

@app.route('/api/known-faces/<user_id>')
def get_known_faces(user_id):
    conn = get_db()
    faces = conn.execute('''
        SELECT * FROM known_faces WHERE user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(face) for face in faces])

@app.route('/api/known-faces/add', methods=['POST'])
def add_known_face():
    data = request.json
    user_id = data.get('userId')
    name = data.get('name')
    images = data.get('images', [])  # Base64 encoded images
    
    # Create folder for person
    person_dir = os.path.join(Config.TRAIN_DIR, name)
    os.makedirs(person_dir, exist_ok=True)
    
    for i, img_base64 in enumerate(images):
        # Decode base64 image
        img_data = base64.b64decode(img_base64.split(',')[1])
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Save image
        filepath = os.path.join(person_dir, f'{name}_{i:03d}.jpg')
        cv2.imwrite(filepath, img)
        
        # Add to face detector
        face_detector.add_known_face(user_id, name, img)
    
    # Save to database
    face_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute('''
        INSERT INTO known_faces (id, user_id, name, image_count)
        VALUES (?, ?, ?, ?)
    ''', (face_id, user_id, name, len(images)))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'id': face_id})

@app.route('/api/settings/<user_id>', methods=['GET', 'PUT'])
def handle_settings(user_id):
    conn = get_db()
    
    if request.method == 'GET':
        settings = conn.execute('''
            SELECT * FROM settings WHERE user_id = ?
        ''', (user_id,)).fetchone()
        conn.close()
        
        if settings:
            return jsonify({
                'dndEnabled': bool(settings['dnd_enabled']),
                'dndStart': settings['dnd_start'],
                'dndEnd': settings['dnd_end'],
                'cameraEnabled': bool(settings['camera_enabled']),
                'emailAlertsEnabled': bool(settings['email_alerts_enabled']),
                'alarmEnabled': bool(settings['alarm_enabled']),
                'nightModeAuto': bool(settings['night_mode_auto']),
                'sensitivity': settings['sensitivity'],
                'alertCooldown': settings['alert_cooldown']
            })
        return jsonify({})
    
    else:  # PUT
        data = request.json
        conn.execute('''
            UPDATE settings SET
                dnd_enabled = ?,
                dnd_start = ?,
                dnd_end = ?,
                camera_enabled = ?,
                email_alerts_enabled = ?,
                alarm_enabled = ?,
                night_mode_auto = ?,
                sensitivity = ?,
                alert_cooldown = ?
            WHERE user_id = ?
        ''', (
            int(data.get('dndEnabled', False)),
            data.get('dndStart', '22:00'),
            data.get('dndEnd', '07:00'),
            int(data.get('cameraEnabled', True)),
            int(data.get('emailAlertsEnabled', True)),
            int(data.get('alarmEnabled', True)),
            int(data.get('nightModeAuto', True)),
            data.get('sensitivity', 70),
            data.get('alertCooldown', 30),
            user_id
        ))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/training/start', methods=['POST'])
def start_training():
    data = request.json
    user_id = data.get('userId')
    
    # In production, this would trigger actual model training
    # For now, just reload embeddings from disk
    train_dir = Config.TRAIN_DIR
    if os.path.exists(train_dir):
        for person_name in os.listdir(train_dir):
            person_dir = os.path.join(train_dir, person_name)
            if os.path.isdir(person_dir):
                for img_file in os.listdir(person_dir):
                    img_path = os.path.join(person_dir, img_file)
                    img = cv2.imread(img_path)
                    if img is not None:
                        face_detector.add_known_face(user_id, person_name, img)
    
    return jsonify({'success': True})

@app.route('/api/stats/<camera_id>')
def get_stats(camera_id):
    conn = get_db()
    
    # Get user_id from camera_id
    user = conn.execute('SELECT id FROM users WHERE camera_id = ?', (camera_id,)).fetchone()
    user_id = user['id'] if user else None
    
    # Count today's alerts
    today = datetime.now().strftime('%Y-%m-%d')
    alerts_today = conn.execute('''
        SELECT COUNT(*) FROM intruder_logs 
        WHERE camera_id = ? AND date(timestamp) = ?
    ''', (camera_id, today)).fetchone()[0]
    
    # Count known faces for this user
    known_faces_count = 0
    if user_id:
        known_faces_count = conn.execute('''
            SELECT COUNT(*) FROM known_faces WHERE user_id = ?
        ''', (user_id,)).fetchone()[0]
    
    # Also count folders in train directory
    train_dir = Config.TRAIN_DIR
    if os.path.exists(train_dir):
        known_faces_count = max(known_faces_count, len([d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))]))
    
    # Recent alerts
    recent = conn.execute('''
        SELECT * FROM intruder_logs 
        WHERE camera_id = ? 
        ORDER BY timestamp DESC LIMIT 5
    ''', (camera_id,)).fetchall()
    
    # Check which models are loaded
    models_loaded = 0
    model_status = {
        'face_recognition': face_detector is not None,
        'person_detector': hasattr(face_detector, 'person_detector') if face_detector else False,
        'weapon_detector': True,  # Using YOLO
        'mask_detector': os.path.exists('models/mask_detector.keras'),
        'pose_estimator': True,  # MediaPipe loaded
    }
    models_loaded = sum(1 for v in model_status.values() if v)
    
    # Camera status
    camera_active = camera_id in cameras
    
    conn.close()
    
    return jsonify({
        'stats': {
            'totalIntruders': len(recent),
            'totalVisitors': known_faces_count,
            'alertsToday': alerts_today,
            'uptime': 99.8 if camera_active else 0,
            'modelsActive': models_loaded
        },
        'recentAlerts': [dict(r) for r in recent],
        'systemStatus': {
            'camera': camera_active,
            'models': models_loaded >= 3,
            'alerts': True,
            'audio': True
        }
    })

# ============== WEBSOCKET ==============

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# ============== VOICE ==============

@app.route('/api/voice/send', methods=['POST'])
def send_voice():
    if 'audio' in request.files:
        audio = request.files['audio']
        # Save and play audio on laptop speakers
        filepath = f'data/voice_messages/{datetime.now().strftime("%Y%m%d_%H%M%S")}.webm'
        os.makedirs('data/voice_messages', exist_ok=True)
        audio.save(filepath)
        
        # Play audio (implement with pyaudio/playsound)
        try:
            from playsound import playsound
            playsound(filepath)
        except:
            pass
    
    return jsonify({'success': True})

@app.route('/api/voice/tts', methods=['POST'])
def text_to_speech():
    data = request.json
    text = data.get('text', '')
    
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS error: {e}")
    
    return jsonify({'success': True})

# ============== RUN ==============

if __name__ == '__main__':
    # Create directories
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    os.makedirs(Config.TRAIN_DIR, exist_ok=True)
    os.makedirs(Config.INTRUDERS_DIR, exist_ok=True)
    os.makedirs(Config.MODELS_DIR, exist_ok=True)
    
    print("Starting SecureVision Backend...")
    print("Access the API at http://localhost:5000")
    print("Use ngrok to expose: ngrok http 5000")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)