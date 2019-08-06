from app.layout_analysis import bp
from flask import render_template, url_for, redirect, flash, jsonify
from flask_login import login_required
from app.db.general import get_document_by_id
from app.layout_analysis.general import create_layout_analysis_request, can_start_layout_analysis, \
    add_layout_request_and_change_document_state, get_first_layout_request, change_layout_request_and_document_state, \
    create_json_from_request


@bp.route('/layout_analysis/<string:document_id>/start')
@login_required
def start_layout_analysis(document_id):
    document = get_document_by_id(document_id)
    request = create_layout_analysis_request(document)
    if can_start_layout_analysis(document):
        add_layout_request_and_change_document_state(request)
        flash(u'Request for layout analysis successfully created!', 'success')
    else:
        flash(u'Request for layout analysis is already pending or document is in unsupported state!', 'danger')
    return redirect(url_for('document.documents'))


@bp.route('/layout_analysis/get_request')
def get_request():
    request = get_first_layout_request()
    if request:
        change_layout_request_and_document_state(request)
        return create_json_from_request(request)
    else:
        return jsonify({})
