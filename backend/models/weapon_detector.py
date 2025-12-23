#weaponDetector.py
import cv2
import numpy as np
import os
from config import Config

class WeaponDetector:
    def __init__(self):
        self.model = None
        self.confidence_threshold = 0.4
        self.weapon_classes = ['knife', 'gun', 'pistol', 'rifle', 'weapon']
        self._load_model()
    
    def _load_model(self):
        """Load weapon detection model"""
        try:
            from ultralytics import YOLO
            model_path = os.path.join(Config.PRETRAINED_MODELS_DIR, 'yolov8n.pt')
            if os.path.exists(model_path):
                self.model = YOLO(model_path)
            else:
                self.model = YOLO('yolov8n.pt')
            print("Weapon detector loaded (using general YOLO)")
        except Exception as e:
            print(f"Could not load weapon detector: {e}")
            self.model = None
    
    def detect(self, frame):
        """Detect weapons in frame"""
        if self.model is None:
            return []
        
        try:
            results = self.model(frame, verbose=False)
            weapons = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = result.names[cls].lower()
                    
                    # Check for weapon-like objects
                    # COCO classes: knife(43), scissors(76)
                    if cls in [43, 76] or any(w in class_name for w in self.weapon_classes):
                        if conf > self.confidence_threshold:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            weapons.append({
                                'bbox': (x1, y1, x2 - x1, y2 - y1),
                                'confidence': conf,
                                'class': class_name,
                                'is_weapon': True
                            })
            
            return weapons
        except Exception as e:
            print(f"Weapon detection error: {e}")
            return []
    
    def has_weapon(self, frame):
        """Check if frame contains any weapon"""
        weapons = self.detect(frame)
        return len(weapons) > 0, weapons