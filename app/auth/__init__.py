from flask import Blueprint

bp = Blueprint('auth', __name__, template_folder='templates', static_folder='static')

from app.auth import routes