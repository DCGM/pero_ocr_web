from flask import Blueprint

bp = Blueprint('document', __name__, template_folder='templates', static_folder='static')

from app.document import routes