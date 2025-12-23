#scene_detector.py
import cv2
import numpy as np
from collections import deque

class SceneDetector:
    def __init__(self, history_size=100):
        self.history = deque(maxlen=history_size)
        self.baseline_histogram = None
        self.baseline_set = False
    
    def set_baseline(self, frame):
        """Set baseline scene for comparison"""
        self.baseline_histogram = self._compute_histogram(frame)
        self.baseline_set = True
    
    def _compute_histogram(self, frame):
        """Compute color histogram of frame"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        return hist
    
    def detect_scene_change(self, frame, threshold=0.5):
        """Detect if scene has changed from baseline"""
        if not self.baseline_set:
            self.set_baseline(frame)
            return {'changed': False, 'similarity': 1.0}
        
        current_hist = self._compute_histogram(frame)
        
        # Compare with baseline
        similarity = cv2.compareHist(self.baseline_histogram, current_hist, cv2.HISTCMP_CORREL)
        
        self.history.append(similarity)
        
        return {
            'changed': similarity < threshold,
            'similarity': similarity,
            'avg_similarity': np.mean(self.history) if self.history else 1.0
        }
    
    def detect_camera_tampering(self, frame):
        """Detect if camera has been tampered with"""
        issues = []
        
        # Check for camera tilt (horizontal line detection)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
        
        if lines is not None:
            horizontal_count = 0
            for rho, theta in lines[:, 0]:
                if abs(theta - np.pi/2) < 0.1:  # Near horizontal
                    horizontal_count += 1
            
            # If very few horizontal lines, camera might be tilted
            if horizontal_count < 2:
                issues.append({
                    'type': 'camera_tilt',
                    'description': 'Camera appears to be tilted'
                })
        
        # Check for camera shake
        if len(self.history) > 10:
            recent_variance = np.var(list(self.history)[-10:])
            if recent_variance > 0.1:
                issues.append({
                    'type': 'camera_shake',
                    'description': 'Camera appears unstable or shaking'
                })
        
        # Check for partial obstruction
        gray_mean = np.mean(gray)
        quarters = [
            gray[:gray.shape[0]//2, :gray.shape[1]//2],
            gray[:gray.shape[0]//2, gray.shape[1]//2:],
            gray[gray.shape[0]//2:, :gray.shape[1]//2],
            gray[gray.shape[0]//2:, gray.shape[1]//2:]
        ]
        
        quarter_means = [np.mean(q) for q in quarters]
        if max(quarter_means) - min(quarter_means) > 100:
            issues.append({
                'type': 'partial_obstruction',
                'description': 'Part of camera view may be blocked'
            })
        
        return issues
    
    def detect_frame_freeze(self, frame, prev_frame, threshold=0.001):
        """Detect frozen/static frame"""
        if prev_frame is None:
            return False
        
        diff = cv2.absdiff(frame, prev_frame)
        diff_mean = np.mean(diff)
        
        return diff_mean < threshold