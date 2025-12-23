#alarm_service.py
import os
import threading
import time
from config import Config

class AlarmService:
    def __init__(self):
        self.is_alarming = False
        self.alarm_thread = None
        self.alarm_file = os.path.join(Config.AUDIO_DIR, 'alarm.wav')
    
    def trigger_alarm(self, duration=10):
        """Trigger alarm sound"""
        if self.is_alarming:
            return False
        
        self.is_alarming = True
        self.alarm_thread = threading.Thread(target=self._alarm_loop, args=(duration,))
        self.alarm_thread.daemon = True
        self.alarm_thread.start()
        
        return True
    
    def _alarm_loop(self, duration):
        """Alarm sound loop"""
        start_time = time.time()
        
        while self.is_alarming and (time.time() - start_time) < duration:
            try:
                if os.path.exists(self.alarm_file):
                    from playsound import playsound
                    playsound(self.alarm_file)
                else:
                    # Generate beep sound
                    self._generate_beep()
            except Exception as e:
                print(f"Alarm error: {e}")
                self._generate_beep()
            
            time.sleep(0.5)
        
        self.is_alarming = False
    
    def _generate_beep(self):
        """Generate beep sound using system"""
        try:
            import winsound
            winsound.Beep(1000, 500)  # 1000Hz for 500ms
        except:
            # Linux/Mac fallback
            os.system('printf "\a"')
    
    def stop_alarm(self):
        """Stop alarm"""
        self.is_alarming = False
    
    def escalate_alarm(self, level):
        """Escalate alarm based on severity level"""
        durations = {
            1: 5,   # Low - 5 seconds
            2: 10,  # Medium - 10 seconds
            3: 30,  # High - 30 seconds
            4: 60,  # Critical - 60 seconds
            5: 120  # Emergency - 2 minutes
        }
        
        duration = durations.get(level, 10)
        return self.trigger_alarm(duration)
    
    def get_status(self):
        """Get alarm status"""
        return {
            'is_active': self.is_alarming
        }