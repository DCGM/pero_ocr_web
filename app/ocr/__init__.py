from flask import Blueprint

bp = Blueprint('ocr', __name__, template_folder='templates', static_folder='static')

from app.ocr import routes
