import os
from app.ocr import bp
from flask import render_template, url_for, redirect, flash, jsonify, request, current_app, send_file, abort
from flask import url_for, redirect, flash, jsonify
from flask_login import login_required
from app.db.general import get_document_by_id, get_request_by_id, get_image_by_id, get_text_region_by_id
from app.ocr.general import create_json_from_request, create_ocr_request, \
                            can_start_ocr, add_ocr_request_and_change_document_state, get_first_ocr_request, \
                            insert_lines_to_db, change_ocr_request_and_document_state_on_success, insert_annotations_to_db, \
                            update_text_lines
from app.document.general import get_document_images
from app.db import DocumentState, OCR
from app import db_session

import json

@bp.route('/select_ocr/<string:document_id>', methods=['GET'])
@login_required
def select_ocr(document_id):
    document = get_document_by_id(document_id)
    ocr_engines = db_session.query(OCR).filter(OCR.active).all()
    return render_template('ocr/ocr_select.html', document=document, ocr_engines=ocr_engines)

@bp.route('/start_ocr/<string:document_id>', methods=['POST'])
@login_required
def start_ocr(document_id):
    document = get_document_by_id(document_id)
    ocr_id = request.form['ocr_id']
    ocr_request = create_ocr_request(document, ocr_id)
    if can_start_ocr(document):
        add_ocr_request_and_change_document_state(ocr_request)
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

    insert_lines_to_db(ocr_result_folder)
    change_ocr_request_and_document_state_on_success(ocr_request)

    return 'OK'

@bp.route('/show_results/<string:document_id>', methods=['GET'])
@login_required
def show_results(document_id):
    document = get_document_by_id(document_id)
    if document.state != DocumentState.COMPLETED_OCR:
        return  # Bad Request or something like that
    images = get_document_images(document)

    return render_template('ocr/ocr_results.html', document=document, images=images)

@bp.route('/get_lines/<string:document_id>/<string:image_id>', methods=['GET'])
@login_required
def get_lines(document_id, image_id):
    lines_dict = {'document_id':document_id, 'image_id':image_id, 'lines':[]}
    image = get_image_by_id(image_id)
    lines_dict['height'] = image.height
    lines_dict['width'] = image.width
    skip_textregion_sorting = False
    for tr in image.textregions:
        if tr.order is None:
            skip_textregion_sorting = True
    if not skip_textregion_sorting:
        textregions = sorted(list(image.textregions), key=lambda x: x.order)
    else:
        textregions = image.textregions
    for textregion in textregions:
        skip_textline_sorting = False
        for tl in textregion.textlines:
            if tl.order is None:
                skip_textline_sorting = True
        if not skip_textline_sorting:
            textlines = sorted(list(textregion.textlines), key=lambda x: x.order)
        else:
            textlines = textregion.textlines
        for line in textlines:
            line_dict = {}
            line_dict['id'] = line.id;
            line_dict['np_points'] = line.np_points.tolist()
            line_dict['np_baseline'] = line.np_baseline.tolist()
            line_dict['np_heights'] = line.np_heights.tolist()
            line_dict['np_confidences'] = line.np_confidences.tolist()
            line_dict['np_textregion_width'] = [min(textregion.np_points[:,1]), max(textregion.np_points[:,1])]
            line_dict['text'] = line.text
            lines_dict['lines'].append(line_dict)
    return jsonify(lines_dict)


@bp.route('/save_annotations', methods=['POST'])
def save_annotations():
    insert_annotations_to_db(json.loads(request.form['annotations']))
    update_text_lines(json.loads(request.form['annotations']))
    print(json.loads(request.form['annotations']))
    return 'OK'
