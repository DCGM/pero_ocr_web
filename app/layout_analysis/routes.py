from app.layout_analysis import bp
from flask import render_template, url_for, redirect, flash, jsonify, request, current_app, send_file, abort
from flask_login import login_required, current_user
from app.db.general import get_document_by_id, get_request_by_id, get_image_by_id, get_text_region_by_id
from app.layout_analysis.general import create_layout_analysis_request, can_start_layout_analysis, \
    add_layout_request_and_change_document_state, get_first_layout_request, change_layout_request_and_document_state_in_progress, \
    create_json_from_request, change_layout_request_and_document_state_on_success, get_coords_and_make_preview, \
    make_image_result_preview, change_document_state_on_complete_layout_analysis
import os
from app.db.model import DocumentState, TextRegion
from app.document.general import get_document_images, is_user_owner_or_collaborator
from PIL import Image
from app.db import db_session
from flask import jsonify


@bp.route('/start/<string:document_id>', methods=['GET'])
@login_required
def start_layout_analysis_get(document_id):
    document = get_document_by_id(document_id)
    return render_template('layout_analysis/start_layout.html', document=document)


@bp.route('/start/<string:document_id>', methods=['POST'])
def start_layout_analysis_post(document_id):
    document = get_document_by_id(document_id)
    type = request.form['layout_analysis_type']
    if type == 'BASIC':
        if len(document.images.all()) == 0:
            flash(u'Can\'t create request without uploading images.', 'danger')
            return redirect(request.referrer)
        layout_request = create_layout_analysis_request(document)
        if can_start_layout_analysis(document):
            add_layout_request_and_change_document_state(layout_request)
            flash(u'Request for layout analysis successfully created!', 'success')
        else:
            flash(u'Request for layout analysis is already pending or document is in unsupported state!', 'danger')
    else:
        if not os.path.exists(os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], str(document_id))):
            os.makedirs(os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], str(document_id)))
        for image in document.images:
            make_image_result_preview([], image.path, image.id)
        change_document_state_on_complete_layout_analysis(document)
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
            regions_coords = get_coords_and_make_preview(image.path, xml_path, image.id)
            for order, region_coords in enumerate(regions_coords):
                text_region = TextRegion(order=order, image_id=image_id, points=region_coords)
                image.textregions.append(text_region)
                db_session.commit()

    change_layout_request_and_document_state_on_success(analysis_request)
    return 'OK'


@bp.route('/show_results/<string:document_id>', methods=['GET'])
@login_required
def show_results(document_id):
    document = get_document_by_id(document_id)
    if document.state != DocumentState.COMPLETED_LAYOUT_ANALYSIS:
        return  # Bad Request or something like that
    images = get_document_images(document)
    return render_template('layout_analysis/layout_results.html', document=document, images=images.all())


@bp.route('/get_xml/<string:document_id>/<string:image_id>')
@login_required
def download_result_xml(document_id, image_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        return abort(403)

    xml_path = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], document_id, image_id + '.xml')
    return send_file(xml_path)


@bp.route('/get_image_result/<string:document_id>/<string:image_id>', methods=['GET'])
@login_required
def get_image_result(document_id, image_id):
    image = get_image_by_id(image_id)
    # TODO Test prav uzivatele
    xml_path = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], document_id, image_id + '.xml')

    img = Image.open(image.path)
    width, height = img.size
    textregions = []
    for textregion in image.textregions:
        if textregion.deleted:
            continue
        textregion_points_string = textregion.points.split(' ')
        textregion_points = []
        for textregion_point_string in textregion_points_string:
            point = textregion_point_string.split(',')
            textregion_points.append([int(point[1]), int(point[0])])
        textregions.append({'uuid': textregion.id, 'deleted': textregion.deleted, 'points': textregion_points})
    return jsonify({"uuid": image_id, 'width': width, 'height': height, 'objects': textregions})


@bp.route('/get_result_preview/<string:document_id>/<string:image_id>')
@login_required
def get_result_preview(document_id, image_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to get this image!', 'danger')
        return redirect(url_for('main.index'))
    image_url = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], document_id, image_id + '.jpg')
    return send_file(image_url, cache_timeout=0)


@bp.route('/edit_layout/<string:image_id>', methods=['POST'])
@login_required
def edit_layout(image_id):
    regions = request.get_json()
    image = get_image_by_id(image_id)
    preview_coords = []
    for region in regions:
        if not region:
            continue
        region_db = get_text_region_by_id(region['uuid'])
        points = ''
        curr_points = []
        if 'points' not in region:
            continue
        if len(region['points']) <= 2:
            continue
        for point in region['points']:
            points += '{},{} '.format(int(point[1]), int(point[0]))
            curr_points.append((int(point[0]), int(point[1])))
        points = points.strip()
        if region_db:
            region_db.points = points
            region_db.deleted = region['deleted']
        else:
            image.textregions.append(TextRegion(id=region['uuid'], deleted=region['deleted'], points=points, image_id=image_id))

        if not region['deleted']:
            curr_points.append(curr_points[0])
            preview_coords.append(curr_points)
    make_image_result_preview(preview_coords, get_image_by_id(image_id).path, image_id)
    db_session.commit()

    return 'OK'
