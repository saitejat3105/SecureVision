import cv2
import numpy as np
import os
from config import Config

class AnomalyDetector:
    def __init__(self):
        self.model = None
        self.background_model = None
        self.prev_frame = None
        self.frame_history = []
        self.max_history = 30
        self._load_model()
    
    def _load_model(self):
        """Load anomaly detection autoencoder"""
        try:
            import tensorflow as tf
            model_path = os.path.join(Config.TRAINED_MODELS_DIR, 'anomaly_autoencoder.h5')
            if os.path.exists(model_path):
                self.model = tf.keras.models.load_model(model_path)
                print("Anomaly autoencoder loaded")
        except Exception as e:
            print(f"Anomaly model not loaded: {e}")
        
        # Initialize background subtractor
        self.background_model = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=50, detectShadows=True
        )
    
    def detect_anomalies(self, frame):
        """Detect various anomalies in frame"""
        anomalies = []
        
        # Check for static/frozen frame
        if self._is_frame_frozen(frame):
            anomalies.append({
                'type': 'frozen_frame',
                'severity': 'high',
                'description': 'Camera feed appears frozen'
            })
        
        # Check for camera obstruction
        obstruction = self._detect_obstruction(frame)
        if obstruction['is_obstructed']:
            anomalies.append({
                'type': 'obstruction',
                'severity': 'high',
                'description': obstruction['description']
            })
        
        # Check for unusual motion
        motion = self._detect_unusual_motion(frame)
        if motion['is_unusual']:
            anomalies.append({
                'type': 'unusual_motion',
                'severity': 'medium',
                'description': motion['description']
            })
        
        # Check for scene change
        scene_change = self._detect_scene_change(frame)
        if scene_change['changed']:
            anomalies.append({
                'type': 'scene_change',
                'severity': 'medium',
                'description': 'Significant scene change detected'
            })
        
        # Check for smoke/fog
        smoke = self._detect_smoke_fog(frame)
        if smoke['detected']:
            anomalies.append({
                'type': smoke['type'],
                'severity': 'high',
                'description': smoke['description']
            })
        
        return anomalies
    
    def _is_frame_frozen(self, frame):
        """Detect if frame is frozen/static"""
        if self.prev_frame is None:
            self.prev_frame = frame.copy()
            return False
        
        diff = cv2.absdiff(frame, self.prev_frame)
        diff_sum = np.sum(diff)
        
        self.prev_frame = frame.copy()
        
        # If almost no difference, frame might be frozen
        return diff_sum < 1000
    
    def _detect_obstruction(self, frame):
        """Detect camera obstruction (solid color, object blocking)"""
        # Check for single color (covered camera)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Check color variance
        h_var = np.var(hsv[:, :, 0])
        s_var = np.var(hsv[:, :, 1])
        v_var = np.var(hsv[:, :, 2])
        
        if h_var < 100 and s_var < 100:
            return {
                'is_obstructed': True,
                'description': 'Camera appears to be covered'
            }
        
        # Check for very dark image
        brightness = np.mean(frame)
        if brightness < 10:
            return {
                'is_obstructed': True,
                'description': 'Camera image too dark - possible obstruction'
            }
        
        # Check for blur (lens fog)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 50:
            return {
                'is_obstructed': True,
                'description': 'Camera lens may be foggy or out of focus'
            }
        
        return {'is_obstructed': False, 'description': ''}
    
    def _detect_unusual_motion(self, frame):
        """Detect unusual motion patterns"""
        if self.background_model is None:
            return {'is_unusual': False, 'description': ''}
        
        fg_mask = self.background_model.apply(frame)
        
        # Count moving pixels
        motion_pixels = np.sum(fg_mask > 127)
        total_pixels = fg_mask.size
        motion_ratio = motion_pixels / total_pixels
        
        if motion_ratio > 0.5:  # More than 50% of frame moving
            return {
                'is_unusual': True,
                'description': 'Excessive motion detected'
            }
        
        return {'is_unusual': False, 'description': ''}
    
    def _detect_scene_change(self, frame):
        """Detect significant scene changes (camera tampered)"""
        self.frame_history.append(frame.copy())
        if len(self.frame_history) > self.max_history:
            self.frame_history.pop(0)
        
        if len(self.frame_history) < 2:
            return {'changed': False}
        
        # Compare with historical average
        current_hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        current_hist = cv2.normalize(current_hist, current_hist).flatten()
        
        old_frame = self.frame_history[0]
        old_hist = cv2.calcHist([old_frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        old_hist = cv2.normalize(old_hist, old_hist).flatten()
        
        correlation = cv2.compareHist(current_hist, old_hist, cv2.HISTCMP_CORREL)
        
        return {'changed': correlation < 0.5}
    
    def _detect_smoke_fog(self, frame):
        """Detect smoke or fog in frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Check for haziness
        contrast = gray.std()
        brightness = gray.mean()
        
        # Smoke/fog typically reduces contrast
        if contrast < 30 and brightness > 100:
            return {
                'detected': True,
                'type': 'fog_smoke',
                'description': 'Possible smoke or fog detected'
            }
        
        return {'detected': False, 'type': '', 'description': ''}
    
    def detect_shadow(self, frame):
        """Detect unusual shadows"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive threshold to detect shadows
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Find contours of dark regions
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        shadows = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 5000:  # Significant shadow
                x, y, w, h = cv2.boundingRect(cnt)
                shadows.append({
                    'bbox': (x, y, w, h),
                    'area': area
                })
        
        return shadows