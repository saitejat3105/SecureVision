#liveness_detector.py
import cv2
import numpy as np
import time

class LivenessDetector:
    def __init__(self):
        self.blink_counter = 0
        self.blink_threshold = 0.2
        self.prev_ear = None
        self.blink_history = []
        self.texture_threshold = 50
        self.motion_history = []
        self.haar_eye = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
    
    def detect(self, face_image, prev_face=None):
        """Detect if face is real (liveness detection)"""
        results = {
            'is_live': True,
            'confidence': 0.5,
            'checks': {}
        }
        
        # Texture analysis (detect printed photos)
        texture_score = self._analyze_texture(face_image)
        results['checks']['texture'] = texture_score > self.texture_threshold
        
        # Blink detection
        blink_detected = self._detect_blink(face_image)
        results['checks']['blink'] = blink_detected
        
        # Motion analysis (compare with previous frame)
        if prev_face is not None:
            motion_score = self._analyze_motion(face_image, prev_face)
            results['checks']['motion'] = motion_score > 0.01
        else:
            results['checks']['motion'] = None
        
        # Color analysis (detect screen display)
        color_natural = self._analyze_color(face_image)
        results['checks']['color'] = color_natural
        
        # Reflection detection
        has_reflection = self._detect_reflection(face_image)
        results['checks']['reflection'] = not has_reflection
        
        # Calculate overall liveness score
        checks = [v for v in results['checks'].values() if v is not None]
        if checks:
            results['confidence'] = sum(checks) / len(checks)
            results['is_live'] = results['confidence'] > 0.5
        
        return results
    
    def _analyze_texture(self, face_image):
        """Analyze face texture to detect printed photos"""
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        
        # Compute Laplacian variance (real faces have more texture)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        return variance
    
    def _detect_blink(self, face_image):
        """Detect eye blink"""
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        
        # Detect eyes
        eyes = self.haar_eye.detectMultiScale(gray, 1.1, 4)
        
        if len(eyes) >= 2:
            # Calculate eye aspect ratio
            ear = self._calculate_ear(eyes, gray)
            
            if self.prev_ear is not None:
                # Detect blink (sudden decrease in EAR)
                if self.prev_ear - ear > self.blink_threshold:
                    self.blink_counter += 1
                    self.blink_history.append(time.time())
            
            self.prev_ear = ear
            
            # Check for recent blinks (within last 5 seconds)
            recent_blinks = [b for b in self.blink_history if time.time() - b < 5]
            self.blink_history = recent_blinks
            
            return len(recent_blinks) > 0
        
        return False
    
    def _calculate_ear(self, eyes, gray):
        """Calculate eye aspect ratio"""
        if len(eyes) < 2:
            return 0.3
        
        # Sort by x coordinate
        eyes = sorted(eyes, key=lambda e: e[0])
        
        # Calculate average eye height/width ratio
        ratios = []
        for (x, y, w, h) in eyes[:2]:
            ratio = h / (w + 1e-7)
            ratios.append(ratio)
        
        return np.mean(ratios)
    
    def _analyze_motion(self, current_face, prev_face):
        """Analyze micro-movements (real faces have subtle motion)"""
        try:
            # Resize to same shape
            h, w = current_face.shape[:2]
            prev_resized = cv2.resize(prev_face, (w, h))
            
            # Calculate optical flow
            gray_curr = cv2.cvtColor(current_face, cv2.COLOR_BGR2GRAY)
            gray_prev = cv2.cvtColor(prev_resized, cv2.COLOR_BGR2GRAY)
            
            flow = cv2.calcOpticalFlowFarneback(
                gray_prev, gray_curr, None, 0.5, 3, 15, 3, 5, 1.2, 0
            )
            
            magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
            return np.mean(magnitude)
        except:
            return 0
    
    def _analyze_color(self, face_image):
        """Analyze color distribution (screens have different color patterns)"""
        hsv = cv2.cvtColor(face_image, cv2.COLOR_BGR2HSV)
        
        # Check for unnatural color distribution
        h_std = np.std(hsv[:, :, 0])
        s_mean = np.mean(hsv[:, :, 1])
        
        # Natural skin has moderate saturation and hue variation
        natural = 10 < h_std < 50 and 30 < s_mean < 180
        
        return natural
    
    def _detect_reflection(self, face_image):
        """Detect screen reflections (indicates fake)"""
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        
        # Find very bright spots (potential reflections)
        _, bright = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
        bright_ratio = np.sum(bright > 0) / bright.size
        
        # High ratio of very bright pixels indicates screen
        return bright_ratio > 0.05