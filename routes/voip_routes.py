"""
CallShield AI — VoIP Routes (Flask-SocketIO Edition)
=====================================================
Handles:
  • WebRTC REST signaling   (SDP offer/answer, ICE candidates)
  • Flask-SocketIO push     (real-time risk_update event to call room)
  • Live fraud analysis     (/api/voip/analyze_chunk)
  • Call history            (/api/voip/call_history)
  • Scam reporting          (/api/voip/report_scam)
  • Demo mode               (/api/voip/demo_analyze)
  • Presence heartbeat      (/api/voip/register, /api/voip/online_users)

Real-Time Flow:
    SpeechRecognition  →  analyze_chunk  →  FraudDetector  →  SocketIO room push
    Android/Browser    ←  'risk_update' event (no polling needed)

Author: CallShield AI — Final Year Project
"""

import time
import json
from flask import Blueprint, render_template, request, jsonify
from core.detector import FraudDetector
from core.voip_session_manager import (
    VoIPSessionManager, save_scam_report, get_call_history, _format_elapsed
)

# ─── Blueprint & Shared Objects ───────────────────────────────────────────────

voip_bp       = Blueprint('voip', __name__)
fraud_detector = FraudDetector()
voip_manager  = VoIPSessionManager()

# socketio is injected at app startup (set in app.py after SocketIO init)
_socketio = None

def set_socketio(sio):
    """Called from app.py to inject the SocketIO instance into this module."""
    global _socketio
    _socketio = sio


def _push_risk_update(call_id: str, payload: dict):
    """Emit a real-time risk_update SocketIO event to everyone in the call room."""
    if _socketio is not None:
        try:
            _socketio.emit('risk_update', payload, room=call_id, namespace='/voip')
        except Exception as e:
            print(f"[SocketIO] Push failed: {e}")


# ─── Page Views ───────────────────────────────────────────────────────────────

@voip_bp.route('/modules/voip')
@voip_bp.route('/voip')
def voip_page():
    """Renders the CallShield VoIP call screen."""
    return render_template('modules/voip.html')


@voip_bp.route('/modules/voip/history')
def voip_history_page():
    """Renders the VoIP call history page."""
    return render_template('modules/voip.html')


# ─── User Presence & Registration ────────────────────────────────────────────

@voip_bp.route('/api/voip/register', methods=['POST'])
def api_register():
    """Register a user and update heartbeat. Called every 20–30 seconds."""
    data = request.json or {}
    user_id = str(data.get('user_id', '')).strip()
    name    = str(data.get('name', '')).strip()
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id is required'}), 400
    user_info = voip_manager.register_user(user_id, name)
    return jsonify({'success': True, 'user': user_info})


@voip_bp.route('/api/voip/heartbeat', methods=['POST'])
def api_heartbeat():
    """Lightweight keep-alive endpoint (no DB write)."""
    data    = request.json or {}
    user_id = str(data.get('user_id', '')).strip()
    voip_manager.heartbeat(user_id)
    return jsonify({'success': True})


@voip_bp.route('/api/voip/online_users', methods=['GET'])
def api_online_users():
    """Returns all currently online users (excluding the requesting user)."""
    voip_manager.cleanup_stale()
    current = request.args.get('current_user', '').strip()
    users = [
        {'user_id': uid, 'name': d['name'], 'status': d['status']}
        for uid, d in voip_manager.users.items()
        if uid != current
    ]
    return jsonify({'success': True, 'users': users, 'total': len(users)})


# ─── WebRTC Signaling ─────────────────────────────────────────────────────────

@voip_bp.route('/api/voip/initiate_call', methods=['POST'])
def api_initiate_call():
    """
    User A creates a VoIP call with SDP Offer.
    Returns a unique call_id used for all subsequent signaling.
    """
    data        = request.json or {}
    caller_id   = str(data.get('caller_id', '')).strip()
    callee_id   = str(data.get('callee_id', '')).strip()
    caller_name = str(data.get('caller_name', '')).strip()
    offer       = data.get('offer')

    if not caller_id or not callee_id or not offer:
        return jsonify({'success': False, 'message': 'caller_id, callee_id, and offer are required'}), 400

    call = voip_manager.create_call(caller_id, callee_id, offer, caller_name)

    # Notify callee via SocketIO if they are connected
    _push_risk_update(callee_id, {
        'type':        'incoming_call',
        'call_id':     call['call_id'],
        'caller_id':   caller_id,
        'caller_name': call['caller_name'],
        'offer':       offer
    })

    return jsonify({'success': True, 'call': {
        'call_id':     call['call_id'],
        'caller':      call['caller'],
        'callee':      call['callee'],
        'caller_name': call['caller_name'],
        'callee_name': call['callee_name'],
        'status':      call['status']
    }})


