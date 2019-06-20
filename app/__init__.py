from flask import Flask, request, current_app
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask_mail import Mail


db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'
bootstrap = Bootstrap()
moment = Moment()
babel = Babel()
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)    
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    with app.app_context():
        from app.errors import bp as errors_bp
        app.register_blueprint(errors_bp)
        from app.auth import bp as auth_bp
        app.register_blueprint(auth_bp,url_prefix='/auth')
        from app.public import bp as public_bp
        app.register_blueprint(public_bp)
        from app.admin import bp as admin_bp
        app.register_blueprint(admin_bp)
    return app


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])

from app import models

