import uuid
from app.db.model import RequestState, RequestType, Request, DocumentState, TextRegion
from app.db import db_session
from flask import jsonify, current_app
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageColor
import os


def create_ocr_analysis_request(document):
    return Request(id=str(uuid.uuid4()), document=document, document_id=document.id,
                   request_type=RequestType.OCR, state=RequestState.PENDING)

def can_start_ocr(document):
    if not Request.query.filter_by(document_id=document.id, request_type=RequestType.OCR,
                                   state=RequestState.PENDING).first() and document.state == DocumentState.COMPLETED_LAYOUT_ANALYSIS:
        return True
    return False

def add_ocr_request_and_change_document_state(request):
    request.document.state = DocumentState.WAITING_OCR
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)

def get_first_ocr_request():
    return Request.query.filter_by(state=RequestState.PENDING, request_type=RequestType.OCR) \
        .order_by(Request.created_date).first()

def create_json_from_request(request):
    val = {'id': request.id, 'document': {'id': request.document.id, 'images': []}}
    for image in request.document.images:
        if not image.deleted:
            val['document']['images'].append(image.id)
    return jsonify(val)
