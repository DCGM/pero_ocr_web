import uuid
from app.db.model import RequestState, RequestType, Request, DocumentState
from app.db import db_session
from flask import jsonify


def create_layout_analysis_request(document):
    return Request(id=str(uuid.uuid4()), document=document, document_id=document.id,
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


def change_layout_request_and_document_state(request):
    # request.state = RequestState.IN_PROGRESS
    request.document.state = DocumentState.RUNNING_LAYOUT_ANALYSIS
    db_session.commit()


def create_json_from_request(request):
    val = {'id': request.id, 'document': {'id': request.document.id, 'images': []}}
    for image in request.document.images:
        if not image.deleted:
            val['document']['images'].append(image.id)
    return jsonify(val)
