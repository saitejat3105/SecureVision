#storage_service.py
import os
import cv2
import shutil
from datetime import datetime, timedelta
from config import Config

class StorageService:
    def __init__(self):
        self.intruders_dir = Config.INTRUDERS_DIR
        self.max_images = Config.MAX_INTRUDER_IMAGES
        self.auto_delete_days = Config.AUTO_DELETE_DAYS
    
    def save_intruder_image(self, frame, camera_id, metadata=None):
        """Save intruder image with smart naming"""
        timestamp = datetime.now()
        
        # Create filename with metadata
        parts = [
            'intruder',
            timestamp.strftime('%Y-%m-%d_%H-%M-%S'),
            camera_id
        ]
        
        if metadata:
            if metadata.get('is_masked'):
                parts.append('masked')
            if metadata.get('weapon_detected'):
                parts.append('weapon')
            if metadata.get('is_running'):
                parts.append('running')
            if metadata.get('severity', 0) > 7:
                parts.append('critical')
        
        filename = '_'.join(parts) + '.jpg'
        filepath = os.path.join(self.intruders_dir, filename)
        
        # Save full frame
        cv2.imwrite(filepath, frame)
        
        # Save cropped face if available
        cropped_path = None
        if metadata and 'face_bbox' in metadata:
            x, y, w, h = metadata['face_bbox']
            face = frame[y:y+h, x:x+w]
            cropped_filename = filename.replace('.jpg', '_face.jpg')
            cropped_path = os.path.join(self.intruders_dir, cropped_filename)
            cv2.imwrite(cropped_path, face)
        
        # Check storage limits
        self._enforce_storage_limits()
        
        return {
            'full_path': filepath,
            'cropped_path': cropped_path,
            'filename': filename,
            'timestamp': timestamp.isoformat()
        }
    
    def _enforce_storage_limits(self):
        """Enforce storage limits by deleting old images"""
        files = []
        for f in os.listdir(self.intruders_dir):
            filepath = os.path.join(self.intruders_dir, f)
            if os.path.isfile(filepath):
                files.append((filepath, os.path.getmtime(filepath)))
        
        # Sort by modification time
        files.sort(key=lambda x: x[1])
        
        # Delete oldest if over limit
        while len(files) > self.max_images:
            os.remove(files[0][0])
            files.pop(0)
    
    def cleanup_old_files(self):
        """Delete files older than auto_delete_days"""
        cutoff = datetime.now() - timedelta(days=self.auto_delete_days)
        cutoff_timestamp = cutoff.timestamp()
        
        deleted = 0
        for f in os.listdir(self.intruders_dir):
            filepath = os.path.join(self.intruders_dir, f)
            if os.path.isfile(filepath):
                if os.path.getmtime(filepath) < cutoff_timestamp:
                    os.remove(filepath)
                    deleted += 1
        
        return deleted
    
    def get_intruder_images(self, camera_id=None, limit=50, offset=0):
        """Get list of intruder images"""
        files = []
        for f in os.listdir(self.intruders_dir):
            if not f.startswith('intruder_'):
                continue
            
            if camera_id and camera_id not in f:
                continue
            
            filepath = os.path.join(self.intruders_dir, f)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files.append({
                    'filename': f,
                    'path': filepath,
                    'size': stat.st_size,
                    'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'is_critical': 'critical' in f,
                    'has_weapon': 'weapon' in f,
                    'is_masked': 'masked' in f
                })
        
        # Sort by timestamp (newest first)
        files.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return files[offset:offset + limit]
    
    def get_storage_stats(self):
        """Get storage statistics"""
        total_size = 0
        file_count = 0
        
        for f in os.listdir(self.intruders_dir):
            filepath = os.path.join(self.intruders_dir, f)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
                file_count += 1
        
        return {
            'total_files': file_count,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'max_files': self.max_images,
            'usage_percent': round(file_count / self.max_images * 100, 1)
        }
    
    def archive_old_logs(self, days_old=30):
        """Archive old intruder logs to compressed folder"""
        archive_dir = os.path.join(self.intruders_dir, 'archive')
        os.makedirs(archive_dir, exist_ok=True)
        
        cutoff = datetime.now() - timedelta(days=days_old)
        archived = 0
        
        for f in os.listdir(self.intruders_dir):
            filepath = os.path.join(self.intruders_dir, f)
            if os.path.isfile(filepath) and not f.startswith('.'):
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < cutoff:
                    shutil.move(filepath, os.path.join(archive_dir, f))
                    archived += 1
        
        return archived
    
    def delete_image(self, filename):
        """Delete specific intruder image"""
        filepath = os.path.join(self.intruders_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    
    def delete_all_images(self):
        """Delete all intruder images (with confirmation)"""
        count = 0
        for f in os.listdir(self.intruders_dir):
            filepath = os.path.join(self.intruders_dir, f)
            if os.path.isfile(filepath):
                os.remove(filepath)
                count += 1
        return count