from flask import render_template, redirect, url_for, flash, request
from app.main import bp
from flask_login import login_required, current_user
from app.auth.forms import LoginForm
from app.document.general import is_user_trusted
from app.db.general import get_request_by_id
from app import db_session
import datetime


@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('document.documents'))
    form_login = LoginForm()
    return render_template('index.html', form_login=form_login)
