#audio_service.py
import os
import threading
import time
import wave
import numpy as np
from config import Config

class AudioService:
    def __init__(self):
        self.is_recording = False
        self.is_playing = False
        self.audio_buffer = []
        self.sample_rate = 44100
        self.channels = 1
        self.chunk_size = 1024
        
        # Try to initialize audio
        self.pyaudio = None
        self.stream = None
        self._init_audio()
    
    def _init_audio(self):
        """Initialize PyAudio"""
        try:
            import pyaudio
            self.pyaudio = pyaudio.PyAudio()
            print("Audio service initialized")
        except Exception as e:
            print(f"Could not initialize audio: {e}")
    
    def start_recording(self):
        """Start recording audio"""
        if self.pyaudio is None or self.is_recording:
            return False
        
        self.is_recording = True
        self.audio_buffer = []
        
        thread = threading.Thread(target=self._record_loop)
        thread.daemon = True
        thread.start()
        
        return True
    
    def _record_loop(self):
        """Recording loop"""
        try:
            stream = self.pyaudio.open(
                format=self.pyaudio.get_format_from_width(2),
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            while self.is_recording:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                self.audio_buffer.append(data)
            
            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"Recording error: {e}")
            self.is_recording = False
    
    def stop_recording(self):
        """Stop recording and return audio data"""
        self.is_recording = False
        time.sleep(0.1)
        return b''.join(self.audio_buffer)
    
    def save_audio(self, audio_data, filename):
        """Save audio data to file"""
        filepath = os.path.join(Config.AUDIO_DIR, filename)
        
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)
        
        return filepath
    
    def play_audio(self, filepath):
        """Play audio file"""
        if self.is_playing:
            return False
        
        thread = threading.Thread(target=self._play_audio, args=(filepath,))
        thread.daemon = True
        thread.start()
        return True
    
    def _play_audio(self, filepath):
        """Play audio file thread"""
        self.is_playing = True
        
        try:
            # Try playsound first
            from playsound import playsound
            playsound(filepath)
        except:
            # Fallback to PyAudio
            try:
                if self.pyaudio and os.path.exists(filepath):
                    wf = wave.open(filepath, 'rb')
                    stream = self.pyaudio.open(
                        format=self.pyaudio.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True
                    )
                    
                    data = wf.readframes(self.chunk_size)
                    while data:
                        stream.write(data)
                        data = wf.readframes(self.chunk_size)
                    
                    stream.stop_stream()
                    stream.close()
                    wf.close()
            except Exception as e:
                print(f"Audio playback error: {e}")
        
        self.is_playing = False
    
    def text_to_speech(self, text):
        """Convert text to speech and play"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 1.0)
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception as e:
            print(f"TTS error: {e}")
            return False
    
    def play_decoy_message(self, message_type='security'):
        """Play pre-recorded decoy message"""
        messages = {
            'security': 'security_activated.wav',
            'monitoring': 'you_are_monitored.wav',
            'alarm': 'alarm.wav'
        }
        
        filename = messages.get(message_type, 'security_activated.wav')
        filepath = os.path.join(Config.AUDIO_DIR, filename)
        
        if os.path.exists(filepath):
            return self.play_audio(filepath)
        else:
            # Generate with TTS
            texts = {
                'security': 'Security system activated. You are being recorded.',
                'monitoring': 'Warning. You are being monitored. Please leave the premises.',
                'alarm': 'Intruder alert. Authorities have been notified.'
            }
            return self.text_to_speech(texts.get(message_type, ''))
    
    def get_audio_stream(self):
        """Get live audio stream for web"""
        if self.pyaudio is None:
            return None
        
        try:
            stream = self.pyaudio.open(
                format=self.pyaudio.get_format_from_width(2),
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            return stream
        except:
            return None