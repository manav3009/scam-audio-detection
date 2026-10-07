"""
CallShield AI — VoIP Session Manager
=====================================
Manages live WebRTC call sessions, risk timelines, call history persistence,
and scam reporting for the CallShield VoIP fraud detection system.

Architecture:
    WebRTC browser audio  →  webkitSpeechRecognition  →  /api/voip/analyze_chunk
    →  FraudDetector  →  SocketIO push  →  Android/browser warning banner

Author: CallShield AI Team | Final Year Project
"""

import time
import uuid
import json
import sqlite3
import os
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────────────
ANALYSIS_CHUNK_SECONDS = 3          # Process audio every 3 seconds
MAX_CALL_DURATION_S    = 3600       # Auto-expire calls after 1 hour
STALE_USER_TIMEOUT_S   = 60        # User considered offline after 60s heartbeat gap
FRAUD_THRESHOLD        = 35.0       # Fraud score >= 35 triggers warning
HIGH_RISK_THRESHOLD    = 65.0       # Score >= 65 = HIGH RISK
MEDIUM_RISK_THRESHOLD  = 40.0       # Score >= 40 = MEDIUM RISK

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'callshield.db')


def _get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_voip_tables():
    """Create VoIP-specific tables if they do not exist."""
    conn = _get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS voip_call_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id         TEXT NOT NULL UNIQUE,
            caller          TEXT NOT NULL,
            receiver        TEXT NOT NULL,
            start_time      TEXT,
            end_time        TEXT,
            duration_s      REAL DEFAULT 0,
            final_risk      REAL DEFAULT 0,
            risk_level      TEXT DEFAULT 'Low',
            category        TEXT DEFAULT 'Unknown',
            indicators      TEXT DEFAULT '[]',
            transcript      TEXT DEFAULT '[]',
            timeline        TEXT DEFAULT '[]',
            action          TEXT DEFAULT 'None',
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS voip_scam_reports (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id         TEXT,
            reporter_user   TEXT,
            scam_category   TEXT,
            description     TEXT,
            caller_number   TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()


def save_call_history(call_data: dict):
    """Persist completed call session to voip_call_history table."""
    try:
        conn = _get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO voip_call_history
              (call_id, caller, receiver, start_time, end_time, duration_s,
               final_risk, risk_level, category, indicators, transcript, timeline, action)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            call_data.get('call_id', ''),
            call_data.get('caller', ''),
            call_data.get('receiver', ''),
            call_data.get('start_time', ''),
            call_data.get('end_time', datetime.now().isoformat()),
            float(call_data.get('duration_s', 0)),
            float(call_data.get('current_risk', 0)),
            call_data.get('risk_level', 'Low'),
            call_data.get('category', 'Unknown'),
            json.dumps(call_data.get('detected_indicators', [])),
            json.dumps(call_data.get('transcript_history', [])[-50:]),  # last 50 chunks
            json.dumps(call_data.get('timeline', [])[-100:]),           # last 100 timeline points
            call_data.get('action', 'None')
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[VoIP] Failed to save call history: {e}")
        return False


def get_call_history(limit=20):
    """Returns most recent completed VoIP call history records."""
    try:
        conn = _get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM voip_call_history ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = cur.fetchall()
        conn.close()
        result = []
        for r in rows:
            d = dict(r)
            for field in ('indicators', 'transcript', 'timeline'):
                try:
                    d[field] = json.loads(d[field])
                except Exception:
                    d[field] = []
            result.append(d)
        return result
    except Exception as e:
        print(f"[VoIP] Failed to get call history: {e}")
        return []


def save_scam_report(report: dict):
    """Save a user-submitted scam report to the database."""
    try:
        conn = _get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO voip_scam_reports (call_id, reporter_user, scam_category, description, caller_number)
            VALUES (?, ?, ?, ?, ?)
        """, (
            report.get('call_id', ''),
            report.get('reporter_user', ''),
            report.get('scam_category', ''),
            report.get('description', ''),
            report.get('caller_number', '')
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[VoIP] Failed to save scam report: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  VoIP Session Manager
# ─────────────────────────────────────────────────────────────────────────────

class VoIPSessionManager:
    """
    Manages all active WebRTC VoIP call sessions and user presence.

    Session lifecycle:
        register → create_call (ringing) → answer_call (connected)
        → [analyze_chunk events] → end_call → persist to DB

    Each call maintains:
      - WebRTC SDP offer/answer & ICE candidates
      - Risk session: current_risk, risk_level, category, indicators, timeline
      - Transcript history (text chunks from Speech Recognition)
      - Performance latency tracking
    """

    def __init__(self):
        # user_id → {name, last_seen, status}
        self.users: dict = {}
        # call_id → full call session dict
        self.calls: dict = {}

        # Initialize DB tables
        try:
            init_voip_tables()
        except Exception as e:
            print(f"[VoIP] DB init warning: {e}")

    # ─── User Presence ────────────────────────────────────────────────────

    def cleanup_stale(self):
        """Remove inactive users and expired calls; persist ended calls to DB."""
        now = time.time()

        stale_users = [
            uid for uid, d in self.users.items()
            if now - d.get('last_seen', 0) > STALE_USER_TIMEOUT_S
        ]
        for uid in stale_users:
            self.users.pop(uid, None)

        stale_calls = [
            cid for cid, c in self.calls.items()
            if now - c.get('created_at', 0) > MAX_CALL_DURATION_S
            or c.get('status') in ('ended', 'rejected')
        ]
        for cid in stale_calls:
            call = self.calls.get(cid, {})
            # Only purge after 60s of being ended (gives clients time to fetch history)
            if now - call.get('updated_at', 0) > 60:
                self.calls.pop(cid, None)

    def register_user(self, user_id: str, display_name: str = ''):
        user_id = str(user_id).strip()
        display_name = str(display_name).strip() or user_id
        self.users[user_id] = {
            'name': display_name,
            'last_seen': time.time(),
            'status': 'online'
        }
        self.cleanup_stale()
        return self.users[user_id]

    def heartbeat(self, user_id: str):
        """Update last_seen for a user (keep-alive ping)."""
        if user_id in self.users:
            self.users[user_id]['last_seen'] = time.time()

    # ─── Call Lifecycle ───────────────────────────────────────────────────

    def create_call(self, caller_id: str, callee_id: str, offer_sdp, caller_name: str = '') -> dict:
        caller_id = str(caller_id).strip()
        callee_id = str(callee_id).strip()
        call_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"
        now = time.time()

        self.calls[call_id] = {
            # Identifiers
            'call_id':              call_id,
            'caller':               caller_id,
            'callee':               callee_id,
            'caller_name':          caller_name or self.users.get(caller_id, {}).get('name', caller_id),
            'callee_name':          self.users.get(callee_id, {}).get('name', callee_id),

            # WebRTC Negotiation
            'status':               'ringing',
            'offer':                offer_sdp,
            'answer':               None,
            'caller_ice':           [],
            'callee_ice':           [],

            # Risk Session
            'current_risk':         0.0,
            'risk_level':           'LOW',
            'category':             'Unknown',
            'detected_indicators':  [],

            # Timeline: [{elapsed_s, risk, text_snippet, level}]
            'timeline':             [],

            # Transcript history: [{speaker, text, time, risk}]
            'transcript_history':   [],

            # Active threat payload for peer polling/SocketIO
            'threat_alert':         None,

            # Performance
            'last_latency_ms':      None,

            # Timestamps
            'start_time':           datetime.now().isoformat(),
            'end_time':             None,
            'created_at':           now,
            'updated_at':           now,
            'call_start_ts':        now,
        }

        if caller_id in self.users:
            self.users[caller_id]['status'] = 'in_call'

        return self.calls[call_id]

    def answer_call(self, call_id: str, answer_sdp) -> dict | None:
        if call_id in self.calls:
            c = self.calls[call_id]
            c['answer']      = answer_sdp
            c['status']      = 'connected'
            c['updated_at']  = time.time()
            c['call_start_ts'] = time.time()  # reset timer from answer
            callee_id = c['callee']
            if callee_id in self.users:
                self.users[callee_id]['status'] = 'in_call'
            return c
        return None

    def end_call(self, call_id: str, reason: str = 'ended') -> bool:
        if call_id not in self.calls:
            return False
        call = self.calls[call_id]
        call['status']     = reason
        call['end_time']   = datetime.now().isoformat()
        call['updated_at'] = time.time()

        # Calculate duration
        duration = time.time() - call.get('call_start_ts', call.get('created_at', time.time()))
        call['duration_s'] = round(duration, 1)

        # Reset user statuses
        for role in ('caller', 'callee'):
            uid = call.get(role)
            if uid and uid in self.users:
                self.users[uid]['status'] = 'online'

        # Persist to DB
        save_call_history(call)
        return True

    # ─── ICE Candidates ───────────────────────────────────────────────────

    def add_ice(self, call_id: str, role: str, candidate):
        if call_id in self.calls:
            key = 'caller_ice' if role == 'caller' else 'callee_ice'
            self.calls[call_id][key].append(candidate)
            return True
        return False

    def get_ice(self, call_id: str, role: str) -> list:
        if call_id not in self.calls:
            return []
        call = self.calls[call_id]
        # If caller asks → give callee's candidates, and vice versa
        return call['callee_ice'] if role == 'caller' else call['caller_ice']

    # ─── Real-Time Fraud Analysis ─────────────────────────────────────────

    def update_risk(self, call_id: str, analysis_result: dict, speaker_id: str, transcript: str, latency_ms: float = None) -> dict:
        """
        Merge new fraud analysis into live call risk session.
        Builds timeline and returns the full threat payload.
        """
        if call_id not in self.calls:
            return {}

        call = self.calls[call_id]
        fraud_score      = float(analysis_result.get('fraud_score', 0))
        risk_level_raw   = str(analysis_result.get('risk_level', 'Low'))
        keywords_found   = [str(k) for k in analysis_result.get('keywords_found', [])]
        patterns         = [str(p) for p in analysis_result.get('patterns_detected', [])]
        warnings         = [str(w) for w in analysis_result.get('warnings', [])]
        detailed_advice  = str(analysis_result.get('detailed_advice', ''))

        # Determine risk level thresholds
        if fraud_score >= HIGH_RISK_THRESHOLD:
            risk_level = 'HIGH'
        elif fraud_score >= MEDIUM_RISK_THRESHOLD:
            risk_level = 'MEDIUM'
        elif fraud_score >= FRAUD_THRESHOLD:
            risk_level = 'LOW-RISK'
        else:
            risk_level = 'LOW'

        # Determine category from keywords
        category = _classify_category(keywords_found + patterns)

        # Accumulate indicators (deduplicate)
        new_indicators = list(set(keywords_found + patterns))
        existing = set(call['detected_indicators'])
        call['detected_indicators'] = list(existing | set(new_indicators))

        # Update peak risk (never go down during active call)
        prev_risk = call['current_risk']
        if fraud_score > prev_risk:
            call['current_risk'] = round(fraud_score, 1)
            call['risk_level']   = risk_level
            call['category']     = category

        # Timeline entry
        elapsed_s = round(time.time() - call.get('call_start_ts', call['created_at']), 1)
        timeline_entry = {
            'elapsed_s':  elapsed_s,
            'elapsed':    _format_elapsed(elapsed_s),
            'risk':       round(fraud_score, 1),
            'level':      risk_level,
            'snippet':    transcript[:60] + ('...' if len(transcript) > 60 else ''),
            'speaker':    speaker_id.upper()
        }
        call['timeline'].append(timeline_entry)

        # Transcript history
        call['transcript_history'].append({
            'speaker':  speaker_id.upper(),
            'text':     transcript,
            'time':     time.strftime('%H:%M:%S'),
            'risk':     round(fraud_score, 1)
        })

        # Performance tracking
        if latency_ms is not None:
            call['last_latency_ms'] = round(float(latency_ms), 0)

        call['updated_at'] = time.time()

        is_fraud = (fraud_score >= FRAUD_THRESHOLD or len(keywords_found) > 0 or len(patterns) > 0)

        # Build threat payload
        threat_payload = {
            'call_id':          call_id,
            'timestamp':        float(time.time()),
            'speaker_id':       speaker_id.upper(),
            'transcript_snippet': transcript[:80],
            'fraud_score':      round(fraud_score, 1),
            'peak_risk':        round(call['current_risk'], 1),
            'risk_level':       risk_level,
            'is_fraud':         is_fraud,
            'category':         category,
            'indicators':       call['detected_indicators'][:8],
            'keywords_found':   keywords_found[:6],
            'patterns':         patterns[:4],
            'warning_title':    '🚨 FRAUD ALERT — ACTIVE CALL' if is_fraud else '🛡️ Call Protected',
            'warning_message':  _build_warning_message(keywords_found, category) if is_fraud else 'Conversation appears safe.',
            'detailed_advice':  detailed_advice,
            'latency_ms':       call.get('last_latency_ms'),
            'timeline_entry':   timeline_entry,
            'elapsed_s':        elapsed_s
        }

        # Store as active threat for peer polling
        if is_fraud:
            call['threat_alert'] = threat_payload

        return threat_payload


# ─────────────────────────────────────────────────────────────────────────────
#  Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def _format_elapsed(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


def _classify_category(indicators: list) -> str:
    """Map detected keywords/patterns to a scam category name."""
    joined = ' '.join(indicators).lower()
    if any(x in joined for x in ['otp', 'one time', 'passcode', 'verification code']):
        return 'OTP Scam'
    if any(x in joined for x in ['kyc', 'know your customer', 'account verify']):
        return 'KYC Fraud'
    if any(x in joined for x in ['upi', 'transfer', 'send money', 'payment', 'gpay', 'paytm', 'phonepe']):
        return 'Payment Fraud'
    if any(x in joined for x in ['bank', 'account number', 'ifsc', 'credit card', 'debit card', 'cvv', 'pin', 'atm']):
        return 'Banking Fraud'
    if any(x in joined for x in ['lottery', 'won', 'prize', 'reward', 'gift']):
        return 'Lottery Scam'
    if any(x in joined for x in ['tax', 'income tax', 'irs', 'government', 'police', 'arrest', 'fir']):
        return 'Government Impersonation'
    if any(x in joined for x in ['job', 'work from home', 'salary', 'recruitment']):
        return 'Job Scam'
    if any(x in joined for x in ['insurance', 'policy', 'premium', 'claim']):
        return 'Insurance Fraud'
    if indicators:
        return 'General Fraud'
    return 'Unknown'


def _build_warning_message(keywords: list, category: str) -> str:
    """Build a human-readable warning message from detected keywords."""
    kw_str = ', '.join(keywords[:3]) if keywords else 'suspicious patterns'
    messages = {
        'OTP Scam':                 f'⚠️ Caller is requesting your OTP or verification code ({kw_str}). NEVER share OTP with anyone!',
        'KYC Fraud':                f'⚠️ Caller is asking for KYC details ({kw_str}). Banks never ask for KYC over phone calls!',
        'Payment Fraud':            f'⚠️ Caller is requesting a money transfer ({kw_str}). Do NOT send money to unknown callers!',
        'Banking Fraud':            f'⚠️ Caller is asking for banking details ({kw_str}). Never share card/account details over phone!',
        'Lottery Scam':             f'⚠️ Suspicious prize/lottery claim detected ({kw_str}). Legitimate lotteries don\'t call you!',
        'Government Impersonation': f'⚠️ Possible government impersonation ({kw_str}). Real officials never demand money over phone!',
        'Job Scam':                 f'⚠️ Suspicious job offer detected ({kw_str}). Legitimate companies don\'t ask for advance payment!',
        'Insurance Fraud':          f'⚠️ Suspicious insurance claim ({kw_str}). Verify independently before sharing any details!',
    }
    return messages.get(category, f'⚠️ Suspicious content detected: {kw_str}. Exercise caution and do NOT share personal information!')
