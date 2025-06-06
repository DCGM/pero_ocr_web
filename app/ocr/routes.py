import os
import shutil
import json
import uuid
from collections import defaultdict
from natsort import natsorted
import copy
import sqlalchemy
import unicodedata
from pero_ocr.core.arabic_helper import ArabicHelper
from flask import render_template, request, current_app, send_file
from flask import url_for, redirect, flash, jsonify
from flask_login import login_required, current_user
from app.ocr import bp
from app.db.general import get_document_by_id, get_request_by_id, get_image_by_id, get_baseline_by_id, get_ocr_by_id, \
                           get_language_model_by_id, get_text_line_by_id, get_text_region_by_id, get_image_annotation_statistics_db, \
                           get_document_annotation_statistics_db, get_previews_for_documents, TextLine
from app.db import DocumentState, RequestState, OCR, Document, Image, TextRegion, Baseline, LanguageModel, User, OCRTrainingDocuments
from app.ocr.general import create_json_from_request, create_ocr_request, \
                            can_start_ocr, add_ocr_request_and_change_document_state, get_first_ocr_request, \
                            insert_lines_to_db, change_ocr_request_and_document_state_on_success_handler, insert_annotations_to_db, \
                            update_text_lines, get_page_annotated_lines, change_ocr_request_and_document_state_in_progress_handler, \
                            post_files_to_folder, change_ocr_request_to_fail_and_document_state_to_success_handler, \
                            change_ocr_request_to_fail_and_document_state_to_completed_layout_analysis_handler, set_delete_flag, \
                            set_training_flag
from app.mail.mail import send_ocr_failed_mail

from app.document.general import get_document_images
from app import db_session, engine
from app.db import Image
from app.document.general import is_user_owner_or_collaborator, is_user_trusted, is_granted_acces_for_page, \
                                 is_granted_acces_for_document, is_score_computed, document_exists, \
                                 document_in_allowed_state


########################################################################################################################
# WEBSITE ROUTES
########################################################################################################################

# MENU PAGE
########################################################################################################################

@bp.route('/show_results/<string:document_id>', methods=['GET'])
@bp.route('/show_results/<string:document_id>/<string:image_id>', methods=['GET'])
@bp.route('/show_results/<string:document_id>/<string:image_id>/<string:line_id>', methods=['GET'])
@login_required
def show_results(document_id, image_id=None, line_id=None):
    if not document_exists(document_id):
        flash(u'Document with this id does not exist!', 'danger')
        return redirect(url_for('main.index'))
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    document = get_document_by_id(document_id)
    if document.state == DocumentState.NEW:
        return redirect(url_for('document.upload_images_to_document', document_id=document.id))
    elif document.state == DocumentState.COMPLETED_LAYOUT_ANALYSIS:
        return redirect(url_for('layout_analysis.show_results', document_id=document.id))
    elif document.state != DocumentState.COMPLETED_OCR:
        flash(u'Document can not be edited in its current state.', 'danger')
        return redirect(url_for('main.index'))

    images = natsorted(get_document_images(document).all(), key=lambda x: x.filename)
    return render_template('ocr/ocr_results.html', document=document, images=images,
                           trusted_user=is_user_trusted(current_user), computed_scores=True, public_view=False)


@bp.route('/show_public_results/<string:document_id>', methods=['GET'])
@bp.route('/show_public_results/<string:document_id>/<string:image_id>', methods=['GET'])
@bp.route('/show_public_results/<string:document_id>/<string:image_id>/<string:line_id>', methods=['GET'])
def show_public_results(document_id, image_id=None, line_id=None):
    if not document_exists(document_id):
        flash(u'This document does not exist or it is not public at the moment!', 'danger')
        return redirect(url_for('document.public_documents'))

    document = get_document_by_id(document_id)
    if not document.is_public:
        flash(u'This document does not exist or it is not public at the moment!', 'danger')
        return redirect(url_for('document.public_documents'))

    if document.state != DocumentState.COMPLETED_OCR:
        flash(u'This public document has not been processed by OCR and it is not viewable.', 'danger')
        return redirect(url_for('document.public_documents'))

    images = natsorted(get_document_images(document).all(), key=lambda x: x.filename)
    return render_template('ocr/ocr_results.html', document=document, images=images,
                           trusted_user=False, computed_scores=True, public_view=True)

