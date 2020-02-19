from app.layout_analysis import bp
from flask import render_template, url_for, redirect, flash, jsonify, request, current_app, send_file, abort
from flask_login import login_required, current_user
from app.db.general import get_document_by_id, get_request_by_id, get_image_by_id, get_layout_detector_by_id
from app.layout_analysis.general import create_layout_analysis_request, can_start_layout_analysis, \
    add_layout_request_and_change_document_state, get_first_layout_request, change_layout_request_and_document_state_in_progress, \
    create_json_from_request, change_layout_request_and_document_state_on_success, get_region_coords_from_xml,\
    make_image_result_preview, change_document_state_on_complete_layout_analysis
import os
import sys
import sqlalchemy
from app.db.model import DocumentState, TextRegion, LayoutDetector
from app.document.general import get_document_images, is_user_owner_or_collaborator
from PIL import Image
from app import db_session
from flask import jsonify
import shutil
import numpy as np


@bp.route('/select_layout/<string:document_id>', methods=['GET'])
@login_required
def select_layout(document_id):
    document = get_document_by_id(document_id)
    layout_engines = db_session.query(LayoutDetector).filter(LayoutDetector.active).all()
    return render_template('layout_analysis/layout_select.html', document=document, layout_engines=layout_engines)


@bp.route('/start/<string:document_id>', methods=['POST'])
def start(document_id):
    document = get_document_by_id(document_id)
    layout_detector_id = request.form['layout_detector_id']
    layout_detector = get_layout_detector_by_id(layout_detector_id)
    if layout_detector.name != "NONE":
        if len(document.images.all()) == 0:
            flash(u'Can\'t create request without uploading images.', 'danger')
            return redirect(request.referrer)
        layout_request = create_layout_analysis_request(document, layout_detector_id)
        if can_start_layout_analysis(document):
            add_layout_request_and_change_document_state(layout_request)
            flash(u'Request for layout analysis successfully created!', 'success')
        else:
            flash(u'Request for layout analysis is already pending or document is in unsupported state!', 'danger')
    else:
        if not os.path.exists(os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], str(document_id))):
            os.makedirs(os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], str(document_id)))
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
            regions_coords = get_region_coords_from_xml(xml_path)
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
    return render_template('layout_analysis/layout_results.html', document=document, images=list(document.images))


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
    image_path = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], document_id, image_id + '.jpg')
    if not os.path.isfile(image_path):
        image_db = get_image_by_id(image_id)
        make_image_result_preview(image_db)

    return send_file(image_path, cache_timeout=0)



@bp.route('/edit_layout/<string:image_id>', methods=['POST'])
@login_required
def edit_layout(image_id):
    regions = request.get_json()
    image = get_image_by_id(image_id)
    existing_regions = dict([(str(region.id), region) for region in image.textregions])

    preview_coords = []
    for region in regions:
        if not region or 'points' not in region or len(region['points']) <= 2:
            continue

        points = region['points']
        np_points = np.array(points)
        points = ['{},{}'.format(int(point[1]), int(point[0])) for point in points]
        points = ' '.join(points)

        if region['uuid'] not in existing_regions:
            db_region = TextRegion(id=region['uuid'], deleted=region['deleted'], points=points, image_id=image_id)
            image.textregions.append(db_region)
        else:
            db_region = existing_regions[region['uuid']]
            db_region.points = points
            db_region.deleted = region['deleted']

        if not region['deleted']:
            preview_coords.append(np_points)

    try:
        db_session.commit()
        make_image_result_preview(image)
    except sqlalchemy.exc.IntegrityError as err:
        print('ERROR: Unable to save text regions.', err, file=sys.stderr)
        db_session.rollback()
        return 'Failed to save.', 420

    return 'OK'


@bp.route('/get_models/<string:layout_detector_name>')
def get_models(layout_detector_name):
    models_folder = os.path.join(current_app.config['LAYOUT_DETECTORS_FOLDER'], layout_detector_name)
    zip_path = os.path.join(current_app.config['LAYOUT_DETECTORS_FOLDER'], layout_detector_name)
    if not os.path.exists("{}.zip".format(zip_path)):
        print("Creating archive:", zip_path)
        shutil.make_archive(zip_path, 'zip', models_folder)
    return send_file("{}.zip".format(zip_path), attachment_filename='models.zip', as_attachment=True)
