from flask import render_template, redirect, url_for, flash, request
from app.main import bp
from flask_login import login_required, current_user
from app.auth.forms import LoginForm
from app.document.general import is_user_trusted
from app.db.general import get_request_by_id
from app import db_session


@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('document.documents'))
    form_login = LoginForm()
    return render_template('index.html', form_login=form_login)


@bp.route('/add_log_to_request/<string:request_id>', methods=['POST'])
@login_required
def add_log_to_request(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to add log to request!', 'danger')
        return redirect(url_for('main.index'))
    my_request = get_request_by_id(request_id)
    my_request.log = request.json['log']
    db_session.commit()
    return 'OK'
