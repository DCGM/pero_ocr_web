from flask import render_template, redirect, url_for
from app.main import bp
from flask_login import current_user
from app.auth.forms import LoginForm


@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('document.documents'))
    form_login = LoginForm()
    return render_template('index.html', form_login=form_login)
