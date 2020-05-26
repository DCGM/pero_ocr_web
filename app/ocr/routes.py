import os
import shutil
import json
import uuid
from natsort import natsorted
from flask import render_template, request, current_app, send_file
from flask import url_for, redirect, flash, jsonify
from flask_login import login_required, current_user
from app.ocr import bp
from app.db.general import get_document_by_id, get_request_by_id, get_image_by_id, get_baseline_by_id, get_ocr_by_id, \
                           get_language_model_by_id, get_text_line_by_id
from app.db import DocumentState, OCR, Document, Image, TextRegion, Baseline, LanguageModel, User
from app.ocr.general import create_json_from_request, create_ocr_request, \
                            can_start_ocr, add_ocr_request_and_change_document_state, get_first_ocr_request, \
                            insert_lines_to_db, change_ocr_request_and_document_state_on_success, insert_annotations_to_db, \
                            update_text_lines, get_page_annotated_lines, change_ocr_request_and_document_state_in_progress, \
                            post_files_to_folder, change_ocr_request_to_fail_and_document_state_to_success, \
                            change_ocr_request_to_fail_and_document_state_to_completed_layout_analysis
from app.document.general import get_document_images
from app import db_session
from app.document.general import is_user_owner_or_collaborator, is_user_trusted, is_granted_acces_for_page, \
                                 is_granted_acces_for_document, is_score_computed


########################################################################################################################
# WEBSITE ROUTES
########################################################################################################################

# MENU PAGE
########################################################################################################################

@bp.route('/show_results/<string:document_id>', methods=['GET'])
@login_required
def show_results(document_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))
    document = get_document_by_id(document_id)
    if document.state != DocumentState.COMPLETED_OCR:
        return  # Bad Request or something like that
    images = get_document_images(document)

    return render_template('ocr/ocr_results.html', document=document, images=natsorted(list(images), key=lambda x: x.filename),
                           trusted_user=is_user_trusted(current_user), computed_scores=True)


@bp.route('/revert_ocr/<string:document_id>', methods=['GET'])
@login_required
def revert_ocr(document_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))
    print()
    print("REVERT OCR")
    print("##################################################################")
    document = Document.query.filter_by(id=document_id, deleted=False).first()
    delete_user = db_session.query(User).filter(User.first_name == "#revert_OCR_backup#").first()
    backup_document = Document(name="revert_backup_" + document.name, state=DocumentState.COMPLETED_OCR,
                               user_id=delete_user.id)

    db_session.add(backup_document)
    new_regions = []
    for img in document.images:
        print(str(img.id))
        backup_img = Image(filename=img.filename, path=img.path, width=img.width, height=img.height,
                           deleted=img.deleted, imagehash=img.imagehash)
        backup_document.images.append(backup_img)
        for region in img.textregions:
            backup_region = TextRegion(id=uuid.uuid4(), order=region.order, points=region.points, deleted=region.deleted)
            backup_img.textregions.append(backup_region)
            new_regions.append((region.id, backup_region))
            for line in region.textlines:
                line.region_id = backup_region.id
        db_session.commit()
    document.state = DocumentState.COMPLETED_LAYOUT_ANALYSIS
    db_session.commit()
    print("##################################################################")
    return document_id


# SELECT PAGE
########################################################################################################################

@bp.route('/select_ocr/<string:document_id>', methods=['GET'])
@login_required
def select_ocr(document_id):
    if not is_granted_acces_for_document(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))
    document = get_document_by_id(document_id)
    ocr_engines = db_session.query(OCR).filter(OCR.active).all()
    baseline_engines = db_session.query(Baseline).filter(Baseline.active).all()
    language_model_engines = db_session.query(LanguageModel).filter(LanguageModel.active).all()
    return render_template('ocr/ocr_select.html', document=document, document_state=DocumentState, ocr_engines=ocr_engines,
                           baseline_engines=baseline_engines, language_model_engines=language_model_engines)