@bp.route('/show_results_new/<string:document_id>', methods=['GET'])
@bp.route('/show_results_new/<string:document_id>/<string:image_id>', methods=['GET'])
@bp.route('/show_results_new/<string:document_id>/<string:image_id>/<string:line_id>', methods=['GET'])
@login_required
def show_results_new(document_id, image_id=None, line_id=None):
    if not document_exists(document_id):
        flash(u'Document with this id does not exist!', 'danger')
        return redirect(url_for('main.index'))
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    document = get_document_by_id(document_id)
    if document.state == DocumentState.NEW:
        return redirect(url_for('document.upload_images_to_document', document_id=document.id))
    elif document.state == DocumentState.COMPLETED_LAYOUT_ANALYSIS:
        return redirect(url_for('layout_analysis.show_results_new', document_id=document.id))
    elif document.state != DocumentState.COMPLETED_OCR:
        flash(u'Document can not be edited int its current state.', 'danger')
        return redirect(url_for('main.index'))

    images = natsorted(get_document_images(document).all(), key=lambda x: x.filename)
    return render_template('ocr/ocr_results_new.html', document=document, images=images,
                           trusted_user=is_user_trusted(current_user), computed_scores=True)

@bp.route('/revert_ocr/<string:document_id>', methods=['GET'])
@login_required
def revert_ocr(document_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    document = get_document_by_id(document_id)
    if document.state != DocumentState.COMPLETED_OCR:
        flash(u'Document is in the state prohibiting OCR revert!', 'danger')
        return redirect(url_for('main.index'))

    print()
    print("REVERT OCR")
    print("##################################################################")
    delete_user = db_session.query(User).filter(User.first_name == "#revert_OCR_backup#").first()
    backup_document = Document(name="revert_backup_" + document.name, state=DocumentState.COMPLETED_OCR,
                               user_id=delete_user.id, line_count=document.line_count,
                               annotated_line_count=document.annotated_line_count)
    db_session.add(backup_document)
    for original_img in document.images:
        backup_img = Image(id=uuid.uuid4(), filename=original_img.filename, path=original_img.path, width=original_img.width, height=original_img.height,
                           deleted=original_img.deleted, imagehash=original_img.imagehash)
        backup_document.images.append(backup_img)
        for region in original_img.textregions:
            region.image_id = backup_img.id
            original_img.textregions.append(
                TextRegion(order=region.order, points=region.points, deleted=region.deleted))
    document.state = DocumentState.COMPLETED_LAYOUT_ANALYSIS
    document.annotated_line_count = 0
    db_session.commit()
    print("##################################################################")
    return document_id


@bp.route('/create_edit_annotation', methods=['POST'])
@login_required
def create_edit_annotation():
    data = request.get_json()
    annotation = data['annotation']
    annotation_type = data['annotation_type']
    points = ' '.join(map(lambda p: f'{int(p["x"])},{int(p["y"])}', annotation['points']))
    baseline = None
    heights = None
    if annotation_type == 'row':
        baseline = ' '.join(map(lambda p: f'{int(p["x"])},{int(p["y"])}', annotation['baseline']))
        heights = f"{annotation['heights'][0]} {annotation['heights'][1]}"

    if annotation_type == 'row':
        text_line = get_text_line_by_id(annotation['uuid'])
        if text_line is not None:
            text_line.points = points
            text_line.baseline = baseline
            text_line.heights = heights
            db_session.commit()
            return 'edited', 200
    elif annotation_type == 'region':
        text_region = get_text_region_by_id(annotation['uuid'])
        if text_region is not None:
            text_region.points = points
            db_session.commit()
        return 'edited', 200
    else:
        return 'Unknown annotation type', 400


    insert_data = None
    if annotation_type == 'row':  # Row
        region_id = annotation['region_annotation_uuid']
        if not region_id:
            return 'Annotation does not exist and image_id is not set', 400
        insert_data = TextLine(
            id=annotation['uuid'],
            region_id=region_id,
            text=annotation['text'],
            points=points,
            baseline=baseline,
            heights=heights,
            order=1  # TODO
        )
    elif annotation_type == 'region':  # Region
        image_id = data['image_id']
        if not image_id:
            return 'Annotation does not exist and image_id is not set', 400
        insert_data = TextRegion(
            id=annotation['uuid'],
            points=points,
            image_id=image_id,
            order=42  # TODO
        )
    db_session.add(insert_data)
    db_session.commit()
    return 'created', 200

# SELECT PAGE
########################################################################################################################

@bp.route('/ocr_training_documents', methods=['GET'])
@login_required
def ocr_training_documents():
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))

    db_all_ocr_engines = db_session.query(OCR).all()
    ocr_id = request.args.getlist('ocr')
    if ocr_id:
        db_ocr_engines = db_session.query(OCR).filter(OCR.id.in_(ocr_id)).all()
    else:
        db_ocr_engines = db_session.query(OCR).filter(OCR.active).all()

    db_documents = db_session.query(Document).filter(Document.state == DocumentState.COMPLETED_OCR)\
        .options(sqlalchemy.orm.joinedload(Document.requests_lazy)).filter(Document.name.notlike('revert_backup_%')).all()

    engine_names = {o.id: o.name for o in db_session.query(OCR)}

    document_ids = [d.id for d in db_documents]
    previews = dict([(im.document_id, im) for im in get_previews_for_documents(document_ids)])

    selected_documents = defaultdict(set)
    for ocr_document in db_session.query(OCRTrainingDocuments):
        selected_documents[ocr_document.ocr_id].add(ocr_document.document_id)

    return render_template('ocr/ocr_training_documents.html',
                           documents=db_documents, ocr_engines=db_ocr_engines, all_ocr_engines=db_all_ocr_engines,
                           previews=previews, engine_names=engine_names, selected_documents=selected_documents)


