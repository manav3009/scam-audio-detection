from flask import Blueprint, request, jsonify, session

auth_bp = Blueprint('auth', __name__)

ADMIN_CREDENTIALS = {'username': 'admin', 'password': 'admin'}

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    
    if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
        session['logged_in'] = True
        session['username'] = username
        session['role'] = 'Admin'
        return jsonify({'success': True, 'message': 'Admin login successful'})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@auth_bp.route('/api/student-login', methods=['POST'])
def student_login():
    data = request.json or {}
    student_name = data.get('name', 'Student User').strip() or 'Student User'
    session['logged_in'] = True
    session['username'] = f"Student ({student_name})" if student_name != 'Student User' else 'Student / Public Tester'
    session['role'] = 'Student'
    return jsonify({'success': True, 'message': 'Student access granted'})

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})
