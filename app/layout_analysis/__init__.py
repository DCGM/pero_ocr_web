from flask import Blueprint

bp = Blueprint('layout_analysis', __name__, template_folder='templates', static_folder='static')

from app.layout_analysis import routes