@bp.route('/set_ocr_training_document/<string:document_id>/<string:ocr_id>/<string:state>', methods=['GET'])
@login_required
def ocr_training_documents_post(document_id, ocr_id, state):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))

    db_training_document = db_session.query(OCRTrainingDocuments)\
        .filter(OCRTrainingDocuments.ocr_id == ocr_id)\
        .filter(OCRTrainingDocuments.document_id == document_id).all()

    if len(db_training_document) == 1:
        db_training_document = db_training_document[0]
    else:
        db_training_document = None

    if state == 'false' and db_training_document:
        db_session.delete(db_training_document)
        db_session.commit()
    elif state == 'true' and not db_training_document:
        db_session.add(OCRTrainingDocuments(document_id=document_id, ocr_id=ocr_id))
        db_session.commit()

    return '', 204


@bp.route('/get_ocr_training_documents/<string:ocr_id>', methods=['GET'])
def get_ocr_training_documents(ocr_id):
    db_training_document = db_session.query(OCRTrainingDocuments)\
        .filter(OCRTrainingDocuments.ocr_id == ocr_id).all()

    document_ids = [d.document_id for d in db_training_document]

    return ','.join(document_ids), 200


@bp.route('/select_ocr/<string:document_id>', methods=['GET'])
@login_required
def select_ocr(document_id):
    if not is_granted_acces_for_document(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))
    document = get_document_by_id(document_id)
    ocr_engines = db_session.query(OCR).filter(OCR.active).order_by(OCR.order).all()
    baseline_engines = db_session.query(Baseline).filter(Baseline.active).order_by(Baseline.order).all()
    language_model_engines = db_session.query(LanguageModel).filter(LanguageModel.active).order_by(LanguageModel.order).all()
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

@bp.route('/get_image_annotation_statistics/<string:image_id>', methods=['GET'])
def get_image_annotation_statistics(image_id):
    try:
        db_image = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404

    line_count, annotated_count = get_image_annotation_statistics_db(image_id)
    response = {'image_id': image_id, 'line_count': line_count, 'annotated_count': annotated_count}

    return jsonify(response)


