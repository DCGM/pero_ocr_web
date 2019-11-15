from app.db.model import RequestState, RequestType, Request, DocumentState, TextLine, Annotation, TextRegion
from app.db.general import get_text_region_by_id, get_text_line_by_id
from app import db_session
from flask import jsonify
import xml.etree.ElementTree as ET
import os


def get_page_annotated_lines(image_id):
    lines = db_session.query(TextLine.id).join(TextRegion).join(Annotation).filter(TextRegion.image_id == image_id)\
        .distinct().all()
    return [x[0] for x in lines]


def create_ocr_request(document, ocr_id):
    return Request(document=document,
                   request_type=RequestType.OCR, state=RequestState.PENDING, ocr_id=ocr_id)


def can_start_ocr(document):
    if not Request.query.filter_by(document_id=document.id, request_type=RequestType.OCR,
                                   state=RequestState.PENDING).first() and (document.state == DocumentState.COMPLETED_LAYOUT_ANALYSIS or document.state == DocumentState.COMPLETED_OCR):
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
    processed = False
    for image in request.document.images:
        if not image.deleted:
            for textregion in image.textregions:
                if not textregion.deleted:
                    if len(textregion.textlines) > 0:
                        processed = True
    val = {'id': request.id, 'ocr_name': request.ocr.name,
           'document': {'id': request.document.id, 'processed': processed, 'images': []}}
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
            text_region = get_text_region_by_id(region_id)
            if len(text_region.lines) == 0:
                for order, line in enumerate(
                        region.iter('{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextLine')):
                    coords = line[0].get('points')
                    baseline = line[1].get('points')
                    heights_split = line.get('custom').split()
                    heights = "{} {}".format(heights_split[1][1:-1], heights_split[2][:-1])
                    line_text = line[2][0].text
                    confidences = line[3].text
                    text_line = TextLine(
                        order=order,
                        points=coords,
                        baseline=baseline,
                        heights=heights,
                        confidences=confidences,
                        text=line_text,
                        deleted=False)
                    text_region.textlines.append(text_line)
            else:
                region_lines = dict([(str(x.id), x) for x in text_region.lines])

                for order, line in enumerate(
                        region.iter('{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextLine')):
                    line_id = line.get('id')
                    if line_id not in region_lines:
                        print('ERROR: Skipping input xml line. Line id not in DB - ', line_id)
                        continue

                    text_line = region_lines[line_id]
                    if len(text_line.annotations) == 0:
                        text_line.text = line[2][0].text
                        text_line.confidences = line[3].text
        db_session.commit()


def insert_annotations_to_db(user, annotations):
    for annotation in annotations:
        text_line = get_text_line_by_id(annotation['id'])
        text_edited = annotation['text_edited']
        if u"\u00A0" in text_edited:
            text_edited = text_edited.replace(u"\u00A0", ' ')
        annotation_db = Annotation(text_original=annotation['text_original'], text_edited=text_edited, deleted=False, user_id=user.id)
        text_line.annotations.append(annotation_db)
    db_session.commit()


def update_text_lines(annotations):
    for annotation in annotations:
        text_line = get_text_line_by_id(annotation['id'])
        text_edited = annotation['text_edited']
        if u"\u00A0" in text_edited:
            text_edited = text_edited.replace(u"\u00A0", ' ')
        text_line.text = text_edited
        text_line.confidences = ' '.join([str(1) for _ in annotation['text_edited']])
    db_session.commit()


def change_ocr_request_and_document_state(request, request_state, document_state):
    request.state = request_state
    request.document.state = document_state
    db_session.commit()


def change_ocr_request_and_document_state_on_success(request):
    change_ocr_request_and_document_state(request, RequestState.SUCCESS, DocumentState.COMPLETED_OCR)
    return
