from flask import Blueprint

bp = Blueprint('ocr', __name__, template_folder='templates', static_folder='static')

from app.layout_analysis import routes
