#audio_utils.py
import numpy as np
import wave
import os

def normalize_audio(audio_data, target_db=-20):
    """Normalize audio level"""
    audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
    
    rms = np.sqrt(np.mean(audio ** 2))
    if rms > 0:
        target_rms = 10 ** (target_db / 20) * 32768
        gain = target_rms / rms
        audio = audio * gain
    
    audio = np.clip(audio, -32768, 32767).astype(np.int16)
    return audio.tobytes()

def remove_noise(audio_data, noise_threshold=500):
    """Simple noise gate"""
    audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
    
    # Apply noise gate
    audio[np.abs(audio) < noise_threshold] = 0
    
    return audio.astype(np.int16).tobytes()

def convert_sample_rate(audio_data, orig_rate, target_rate):
    """Resample audio"""
    from scipy import signal
    
    audio = np.frombuffer(audio_data, dtype=np.int16)
    
    # Calculate resampling ratio
    ratio = target_rate / orig_rate
    new_length = int(len(audio) * ratio)
    
    resampled = signal.resample(audio, new_length).astype(np.int16)
    return resampled.tobytes()

def get_audio_duration(filepath):
    """Get duration of audio file in seconds"""
    with wave.open(filepath, 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / rate

def merge_audio_files(filepaths, output_path):
    """Merge multiple audio files"""
    if not filepaths:
        return False
    
    # Read first file to get parameters
    with wave.open(filepaths[0], 'rb') as wf:
        params = wf.getparams()
    
    # Merge all files
    all_frames = []
    for fp in filepaths:
        with wave.open(fp, 'rb') as wf:
            all_frames.append(wf.readframes(wf.getnframes()))
    
    # Write output
    with wave.open(output_path, 'wb') as wf:
        wf.setparams(params)
        for frames in all_frames:
            wf.writeframes(frames)
    
    return True