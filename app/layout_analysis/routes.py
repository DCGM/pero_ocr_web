from app.layout_analysis import bp
from flask import render_template, url_for, redirect, flash, jsonify, request, current_app
from flask_login import login_required
from app.db.general import get_document_by_id, get_request_by_id
from app.layout_analysis.general import create_layout_analysis_request, can_start_layout_analysis, \
    add_layout_request_and_change_document_state, get_first_layout_request, change_layout_request_and_document_state_in_progress, \
    create_json_from_request, change_layout_request_and_document_state_on_success
import os


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
    analysis_request = get_first_layout_request()
    if analysis_request:
        change_layout_request_and_document_state_in_progress(analysis_request)
        return create_json_from_request(analysis_request)
    else:
        return jsonify({})


@bp.route('/layout_analysis/<string:request_id>/post_result', methods=['POST'])
def post_result(request_id):
    analysis_request = get_request_by_id(request_id)
    if not analysis_request:
        return

    path = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], str(analysis_request.document_id))
    if not os.path.exists(path):
        os.makedirs(path)

    files = request.files
    for file_id in files:
        file = files[file_id]
        file.save(os.path.join(path, file.filename))

    change_layout_request_and_document_state_on_success(analysis_request)
    return


@bp.route('/layout_analysis/<string:document_id>/results', methods=['GET'])
def show_results(document_id):
    return '<h1>LAYOUT RESULTS</h1><p>{}</p>'.format(document_id)