@voip_bp.route('/api/voip/check_incoming_call', methods=['GET'])
def api_check_incoming_call():
    """
    User B polls for an incoming call.
    Also updates their heartbeat.
    """
    user_id = str(request.args.get('user_id', '')).strip()
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id required'}), 400

    voip_manager.heartbeat(user_id)

    for call_id, call in voip_manager.calls.items():
        if call['callee'] == user_id and call['status'] == 'ringing':
            return jsonify({
                'success':  True,
                'has_call': True,
                'call': {
                    'call_id':     call['call_id'],
                    'caller':      call['caller'],
                    'caller_name': call['caller_name'],
                    'offer':       call['offer']
                }
            })

    return jsonify({'success': True, 'has_call': False})


@voip_bp.route('/api/voip/check_call_status', methods=['GET'])
def api_check_call_status():
    """User A polls to check if User B answered the call."""
    call_id = str(request.args.get('call_id', '')).strip()
    if not call_id or call_id not in voip_manager.calls:
        return jsonify({'success': False, 'status': 'not_found'})

    call = voip_manager.calls[call_id]
    return jsonify({
        'success': True,
        'status':  call['status'],
        'answer':  call.get('answer')
    })


@voip_bp.route('/api/voip/answer_call', methods=['POST'])
def api_answer_call():
    """User B accepts the call and provides their SDP Answer."""
    data    = request.json or {}
    call_id = str(data.get('call_id', '')).strip()
    answer  = data.get('answer')

    if not call_id or not answer:
        return jsonify({'success': False, 'message': 'call_id and answer required'}), 400

    call = voip_manager.answer_call(call_id, answer)
    if not call:
        return jsonify({'success': False, 'message': 'Call not found'}), 404

    # Notify caller via SocketIO
    _push_risk_update(call['caller'], {
        'type':    'call_answered',
        'call_id': call_id,
        'answer':  answer
    })

    return jsonify({'success': True, 'call': {
        'call_id': call['call_id'],
        'status':  call['status']
    }})


@voip_bp.route('/api/voip/reject_call', methods=['POST'])
def api_reject_call():
    """User B rejects the incoming call."""
    data    = request.json or {}
    call_id = str(data.get('call_id', '')).strip()
    voip_manager.end_call(call_id, reason='rejected')
    _push_risk_update(call_id, {'type': 'call_rejected', 'call_id': call_id})
    return jsonify({'success': True, 'message': 'Call rejected'})


@voip_bp.route('/api/voip/end_call', methods=['POST'])
def api_end_call():
    """Either party ends the active call. Call session is saved to DB."""
    data    = request.json or {}
    call_id = str(data.get('call_id', '')).strip()

    summary = None
    if call_id in voip_manager.calls:
        call = voip_manager.calls[call_id]
        summary = {
            'call_id':    call_id,
            'duration_s': round(time.time() - call.get('call_start_ts', call['created_at']), 1),
            'final_risk': call['current_risk'],
            'risk_level': call['risk_level'],
            'category':   call['category'],
            'indicators': call['detected_indicators']
        }

    voip_manager.end_call(call_id, reason='ended')
    _push_risk_update(call_id, {'type': 'call_ended', 'call_id': call_id, 'summary': summary})
    return jsonify({'success': True, 'message': 'Call ended', 'summary': summary})


# ─── ICE Candidates ───────────────────────────────────────────────────────────

@voip_bp.route('/api/voip/ice_candidate', methods=['POST'])
def api_send_ice():
    """One side sends its ICE candidate for NAT traversal."""
    data      = request.json or {}
    call_id   = str(data.get('call_id', '')).strip()
    role      = str(data.get('role', 'caller'))
    candidate = data.get('candidate')

    if not call_id or not candidate:
        return jsonify({'success': False, 'message': 'call_id and candidate required'}), 400

    voip_manager.add_ice(call_id, role, candidate)
    return jsonify({'success': True})


@voip_bp.route('/api/voip/get_ice_candidates', methods=['GET'])
def api_get_ice():
    """Fetches the peer's ICE candidates."""
    call_id = str(request.args.get('call_id', '')).strip()
    role    = str(request.args.get('role', 'caller'))
    candidates = voip_manager.get_ice(call_id, role)
    return jsonify({'success': True, 'candidates': candidates})


# ─── REAL-TIME FRAUD ANALYSIS ─────────────────────────────────────────────────

