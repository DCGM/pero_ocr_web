import os
import shutil
import json
import configparser
from flask import render_template, request, current_app, send_file
from flask import url_for, redirect, flash, jsonify
from flask_login import login_required, current_user
from app.ocr import bp
from app.db.general import get_document_by_id, get_request_by_id, get_image_by_id, get_baseline_by_id, get_ocr_by_id, \
                           get_language_model_by_id
from app.db import DocumentState, OCR, Document, Image, TextRegion, Baseline, LanguageModel, User
from app.ocr.general import create_json_from_request, create_ocr_request, \
                            can_start_ocr, add_ocr_request_and_change_document_state, get_first_ocr_request, \
                            insert_lines_to_db, change_ocr_request_and_document_state_on_success, insert_annotations_to_db, \
                            update_text_lines, get_page_annotated_lines, change_ocr_request_and_document_state_in_progress, \
                            post_files_to_folder
from app.document.general import get_document_images
from app import db_session


########################################################################################################################
# WEBSITE ROUTES
########################################################################################################################

# MENU PAGE
########################################################################################################################

@bp.route('/show_results/<string:document_id>', methods=['GET'])
@login_required
def show_results(document_id):
    document = get_document_by_id(document_id)
    if document.state != DocumentState.COMPLETED_OCR:
        return  # Bad Request or something like that
    images = get_document_images(document)
    return render_template('ocr/ocr_results.html', document=document, images=list(images))


@bp.route('/revert_ocr/<string:document_id>', methods=['GET'])
@login_required
def revert_ocr(document_id):
    print()
    print("REVERT OCR")
    print("##################################################################")
    document = Document.query.filter_by(id=document_id, deleted=False).first()
    delete_user = db_session.query(User).filter(User.first_name == "#revert_OCR_backup#").first()
    backup_document = Document(name="revert_backup_" + document.name, state=DocumentState.COMPLETED_OCR,
                               user_id=delete_user.id)
    new_regions = []
    for img in document.images:
        print(str(img.id))
        backup_img = Image(filename=img.filename, path=img.path, width=img.width, height=img.height,
                           deleted=img.deleted, imagehash=img.imagehash)
        backup_document.images.append(backup_img)
        for region in img.textregions:
            backup_region = TextRegion(order=region.order, points=region.points, deleted=region.deleted)
            backup_img.textregions.append(backup_region)
            new_regions.append((region.id, backup_region))
            for line in region.textlines:
                line.region_id = backup_region.id
    db_session.add(backup_document)
    document.state = DocumentState.COMPLETED_LAYOUT_ANALYSIS
    db_session.commit()
    print("##################################################################")
    return document_id


# SELECT PAGE
########################################################################################################################

@bp.route('/select_ocr/<string:document_id>', methods=['GET'])
@login_required
def select_ocr(document_id):
    document = get_document_by_id(document_id)
    ocr_engines = db_session.query(OCR).filter(OCR.active).all()
    baseline_engines = db_session.query(Baseline).filter(Baseline.active).all()
    language_model_engines = db_session.query(LanguageModel).filter(LanguageModel.active).all()
    return render_template('ocr/ocr_select.html', document=document, ocr_engines=ocr_engines,
                           baseline_engines=baseline_engines, language_model_engines=language_model_engines)


@bp.route('/start_ocr/<string:document_id>', methods=['POST'])
@login_required
def start_ocr(document_id):
    document = get_document_by_id(document_id)
    baseline_id = request.form['baseline_id']
    ocr_id = request.form['ocr_id']
    language_model_id = request.form['language_model_id']
    ocr_request = create_ocr_request(document, baseline_id, ocr_id, language_model_id)
    if can_start_ocr(document):
        add_ocr_request_and_change_document_state(ocr_request)
        flash(u'Request for ocr successfully created!', 'success')
    else:
        flash(u'Request for ocr is already pending or document is in unsupported state!', 'danger')
    return redirect(url_for('document.documents'))


# RESULTS PAGE
########################################################################################################################

@bp.route('/get_lines/<string:document_id>/<string:image_id>', methods=['GET'])
@login_required
def get_lines(document_id, image_id):
    lines_dict = {'document_id': document_id, 'image_id': image_id, 'lines': []}
    image = get_image_by_id(image_id)
    lines_dict['height'] = image.height
    lines_dict['width'] = image.width
    skip_textregion_sorting = False
    for tr in image.textregions:
        if tr.order is None:
            skip_textregion_sorting = True
    if not skip_textregion_sorting:
        text_regions = sorted(list(image.textregions), key=lambda x: x.order)
    else:
        text_regions = image.textregions

    annotated_lines = set(get_page_annotated_lines(image_id))

    for text_region in text_regions:
        text_lines = sorted(list(text_region.textlines), key=lambda x: x.order)
        lines_dict['lines'] += [{
                    'id': line.id,
                    'np_points':  line.np_points.tolist(),
                    'np_baseline':  line.np_baseline.tolist(),
                    'np_heights':  line.np_heights.tolist(),
                    'np_confidences':  line.np_confidences.tolist(),
                    'np_textregion_width':  [text_region.np_points[:, 0].min(), text_region.np_points[:, 0].max()],
                    'annotated': line.id in annotated_lines,
                    'text': line.text if line.text is not None else ""
                } for line in text_lines]
    return jsonify(lines_dict)


