from app.layout_analysis import bp
from natsort import natsorted
from flask import escape, render_template, url_for, redirect, flash, request, current_app, send_file, abort
from flask_login import login_required, current_user
from app.db.general import get_document_by_id, get_request_by_id, get_image_by_id, get_layout_detector_by_id
from app.layout_analysis.general import create_layout_analysis_request, can_start_layout_analysis, \
    add_layout_request_and_change_document_state, get_first_layout_request, change_layout_request_and_document_state_in_progress_handler, \
    create_json_from_request, change_layout_request_and_document_state_on_success_handler, \
    change_document_state_on_complete_layout_analysis_handler, post_files_to_folder, insert_regions_to_db, \
    set_whole_page_region_layout_to_document, change_layout_request_to_fail_and_document_state_to_new_handler, \
    not_deleted_images_in_document
from app.mail.mail import send_layout_failed_mail
import os
import sys
import sqlalchemy
from app.db.model import DocumentState, TextRegion, LayoutDetector, Document
from app.document.general import is_user_owner_or_collaborator, is_granted_acces_for_document, is_user_trusted, \
                                 document_exists, get_document_images, make_image_preview
from app import db_session
from flask import jsonify
import shutil


########################################################################################################################
# WEBSITE ROUTES
########################################################################################################################

# MENU PAGE
########################################################################################################################

@bp.route('/show_results/<string:document_id>', methods=['GET'])
@bp.route('/show_results/<string:document_id>/<string:image_id>', methods=['GET'])
@login_required
def show_results(document_id, image_id=None):
    if not document_exists(document_id):
        flash(u'Document with this id does not exist!', 'danger')
        return redirect(url_for('main.index'))
    if not is_granted_acces_for_document(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    document = get_document_by_id(document_id)
    if document.state == DocumentState.NEW:
        return redirect(url_for('document.upload_images_to_document', document_id=document.id))
    elif document.state == DocumentState.COMPLETED_OCR:
        return redirect(url_for('ocr.show_results', document_id=document.id))
    elif document.state != DocumentState.COMPLETED_LAYOUT_ANALYSIS:
        flash(u'Document can not be edited in its current state.', 'danger')
        return redirect(url_for('main.index'))

    images = natsorted(get_document_images(document).all(), key=lambda x: x.filename)
    if len(images) == 0:
        flash(u'Document has not images and thus can not be viewed and edited.', 'danger')
        return redirect(url_for('main.index'))

    return render_template('layout_analysis/layout_results.html', document=document, images=images)


@bp.route('/revert_layout_analysis/<string:document_id>', methods=['GET'])
@login_required
def revert_layout(document_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))
    print()
    print("REVERT Layout")
    print("##################################################################")
    document = Document.query.filter_by(id=document_id, deleted=False).first()
    if document.state != DocumentState.COMPLETED_LAYOUT_ANALYSIS:
        return f'Error: Unable to revert layout, document in wrong state {document.state}.', 400
    for img in document.images:
        print(img.id)
        for region in img.textregions:
            db_session.delete(region)
    document.state = DocumentState.NEW
    db_session.commit()
    print("##################################################################")
    return escape(document_id)

# SELECT PAGE
########################################################################################################################


@bp.route('/select_layout/<string:document_id>', methods=['GET'])
@login_required
def select_layout(document_id):
    if not is_granted_acces_for_document(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))
    document = get_document_by_id(document_id)
    layout_engines = db_session.query(LayoutDetector).filter(LayoutDetector.active).order_by(LayoutDetector.order).all()
    return render_template('layout_analysis/layout_select.html', document=document, layout_engines=layout_engines)


@bp.route('/start_layout/<string:document_id>', methods=['POST'])
@login_required
def start_layout(document_id):
    if not is_granted_acces_for_document(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))
    document = get_document_by_id(document_id)
    if not not_deleted_images_in_document(document):
        flash(u'Can\'t create request without uploading images.', 'danger')
        return redirect(request.referrer)
    layout_detector_id = request.form['layout_detector_id']
    layout_detector = get_layout_detector_by_id(layout_detector_id)
    layout_detector_name = get_layout_detector_folder_name(layout_detector.name)
    if layout_detector_name == "none":
        change_document_state_on_complete_layout_analysis_handler(document)
    elif layout_detector_name == "whole_page_region":
        set_whole_page_region_layout_to_document(document)
        change_document_state_on_complete_layout_analysis_handler(document)
    else:
        layout_request = create_layout_analysis_request(document, layout_detector_id)
        if can_start_layout_analysis(document):
            add_layout_request_and_change_document_state(layout_request)
            flash(u'Request for layout analysis successfully created!', 'success')
        else:
            flash(u'Request for layout analysis is already pending or document is in unsupported state!', 'danger')
    return redirect(url_for('document.documents'))


# RESULTS PAGE
########################################################################################################################

