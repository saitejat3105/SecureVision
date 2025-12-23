#config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-secret-key')
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database
    DATABASE_PATH = 'security.db'
    
    # Email
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    ALERT_RECIPIENT = os.getenv('ALERT_RECIPIENT', '')
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    
    # Paths
    DATA_DIR = 'data'
    TRAIN_DIR = os.path.join(DATA_DIR, 'train')
    TEST_DIR = os.path.join(DATA_DIR, 'test')
    INTRUDERS_DIR = os.path.join(DATA_DIR, 'intruders')
    MODELS_DIR = 'models'
    TRAINED_MODELS_DIR = os.path.join(MODELS_DIR, 'trained')
    PRETRAINED_MODELS_DIR = os.path.join(MODELS_DIR, 'pretrained')
    HAARCASCADES_DIR = 'haarcascades'
    STATIC_DIR = 'static'
    AUDIO_DIR = os.path.join(STATIC_DIR, 'audio')
    LOGS_DIR = 'logs'
    
    # Detection
    FACE_CONFIDENCE_THRESHOLD = float(os.getenv('FACE_CONFIDENCE_THRESHOLD', 0.6))
    INTRUDER_ALERT_COOLDOWN = int(os.getenv('INTRUDER_ALERT_COOLDOWN', 30))
    
    # Night Mode
    NIGHT_MODE_START = int(os.getenv('NIGHT_MODE_START', 22))
    NIGHT_MODE_END = int(os.getenv('NIGHT_MODE_END', 6))
    
    # Storage
    MAX_INTRUDER_IMAGES = int(os.getenv('MAX_INTRUDER_IMAGES', 1000))
    AUTO_DELETE_DAYS = int(os.getenv('AUTO_DELETE_DAYS', 30))
    
    # Image Settings
    FACE_SIZE = (160, 160)
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    
    @classmethod
    def ensure_dirs(cls):
        """Create all required directories"""
        dirs = [
            cls.DATA_DIR, cls.TRAIN_DIR, cls.TEST_DIR, cls.INTRUDERS_DIR,
            cls.MODELS_DIR, cls.TRAINED_MODELS_DIR, cls.PRETRAINED_MODELS_DIR,
            cls.HAARCASCADES_DIR, cls.STATIC_DIR, cls.AUDIO_DIR, cls.LOGS_DIR
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

Config.ensure_dirs()