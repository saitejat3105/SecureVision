#image_utils.py
import cv2
import numpy as np
import os

def resize_image(image, target_size):
    """Resize image maintaining aspect ratio"""
    h, w = image.shape[:2]
    target_w, target_h = target_size
    
    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    resized = cv2.resize(image, (new_w, new_h))
    
    # Add padding if needed
    delta_w = target_w - new_w
    delta_h = target_h - new_h
    top = delta_h // 2
    bottom = delta_h - top
    left = delta_w // 2
    right = delta_w - left
    
    padded = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    
    return padded

def crop_face(image, bbox, padding=20):
    """Crop face from image with padding"""
    x, y, w, h = bbox
    h_img, w_img = image.shape[:2]
    
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(w_img, x + w + padding)
    y2 = min(h_img, y + h + padding)
    
    return image[y1:y2, x1:x2]

def draw_detections(frame, detections, color=(0, 255, 0)):
    """Draw detection boxes on frame"""
    for det in detections:
        bbox = det.get('bbox')
        if bbox:
            x, y, w, h = bbox
            label = det.get('label', '')
            confidence = det.get('confidence', 0)
            
            # Draw box
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw label
            text = f"{label}: {confidence:.2f}"
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return frame

def enhance_contrast(image):
    """Enhance image contrast using CLAHE"""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    
    enhanced = cv2.merge([l, a, b])
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

def denoise_image(image):
    """Denoise image"""
    return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

def detect_blur(image, threshold=100):
    """Detect if image is blurry"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var < threshold, laplacian_var

def get_image_brightness(image):
    """Get average brightness of image"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return np.mean(gray)

def apply_thermal_colormap(image):
    """Apply thermal-like colormap to image"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.applyColorMap(gray, cv2.COLORMAP_JET)