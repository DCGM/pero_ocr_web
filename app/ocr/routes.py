import os
from app.ocr import bp
from flask import render_template, url_for, redirect, flash, jsonify, request, current_app, send_file, abort
from flask import url_for, redirect, flash, jsonify
from flask_login import login_required
from app.db.general import get_document_by_id, get_request_by_id, get_image_by_id, get_text_region_by_id
from app.ocr.general import create_json_from_request, create_ocr_analysis_request, \
                            can_start_ocr, add_ocr_request_and_change_document_state, get_first_ocr_request


@bp.route('/start_ocr/<string:document_id>')
@login_required
def start_ocr(document_id):
    document = get_document_by_id(document_id)
    request = create_ocr_analysis_request(document)
    if can_start_ocr(document):
        add_ocr_request_and_change_document_state(request)
        flash(u'Request for ocr successfully created!', 'success')
    else:
        flash(u'Request for ocr is already pending or document is in unsupported state!', 'danger')
    return redirect(url_for('document.documents'))


@bp.route('/get_request')
def get_ocr_request():
    ocr_request = get_first_ocr_request()
    if ocr_request:
        return create_json_from_request(ocr_request)
    else:
        return jsonify({})


@bp.route('/post_result/<string:request_id>', methods=['POST'])
def post_result(request_id):

    print("POST OCR LINES")

    ocr_request = get_request_by_id(request_id)
    document = get_document_by_id(ocr_request.document_id)
    ocr_result_folder = os.path.join(current_app.config['OCR_RESULTS_FOLDER'], str(document.id))
    if not os.path.exists(ocr_result_folder):
        os.makedirs(ocr_result_folder)

    if not ocr_request:
        return

    files = request.files
    for file_id in files:
        file = files[file_id]
        xml_path = os.path.join(ocr_result_folder, file.filename)
        file.save(xml_path)

    '''
    files = request.files
    for file_id in files:
        file = files[file_id]
        xml_path = os.path.join(path, file.filename)
        file.save(xml_path)
    '''

    return 'OK'
