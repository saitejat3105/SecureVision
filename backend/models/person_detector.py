#personDetector.py
import cv2
import numpy as np
import os
from config import Config

class PersonDetector:
    def __init__(self):
        self.model = None
        self.confidence_threshold = 0.5
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model for person detection"""
        try:
            from ultralytics import YOLO
            model_path = os.path.join(Config.PRETRAINED_MODELS_DIR, 'yolov8n.pt')
            if os.path.exists(model_path):
                self.model = YOLO(model_path)
            else:
                # Download if not exists
                self.model = YOLO('yolov8n.pt')
                # Save for later
                os.makedirs(Config.PRETRAINED_MODELS_DIR, exist_ok=True)
            print("YOLO person detector loaded")
        except Exception as e:
            print(f"Could not load YOLO: {e}")
            self.model = None
    
    def detect(self, frame):
        """Detect persons in frame"""
        if self.model is None:
            return self._detect_with_hog(frame)
        
        try:
            results = self.model(frame, verbose=False)
            persons = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # Class 0 is person in COCO
                    if cls == 0 and conf > self.confidence_threshold:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        persons.append({
                            'bbox': (x1, y1, x2 - x1, y2 - y1),
                            'confidence': conf,
                            'class': 'person'
                        })
            
            return persons
        except Exception as e:
            print(f"YOLO detection error: {e}")
            return self._detect_with_hog(frame)
    
    def _detect_with_hog(self, frame):
        """Fallback HOG person detector"""
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        boxes, weights = hog.detectMultiScale(
            gray, winStride=(8, 8), padding=(4, 4), scale=1.05
        )
        
        persons = []
        for i, (x, y, w, h) in enumerate(boxes):
            persons.append({
                'bbox': (x, y, w, h),
                'confidence': float(weights[i]) if i < len(weights) else 0.5,
                'class': 'person'
            })
        
        return persons
    
    def count_persons(self, frame):
        """Count number of persons in frame"""
        persons = self.detect(frame)
        return len(persons)
    
    def is_running(self, person_bbox, prev_bbox, time_delta):
        """Detect if person is running based on movement speed"""
        if prev_bbox is None:
            return False
        
        x1, y1, w1, h1 = person_bbox
        x2, y2, w2, h2 = prev_bbox
        
        center1 = (x1 + w1/2, y1 + h1/2)
        center2 = (x2 + w2/2, y2 + h2/2)
        
        distance = np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
        speed = distance / time_delta if time_delta > 0 else 0
        
        # Running threshold (pixels per second)
        return speed > 200