@bp.route('/start_ocr/<string:document_id>', methods=['POST'])
@login_required
def start_ocr(document_id):
    if not is_granted_acces_for_document(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))
    document = get_document_by_id(document_id)
    if 'baseline_id' in request.form:
        baseline_id = request.form['baseline_id']
    else:
        baseline_id = None
    ocr_id = request.form['ocr_id']
    language_model_id = request.form['language_model_id']
    language_model = get_language_model_by_id(language_model_id)
    if language_model.name == "NONE":
        language_model_id = None
    ocr_request = create_ocr_request(document, baseline_id, ocr_id, language_model_id)
    if can_start_ocr(document):
        add_ocr_request_and_change_document_state(ocr_request)
        flash(u'Request for ocr successfully created!', 'success')
    else:
        flash(u'Request for ocr is already pending or document is in unsupported state!', 'danger')
    return redirect(url_for('document.documents'))


# RESULTS PAGE
########################################################################################################################

@bp.route('/get_lines/<string:image_id>', methods=['GET'])
@login_required
def get_lines(image_id):
    if not is_granted_acces_for_page(image_id, current_user):
        flash(u'You do not have sufficient rights to get lines!', 'danger')
        return redirect(url_for('main.index'))
    lines_dict = {'image_id': image_id, 'lines': []}
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


@bp.route('/save_annotations', methods=['POST'])
@login_required
def save_annotations():
    annotations = json.loads(request.form['annotations'])
    if not annotations:
        return
    document_completed_ocr = True
    for annotation in annotations:
        text_line = get_text_line_by_id(annotation['id'])
        document = text_line.region.image.document
        if not is_user_owner_or_collaborator(document.id, current_user):
            flash(u'You do not have sufficient rights to add some annotations!', 'danger')
            return redirect(url_for('main.index'))
        if document.state != DocumentState.COMPLETED_OCR:
            document_completed_ocr = False
    if document_completed_ocr:
        insert_annotations_to_db(current_user, json.loads(request.form['annotations']))
        update_text_lines(json.loads(request.form['annotations']))
        print(json.loads(request.form['annotations']))
        return jsonify({'status': 'success'})
    else:
        flash(u'You cannot add annotations to unprocessed document!', 'danger')
        return jsonify({'status': 'redirect', 'href': url_for('document.documents')})


########################################################################################################################
# CLIENT ROUTES
########################################################################################################################

# POST RESPONSE FROM CLIENT, XMLS AND LOGITS
########################################################################################################################

