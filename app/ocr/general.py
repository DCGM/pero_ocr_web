import uuid
from app.db.model import RequestState, RequestType, Request, DocumentState, TextLine, Annotation, OCR
from app.db.general import get_text_region_by_id, get_text_line_by_id
from app import db_session
from flask import jsonify
import xml.etree.ElementTree as ET
import os


def create_ocr_request(document, ocr_id):
    return Request(document=document,
                   request_type=RequestType.OCR, state=RequestState.PENDING, ocr_id=ocr_id)

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
    val = {'id': request.id, 'parse_folder_config_path': request.ocr.parse_folder_config_path,
           'ocr_json_path': request.ocr.ocr_json_path,
           'document': {'id': request.document.id, 'images': []}}
    for image in request.document.images:
        if not image.deleted:
            val['document']['images'].append(image.id)
    return jsonify(val)

def insert_lines_to_db(ocr_results_folder):
    for xml_file_name in os.listdir(ocr_results_folder):
        xml_path = os.path.join(ocr_results_folder, xml_file_name)
        root = ET.parse(xml_path).getroot()
        for region in root.iter('{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextRegion'):
            region_id = region.get('id')
            textregion = get_text_region_by_id(region_id)
            print(region_id)
            for order, line in enumerate(region.iter('{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextLine')):
                coords = line[0].get('points')
                baseline = line[1].get('points')
                heights_split = line.get('custom').split()
                heights = "{} {}".format(heights_split[1][1:-1], heights_split[2][:-1])
                line_text = line[2][0].text
                confidences = line[3].text
                print("Coords:", coords)
                print("Baseline:", baseline)
                print("Heights:", heights)
                print("Confidences:", confidences)
                print(line_text)
                text_line = TextLine(order=order, points=coords, baseline=baseline,
                                     heights=heights, confidences=confidences, text=line_text, deleted=False)
                textregion.textlines.append(text_line)
        db_session.commit()

def insert_annotations_to_db(user, annotations):
    for annotation in annotations:
        text_line = get_text_line_by_id(annotation['id'])
        annotation_db = Annotation(text_original=annotation['text_original'], text_edited=annotation['text_edited'], deleted=False, user_id=user.id)
        text_line.annotations.append(annotation_db)
    db_session.commit()

def update_text_lines(annotations):
    for annotation in annotations:
        text_line = get_text_line_by_id(annotation['id'])
        text_line.text = annotation['text_edited']
        text_line.confidences = ' '.join([str(1) for _ in annotation['text_edited']])
    db_session.commit()

def change_ocr_request_and_document_state(request, request_state, document_state):
    request.state = request_state
    request.document.state = document_state
    db_session.commit()

def change_ocr_request_and_document_state_on_success(request):
    change_ocr_request_and_document_state(request, RequestState.SUCCESS, DocumentState.COMPLETED_OCR)
    return