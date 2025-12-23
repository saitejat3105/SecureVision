#mask_detector.py
import cv2
import numpy as np
import os
from config import Config

class MaskDetector:
    def __init__(self):
        self.model = None
        self.haar_cascade = cv2.CascadeClassifier(
            os.path.join(Config.HAARCASCADES_DIR, 'haarcascade_frontalface_default.xml')
        )
        self._load_model()
    
    def _load_model(self):
        """Load mask detection model"""
        try:
            import tensorflow as tf
            model_path = os.path.join(Config.TRAINED_MODELS_DIR, 'mask_detector.h5')
            if os.path.exists(model_path):
                self.model = tf.keras.models.load_model(model_path)
                print("Mask detector model loaded")
            else:
                print("Mask detector model not found, using heuristic method")
        except Exception as e:
            print(f"Could not load mask detector: {e}")
    
    def detect(self, face_image):
        """Detect if face is wearing a mask"""
        if self.model is not None:
            return self._detect_with_model(face_image)
        return self._detect_heuristic(face_image)
    
    def _detect_with_model(self, face_image):
        """Use trained model for mask detection"""
        try:
            img = cv2.resize(face_image, (128, 128))
            img = img / 255.0
            img = np.expand_dims(img, axis=0)
            
            pred = self.model.predict(img, verbose=0)[0]
            is_masked = pred[0] > 0.5  # Assuming binary classification
            confidence = float(pred[0]) if is_masked else float(1 - pred[0])
            
            return {
                'is_masked': is_masked,
                'confidence': confidence
            }
        except Exception as e:
            return self._detect_heuristic(face_image)
    
    def _detect_heuristic(self, face_image):
        """Heuristic mask detection based on face coverage"""
        try:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            
            # Analyze lower half of face (where mask would be)
            lower_half = gray[h//2:, :]
            upper_half = gray[:h//2, :]
            
            # Compare variance between upper and lower face
            lower_var = np.var(lower_half)
            upper_var = np.var(upper_half)
            
            # If lower face has significantly less variance, might be masked
            ratio = lower_var / (upper_var + 1e-7)
            is_masked = ratio < 0.3
            
            # Edge detection for mask boundary
            edges = cv2.Canny(gray, 50, 150)
            mid_edges = edges[h//3:2*h//3, w//4:3*w//4]
            edge_density = np.sum(mid_edges > 0) / mid_edges.size
            
            if edge_density > 0.15:
                is_masked = True
            
            confidence = 0.7 if is_masked else 0.6
            
            return {
                'is_masked': is_masked,
                'confidence': confidence,
                'method': 'heuristic'
            }
        except:
            return {'is_masked': False, 'confidence': 0.5}