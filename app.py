"""
CallShield AI — Flask Application Entry Point (Flask-SocketIO Edition)
=======================================================================
Initialises Flask + Flask-SocketIO for real-time WebSocket risk push,
registers all blueprints, and sets up SocketIO namespace event handlers
for the /voip namespace.

Run locally:
    python app.py
    → http://localhost:5000

Deploy on VPS (Vercel NOT supported for SocketIO):
    gunicorn -k eventlet -w 1 app:app
    OR: python app.py  (uses eventlet dev server)
"""

import os
from flask import Flask, render_template, redirect, session, request
from flask_socketio import SocketIO, join_room, leave_room, emit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'callshield_secret_key_2024')
app.url_map.strict_slashes = False

# ─── Flask-SocketIO Setup ─────────────────────────────────────────────────────
try:
    from flask_socketio import SocketIO, join_room, leave_room, emit
    socketio = SocketIO(
        app,
        async_mode='threading',
        cors_allowed_origins='*',
        logger=False,
        engineio_logger=False
    )
except Exception as _sio_err:
    socketio = None

# ─── Database Init ────────────────────────────────────────────────────────────
@app.before_request
def clear_obsolete_sessions():
    session.clear()

from core.database import init_db
init_db()

# ─── Blueprints ───────────────────────────────────────────────────────────────
from routes.views_routes   import views_bp
from routes.auth_routes    import auth_bp
from routes.analysis_routes import analysis_bp
from routes.chatbot_routes import chatbot_bp
from routes.voip_routes    import voip_bp, set_socketio

app.register_blueprint(views_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(voip_bp)

# Inject SocketIO into voip_routes so it can push real-time events
set_socketio(socketio)

# ─── Catch-All Route (Vercel SPA rewrite support) ─────────────────────────────
@app.route('/<path:path>')
def catch_all_routes(path):
    p = path.lower()
    if 'voip' in p:
        return render_template('modules/voip.html')
    elif 'dialer' in p or 'phone' in p:
        return render_template('modules/dialer.html')
    elif 'live' in p:
        return render_template('modules/live_call.html')
    elif 'recorded' in p:
        return render_template('modules/recorded.html')
    elif 'chatbot' in p:
        return render_template('modules/chatbot.html')
    elif 'awareness' in p:
        return render_template('modules/awareness.html')
    elif 'dashboard' in p:
        return render_template('dashboard.html')
    elif 'login' in p or 'student' in p:
        return redirect('/')
    return render_template('index.html')


# ─── SocketIO Events — /voip Namespace ────────────────────────────────────────
if socketio is not None:
    @socketio.on('connect', namespace='/voip')
    def voip_connect():
        """Client connected to SocketIO /voip namespace."""
        print(f'[SocketIO] Client connected: {request.sid}')
        emit('connected', {'status': 'Connected to CallShield VoIP Server'})

    @socketio.on('disconnect', namespace='/voip')
    def voip_disconnect():
        """Client disconnected from /voip namespace."""
        print(f'[SocketIO] Client disconnected: {request.sid}')

    @socketio.on('join_call', namespace='/voip')
    def voip_join_call(data):
        """
        Client joins a SocketIO room identified by call_id.
        This enables server to push risk_update events to all participants.
        Payload: { call_id: str, user_id: str }
        """
        call_id = str(data.get('call_id', '')).strip()
        user_id = str(data.get('user_id', '')).strip()
        if call_id:
            join_room(call_id)
            emit('joined_room', {
                'call_id': call_id,
                'user_id': user_id,
                'message': f'Joined call room {call_id}. Real-time fraud detection active.'
            })
            print(f'[SocketIO] {user_id} joined room {call_id}')

    @socketio.on('leave_call', namespace='/voip')
    def voip_leave_call(data):
        """Client leaves the call room on hang-up."""
        call_id = str(data.get('call_id', '')).strip()
        if call_id:
            leave_room(call_id)
            emit('left_room', {'call_id': call_id})

    @socketio.on('user_online', namespace='/voip')
    def voip_user_online(data):
        """
        User registers their SocketIO SID in a personal room (user_id).
        This allows server to push incoming_call events directly.
        """
        user_id = str(data.get('user_id', '')).strip()
        if user_id:
            join_room(user_id)
            print(f'[SocketIO] {user_id} listening on personal room')
            emit('online_ack', {'user_id': user_id, 'status': 'online'})



# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("  CallShield AI — Real-Time VoIP Fraud Detection Server")
    print("  http://localhost:5000")
    print("  WebSocket: ws://localhost:5000/voip")
    print("=" * 60)
    # Use socketio.run() instead of app.run() for WebSocket support
    socketio.run(app, debug=True, port=5000, host='0.0.0.0', allow_unsafe_werkzeug=True)
