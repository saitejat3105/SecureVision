#training_service.py
import os
import cv2
import numpy as np
import shutil
from datetime import datetime
from config import Config
from models.face_recognition import FaceRecognizer

class TrainingService:
    def __init__(self):
        self.face_recognizer = FaceRecognizer()
        self.is_training = False
        self.training_progress = 0
        self.haar_cascade = cv2.CascadeClassifier(
            os.path.join(Config.HAARCASCADES_DIR, 'haarcascade_frontalface_default.xml')
        )
    
    def collect_images(self, camera_service, camera_id, person_name, num_images=20, interval=2):
        """Collect face images for training"""
        person_dir = os.path.join(Config.TRAIN_DIR, person_name)
        os.makedirs(person_dir, exist_ok=True)
        
        collected = 0
        while collected < num_images:
            frame = camera_service.get_frame(camera_id)
            if frame is None:
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.haar_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                x, y, w, h = faces[0]
                face = frame[y:y+h, x:x+w]
                
                # Save face image
                filename = f"{person_name}_{collected:03d}.jpg"
                filepath = os.path.join(person_dir, filename)
                cv2.imwrite(filepath, face)
                
                collected += 1
                yield {
                    'collected': collected,
                    'total': num_images,
                    'progress': collected / num_images * 100,
                    'image_path': filepath
                }
            
            cv2.waitKey(int(interval * 1000))
    
    def auto_capture(self, camera_service, camera_id, person_name, duration=30, interval=2):
        """Auto capture images at regular intervals"""
        person_dir = os.path.join(Config.TRAIN_DIR, person_name)
        os.makedirs(person_dir, exist_ok=True)
        
        import time
        start_time = time.time()
        count = 0
        
        while (time.time() - start_time) < duration:
            frame = camera_service.get_frame(camera_id)
            if frame is None:
                time.sleep(0.1)
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.haar_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                x, y, w, h = faces[0]
                face = frame[y:y+h, x:x+w]
                
                filename = f"{person_name}_{count:03d}.jpg"
                filepath = os.path.join(person_dir, filename)
                cv2.imwrite(filepath, face)
                count += 1
            
            time.sleep(interval)
        
        return count
    
    def train_models(self, callback=None):
        """Train all face recognition models"""
        if self.is_training:
            return False, "Training already in progress"
        
        self.is_training = True
        self.training_progress = 0
        
        try:
            # Count total training images
            total_images = 0
            for person in os.listdir(Config.TRAIN_DIR):
                person_dir = os.path.join(Config.TRAIN_DIR, person)
                if os.path.isdir(person_dir):
                    total_images += len(os.listdir(person_dir))
            
            if callback:
                callback({'status': 'starting', 'total_images': total_images})
            
            # Split data
            self._split_train_test()
            
            if callback:
                callback({'status': 'splitting', 'progress': 20})
            
            # Train models
            success, results = self.face_recognizer.train()
            
            if callback:
                callback({'status': 'complete', 'progress': 100, 'results': results})
            
            self.is_training = False
            return success, results
            
        except Exception as e:
            self.is_training = False
            return False, str(e)
    
    def _split_train_test(self, test_ratio=0.2):
        """Split data into train and test sets"""
        os.makedirs(Config.TEST_DIR, exist_ok=True)
        
        for person in os.listdir(Config.TRAIN_DIR):
            person_train_dir = os.path.join(Config.TRAIN_DIR, person)
            if not os.path.isdir(person_train_dir):
                continue
            
            person_test_dir = os.path.join(Config.TEST_DIR, person)
            os.makedirs(person_test_dir, exist_ok=True)
            
            images = os.listdir(person_train_dir)
            np.random.shuffle(images)
            
            test_count = int(len(images) * test_ratio)
            test_images = images[:test_count]
            
            for img in test_images:
                src = os.path.join(person_train_dir, img)
                dst = os.path.join(person_test_dir, img)
                shutil.copy(src, dst)
    
    def incremental_train(self, person_name, images):
        """Incrementally train model with new images"""
        count = self.face_recognizer.add_face(person_name, images)
        return count
    
    def get_training_status(self):
        """Get current training status"""
        return {
            'is_training': self.is_training,
            'progress': self.training_progress
        }
    
    def get_people_list(self):
        """Get list of trained people"""
        people = []
        for person in os.listdir(Config.TRAIN_DIR):
            person_dir = os.path.join(Config.TRAIN_DIR, person)
            if os.path.isdir(person_dir):
                image_count = len([f for f in os.listdir(person_dir) if f.endswith(('.jpg', '.png'))])
                people.append({
                    'name': person,
                    'image_count': image_count,
                    'path': person_dir
                })
        return people
    
    def delete_person(self, person_name):
        """Delete person from training data"""
        person_dir = os.path.join(Config.TRAIN_DIR, person_name)
        if os.path.exists(person_dir):
            shutil.rmtree(person_dir)
            return True
        return False