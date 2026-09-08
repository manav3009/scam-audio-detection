from flask import Blueprint, render_template, session, redirect, url_for

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def landing():
    return render_template('index.html')

@views_bp.route('/student-access')
def student_access():
    return redirect(url_for('views.dialer'))

@views_bp.route('/login')
def login_page():
    return redirect(url_for('views.dialer'))

@views_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@views_bp.route('/modules/dialer')
def dialer():
    return render_template('modules/dialer.html')

@views_bp.route('/modules/live-call')
def live_call():
    return render_template('modules/live_call.html')

@views_bp.route('/modules/recorded')
def recorded_analysis():
    return render_template('modules/recorded.html')

@views_bp.route('/modules/awareness')
def awareness():
    return render_template('modules/awareness.html')

@views_bp.route('/modules/chatbot')
def chatbot():
    return render_template('modules/chatbot.html')
