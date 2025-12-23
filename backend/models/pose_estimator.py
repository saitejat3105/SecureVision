#poseEstimator.py
import cv2
import numpy as np

class PoseEstimator:
    def __init__(self):
        self.mp_pose = None
        self.pose = None
        self._load_model()
    
    def _load_model(self):
        """Load MediaPipe pose estimator"""
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                enable_segmentation=False,
                min_detection_confidence=0.5
            )
            self.mp_drawing = mp.solutions.drawing_utils
            print("MediaPipe pose estimator loaded")
        except Exception as e:
            print(f"Could not load pose estimator: {e}")
    
    def estimate(self, frame):
        """Estimate pose in frame"""
        if self.pose is None:
            return None
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)
        
        if results.pose_landmarks:
            return self._analyze_pose(results.pose_landmarks, frame.shape)
        return None
    
    def _analyze_pose(self, landmarks, frame_shape):
        """Analyze pose for suspicious behavior"""
        h, w = frame_shape[:2]
        
        # Extract key points
        points = {}
        for idx, landmark in enumerate(landmarks.landmark):
            points[idx] = {
                'x': landmark.x * w,
                'y': landmark.y * h,
                'visibility': landmark.visibility
            }
        
        analysis = {
            'is_crouching': self._is_crouching(points),
            'is_crawling': self._is_crawling(points),
            'is_raising_arm': self._is_raising_arm(points),
            'body_orientation': self._get_orientation(points),
            'pose_confidence': np.mean([p['visibility'] for p in points.values()])
        }
        
        return analysis
    
    def _is_crouching(self, points):
        """Detect crouching pose"""
        try:
            hip_y = (points[23]['y'] + points[24]['y']) / 2  # Hips
            knee_y = (points[25]['y'] + points[26]['y']) / 2  # Knees
            ankle_y = (points[27]['y'] + points[28]['y']) / 2  # Ankles
            
            # In crouching, knees are significantly bent
            hip_knee_dist = abs(knee_y - hip_y)
            knee_ankle_dist = abs(ankle_y - knee_y)
            
            return hip_knee_dist < knee_ankle_dist * 0.7
        except:
            return False
    
    def _is_crawling(self, points):
        """Detect crawling pose"""
        try:
            nose_y = points[0]['y']
            hip_y = (points[23]['y'] + points[24]['y']) / 2
            
            # In crawling, nose is close to hip level
            return abs(nose_y - hip_y) < 50
        except:
            return False
    
    def _is_raising_arm(self, points):
        """Detect raised arm (potential threat gesture)"""
        try:
            # Check if either wrist is above shoulder
            left_shoulder_y = points[11]['y']
            right_shoulder_y = points[12]['y']
            left_wrist_y = points[15]['y']
            right_wrist_y = points[16]['y']
            
            left_raised = left_wrist_y < left_shoulder_y - 30
            right_raised = right_wrist_y < right_shoulder_y - 30
            
            return left_raised or right_raised
        except:
            return False
    
    def _get_orientation(self, points):
        """Get body orientation"""
        try:
            left_shoulder = points[11]
            right_shoulder = points[12]
            
            shoulder_diff = left_shoulder['x'] - right_shoulder['x']
            
            if abs(shoulder_diff) < 30:
                return 'facing_camera'
            elif shoulder_diff > 0:
                return 'facing_left'
            else:
                return 'facing_right'
        except:
            return 'unknown'
    
    def draw_pose(self, frame, landmarks):
        """Draw pose landmarks on frame"""
        if self.mp_drawing and landmarks:
            self.mp_drawing.draw_landmarks(
                frame, landmarks, self.mp_pose.POSE_CONNECTIONS
            )
        return frame