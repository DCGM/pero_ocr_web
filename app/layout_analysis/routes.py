from app.layout_analysis import bp
from flask import render_template, url_for, redirect, flash, jsonify, request, current_app, send_file, abort
from flask_login import login_required, current_user
from app.db.general import get_document_by_id, get_request_by_id, get_image_by_id
from app.layout_analysis.general import create_layout_analysis_request, can_start_layout_analysis, \
    add_layout_request_and_change_document_state, get_first_layout_request, change_layout_request_and_document_state_in_progress, \
    create_json_from_request, change_layout_request_and_document_state_on_success, make_image_result_preview
import os
from app.db.model import DocumentState, TextRegion
import xml.etree.ElementTree as ET
from app.document.general import get_document_images, is_user_owner_or_collaborator
from PIL import Image
from app.db import db_session


@bp.route('/start/<string:document_id>')
@login_required
def start_layout_analysis(document_id):
    document = get_document_by_id(document_id)
    if len(document.images.all()) == 0:
        flash(u'Can\'t create request without uploading images.', 'danger')
        return redirect(request.referrer)
    layout_request = create_layout_analysis_request(document)
    if can_start_layout_analysis(document):
        add_layout_request_and_change_document_state(layout_request)
        flash(u'Request for layout analysis successfully created!', 'success')
    else:
        flash(u'Request for layout analysis is already pending or document is in unsupported state!', 'danger')
    return redirect(url_for('document.documents'))

@bp.route('/get_request')
def get_request():
    analysis_request = get_first_layout_request()
    if analysis_request:
        change_layout_request_and_document_state_in_progress(analysis_request)
        return create_json_from_request(analysis_request)
    else:
        return jsonify({})

@bp.route('/post_result/<string:request_id>', methods=['POST'])
def post_result(request_id):
    analysis_request = get_request_by_id(request_id)
    document = get_document_by_id(analysis_request.document_id)
    folder_path = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], str(document.id))

    if not analysis_request:
        return

    path = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], str(analysis_request.document_id))
    if not os.path.exists(path):
        os.makedirs(path)

    files = request.files
    for file_id in files:
        file = files[file_id]
        xml_path = os.path.join(path, file.filename)
        file.save(xml_path)

    for image in document.images.all():
        if not image.deleted:
            image_id = str(image.id)
            xml_path = os.path.join(folder_path, image_id + '.xml')
            regions_coords = make_image_result_preview(image.path, xml_path, image.id)
            for region_coords in regions_coords:
                text_region = TextRegion(image_id=image_id, points=region_coords)
                image.textregions.append(text_region)
                db_session.commit()

    change_layout_request_and_document_state_on_success(analysis_request)
    return 'OK'


@bp.route('/results/<string:document_id>', methods=['GET'])
@login_required
def show_results(document_id):
    document = get_document_by_id(document_id)
    if document.state != DocumentState.COMPLETED_LAYOUT_ANALYSIS:
        return  # Bad Request or something like that
    folder_path = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], str(document_id))
    xml_files = dict()
    images = get_document_images(document)
    for image in document.images.all():
        if not image.deleted:
            image_id = str(image.id)
            xml_path = os.path.join(folder_path, image_id + '.xml')
            et = ET.parse(xml_path)
            xml_string = ET.tostring(et.getroot(), encoding='utf8', method='xml')
            xml_files[image_id] = xml_string

    return render_template('layout_analysis/layout_results.html', document=document, images=images, xml_files=xml_files)


@bp.route('/get_xml/<string:document_id>/<string:image_id>')
@login_required
def download_result_xml(document_id, image_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        return abort(403)

    xml_path = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], document_id, image_id + '.xml')
    return send_file(xml_path)


@bp.route('/get_image_result/<string:document_id>/<string:image_id>', methods=['POST'])
@login_required
def get_image_result(document_id, image_id):
    image = get_image_by_id(image_id)
    # TODO Test prav uzivatele
    xml_path = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], document_id, image_id + '.xml')

    img = Image.open(image.path)
    width, height = img.size
    textregions = []
    for textregion in image.textregions:
        textregion_points_string = textregion.points.split(' ')
        textregion_points = []
        for textregion_point_string in textregion_points_string:
            point = textregion_point_string.split(',')
            textregion_points.append([int(point[1]), int(point[0])])
        textregions.append(textregion_points)

    return {'width': width, 'height': height, 'textregions': textregions}

@bp.route('/get_result_preview/<string:document_id>/<string:image_id>')
@login_required
def get_result_preview(document_id, image_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to get this image!', 'danger')
        return redirect(url_for('main.index'))
    image_url = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], document_id, image_id + '.jpg')
    return send_file(image_url)
