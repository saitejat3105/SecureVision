import numpy as np
from .face_recognition import FaceRecognizer
from .person_detector import PersonDetector
from .weapon_detector import WeaponDetector
from .mask_detector import MaskDetector
from .anomaly_detector import AnomalyDetector
from .pose_estimator import PoseEstimator
from .liveness_detector import LivenessDetector

class EnsembleClassifier:
    def __init__(self):
        self.face_recognizer = FaceRecognizer()
        self.person_detector = PersonDetector()
        self.weapon_detector = WeaponDetector()
        self.mask_detector = MaskDetector()
        self.anomaly_detector = AnomalyDetector()
        self.pose_estimator = PoseEstimator()
        self.liveness_detector = LivenessDetector()
        
        self.prev_faces = {}
        print("Ensemble classifier initialized with all models")
    
    def process_frame(self, frame, camera_id):
        """Process frame through all models and return combined results"""
        results = {
            'camera_id': camera_id,
            'frame_processed': True,
            'persons': [],
            'faces': [],
            'weapons': [],
            'anomalies': [],
            'alerts': [],
            'severity_score': 0
        }
        
        # Detect persons
        persons = self.person_detector.detect(frame)
        results['persons'] = persons
        
        # Detect faces
        faces = self.face_recognizer.detect_faces(frame)
        
        for (x, y, w, h) in faces:
            face_img = frame[y:y+h, x:x+w]
            
            # Recognize face
            label, confidence = self.face_recognizer.recognize(face_img)
            
            # Check for mask
            mask_result = self.mask_detector.detect(face_img)
            
            # Liveness check
            prev_face = self.prev_faces.get(f"{x}_{y}", None)
            liveness = self.liveness_detector.detect(face_img, prev_face)
            self.prev_faces[f"{x}_{y}"] = face_img.copy()
            
            face_data = {
                'bbox': (x, y, w, h),
                'label': label,
                'confidence': confidence,
                'is_masked': mask_result['is_masked'],
                'mask_confidence': mask_result['confidence'],
                'is_live': liveness['is_live'],
                'liveness_confidence': liveness['confidence']
            }
            results['faces'].append(face_data)
            
            # Generate alerts for unknown/intruders
            if label == 'unknown' and confidence > 0.3:
                alert = {
                    'type': 'unknown_person',
                    'severity': 5,
                    'description': f'Unknown person detected (confidence: {confidence:.2f})'
                }
                if mask_result['is_masked']:
                    alert['severity'] += 2
                    alert['description'] += ' - WEARING MASK'
                if not liveness['is_live']:
                    alert['severity'] += 1
                    alert['description'] += ' - POSSIBLE SPOOFING'
                results['alerts'].append(alert)
        
        # Detect weapons
        weapons = self.weapon_detector.detect(frame)
        results['weapons'] = weapons
        
        if weapons:
            for weapon in weapons:
                results['alerts'].append({
                    'type': 'weapon_detected',
                    'severity': 10,
                    'description': f"WEAPON DETECTED: {weapon['class']} (confidence: {weapon['confidence']:.2f})"
                })
        
        # Detect anomalies
        anomalies = self.anomaly_detector.detect_anomalies(frame)
        results['anomalies'] = anomalies
        
        for anomaly in anomalies:
            results['alerts'].append({
                'type': anomaly['type'],
                'severity': 8 if anomaly['severity'] == 'high' else 5,
                'description': anomaly['description']
            })
        
        # Pose estimation for detected persons
        if persons:
            pose_result = self.pose_estimator.estimate(frame)
            if pose_result:
                if pose_result['is_crouching']:
                    results['alerts'].append({
                        'type': 'suspicious_pose',
                        'severity': 6,
                        'description': 'Crouching behavior detected'
                    })
                if pose_result['is_crawling']:
                    results['alerts'].append({
                        'type': 'suspicious_pose',
                        'severity': 7,
                        'description': 'Crawling behavior detected'
                    })
        
        # Calculate overall severity
        if results['alerts']:
            results['severity_score'] = max(a['severity'] for a in results['alerts'])
        
        # Person count alert
        if len(persons) > 5:
            results['alerts'].append({
                'type': 'crowd_detected',
                'severity': 6,
                'description': f'{len(persons)} people detected in frame'
            })
        
        return results
    
    def get_severity_label(self, score):
        """Convert severity score to label"""
        if score >= 8:
            return 'critical'
        elif score >= 6:
            return 'high'
        elif score >= 4:
            return 'medium'
        elif score >= 2:
            return 'low'
        return 'info'