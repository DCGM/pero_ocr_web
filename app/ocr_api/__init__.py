from flask import Blueprint

bp = Blueprint('orc_api', __name__, template_folder='templates', static_folder='static')

from app.ocr_api import routes