@voip_bp.route('/api/voip/analyze_chunk', methods=['POST'])
def api_analyze_chunk():
    """
    ★ CORE INNOVATION — Live Call Fraud Detection ★

    Receives a 1–3 second speech-to-text chunk from the active VoIP call.
    Runs it through the existing FraudDetector (TF-IDF + ML + rule-based engine).
    Pushes a real-time SocketIO 'risk_update' event to the call room instantly.
    Returns analysis result including fraud score, risk level, indicators & latency.

    Request body:
        call_id     — active call session ID
        speaker_id  — 'CALLER' | 'RECEIVER' | 'UNKNOWN'
        transcript  — live speech text chunk
        chunk_ms    — (optional) duration of audio chunk in milliseconds

    Returns:
        success, analysis { fraud_score, risk_level, is_fraud, category, indicators,
                            warning_title, warning_message, latency_ms, timeline_entry }
    """
    t_start = time.time()

    data        = request.json or {}
    call_id     = str(data.get('call_id', '')).strip()
    speaker_id  = str(data.get('speaker_id', 'UNKNOWN')).upper()
    transcript  = str(data.get('transcript', '')).strip()
    chunk_ms    = data.get('chunk_ms')

    if not transcript:
        return jsonify({'success': False, 'message': 'Transcript is empty'}), 400

    # ── Run existing ML + rule-based fraud detector ──
    result = fraud_detector.analyze_text(transcript)

    # ── Measure processing latency ──
    t_end      = time.time()
    latency_ms = round((t_end - t_start) * 1000, 0)

    # ── Update call session risk state ──
    threat_payload = voip_manager.update_risk(
        call_id, result, speaker_id, transcript, latency_ms
    )

    if not threat_payload:
        # call_id not found — still return analysis result with all fields
        from core.voip_session_manager import _classify_category, _build_warning_message
        fraud_score  = float(result.get('fraud_score', 0))
        keywords     = [str(k) for k in result.get('keywords_found', [])]
        patterns     = [str(p) for p in result.get('patterns_detected', [])]
        risk_level   = 'HIGH' if fraud_score >= 65 else 'MEDIUM' if fraud_score >= 40 else 'LOW-RISK' if fraud_score >= 35 else 'LOW'
        category     = _classify_category(keywords + patterns)
        is_fraud     = fraud_score >= 35.0 or len(keywords) > 0
        threat_payload = {
            'call_id':             call_id,
            'fraud_score':         round(fraud_score, 1),
            'peak_risk':           round(fraud_score, 1),
            'risk_level':          risk_level,
            'is_fraud':            is_fraud,
            'category':            category,
            'keywords_found':      keywords[:6],
            'indicators':          keywords[:6],
            'warning_title':       '🚨 Fraud Detected' if is_fraud else '🛡️ Call Safe',
            'warning_message':     _build_warning_message(keywords, category) if is_fraud else 'Conversation appears safe.',
            'detailed_advice':     str(result.get('detailed_advice', '')),
            'latency_ms':          latency_ms,
            'speaker_id':          speaker_id,
            'transcript_snippet':  transcript[:80]
        }

    # ── Push via SocketIO to all devices in this call room ──
    if threat_payload.get('is_fraud'):
        _push_risk_update(call_id, {
            'type': 'risk_update',
            **threat_payload
        })

    return jsonify({'success': True, 'analysis': threat_payload})


@voip_bp.route('/api/voip/threat_status', methods=['GET'])
def api_threat_status():
    """
    Fallback polling endpoint for browsers that do not support SocketIO.
    Returns the latest threat state for the given call_id.
    Poll every 1.2 seconds maximum.
    """
    call_id = str(request.args.get('call_id', '')).strip()
    if not call_id or call_id not in voip_manager.calls:
        return jsonify({'success': False, 'threat': None})

    call = voip_manager.calls[call_id]
    return jsonify({
        'success':     True,
        'threat':      call.get('threat_alert'),
        'call_status': call.get('status'),
        'peak_risk':   call.get('current_risk', 0),
        'risk_level':  call.get('risk_level', 'LOW'),
        'category':    call.get('category', 'Unknown'),
        'indicators':  call.get('detected_indicators', []),
        'latency_ms':  call.get('last_latency_ms'),
        'timeline':    call.get('timeline', [])[-5:]   # last 5 entries for polling
    })


# ─── DEMO MODE ────────────────────────────────────────────────────────────────

