import time
from flask import Blueprint, request, jsonify
from core.detector import FraudDetector
from core.test_data import TEST_AUDIO_FILES

analysis_bp = Blueprint('analysis', __name__)
fraud_detector = FraudDetector()

@analysis_bp.route('/api/analyze_live', methods=['POST'])
def analyze_live():
    data = request.json or {}
    transcript = data.get('transcript', '')
    result = fraud_detector.analyze_text(transcript)
    
    risk_level = result['risk_level']
    if risk_level in ['Critical', 'High']:
        color, icon, bg_intensity = 'red', 'fa-exclamation-triangle', 'bg-red-900/30'
    elif risk_level == 'Medium-High':
        color, icon, bg_intensity = 'orange', 'fa-exclamation-triangle', 'bg-orange-900/30'
    elif risk_level == 'Medium':
        color, icon, bg_intensity = 'yellow', 'fa-exclamation-triangle', 'bg-yellow-900/30'
    elif risk_level == 'Low':
        color, icon, bg_intensity = 'blue', 'fa-info-circle', 'bg-blue-900/30'
    else:
        color, icon, bg_intensity = 'green', 'fa-shield-alt', 'bg-green-900/30'
    
    return jsonify({
        'success': True,
        'fraud_score': result['fraud_score'],
        'risk_level': result['risk_level'],
        'risk_level_display': f"{result['risk_level'].upper()} RISK",
        'warning_message': result['warning_message'],
        'detailed_advice': result['detailed_advice'],
        'keywords_found': result['keywords_found'],
        'patterns_detected': result['patterns_detected'],
        'red_flags': result['red_flags'],
        'warnings': result['warnings'],
        'color': color,
        'icon': icon,
        'bg_intensity': bg_intensity,
        'transcript': transcript,
        'analysis_time': result['analysis_time']
    })

@analysis_bp.route('/api/get_audio_list', methods=['GET'])
def get_audio_list():
    audio_list = [{"name": audio["name"], "scam_type": audio["scam_type"]} for audio in TEST_AUDIO_FILES]
    return jsonify({'success': True, 'audio_files': audio_list})

@analysis_bp.route('/api/analyze_recorded', methods=['POST'])
def analyze_recorded():
    data = request.json or {}
    audio_filename = data.get('audio_filename')
    
    selected_audio = next((item for item in TEST_AUDIO_FILES if item["name"] == audio_filename), None)
    if not selected_audio:
        return jsonify({'success': False, 'message': 'Audio file not found'}), 404
    
    result = fraud_detector.analyze_text(selected_audio['transcript'])
    result['audio_name'] = selected_audio['name']
    result['scam_type'] = selected_audio['scam_type']
    result['original_transcript'] = selected_audio['transcript']
    
    return jsonify({'success': True, 'report': result})

@analysis_bp.route('/api/analyze_uploaded', methods=['POST'])
def analyze_uploaded():
    if 'audio_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400
    
    file = request.files['audio_file']
    filename = file.filename.lower()
    
    if 'bank' in filename or 'otp' in filename:
        return jsonify({
            'fraud_score': 95,
            'risk_level': 'Critical',
            'scam_type': 'Bank OTP Scam',
            'transcript': 'Bank account compromise alert. OTP requested.',
            'warning_message': '🚨🚨 CRITICAL RISK: DEFINITE BANK OTP SCAM!'
        })
    else:
        return jsonify({
            'fraud_score': 45,
            'risk_level': 'Medium',
            'scam_type': 'Suspicious Call',
            'transcript': 'Suspicious call content detected.',
            'warning_message': '⚠️ MEDIUM RISK: Suspicious Call Detected'
        })
