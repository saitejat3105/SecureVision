#voice_routes.py
from flask import Blueprint, request, jsonify, send_file
from services.audio_service import AudioService
import os
import uuid
from config import Config

voice_bp = Blueprint('voice', __name__)
audio_service = AudioService()

@voice_bp.route('/record/start', methods=['POST'])
def start_recording():
    success = audio_service.start_recording()
    return jsonify({'success': success})

@voice_bp.route('/record/stop', methods=['POST'])
def stop_recording():
    audio_data = audio_service.stop_recording()
    
    if audio_data:
        filename = f"recording_{uuid.uuid4().hex[:8]}.wav"
        filepath = audio_service.save_audio(audio_data, filename)
        
        return jsonify({
            'success': True,
            'path': filepath,
            'filename': filename
        })
    
    return jsonify({'success': False, 'error': 'No audio data'})

@voice_bp.route('/play', methods=['POST'])
def play_audio():
    data = request.json
    filepath = data.get('path')
    
    if filepath and os.path.exists(filepath):
        success = audio_service.play_audio(filepath)
        return jsonify({'success': success})
    
    return jsonify({'success': False, 'error': 'File not found'})

@voice_bp.route('/tts', methods=['POST'])
def text_to_speech():
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'Text required'}), 400
    
    success = audio_service.text_to_speech(text)
    return jsonify({'success': success})

@voice_bp.route('/decoy/<message_type>', methods=['POST'])
def play_decoy(message_type):
    success = audio_service.play_decoy_message(message_type)
    return jsonify({'success': success})

@voice_bp.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    file = request.files['audio']
    filename = f"message_{uuid.uuid4().hex[:8]}.wav"
    filepath = os.path.join(Config.AUDIO_DIR, filename)
    file.save(filepath)
    
    # Play the uploaded audio
    audio_service.play_audio(filepath)
    
    return jsonify({
        'success': True,
        'path': filepath
    })

@voice_bp.route('/stream', methods=['GET'])
def audio_stream():
    """Stream live audio from camera mic"""
    # This would require WebSocket for real-time
    # For now, return audio file list
    audio_files = []
    for f in os.listdir(Config.AUDIO_DIR):
        if f.endswith('.wav'):
            audio_files.append(f)
    
    return jsonify({'files': audio_files})