@bp.route('/post_result/<string:image_id>', methods=['POST'])
@login_required
def post_result(image_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    image = get_image_by_id(image_id)
    if image.document.state != DocumentState.COMPLETED_OCR:
        print()
        print("INSERT LINES FROM XMLS AND LOGITS TO DB")
        print("##################################################################")
        result_folder = os.path.join(current_app.config['OCR_RESULTS_FOLDER'], str(image.document_id))
        if not os.path.exists(result_folder):
            os.makedirs(result_folder)
        file_names = post_files_to_folder(request, result_folder)
        insert_lines_to_db(result_folder, file_names)
        print("##################################################################")
    return 'OK'


@bp.route('/change_ocr_request_and_document_state_on_success/<string:request_id>', methods=['POST'])
@login_required
def success_request(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    ocr_request = get_request_by_id(request_id)
    change_ocr_request_and_document_state_on_success(ocr_request)
    return 'OK'


@bp.route('/change_ocr_request_to_fail_and_document_state_to_success/<string:request_id>', methods=['POST'])
@login_required
def fail_completed_request(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    ocr_request = get_request_by_id(request_id)
    change_ocr_request_to_fail_and_document_state_to_success(ocr_request)
    return 'OK'


@bp.route('/change_ocr_request_to_fail_and_document_state_to_completed_layout_analysis/<string:request_id>', methods=['POST'])
@login_required
def fail_layout_request(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    ocr_request = get_request_by_id(request_id)
    change_ocr_request_to_fail_and_document_state_to_completed_layout_analysis(ocr_request)
    return 'OK'


# GET CONFIG AND MODELS FOR PARSE FOLDER
########################################################################################################################

@bp.route('/get_request')
@login_required
def get_ocr_request():
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    ocr_request = get_first_ocr_request()
    if ocr_request:
        change_ocr_request_and_document_state_in_progress(ocr_request)
        return create_json_from_request(ocr_request)
    else:
        return jsonify({})


@bp.route('/get_config/<string:baseline_id>/<string:ocr_id>/<string:language_model_id>')
@login_required
def get_config(baseline_id, ocr_id, language_model_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    if baseline_id == "none":
        baseline_id = None
    if language_model_id == "none":
        language_model_id = None
    baseline_name = "none"
    if baseline_id is not None:
        baseline_name = get_model_folder_name(get_baseline_by_id(baseline_id).name)
    ocr_name = get_model_folder_name(get_ocr_by_id(ocr_id).name)
    language_model_name = "none"
    if language_model_id is not None:
        language_model_name = get_model_folder_name(get_language_model_by_id(language_model_id).name)
    config_name = "{}_{}_{}.ini".format(baseline_name, ocr_name, language_model_name)
    config_path = os.path.join(current_app.config['MODELS_FOLDER'], "configs", config_name)

    base_config = "config_base_ocr.ini"
    model_types = ["ocr"]
    model_names = [ocr_name]
    if baseline_id is not None and language_model_id is None:
        base_config = "config_base_baseline_ocr.ini"
        model_types.append("baseline")
        model_names.append(baseline_name)
    elif baseline_id is None and language_model_id is not None:
        base_config = "config_base_ocr_language_model.ini"
        model_types.append("language_model")
        model_names.append(language_model_name)
    elif baseline_id is not None and language_model_id is not None:
        base_config = "config_base_baseline_ocr_language_model.ini"
        model_types += ["baseline", "language_model"]
        model_names += [baseline_name, language_model_name]
    model_configs = [os.path.join(current_app.config['MODELS_FOLDER'], base_config)]
    for model_type, model_name in zip(model_types, model_names):
        model_configs.append(get_model_config(model_type, model_name))
    concatenate_text_files_and_save(model_configs, config_path)

    return send_file(config_path, attachment_filename="config.ini", as_attachment=True)


@bp.route('/get_baseline/<string:baseline_id>')
@login_required
def get_baseline(baseline_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    baseline = get_baseline_by_id(baseline_id)
    return get_model(baseline, "baseline")


@bp.route('/get_ocr/<string:ocr_id>')
@login_required
def get_ocr(ocr_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    ocr = get_ocr_by_id(ocr_id)
    return get_model(ocr, "ocr")


@bp.route('/get_language_model/<string:language_model_id>')
@login_required
def get_language_model(language_model_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    language_model = get_language_model_by_id(language_model_id)
    return get_model(language_model, "language_model")


def get_model(model, model_type):
    model_folder = os.path.join(current_app.config['MODELS_FOLDER'], model_type, get_model_folder_name(model.name),
                                "model")
    if not os.path.exists("{}.zip".format(model_folder)):
        shutil.make_archive(model_folder, 'zip', model_folder)
    return send_file("{}.zip".format(model_folder), attachment_filename="{}.zip".format(model_type), as_attachment=True)


def get_model_config(model_type, model_name):
    return os.path.join(current_app.config['MODELS_FOLDER'], model_type, model_name, "config", "config.ini")


def get_model_folder_name(model_name):
    return model_name.replace(" ", "_").lower()


def concatenate_text_files_and_save(text_files, output_text_file):
    with open(output_text_file, 'wb') as wfd:
        for f in text_files:
            with open(f, 'rb') as fd:
                shutil.copyfileobj(fd, wfd)
