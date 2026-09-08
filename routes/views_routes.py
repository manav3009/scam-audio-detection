from flask import Blueprint, render_template, session, redirect, url_for, send_from_directory
import os

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def landing():
    return render_template('index.html')

@views_bp.route('/student-access')
def student_access():
    session['logged_in'] = True
    session['username'] = 'Student / Public Tester'
    session['role'] = 'Student'
    return redirect(url_for('views.dashboard'))

@views_bp.route('/login')
def login_page():
    if session.get('logged_in'):
        return redirect(url_for('views.dashboard'))
    return render_template('login.html')

@views_bp.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        # Default auto-grant Student access if visiting dashboard directly on mobile
        session['logged_in'] = True
        session['username'] = 'Student / Public Tester'
        session['role'] = 'Student'
    return render_template('dashboard.html')

@views_bp.route('/modules/live-call')
def live_call():
    if not session.get('logged_in'):
        session['logged_in'] = True
        session['username'] = 'Student / Public Tester'
        session['role'] = 'Student'
    return render_template('modules/live_call.html')

@views_bp.route('/modules/recorded')
def recorded_analysis():
    if not session.get('logged_in'):
        session['logged_in'] = True
        session['username'] = 'Student / Public Tester'
        session['role'] = 'Student'
    return render_template('modules/recorded.html')

@views_bp.route('/modules/awareness')
def awareness():
    if not session.get('logged_in'):
        session['logged_in'] = True
        session['username'] = 'Student / Public Tester'
        session['role'] = 'Student'
    return render_template('modules/awareness.html')

@views_bp.route('/modules/chatbot')
def chatbot():
    if not session.get('logged_in'):
        session['logged_in'] = True
        session['username'] = 'Student / Public Tester'
        session['role'] = 'Student'
    return render_template('modules/chatbot.html')

@views_bp.route('/download-apk')
def download_apk():
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    return send_from_directory(static_dir, 'CallShield_AI_v1.0.apk', as_attachment=True)
