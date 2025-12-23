#face_recognition.py
import cv2
import numpy as np
import os
import pickle
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from config import Config

class FaceRecognizer:
    def __init__(self):
        self.haar_cascade = cv2.CascadeClassifier(
            os.path.join(Config.HAARCASCADES_DIR, 'haarcascade_frontalface_default.xml')
        )
        self.face_size = Config.FACE_SIZE
        self.threshold = Config.FACE_CONFIDENCE_THRESHOLD
        
        # Models
        self.svm_model = None
        self.knn_model = None
        self.rf_model = None
        self.label_encoder = LabelEncoder()
        
        # Embeddings storage
        self.known_embeddings = []
        self.known_labels = []
        
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models if available"""
        try:
            svm_path = os.path.join(Config.TRAINED_MODELS_DIR, 'face_svm.pkl')
            if os.path.exists(svm_path):
                with open(svm_path, 'rb') as f:
                    self.svm_model = pickle.load(f)
            
            knn_path = os.path.join(Config.TRAINED_MODELS_DIR, 'face_knn.pkl')
            if os.path.exists(knn_path):
                with open(knn_path, 'rb') as f:
                    self.knn_model = pickle.load(f)
            
            rf_path = os.path.join(Config.TRAINED_MODELS_DIR, 'face_rf.pkl')
            if os.path.exists(rf_path):
                with open(rf_path, 'rb') as f:
                    self.rf_model = pickle.load(f)
            
            embeddings_path = os.path.join(Config.TRAINED_MODELS_DIR, 'face_embeddings.pkl')
            if os.path.exists(embeddings_path):
                with open(embeddings_path, 'rb') as f:
                    data = pickle.load(f)
                    self.known_embeddings = data['embeddings']
                    self.known_labels = data['labels']
            
            encoder_path = os.path.join(Config.TRAINED_MODELS_DIR, 'label_encoder.pkl')
            if os.path.exists(encoder_path):
                with open(encoder_path, 'rb') as f:
                    self.label_encoder = pickle.load(f)
                    
            print("Face recognition models loaded successfully")
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def detect_faces(self, frame):
        """Detect faces in frame using Haar Cascade"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.haar_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        return faces
    
    def extract_embedding(self, face_image):
        """Extract face embedding using histogram-based features"""
        # Resize to standard size
        face = cv2.resize(face_image, self.face_size)
        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY) if len(face.shape) == 3 else face
        
        # Compute LBP histogram
        lbp = self._compute_lbp(gray)
        hist_lbp, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
        
        # Compute HOG-like features
        hog = self._compute_hog(gray)
        
        # Combine features
        embedding = np.concatenate([hist_lbp, hog])
        embedding = embedding / (np.linalg.norm(embedding) + 1e-7)
        
        return embedding
    
    def _compute_lbp(self, image, radius=1, neighbors=8):
        """Compute Local Binary Pattern"""
        rows, cols = image.shape
        lbp = np.zeros_like(image, dtype=np.uint8)
        
        for i in range(radius, rows - radius):
            for j in range(radius, cols - radius):
                center = image[i, j]
                code = 0
                for k in range(neighbors):
                    angle = 2 * np.pi * k / neighbors
                    x = int(round(i + radius * np.cos(angle)))
                    y = int(round(j - radius * np.sin(angle)))
                    if image[x, y] >= center:
                        code |= (1 << k)
                lbp[i, j] = code
        
        return lbp
    
    def _compute_hog(self, image, cell_size=16, bins=9):
        """Compute HOG features"""
        # Compute gradients
        gx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        
        magnitude = np.sqrt(gx**2 + gy**2)
        angle = np.arctan2(gy, gx) * (180 / np.pi) % 180
        
        # Compute histogram for each cell
        h, w = image.shape
        features = []
        
        for i in range(0, h - cell_size, cell_size):
            for j in range(0, w - cell_size, cell_size):
                cell_mag = magnitude[i:i+cell_size, j:j+cell_size]
                cell_angle = angle[i:i+cell_size, j:j+cell_size]
                
                hist, _ = np.histogram(
                    cell_angle.ravel(), bins=bins, range=(0, 180),
                    weights=cell_mag.ravel()
                )
                features.extend(hist)
        
        return np.array(features)
    
    def recognize(self, face_image):
        """Recognize face and return label with confidence"""
        if self.svm_model is None and len(self.known_embeddings) == 0:
            return "unknown", 0.0
        
        embedding = self.extract_embedding(face_image)
        
        results = []
        
        # SVM prediction
        if self.svm_model is not None:
            try:
                proba = self.svm_model.predict_proba([embedding])[0]
                pred_idx = np.argmax(proba)
                results.append(('svm', self.label_encoder.classes_[pred_idx], proba[pred_idx]))
            except:
                pass
        
        # KNN prediction
        if self.knn_model is not None:
            try:
                proba = self.knn_model.predict_proba([embedding])[0]
                pred_idx = np.argmax(proba)
                results.append(('knn', self.label_encoder.classes_[pred_idx], proba[pred_idx]))
            except:
                pass
        
        # Random Forest prediction
        if self.rf_model is not None:
            try:
                proba = self.rf_model.predict_proba([embedding])[0]
                pred_idx = np.argmax(proba)
                results.append(('rf', self.label_encoder.classes_[pred_idx], proba[pred_idx]))
            except:
                pass
        
        # Distance-based matching
        if len(self.known_embeddings) > 0:
            distances = [np.linalg.norm(embedding - known) for known in self.known_embeddings]
            min_idx = np.argmin(distances)
            min_dist = distances[min_idx]
            confidence = max(0, 1 - min_dist)
            results.append(('distance', self.known_labels[min_idx], confidence))
        
        if not results:
            return "unknown", 0.0
        
        # Ensemble voting
        label_scores = {}
        for method, label, conf in results:
            if label not in label_scores:
                label_scores[label] = []
            label_scores[label].append(conf)
        
        best_label = max(label_scores, key=lambda x: np.mean(label_scores[x]))
        avg_confidence = np.mean(label_scores[best_label])
        
        if avg_confidence < self.threshold:
            return "unknown", avg_confidence
        
        return best_label, avg_confidence
    
    def train(self, train_dir=None):
        """Train face recognition models"""
        if train_dir is None:
            train_dir = Config.TRAIN_DIR
        
        embeddings = []
        labels = []
        
        for person_name in os.listdir(train_dir):
            person_dir = os.path.join(train_dir, person_name)
            if not os.path.isdir(person_dir):
                continue
            
            for img_name in os.listdir(person_dir):
                img_path = os.path.join(person_dir, img_name)
                img = cv2.imread(img_path)
                if img is None:
                    continue
                
                embedding = self.extract_embedding(img)
                embeddings.append(embedding)
                labels.append(person_name)
        
        if len(embeddings) < 2:
            return False, "Need at least 2 images to train"
        
        embeddings = np.array(embeddings)
        labels = np.array(labels)
        
        # Fit label encoder
        self.label_encoder.fit(labels)
        encoded_labels = self.label_encoder.transform(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            embeddings, encoded_labels, test_size=0.2, random_state=42
        )
        
        # Train SVM
        self.svm_model = SVC(kernel='rbf', probability=True, C=1.0)
        self.svm_model.fit(X_train, y_train)
        svm_acc = self.svm_model.score(X_test, y_test) if len(X_test) > 0 else 0
        
        # Train KNN
        n_neighbors = min(5, len(X_train))
        self.knn_model = KNeighborsClassifier(n_neighbors=n_neighbors)
        self.knn_model.fit(X_train, y_train)
        knn_acc = self.knn_model.score(X_test, y_test) if len(X_test) > 0 else 0
        
        # Train Random Forest
        self.rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.rf_model.fit(X_train, y_train)
        rf_acc = self.rf_model.score(X_test, y_test) if len(X_test) > 0 else 0
        
        # Store embeddings
        self.known_embeddings = embeddings.tolist()
        self.known_labels = labels.tolist()
        
        # Save models
        self._save_models()
        
        return True, {
            'svm_accuracy': svm_acc,
            'knn_accuracy': knn_acc,
            'rf_accuracy': rf_acc,
            'total_samples': len(embeddings),
            'classes': list(self.label_encoder.classes_)
        }
    
    def _save_models(self):
        """Save trained models"""
        os.makedirs(Config.TRAINED_MODELS_DIR, exist_ok=True)
        
        if self.svm_model:
            with open(os.path.join(Config.TRAINED_MODELS_DIR, 'face_svm.pkl'), 'wb') as f:
                pickle.dump(self.svm_model, f)
        
        if self.knn_model:
            with open(os.path.join(Config.TRAINED_MODELS_DIR, 'face_knn.pkl'), 'wb') as f:
                pickle.dump(self.knn_model, f)
        
        if self.rf_model:
            with open(os.path.join(Config.TRAINED_MODELS_DIR, 'face_rf.pkl'), 'wb') as f:
                pickle.dump(self.rf_model, f)
        
        with open(os.path.join(Config.TRAINED_MODELS_DIR, 'face_embeddings.pkl'), 'wb') as f:
            pickle.dump({'embeddings': self.known_embeddings, 'labels': self.known_labels}, f)
        
        with open(os.path.join(Config.TRAINED_MODELS_DIR, 'label_encoder.pkl'), 'wb') as f:
            pickle.dump(self.label_encoder, f)
    
    def add_face(self, name, images):
        """Add new face to the system (incremental learning)"""
        person_dir = os.path.join(Config.TRAIN_DIR, name)
        os.makedirs(person_dir, exist_ok=True)
        
        for i, img in enumerate(images):
            img_path = os.path.join(person_dir, f'{name}_{i:03d}.jpg')
            cv2.imwrite(img_path, img)
            
            embedding = self.extract_embedding(img)
            self.known_embeddings.append(embedding)
            self.known_labels.append(name)
        
        # Retrain models incrementally
        self.train()
        
        return len(images)