import os
from flask import Flask, render_template, redirect, url_for, session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.config['SECRET_KEY'] = 'callshield_secret_key_2024'
app.url_map.strict_slashes = False

@app.before_request
def clear_obsolete_sessions():
    session.clear()

from core.database import init_db
init_db()

from routes.views_routes import views_bp
from routes.auth_routes import auth_bp
from routes.analysis_routes import analysis_bp
from routes.chatbot_routes import chatbot_bp

app.register_blueprint(views_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(chatbot_bp)

# Bulletproof Catch-All Handler for Vercel Serverless Rewrites
@app.route('/<path:path>')
def catch_all_routes(path):
    p = path.lower()
    if 'dialer' in p or 'phone' in p:
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
