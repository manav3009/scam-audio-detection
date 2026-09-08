import os
from flask import Flask, render_template, redirect, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.config['SECRET_KEY'] = 'callshield_secret_key_2024'
app.url_map.strict_slashes = False

@app.route('/dialer')
@app.route('/phone')
@app.route('/modules/dialer')
def dialer_route():
    return render_template('modules/dialer.html')

@app.route('/student-access')
@app.route('/login')
def login_bypass():
    return redirect('/')

from routes.views_routes import views_bp
from routes.auth_routes import auth_bp
from routes.analysis_routes import analysis_bp
from routes.chatbot_routes import chatbot_bp

app.register_blueprint(views_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(chatbot_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
