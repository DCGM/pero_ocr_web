import sqlalchemy
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_jsglue import JSGlue
from flask_dropzone import Dropzone

from config import *
from .db import Base
from app.db.user import User

engine = create_engine(database_url, convert_unicode=True, connect_args={'check_same_thread': False})

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base.query = db_session.query_property()

from app.auth.general import create_user


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db()
    add_delete_user_for_deleted_documents()
    Bootstrap(app)
    Dropzone(app)

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


def add_delete_user_for_deleted_documents():
    delete_user = db_session.query(User).filter(User.first_name == "#deleted_documents#").first()
    if delete_user is None:
        try:
            create_user("#revert_OCR_backup#", "#revert_OCR_backup#", "#revert_OCR_backup#", "#revert_OCR_backup#",
                        "#revert_OCR_backup#")
        except sqlalchemy.exc.IntegrityError as err:
            db_session.rollback()