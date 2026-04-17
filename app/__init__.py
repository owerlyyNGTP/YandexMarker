from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
bootstrap = Bootstrap()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    bootstrap.init_app(app)

    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from app.routes import main
    from app.api import api_bp

    app.register_blueprint(main)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
