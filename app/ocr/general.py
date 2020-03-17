import os
import numpy as np

from app.db.model import RequestState, RequestType, Request, DocumentState, TextLine, Annotation, TextRegion
from app.db.general import get_text_region_by_id, get_text_line_by_id
from app import db_session
from flask import jsonify

from pero_ocr.document_ocr import PageLayout
from pero_ocr.force_alignment import force_align
from pero_ocr.confidence_estimation import get_letter_confidence


def insert_lines_to_db(ocr_results_folder):

    base_file_names = [os.path.splitext(file_name)[0] for file_name in os.listdir(ocr_results_folder)]
    base_file_names = list(set(base_file_names))

    for base_file_name in base_file_names:
        print(base_file_name)
        xml_path = os.path.join(ocr_results_folder, "{}.{}".format(base_file_name, "xml"))
        logits_path = os.path.join(ocr_results_folder, "{}.{}".format(base_file_name, "logits"))
        page_layout = PageLayout()
        page_layout.from_pagexml(xml_path)
        page_layout.load_logits(logits_path)
        for region in page_layout.regions:
            db_region = get_text_region_by_id(region.id)
            for order, line in enumerate(region.lines):
                db_line = get_text_line_by_id(line.id)
                if db_line is not None:
                    if len(db_line.annotations) == 0:
                        db_line.text = line.transcription
                        db_line.confidences = get_confidences(line)
                    continue
                text_line = TextLine(order=order,
                                     np_points=line.polygon,
                                     np_baseline=line.baseline,
                                     np_heights=line.heights,
                                     np_confidences=get_confidences(line),
                                     text=line.transcription,
                                     deleted=False)
                db_region.textlines.append(text_line)
        db_session.commit()


def get_confidences(line):
    if line.transcription is not None and line.transcription != "":
        c_idx = []
        for c in line.transcription:
            c_idx.append(line.characters.index(c))

        line_logits = np.array(line.logits.todense())
        line_logits[line_logits == 0] = -80

        blank_char_index = line_logits.shape[1] - 1

        al_res = force_align(-line_logits, c_idx, blank_char_index)
        con_res = get_letter_confidence(line_logits, al_res, blank_char_index)
        return np.exp(con_res)
    return np.asarray([])


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


def create_json_from_request(request):
    processed = False
    for image in request.document.images:
        if not image.deleted:
            for textregion in image.textregions:
                if not textregion.deleted:
                    if len(textregion.textlines) > 0:
                        processed = True
    val = {'id': request.id, 'baseline_id': request.baseline.id, 'ocr_id': request.ocr.id,
           'language_model_id': request.language_model.id, 'document': {'id': request.document.id,
                                                                        'processed': processed, 'images': []}}
    for image in request.document.images:
        if not image.deleted:
            val['document']['images'].append(image.id)
    return jsonify(val)


def change_ocr_request_and_document_state(request, request_state, document_state):
    request.state = request_state
    request.document.state = document_state
    db_session.commit()


def change_ocr_request_and_document_state_on_success(request):
    change_ocr_request_and_document_state(request, RequestState.SUCCESS, DocumentState.COMPLETED_OCR)
    return


def change_ocr_request_and_document_state_in_progress(request):
    change_ocr_request_and_document_state(request, RequestState.IN_PROGRESS, DocumentState.RUNNING_OCR)
    return


def get_page_annotated_lines(image_id):
    lines = db_session.query(TextLine.id).join(TextRegion).join(Annotation).filter(TextRegion.image_id == image_id)\
        .distinct().all()
    return [x[0] for x in lines]


def create_ocr_request(document, baseline_id, ocr_id, language_model_id):
    return Request(document=document,
                   request_type=RequestType.OCR, state=RequestState.PENDING, baseline_id=baseline_id, ocr_id=ocr_id,
                   language_model_id=language_model_id)


def can_start_ocr(document):
    if not Request.query.filter_by(document_id=document.id, request_type=RequestType.OCR,
                                   state=RequestState.PENDING).first() and (document.state == DocumentState.COMPLETED_LAYOUT_ANALYSIS or document.state == DocumentState.COMPLETED_OCR):
        return True
    return False


def add_ocr_request_and_change_document_state(request):
    request.document.state = DocumentState.WAITING_OCR
    db_session.add(request)
    db_session.commit()


def get_first_ocr_request():
    return Request.query.filter_by(state=RequestState.PENDING, request_type=RequestType.OCR) \
        .order_by(Request.created_date).first()

