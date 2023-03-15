from app.db.model import RequestState, RequestType, Request, DocumentState, TextRegion, Document
from app.db.user import User
from app import db_session
from flask import jsonify
import numpy as np
import os
import datetime
from app.db.general import get_image_by_id
from pero_ocr.core.layout import PageLayout


def set_whole_page_region_layout_to_document(document):
    for image in document.images:
        coords = np.asarray([[0, 0], [0, image.height], [image.width, image.height], [image.width, 0]])
        text_region = TextRegion(order=0, image_id=image.id, np_points=coords)
        image.textregions.append(text_region)
    db_session.commit()


def insert_regions_to_db(results_folder, file_names):
    for file_name in file_names:
        print(file_name)
        image_id = os.path.splitext(file_name)[0]
        image = get_image_by_id(image_id)
        xml_path = os.path.join(results_folder, file_name)
        page_layout = PageLayout()
        page_layout.from_pagexml(xml_path)
        for order, region in enumerate(page_layout.regions):
            text_region = TextRegion(order=order, image_id=image_id, np_points=region.polygon)
            image.textregions.append(text_region)
    db_session.commit()


def post_files_to_folder(request, folder):
    files = request.files
    file_names = []
    for file_id in files:
        file = files[file_id]
        path = os.path.join(folder, file.filename)
        file.save(path)
        file_names.append(file.filename)
    return file_names


def create_json_from_request(request):
    value = {'id': request.id, 'layout_detector_id': request.layout_detector.id, 'document': {'id': request.document.id, 'images': []}}
    for image in request.document.images:
        if not image.deleted:
            value['document']['images'].append(image.id)
    return jsonify(value)


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
    requests = Request.query.filter_by(state=RequestState.PENDING, request_type=RequestType.LAYOUT_ANALYSIS) \
        .order_by(Request.created_date)
    if False:
        requests = requests.join(Document).join(User).filter(User.trusted > 0)

    return requests.first()


def change_layout_request_and_document_state(request, request_state, document_state):
    request.state = request_state
    request.document.state = document_state
    db_session.commit()


def change_layout_request_and_document_state_in_progress_handler(request):
    request.state = RequestState.IN_PROGRESS
    request.document.state = DocumentState.RUNNING_LAYOUT_ANALYSIS
    request.last_processed_page = datetime.datetime.utcnow()
    db_session.commit()
    return


def change_layout_request_and_document_state_on_success_handler(request):
    change_layout_request_and_document_state(request, RequestState.SUCCESS, DocumentState.COMPLETED_LAYOUT_ANALYSIS)
    return


def change_layout_request_to_fail_and_document_state_to_new_handler(request):
    change_layout_request_and_document_state(request, RequestState.FAILURE, DocumentState.NEW)


def change_document_state_on_complete_layout_analysis_handler(document):
    document.state = DocumentState.COMPLETED_LAYOUT_ANALYSIS
    db_session.commit()


def not_deleted_images_in_document(document):
    for image in document.images:
        if not image.deleted:
            return True
    return False