@voip_bp.route('/api/voip/demo_analyze', methods=['POST'])
def api_demo_analyze():
    """
    ★ DEMO MODE — Clearly labelled, NOT a live call ★

    Allows testing fraud detection without a real VoIP call.
    Used for college demonstrations where VoIP infrastructure may not be available.
    The response includes a 'demo_mode: true' flag — never present it as a live call.
    """
    t_start    = time.time()
    data       = request.json or {}
    transcript = str(data.get('transcript', '')).strip()
    speaker_id = str(data.get('speaker_id', 'UNKNOWN')).upper()

    if not transcript:
        return jsonify({'success': False, 'message': 'transcript required'}), 400

    result     = fraud_detector.analyze_text(transcript)
    latency_ms = round((time.time() - t_start) * 1000, 0)

    fraud_score   = float(result.get('fraud_score', 0))
    keywords      = [str(k) for k in result.get('keywords_found', [])]
    patterns      = [str(p) for p in result.get('patterns_detected', [])]

    if fraud_score >= 65:
        risk_level = 'HIGH'
    elif fraud_score >= 40:
        risk_level = 'MEDIUM'
    elif fraud_score >= 35:
        risk_level = 'LOW-RISK'
    else:
        risk_level = 'LOW'

    return jsonify({
        'success':    True,
        'demo_mode':  True,        # ← always mark demo clearly
        'analysis': {
            'fraud_score':      round(fraud_score, 1),
            'risk_level':       risk_level,
            'is_fraud':         fraud_score >= 35.0 or len(keywords) > 0,
            'keywords_found':   keywords[:6],
            'patterns':         patterns[:4],
            'warnings':         [str(w) for w in result.get('warnings', [])],
            'detailed_advice':  str(result.get('detailed_advice', '')),
            'speaker_id':       speaker_id,
            'transcript':       transcript,
            'latency_ms':       latency_ms,
            'note':             '⚠️ DEMO MODE — This is a simulated analysis. Not a live protected call.'
        }
    })


# ─── CALL HISTORY ─────────────────────────────────────────────────────────────

@voip_bp.route('/api/voip/call_history', methods=['GET'])
def api_call_history():
    """Returns saved VoIP call history from database (most recent first)."""
    limit   = min(int(request.args.get('limit', 20)), 100)
    history = get_call_history(limit)
    return jsonify({'success': True, 'calls': history, 'total': len(history)})


@voip_bp.route('/api/voip/call_detail/<call_id>', methods=['GET'])
def api_call_detail(call_id):
    """Returns full detail for a specific call (live or from history)."""
    # Check live sessions first
    if call_id in voip_manager.calls:
        call = voip_manager.calls[call_id]
        return jsonify({'success': True, 'source': 'live', 'call': {
            'call_id':             call['call_id'],
            'caller':              call['caller'],
            'callee':              call['callee'],
            'caller_name':         call['caller_name'],
            'callee_name':         call['callee_name'],
            'status':              call['status'],
            'current_risk':        call['current_risk'],
            'risk_level':          call['risk_level'],
            'category':            call['category'],
            'detected_indicators': call['detected_indicators'],
            'timeline':            call['timeline'],
            'transcript_history':  call['transcript_history'][-20:],
            'last_latency_ms':     call.get('last_latency_ms'),
            'start_time':          call.get('start_time')
        }})

    # Fall back to database
    history = get_call_history(100)
    for c in history:
        if c.get('call_id') == call_id:
            return jsonify({'success': True, 'source': 'history', 'call': c})

    return jsonify({'success': False, 'message': 'Call not found'}), 404


# ─── SCAM REPORTING ───────────────────────────────────────────────────────────

@voip_bp.route('/api/voip/report_scam', methods=['POST'])
def api_report_scam():
    """
    User submits a scam report for a completed call.
    Stores in voip_scam_reports table.
    """
    data = request.json or {}
    required = ('call_id', 'reporter_user', 'scam_category')
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'{field} is required'}), 400

    report = {
        'call_id':       str(data.get('call_id', '')),
        'reporter_user': str(data.get('reporter_user', '')),
        'scam_category': str(data.get('scam_category', '')),
        'description':   str(data.get('description', '')),
        'caller_number': str(data.get('caller_number', ''))
    }
    ok = save_scam_report(report)
    if ok:
        return jsonify({'success': True, 'message': 'Scam report submitted. Thank you for keeping others safe!'})
    return jsonify({'success': False, 'message': 'Failed to save report'}), 500


# ─── FLASK-SOCKETIO EVENTS ────────────────────────────────────────────────────
# These handlers are registered on the SocketIO object in app.py
# because Flask blueprints cannot directly register SocketIO namespaces.
# See app.py for:  @socketio.on('join_call', namespace='/voip')
