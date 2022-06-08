from flask import render_template, redirect, url_for, flash, request
from app.main import bp
from flask_login import login_required, current_user
from app.auth.forms import LoginForm
from app.document.general import is_user_trusted
from app.db.general import get_request_by_id
from app import db_session
import datetime


@bp.route('/add_log/<string:request_id>', methods=['POST'])
@login_required
def add_log_to_request(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to add log to request!', 'danger')
        return redirect(url_for('main.index'))
    request = get_request_by_id(request_id)
    request.log = request.json['log']
    db_session.commit()
    return 'OK'


@bp.route('/increment_processed_pages/<string:request_id>', methods=['POST'])
@login_required
def increment_processed_pages(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to add log to request!', 'danger')
        return redirect(url_for('main.index'))
    request = get_request_by_id(request_id)
    request.processed_pages += 1
    request.last_processed_page = datetime.datetime.utcnow()
    db_session.commit()
    return 'OK'


@bp.route('/get_request_state/<string:request_id>', methods=['POST'])
@login_required
def get_request_state(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to add log to request!', 'danger')
        return redirect(url_for('main.index'))
    request = get_request_by_id(request_id)
    if request:
        value = {'id': request.id, 'state': request.state}
        return jsonify(value)
    else:
        return jsonify({})
