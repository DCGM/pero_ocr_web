from flask import render_template, redirect, url_for, flash, request, jsonify
from app.request import bp
from flask_login import login_required, current_user
from app.auth.forms import LoginForm
from app.document.general import is_user_trusted
from app.db.general import get_request_by_id
from app import db_session
from app.db import RequestState
import datetime


@bp.route('/add_log/<string:request_id>', methods=['POST'])
@login_required
def add_log_to_request(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to add log to request!', 'danger')
        return redirect(url_for('main.index'))
    job_request = get_request_by_id(request_id)
    job_request.log = request.json['log']
    db_session.commit()
    return 'OK'


@bp.route('/increment_processed_pages/<string:request_id>', methods=['POST'])
@login_required
def increment_processed_pages(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to add log to request!', 'danger')
        return redirect(url_for('main.index'))
    job_request = get_request_by_id(request_id)
    job_request.processed_pages += 1
    job_request.last_processed_page = datetime.datetime.utcnow()
    db_session.commit()
    return 'OK'


@bp.route('/update_last_processed_page/<string:request_id>', methods=['POST'])
@login_required
def update_last_processed_page(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to add log to request!', 'danger')
        return redirect(url_for('main.index'))
    job_request = get_request_by_id(request_id)
    job_request.last_processed_page = datetime.datetime.utcnow()
    db_session.commit()
    return 'OK'


@bp.route('/get_request_state/<string:request_id>')
@login_required
def get_request_state(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to add log to request!', 'danger')
        return redirect(url_for('main.index'))
    job_request = get_request_by_id(request_id)
    if job_request:
        if job_request.state == RequestState.PENDING:
            state = "PENDING"
        elif job_request.state == RequestState.FAILURE:
            state = "FAILURE"
        elif job_request.state == RequestState.SUCCESS:
            state = "SUCCESS"
        elif job_request.state == RequestState.IN_PROGRESS:
            state = "IN_PROGRESS"
        else:
            state = "CANCELED"
        value = {'id': job_request.id, 'state': state}
        return jsonify(value)
    else:
        return jsonify({})


@bp.route('/change_request_state_to_in_progress_interrupted/<string:request_id>', methods=['POST'])
@login_required
def change_request_state_to_in_progress_interrupted(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    request = get_request_by_id(request_id)
    request.state = RequestState.IN_PROGRESS_INTERRUPTED
    db_session.commit()
    return 'OK'
