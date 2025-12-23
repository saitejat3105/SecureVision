from .auth_routes import auth_bp
from .camera_routes import camera_bp
from .detection_routes import detection_bp
from .settings_routes import settings_bp
from .training_routes import training_bp
from .voice_routes import voice_bp
from .face_routes import faces_bp

__all__ = [
    'faces_bp',
    'auth_bp',
    'camera_bp',
    'detection_bp',
    'settings_bp',
    'training_bp',
    'voice_bp'
]