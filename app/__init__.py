from flask import Flask
from sqlalchemy import create_engine
from flask_login import LoginManager
import os
from flask_bootstrap import Bootstrap
from flask_jsglue import JSGlue



database_url = 'sqlite:///db.sqlite'
engine = create_engine(database_url, convert_unicode=True, connect_args={'check_same_thread': False})
SECRET_KEY = os.urandom(32)


def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    app.config['SECRET_KEY'] = SECRET_KEY
    init_db()
    Bootstrap(app)

    jsglue = JSGlue()
    jsglue.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'main.index'
    login_manager.login_message = 'Please log in to access this page.'

    from app.db.user import User
    from app.db.general import get_user_by_id

    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(user_id)

    login_manager.init_app(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.document import bp as document_bp
    app.register_blueprint(document_bp, url_prefix='/document')

    from app.profile import bp as profile_bp
    app.register_blueprint(profile_bp)

    from app.layout_analysis import bp as layout_analysis_bp
    app.register_blueprint(layout_analysis_bp, url_prefix='/layout_analysis')

    from app.ocr import bp as ocr_bp
    app.register_blueprint(ocr_bp, url_prefix='/ocr')

    return app


def init_db():
    from app.db import Base
    Base.metadata.create_all(bind=engine)