@bp.route('/get_document_annotation_statistics/<string:document_id>', methods=['GET'])
@login_required
def get_document_annotation_statistics(document_id):
    if not is_granted_acces_for_document(document_id, current_user):
        return "Access denied.", 401

    try:
        db_document = get_document_by_id(document_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404


    annotated_count = get_document_annotation_statistics_db(document_id)
    response = {'document_id': document_id, 'annotated_count': annotated_count}

    return jsonify(response)


def get_lines_common(image_id, public=False):
    try:
        db_image = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404

    if public:
        if not db_image.document.is_public:
            return "The requested document is not public at the moment.", 403
    else:
        if not is_granted_acces_for_page(image_id, current_user):
            return "You do not have sufficient rights to get lines from the requested document!", 403

    lines_dict = {'image_id': image_id, 'lines': []}
    lines_dict['height'] = db_image.height
    lines_dict['width'] = db_image.width
    skip_textregion_sorting = False
    for tr in db_image.textregions:
        if tr.order is None:
            skip_textregion_sorting = True
    if not skip_textregion_sorting:
        text_regions = sorted(list(db_image.textregions), key=lambda x: x.order)
    else:
        text_regions = db_image.textregions
    text_regions = list(filter(lambda region: not region.deleted, text_regions))

    annotated_lines = set(get_page_annotated_lines(image_id))

    arabic_helper = ArabicHelper()
    arabic = False

    # Add regions
    lines_dict['regions'] = list(map(lambda r: {
        'uuid': r.id,
        'np_points': r.np_points.tolist()
    }, text_regions))

    for text_region in text_regions:
        text_lines = sorted(list(text_region.textlines), key=lambda x: x.order)

        for line in text_lines:
            if line.deleted:
                continue
            text = line.text if line.text is not None else ""
            confidences = line.np_confidences.tolist()
            if len(text) != len(confidences):
                confidences = []
            if line.text and arabic_helper.is_arabic_line(line.text):
                arabic = True
                text_to_detect_ligatures = arabic_helper._reverse_transcription(copy.deepcopy(text))
            else:
                text_to_detect_ligatures = text

            ligatures_mapping = []

            for i, c in enumerate(text_to_detect_ligatures):
                if unicodedata.combining(c) and i:
                    ligatures_mapping[-1].append(i)
                else:
                    ligatures_mapping.append([i])

            lines_dict['lines'].append({
                            'id': line.id,
                            'region_id': line.region_id,
                            'np_points':  line.np_points.tolist(),
                            'np_baseline':  line.np_baseline.tolist(),
                            'np_heights':  line.np_heights.tolist(),
                            'np_confidences': confidences,
                            'ligatures_mapping': ligatures_mapping,
                            'np_textregion_width':  [text_region.np_points[:, 0].min(), text_region.np_points[:, 0].max()],
                            'annotated': line.id in annotated_lines,
                            'text': text,
                            'for_training': line.for_training
                        })

    for l in lines_dict['lines']:
        if arabic:
            l['arabic'] = True
        else:
            l['arabic'] = False

    return jsonify(lines_dict)


@bp.route('/get_lines/<string:image_id>', methods=['GET'])
@login_required
def get_lines(image_id):
    return get_lines_common(image_id, False)


@bp.route('/get_public_lines/<string:image_id>', methods=['GET'])
def get_public_lines(image_id):
    return get_lines_common(image_id, True)


@bp.route('/get_arabic_label_form/<string:text>', methods=['GET'])
@login_required
def get_arabic_label_form(text):
    arabic_helper = ArabicHelper()
    return arabic_helper.visual_form_to_label_form(text)


@bp.route('/save_annotations', methods=['POST'])
@login_required
def save_annotations():
    annotations = json.loads(request.form['annotations'])
    if not annotations:
        return jsonify({'status': 'success'})

    document_completed_ocr = True
    for annotation in annotations:
        text_line = get_text_line_by_id(annotation['id'])
        document = text_line.region.image.document
        if not is_user_owner_or_collaborator(document.id, current_user):
            flash(u'You do not have sufficient rights to add annotations to the document!', 'danger')
            return jsonify({'status': 'redirect', 'href': url_for('document.documents')})
        if document.state != DocumentState.COMPLETED_OCR:
            document_completed_ocr = False
    if not document_completed_ocr:
        flash(u'You cannot add annotations to unprocessed document!', 'danger')
        return jsonify({'status': 'redirect', 'href': url_for('document.documents')})

    insert_annotations_to_db(current_user, annotations)
    update_text_lines(annotations)
    print(annotations)
    return jsonify({'status': 'success'})


@bp.route('/delete_line/<string:line_id>/<int:delete_flag>', methods=['POST'])
@login_required
def delete_line(line_id, delete_flag):
    # Get text_line
    text_line = get_text_line_by_id(line_id)
    if text_line is None:
        return "Line does not exist.", 404

    document = text_line.region.image.document
    #
    if not is_user_owner_or_collaborator(document.id, current_user):
        flash(u'You do not have sufficient rights to add annotations to the document!', 'danger')
        return jsonify({'status': 'redirect', 'href': url_for('document.documents')})
    if document.state != DocumentState.COMPLETED_OCR:
        flash(u'You cannot add annotations to unprocessed document!', 'danger')
        return jsonify({'status': 'redirect', 'href': url_for('document.documents')})

    # Delete text_line
    if text_line:
        set_delete_flag(text_line, delete_flag)

    return jsonify({'status': 'success'})

@bp.route('/delete_region/<string:region_id>/<int:delete_flag>', methods=['POST'])
@login_required
def delete_region(region_id, delete_flag):
    # Get text_region
    text_region = get_text_region_by_id(region_id)
    if text_region:
        document = text_region.image.document

    #
    if not is_user_owner_or_collaborator(document.id, current_user):
        flash(u'You do not have sufficient rights to add annotations to the document!', 'danger')
        return jsonify({'status': 'redirect', 'href': url_for('document.documents')})
    if document.state != DocumentState.COMPLETED_OCR:
        flash(u'You cannot add annotations to unprocessed document!', 'danger')
        return jsonify({'status': 'redirect', 'href': url_for('document.documents')})

    # Delete text_line / text_region + nested text_lines
    if text_region:
        set_delete_flag(text_region, delete_flag)
        # Delete all nested text_lines after deleting text_region
        for text_line_child in text_region.textlines:
            set_delete_flag(text_line_child, delete_flag)

    return jsonify({'status': 'success'})


@bp.route('/training_line/<string:line_id>/<int:training_flag>', methods=['POST'])
@login_required
def training_line(line_id, training_flag):
    text_line = get_text_line_by_id(line_id)
    document = text_line.region.image.document
    if not is_user_owner_or_collaborator(document.id, current_user):
        flash(u'You do not have sufficient rights to add annotations to the document!', 'danger')
        return jsonify({'status': 'redirect', 'href': url_for('document.documents')})
    if document.state != DocumentState.COMPLETED_OCR:
        flash(u'You cannot add annotations to unprocessed document!', 'danger')
        return jsonify({'status': 'redirect', 'href': url_for('document.documents')})

    set_training_flag(text_line, training_flag)

    return jsonify({'status': 'success'})


########################################################################################################################
# CLIENT ROUTES
########################################################################################################################

# POST RESPONSE FROM CLIENT, XMLS AND LOGITS
########################################################################################################################

@bp.route('/post_result/<string:request_id>/<string:image_id>', methods=['POST'])
@login_required
def post_result(request_id, image_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))

    db_request = get_request_by_id(request_id)
    if db_request.state != RequestState.IN_PROGRESS:
        return "Request in wrong state: {}.".format(db_request.state), 406

    try:
        db_image = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404

    if db_image.document.state != DocumentState.COMPLETED_OCR:
        print()
        print("INSERT LINES FROM XMLS AND LOGITS TO DB")
        print("##################################################################")
        result_folder = os.path.join(current_app.config['OCR_RESULTS_FOLDER'], str(db_image.document_id))
        if not os.path.exists(result_folder):
            os.makedirs(result_folder, exist_ok=True)  # exist_ok=True is needed due to multi-processing
        file_names = post_files_to_folder(request, result_folder)
        insert_lines_to_db(result_folder, file_names)
        print("##################################################################")
    return 'OK'