@bp.route('/edit_layout/<string:image_id>', methods=['POST'])
@login_required
def edit_layout(image_id):
    try:
        db_image = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404
    
    document_id = db_image.document_id
    if not is_granted_acces_for_document(document_id, current_user):
        return 'You do not have sufficient rights to this document!', 403
    regions = request.get_json()
    existing_regions = dict([(str(region.id), region) for region in db_image.textregions])
    for region in regions:
        if not region or 'points' not in region or len(region['points']) <= 2:
            continue
        points = region['points']
        if region['uuid'] not in existing_regions:
            db_region = TextRegion(id=region['uuid'], deleted=region['deleted'], image_id=image_id, order=region['order'])
            db_region.np_points = points
            db_image.textregions.append(db_region)
        else:
            db_region = existing_regions[region['uuid']]
            db_region.np_points = points
            db_region.deleted = region['deleted']
            db_region.order = region['order']
    try:
        db_session.commit()
        make_image_preview(db_image)
    except sqlalchemy.exc.IntegrityError as err:
        print('ERROR: Unable to save text regions.', err, file=sys.stderr)
        db_session.rollback()
        return 'Failed to save.', 420
    return 'OK'


########################################################################################################################
# CLIENT ROUTES
########################################################################################################################

# POST RESPONSE FROM CLIENT, XMLS
########################################################################################################################

@bp.route('/post_result/<string:image_id>', methods=['POST'])
@login_required
def post_result(image_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    try:
        image = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404
    if image.document.state != DocumentState.COMPLETED_LAYOUT_ANALYSIS:
        print()
        print("INSERT REGIONS FROM XMLS TO DB")
        print("##################################################################")
        result_folder = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], str(image.document_id))
        if not os.path.exists(result_folder):
            os.makedirs(result_folder, exist_ok=True) # exist_ok=True is needed due to multi-processing
        file_names = post_files_to_folder(request, result_folder)
        insert_regions_to_db(result_folder, file_names)
        print("##################################################################")
    return 'OK'


@bp.route('/change_layout_request_and_document_state_on_success/<string:request_id>', methods=['POST'])
@login_required
def change_layout_request_and_document_state_on_success(request_id):
    layout_analysis_request = get_request_by_id(request_id)
    change_layout_request_and_document_state_on_success_handler(layout_analysis_request)
    return 'OK'


@bp.route('/change_layout_request_to_fail_and_document_state_to_new/<string:request_id>', methods=['POST'])
@login_required
def change_layout_request_to_fail_and_document_state_to_new(request_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights!', 'danger')
        return redirect(url_for('main.index'))
    layout_request = get_request_by_id(request_id)
    change_layout_request_to_fail_and_document_state_to_new_handler(layout_request)
    if 'EMAIL_NOTIFICATION_ADDRESSES' in current_app.config and current_app.config['EMAIL_NOTIFICATION_ADDRESSES']:
        send_layout_failed_mail(layout_request, request)
    return 'OK'


# GET RESULT
########################################################################################################################

@bp.route('/get_image_result/<string:image_id>', methods=['GET'])
@login_required
def get_image_result(image_id):
    try:
        db_image = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404

    document_id = db_image.document_id
    if not is_granted_acces_for_document(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))
    textregions = []
    for textregion in db_image.textregions:
        if textregion.deleted:
            continue
        textregion_points = textregion.np_points.tolist()
        textregions.append({'uuid': textregion.id, 'deleted': textregion.deleted, 'points': textregion_points,
                            'order': textregion.order})
    return jsonify({"uuid": image_id, 'width': db_image.width, 'height': db_image.height, 'objects': textregions})


# GET LAYOUT DETECTOR FOR PARSE FOLDER
########################################################################################################################

@bp.route('/get_request')
@login_required
def get_request():
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to edit collaborators!', 'danger')
        return redirect(url_for('main.index'))
    analysis_request = get_first_layout_request()
    if analysis_request:
        change_layout_request_and_document_state_in_progress_handler(analysis_request)
        return create_json_from_request(analysis_request)
    else:
        return jsonify({})


@bp.route('/get_layout_detector/<string:layout_detector_id>')
@login_required
def get_layout_detector(layout_detector_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to edit collaborators!', 'danger')
        return redirect(url_for('main.index'))
    layout_detector = get_layout_detector_by_id(layout_detector_id)
    layout_detector_folder = os.path.join(current_app.config['LAYOUT_DETECTORS_FOLDER'], get_layout_detector_folder_name(layout_detector.name))
    if not os.path.exists("{}.zip".format(layout_detector_folder)):
        shutil.make_archive(layout_detector_folder, 'zip', layout_detector_folder)
    return send_file("{}.zip".format(layout_detector_folder), attachment_filename='layout_detector.zip', as_attachment=True)


def get_layout_detector_folder_name(layout_detector_name):
    return layout_detector_name.replace(" ", "_").lower()

