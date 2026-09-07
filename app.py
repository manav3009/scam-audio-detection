from flask import Flask
from flask_session import Session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'callshield_secret_key_2024'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

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
