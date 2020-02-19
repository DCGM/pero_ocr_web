from app.db.model import RequestState, RequestType, Request, DocumentState
from app import db_session
from flask import jsonify, current_app
import xml.etree.ElementTree as ET
import numpy as np
import cv2
import os
from app.db.general import get_image_by_id


def create_layout_analysis_request(document, layout_id):
    return Request(document=document, layout_id=layout_id,
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
    value = {'id': request.id, 'layout_detector_name': request.layout_detector.name, 'document': {'id': request.document.id, 'images': []}}
    for image in request.document.images:
        if not image.deleted:
            value['document']['images'].append(image.id)
    return jsonify(value)


def make_image_result_preview(image_db):
    regions = [region.np_points[:, ::-1] for region in image_db.textregions]
    image_path = image_db.path
    image_id = str(image_db.id)
    if image_db:
        image = cv2.imread(image_path, 1)
        scale = (100000.0 / (image.shape[0] * image.shape[1]))**0.5
        image = cv2.resize(image, (0,0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        if regions:
            regions = [(region * scale).astype(np.int32) for region in regions]
            cv2.polylines(image, regions, isClosed=True, thickness=4, color=(0,255,0))
        print(image.shape, scale)

        new_dir = os.path.join(current_app.config['LAYOUT_RESULTS_FOLDER'], str(image_db.document_id))
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        cv2.imwrite(os.path.join(new_dir, str(image_id) + '.jpg'), image)


def get_region_coords_from_xml(xml_path):
    root = ET.parse(xml_path).getroot()
    region_coords = []
    for region in root.iter('{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextRegion'):
        for coords in region.iter('{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Coords'):
            coords_string = coords.get('points')
            coords_string_splited = coords_string.split(' ')
            region_points = []
            for point_string in coords_string_splited:
                point = point_string.split(',')
                region_points.append((int(point[1]), int(point[0])))
            region_points.append(region_points[0])
            region_coords.append(coords_string)
    return region_coords
