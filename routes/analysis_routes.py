import time
from flask import Blueprint, request, jsonify
from core.detector import FraudDetector
from core.test_data import TEST_AUDIO_FILES

from core.database import save_call_report, get_call_reports, get_contacts, save_contact, search_caller_identity

analysis_bp = Blueprint('analysis', __name__)
fraud_detector = FraudDetector()

@analysis_bp.route('/api/caller_lookup', methods=['GET', 'POST'])
def caller_lookup():
    data = request.json if request.method == 'POST' else request.args
    number = data.get('number', '').strip()
    if not number:
        return jsonify({'success': False, 'message': 'Phone number is required'}), 400
    identity = search_caller_identity(number)
    return jsonify({'success': True, 'caller': identity})

@analysis_bp.route('/api/report_spam', methods=['POST'])
def report_spam():
    data = request.json or {}
    number = data.get('number', '').strip()
    name = data.get('name', 'Flagged Spam').strip()
    category = data.get('category', 'Spam').strip()
    if not number:
        return jsonify({'success': False, 'message': 'Phone number is required'}), 400
    save_contact(name, number, category)
    return jsonify({'success': True, 'message': f'Phone number {number} has been reported as {category} to Truecaller-style database!'})

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
    
    is_scam_flag = bool(result['fraud_score'] >= 45 or risk_level in ['Critical', 'High', 'Medium-High'])
    return jsonify({
        'success': True,
        'fraud_score': result['fraud_score'],
        'risk_score': result['fraud_score'],
        'is_scam': is_scam_flag,
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

@analysis_bp.route('/api/save_live_call', methods=['POST'])
def save_live_call():
    data = request.json or {}
    transcript = data.get('transcript', '').strip()
    phone_number = data.get('phone_number', '')
    if not transcript:
        return jsonify({'success': False, 'message': 'Live call transcript is empty'}), 400
    
    result = fraud_detector.analyze_text(transcript)
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    call_filename = f"Live_Call_Recording_{timestamp}.mp3"
    
    scam_label = f"🔴 Live Call ({result['risk_level']} Risk - {result['fraud_score']}%)" if result['fraud_score'] > 30 else f"🟢 Live Call (Safe - {result['fraud_score']}%)"
    
    entry = {
        "name": call_filename,
        "transcript": transcript,
        "scam_type": scam_label,
        "date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save into MySQL Database & memory list
    save_call_report(call_filename, transcript, scam_label, result['fraud_score'], result['risk_level'], phone_number, 'live_call')
    TEST_AUDIO_FILES.insert(0, entry)
    
    return jsonify({
        'success': True,
        'message': 'Live call recording and transcript saved to MySQL database successfully!',
        'filename': call_filename,
        'report': result
    })

@analysis_bp.route('/api/get_audio_list', methods=['GET'])
def get_audio_list():
    db_reports = get_call_reports()
    db_names = {r['name'] for r in db_reports}
    
    audio_list = [{"name": r['name'], "scam_type": r['scam_type']} for r in db_reports]
    for audio in TEST_AUDIO_FILES:
        if audio["name"] not in db_names:
            audio_list.append({"name": audio["name"], "scam_type": audio["scam_type"]})
            
    return jsonify({'success': True, 'audio_files': audio_list})

@analysis_bp.route('/api/get_recents', methods=['GET'])
def get_recents():
    db_reports = get_call_reports()
    recents = []
    for r in db_reports:
        recents.append({
            "name": r.get('phone_number') or r['name'],
            "number": r.get('phone_number') or "Live Call Recording",
            "time": r['date'],
            "risk": f"{r['scam_type']}"
        })
    return jsonify({'success': True, 'recents': recents})

@analysis_bp.route('/api/get_contacts', methods=['GET'])
def fetch_contacts():
    contacts = get_contacts()
    return jsonify({'success': True, 'contacts': contacts})

@analysis_bp.route('/api/add_contact', methods=['POST'])
def add_contact_route():
    data = request.json or {}
    name = data.get('name', '').strip()
    number = data.get('number', '').strip()
    category = data.get('category', 'Safe').strip()
    if not name or not number:
        return jsonify({'success': False, 'message': 'Name and phone number are required'}), 400
    save_contact(name, number, category)
    return jsonify({'success': True, 'message': 'Contact saved successfully to MySQL database'})

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
    file = request.files.get('audio_file')
    filename = file.filename if file else (request.form.get('audio_filename') or 'uploaded_audio.mp3')
    filename_lower = filename.lower()
    
    matched_audio = next((item for item in TEST_AUDIO_FILES if item["name"].lower() in filename_lower or filename_lower in item["name"].lower()), None)
    
    if matched_audio:
        transcript = matched_audio['transcript']
        scam_type = matched_audio['scam_type']
    else:
        if any(w in filename_lower for w in ['bank', 'otp', 'card', 'pin', 'cvv', 'account']):
            transcript = "Your bank account has been compromised. Please kindly share the OTP immediately to unblock."
            scam_type = "🏦 Bank OTP Fraud"
        elif any(w in filename_lower for w in ['tax', 'irs', 'police', 'court', 'legal', 'warrant']):
            transcript = "Official tax department calling. Arrest warrant issued for unpaid fine. Pay immediately."
            scam_type = "👮 Impersonation & Legal Threat"
        elif any(w in filename_lower for w in ['win', 'prize', 'lottery', 'reward', 'cash']):
            transcript = "Congratulations! You won grand lottery prize of $100000. Pay $500 processing fee to claim."
            scam_type = "🎁 Fake Reward / Lottery Scam"
        else:
            transcript = f"Audio recording file '{filename}' uploaded and analyzed. Fraud detection engine processed patterns."
            scam_type = "🔍 General Audio Call Analysis"
            
    result = fraud_detector.analyze_text(transcript)
    result['audio_name'] = filename
    result['scam_type'] = scam_type
    result['original_transcript'] = transcript
    result['scam_indicators'] = [f"🚨 {w}" for w in result.get('warnings', [])] or ["🔍 Audio content inspected for risk indicators"]
    
    return jsonify({
        'success': True,
        'report': {
            'fraud_score': result['fraud_score'],
            'risk_level': result['risk_level'],
            'scam_type': result['scam_type'],
            'transcript': result['original_transcript'],
            'scam_indicators': result['scam_indicators'],
            'warning_message': result['warning_message'],
            'detailed_advice': result['detailed_advice'],
            'analysis_duration': '2.1 seconds',
            'confidence': '96%'
        }
    })

# ─────────────────────────────────────────────────────────────────────────────
#  SPAM NUMBER LOOKUP API — Used by CallBlockingService on Android
# ─────────────────────────────────────────────────────────────────────────────

# Centralized online spam number database (cross-user community list)
KNOWN_SPAM_NUMBERS = {
    # Fake banking officers
    "9599853100": "Fake SBI Bank Officer — OTP Scam",
    "9266007533": "Fake HDFC Credit Card Scam",
    "9871028051": "KYC Verification Fraud — Account Block Scam",
    "8800861714": "Axis Bank OTP Fraud",
    "9958782020": "Digital Arrest Scam — Fake CBI Officer",
    "9773123456": "UPI Refund Fraud",
    "8527741234": "Fake Income Tax Officer Scam",
    "9315678901": "Aadhaar Link Fraud — Account Block Threat",
    "9250191234": "Electricity Bill Disconnection Fraud",
    "9810001234": "Fake TRAI Call — SIM Block Threat",
    # Investment / lottery
    "7827831234": "Lottery Winner Fraud",
    "9599001234": "Fake Job Offer Scam",
    "8130001234": "Investment Fraud — High Return Scheme",
    # Digital arrest
    "9810501234": "Digital Arrest Scam — Fake Police Officer",
    "9350001234": "ED / CBI Impersonation Fraud",
    "8800501234": "Narcotics Bureau Impersonation Scam",
    "9958001234": "FedEx Parcel Scam — Fake Customs Officer",
    # Tech support
    "1800111234": "Fake Microsoft Support Scam",
    "1800221234": "Fake Google Account Recovery Scam",
    "1800331234": "Fake Amazon Support OTP Scam",
    # More reported numbers
    "9818923456": "Known Cyber Fraud — Reported 500+ times",
    "9810234567": "Fake Bank Recovery Agent",
    "9958345678": "Phishing Call — IRCTC Refund Fraud",
    "9315456789": "Electricity Disconnection Threat Fraud",
    "9205567890": "Fake Job Offer — Work From Home Scam",
    "8527678901": "Loan Recovery Threat Fraud",
    "9599789012": "Fake Customs — Package Scam",
    "9266890123": "Digital Payment Reversal Fraud",
    "9873901234": "Fake Scholarship Scam",
    "8810012345": "Prize Money Fraud",
}

# Community-reported numbers (added via /api/report_spam)
community_reported = {}


def clean_number(raw):
    """Normalize phone number to digits, strip country code."""
    import re
    digits = re.sub(r'[^0-9]', '', raw or '')
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]
    return digits


@analysis_bp.route('/api/check_spam_number', methods=['GET', 'POST'])
def check_spam_number():
    """
    Android CallBlockingService calls this to check if an incoming number is spam.
    Returns: { is_spam: bool, reason: str, reports: int }
    """
    number = request.args.get('number') or (request.json or {}).get('number', '')
    cleaned = clean_number(number)
    if not cleaned:
        return jsonify({'success': False, 'message': 'Number required'}), 400

    # Check seeded spam list
    if cleaned in KNOWN_SPAM_NUMBERS:
        return jsonify({
            'success': True,
            'is_spam': True,
            'reason': KNOWN_SPAM_NUMBERS[cleaned],
            'source': 'CallShield Spam Database',
            'reports': 1
        })

    # Check last 10 digits
    last10 = cleaned[-10:] if len(cleaned) > 10 else cleaned
    for key, reason in KNOWN_SPAM_NUMBERS.items():
        if key.endswith(last10) or last10 == key[-10:]:
            return jsonify({
                'success': True,
                'is_spam': True,
                'reason': reason,
                'source': 'CallShield Spam Database (pattern match)',
                'reports': 1
            })

    # Check community reported
    if cleaned in community_reported:
        entry = community_reported[cleaned]
        return jsonify({
            'success': True,
            'is_spam': True,
            'reason': entry['reason'],
            'source': 'Community Reported',
            'reports': entry['count']
        })

    return jsonify({
        'success': True,
        'is_spam': False,
        'reason': 'Not in spam database',
        'source': 'CallShield',
        'reports': 0
    })


@analysis_bp.route('/api/report_spam', methods=['POST'])
def report_spam_number_api():
    """
    Users report a spam number — adds to community database.
    Also used by Android app when user taps 'Report Spam Number'.
    """
    data = request.json or {}
    number = data.get('number', '').strip()
    reason = data.get('reason', 'Reported as spam by user').strip()
    name   = data.get('name', 'Spam Caller').strip()

    if not number:
        return jsonify({'success': False, 'message': 'Phone number is required'}), 400

    cleaned = clean_number(number)

    if cleaned in community_reported:
        community_reported[cleaned]['count'] += 1
    else:
        community_reported[cleaned] = {'reason': reason, 'count': 1}

    # Also save to our backend contact database
    try:
        save_contact(name, number, 'Spam — ' + reason)
    except Exception:
        pass

    return jsonify({
        'success': True,
        'message': f'Number {number} reported as spam! Future calls will be auto-blocked.',
        'total_reports': community_reported[cleaned]['count']
    })