@bp.route('/change_ocr_request_and_document_state_on_success/<string:request_id>', methods=['POST'])
@login_required
def change_ocr_request_and_document_state_on_success(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    ocr_request = get_request_by_id(request_id)
    change_ocr_request_and_document_state_on_success_handler(ocr_request)
    return 'OK'


@bp.route('/change_ocr_request_to_fail_and_document_state_to_success/<string:request_id>', methods=['POST'])
@login_required
def change_ocr_request_to_fail_and_document_state_to_success(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    ocr_request = get_request_by_id(request_id)
    change_ocr_request_to_fail_and_document_state_to_success_handler(ocr_request)
    if 'EMAIL_NOTIFICATION_ADDRESSES' in current_app.config and current_app.config['EMAIL_NOTIFICATION_ADDRESSES']:
        send_ocr_failed_mail(ocr_request, request)
    return 'OK'


@bp.route('/change_ocr_request_to_fail_and_document_state_to_completed_layout_analysis/<string:request_id>', methods=['POST'])
@login_required
def change_ocr_request_to_fail_and_document_state_to_completed_layout_analysis(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    ocr_request = get_request_by_id(request_id)
    change_ocr_request_to_fail_and_document_state_to_completed_layout_analysis_handler(ocr_request)
    if 'EMAIL_NOTIFICATION_ADDRESSES' in current_app.config and current_app.config['EMAIL_NOTIFICATION_ADDRESSES']:
        send_ocr_failed_mail(ocr_request, request)
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
        change_ocr_request_and_document_state_in_progress_handler(ocr_request)
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

