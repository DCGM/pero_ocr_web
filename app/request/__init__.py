from flask import Blueprint

bp = Blueprint('request', __name__, template_folder='templates', static_folder='static')

from app.request import routes