from flask import Flask
from sqlalchemy import create_engine
from flask_login import LoginManager
import os
from flask_bootstrap import Bootstrap

database_url = 'sqlite:///db.sqlite'
engine = create_engine(database_url, convert_unicode=True)
SECRET_KEY = os.urandom(32)


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    init_db()
    Bootstrap(app)

    login_manager = LoginManager()
    login_manager.login_view = 'main.index'
    login_manager.login_message = 'Please log in to access this page.'

    from app.db.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.init_app(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.document import bp as document_bp
    app.register_blueprint(document_bp)

    from app.profile import bp as profile_bp
    app.register_blueprint(profile_bp)

    return app


def init_db():
    from app.db import Base
    Base.metadata.create_all(bind=engine)
