#camera_service.py
import cv2
import threading
import time
import numpy as np
from config import Config

class CameraService:
    def __init__(self):
        self.cameras = {}  # camera_id -> VideoCapture
        self.camera_threads = {}
        self.frame_buffers = {}  # camera_id -> latest frame
        self.is_running = {}
        self.night_mode = {}
        self.lock = threading.Lock()
    
    def start_camera(self, camera_id, device_index=0):
        """Start camera capture"""
        if camera_id in self.cameras and self.is_running.get(camera_id):
            return True
        
        cap = cv2.VideoCapture(device_index)
        if not cap.isOpened():
            return False
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.cameras[camera_id] = cap
        self.frame_buffers[camera_id] = None
        self.is_running[camera_id] = True
        self.night_mode[camera_id] = False
        
        # Start capture thread
        thread = threading.Thread(target=self._capture_loop, args=(camera_id,))
        thread.daemon = True
        thread.start()
        self.camera_threads[camera_id] = thread
        
        return True
    
    def stop_camera(self, camera_id):
        """Stop camera capture"""
        self.is_running[camera_id] = False
        
        if camera_id in self.cameras:
            self.cameras[camera_id].release()
            del self.cameras[camera_id]
        
        if camera_id in self.frame_buffers:
            del self.frame_buffers[camera_id]
    
    def _capture_loop(self, camera_id):
        """Continuous frame capture loop"""
        while self.is_running.get(camera_id, False):
            cap = self.cameras.get(camera_id)
            if cap is None:
                break
            
            ret, frame = cap.read()
            if ret:
                # Apply night vision if enabled
                if self.night_mode.get(camera_id, False):
                    frame = self._apply_night_vision(frame)
                
                with self.lock:
                    self.frame_buffers[camera_id] = frame
            
            time.sleep(0.033)  # ~30 FPS
    
    def get_frame(self, camera_id):
        """Get latest frame from camera"""
        with self.lock:
            return self.frame_buffers.get(camera_id)
    
    def set_night_mode(self, camera_id, enabled):
        """Enable/disable night vision mode"""
        self.night_mode[camera_id] = enabled
    
    def _apply_night_vision(self, frame):
        """Apply night vision enhancement"""
        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge and convert back
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Increase brightness
        enhanced = cv2.convertScaleAbs(enhanced, alpha=1.2, beta=30)
        
        return enhanced
    
    def generate_frames(self, camera_id):
        """Generator for video streaming"""
        while self.is_running.get(camera_id, False):
            frame = self.get_frame(camera_id)
            if frame is not None:
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.033)
    
    def capture_image(self, camera_id):
        """Capture single image from camera"""
        frame = self.get_frame(camera_id)
        if frame is not None:
            return frame.copy()
        return None
    
    def get_status(self, camera_id):
        """Get camera status"""
        return {
            'is_active': self.is_running.get(camera_id, False),
            'night_mode': self.night_mode.get(camera_id, False),
            'has_frame': self.frame_buffers.get(camera_id) is not None
        }