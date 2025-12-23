#night_vision.py
import cv2
import numpy as np
from datetime import datetime
from config import Config

class NightVisionService:
    def __init__(self):
        self.is_night_mode = False
        self.auto_mode = True
        self.brightness_threshold = 50
    
    def is_low_light(self, frame):
        """Check if frame is in low light conditions"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        return brightness < self.brightness_threshold
    
    def should_enable_night_mode(self):
        """Check if night mode should be enabled based on time"""
        current_hour = datetime.now().hour
        return current_hour >= Config.NIGHT_MODE_START or current_hour < Config.NIGHT_MODE_END
    
    def enhance(self, frame):
        """Apply night vision enhancement"""
        if frame is None:
            return None
        
        # Method 1: CLAHE enhancement
        enhanced = self._clahe_enhance(frame)
        
        # Check if still too dark
        if self.is_low_light(enhanced):
            # Method 2: Gamma correction
            enhanced = self._gamma_correction(enhanced, gamma=2.0)
        
        # Still dark? Apply more aggressive enhancement
        if self.is_low_light(enhanced):
            enhanced = self._aggressive_enhance(enhanced)
        
        return enhanced
    
    def _clahe_enhance(self, frame):
        """CLAHE enhancement"""
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def _gamma_correction(self, frame, gamma=1.5):
        """Apply gamma correction"""
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(frame, table)
    
    def _aggressive_enhance(self, frame):
        """Aggressive enhancement for very dark conditions"""
        # Convert to float
        img = frame.astype(np.float32) / 255.0
        
        # Apply histogram stretching
        for i in range(3):
            channel = img[:, :, i]
            min_val = np.min(channel)
            max_val = np.max(channel)
            if max_val > min_val:
                img[:, :, i] = (channel - min_val) / (max_val - min_val)
        
        # Apply brightness boost
        img = np.clip(img * 2.0, 0, 1)
        
        # Convert back
        enhanced = (img * 255).astype(np.uint8)
        
        # Denoise
        enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
        
        return enhanced
    
    def apply_thermal_effect(self, frame):
        """Apply fake thermal vision effect"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply colormap for thermal effect
        thermal = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
        
        return thermal
    
    def flash_screen(self, frame):
        """Create flash effect for better face capture in dark"""
        # Create bright overlay
        bright = np.ones_like(frame) * 255
        
        # Blend
        alpha = 0.5
        flashed = cv2.addWeighted(frame, 1 - alpha, bright, alpha, 0)
        
        return flashed