@bp.route('/save_annotations/<string:document_id>', methods=['POST'])
@login_required
def save_annotations(document_id):
    document = get_document_by_id(document_id)
    if document.state == DocumentState.COMPLETED_OCR:
        insert_annotations_to_db(current_user, json.loads(request.form['annotations']))
        update_text_lines(json.loads(request.form['annotations']))
        print(json.loads(request.form['annotations']))
        return jsonify({'status': 'success'})
    else:
        flash(u'Document is not processed by any OCR!', 'danger')
        return jsonify({'status': 'redirect', 'href': url_for('document.documents')})


########################################################################################################################
# CLIENT ROUTES
########################################################################################################################

# POST RESPONSE FROM CLIENT, XMLS AND LOGITS
########################################################################################################################

@bp.route('/post_result/<string:ocr_request_id>', methods=['POST'])
def post_result(ocr_request_id):
    print()
    print("INSERT LINES FROM XMLS AND LOGITS TO DB")
    print("##################################################################")
    ocr_request = get_request_by_id(ocr_request_id)
    document = get_document_by_id(ocr_request.document_id)
    result_folder = os.path.join(current_app.config['OCR_RESULTS_FOLDER'], str(document.id))
    post_files_to_folder(request, result_folder)
    insert_lines_to_db(result_folder)
    change_ocr_request_and_document_state_on_success(ocr_request)
    print("##################################################################")
    return 'OK'


# GET CONFIG AND MODELS FOR PARSE FOLDER
########################################################################################################################

@bp.route('/get_request')
def get_ocr_request():
    ocr_request = get_first_ocr_request()
    if ocr_request:
        change_ocr_request_and_document_state_in_progress(ocr_request)
        return create_json_from_request(ocr_request)
    else:
        return jsonify({})


@bp.route('/get_config/<string:baseline_id>/<string:ocr_id>/<string:language_model_id>')
def get_config(baseline_id, ocr_id, language_model_id):
    baseline = get_baseline_by_id(baseline_id)
    ocr = get_ocr_by_id(ocr_id)
    language_model = get_language_model_by_id(language_model_id)
    language_model_name = language_model.name
    config_name = "{}_{}_{}.ini".format(get_model_folder_name(baseline.name), get_model_folder_name(ocr.name),
                                        get_model_folder_name(language_model_name))
    config = os.path.join(current_app.config['MODELS_FOLDER'], "configs", config_name)
    if not os.path.exists(config):
        model_configs = [os.path.join(current_app.config['MODELS_FOLDER'], "config_base.ini")]
        for model, model_type in zip([baseline, ocr, language_model], ["baseline", "ocr", "language_model"]):
            model_configs.append(get_model_config(model, model_type))
        concatenate_text_files(model_configs, config)
        config_parser = configparser.RawConfigParser()
        config_parser.optionxform = str
        config_parser.read(config)
        if get_model_folder_name(language_model_name) == "none":
            config_parser['PAGE_PARSER']['RUN_DECODER'] = "no"
        with open(config, 'w') as configfile:
            config_parser.write(configfile)

    return send_file(config, attachment_filename="config.ini", as_attachment=True)


@bp.route('/get_baseline/<string:baseline_id>')
def get_baseline(baseline_id):
    baseline = get_baseline_by_id(baseline_id)
    return get_model(baseline, "baseline")


@bp.route('/get_ocr/<string:ocr_id>')
def get_ocr(ocr_id):
    ocr = get_ocr_by_id(ocr_id)
    return get_model(ocr, "ocr")


@bp.route('/get_language_model/<string:language_model_id>')
def get_language_model(language_model_id):
    language_model = get_language_model_by_id(language_model_id)
    return get_model(language_model, "language_model")


def get_model(model, model_type):
    model_folder = os.path.join(current_app.config['MODELS_FOLDER'], model_type, get_model_folder_name(model.name),
                                "model")
    if not os.path.exists("{}.zip".format(model_folder)):
        shutil.make_archive(model_folder, 'zip', model_folder)
    return send_file("{}.zip".format(model_folder), attachment_filename="{}.zip".format(model_type), as_attachment=True)


def get_model_config(model, model_type):
    return os.path.join(current_app.config['MODELS_FOLDER'], model_type, get_model_folder_name(model.name), "config", "config.ini")


def get_model_folder_name(model_name):
    return model_name.replace(" ", "_").lower()


def concatenate_text_files(text_files, output_text_file):
    with open(output_text_file, 'wb') as wfd:
        for f in text_files:
            with open(f, 'rb') as fd:
                shutil.copyfileobj(fd, wfd)
