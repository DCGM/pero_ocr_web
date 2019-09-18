from app.db.model import RequestState, RequestType, Request, DocumentState
from app.db import db_session
from flask import jsonify, current_app
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
import os
from app.db.general import get_image_by_id


def create_layout_analysis_request(document):
    return Request(document=document,
                   request_type=RequestType.LAYOUT_ANALYSIS, state=RequestState.PENDING)


def can_start_layout_analysis(document):
    if not Request.query.filter_by(document_id=document.id, request_type=RequestType.LAYOUT_ANALYSIS,
                                   state=RequestState.PENDING).first() and document.state == DocumentState.NEW:
        return True
    return False


def add_layout_request_and_change_document_state(request):
    request.document.state = DocumentState.WAITING_LAYOUT_ANALYSIS
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)


def get_first_layout_request():
    return Request.query.filter_by(state=RequestState.PENDING, request_type=RequestType.LAYOUT_ANALYSIS) \
        .order_by(Request.created_date).first()


def change_layout_request_and_document_state(request, request_state, document_state):
    request.state = request_state
    request.document.state = document_state
    db_session.commit()


def change_layout_request_and_document_state_in_progress(request):
    change_layout_request_and_document_state(request, RequestState.IN_PROGRESS, DocumentState.RUNNING_LAYOUT_ANALYSIS)
    return


def change_layout_request_and_document_state_on_success(request):
    change_layout_request_and_document_state(request, RequestState.SUCCESS, DocumentState.COMPLETED_LAYOUT_ANALYSIS)
    return


def change_document_state_on_complete_layout_analysis(document):
    document.state = DocumentState.COMPLETED_LAYOUT_ANALYSIS
    db_session.commit()


def create_json_from_request(request):
    value = {'id': request.id, 'document': {'id': request.document.id, 'images': []}}
    for image in request.document.images:
        if not image.deleted:
            value['document']['images'].append(image.id)
    return jsonify(value)


def make_image_result_preview(regions, image_path, image_id):
    image_db = get_image_by_id(image_id)
    if image_db:
        image = Image.open(image_path)
        image = image.convert('RGB')
        for region in regions:
            ImageDraw.Draw(image).line(region, width=35, fill=(0, 255, 0))
        new_path = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], str(image_db.document_id), str(image_id) + '.jpg')
        scale = (100000.0 / (image.width * image.height))**0.5
        image = image.resize((int(image.width * scale + 0.5), int(image.height * scale + 0.5)), resample=Image.LANCZOS)
        print(image.width, image.height, scale)
        image.save(new_path)


def get_coords_and_make_preview(image_path, xml_path, image_id):
    root = ET.parse(xml_path).getroot()
    region_coords = []
    preview_coords = []
    for region in root.iter('{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextRegion'):
        for coords in region.iter('{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Coords'):
            coords_string = coords.get('points')
            coords_string_splited = coords_string.split(' ')
            region_points = []
            for point_string in coords_string_splited:
                point = point_string.split(',')
                region_points.append((int(point[1]), int(point[0])))
            region_points.append(region_points[0])
            preview_coords.append(region_points)
            region_coords.append(coords_string)
    make_image_result_preview(preview_coords, image_path, image_id)
    return region_coords
