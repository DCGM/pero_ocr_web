import os
import numpy as np
import shutil

from app.db.model import RequestState, RequestType, Request, DocumentState, TextLine, Annotation, TextRegion, Document
from app.db.user import User
from app.db.general import get_text_region_by_id, get_text_line_by_id
from app import db_session
from flask import jsonify
import uuid

from pero_ocr.document_ocr.layout import PageLayout
from pero_ocr.force_alignment import force_align
from pero_ocr.confidence_estimation import get_letter_confidence
from pero_ocr.confidence_estimation import get_letter_confidence, get_line_confidence


def insert_lines_to_db(ocr_results_folder, file_names):

    base_file_names = [os.path.splitext(file_name)[0] for file_name in file_names]
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
            db_line_map = dict([(str(line.id), line) for line in db_region.textlines])
            if db_region is not None:
                for order, line in enumerate(region.lines):
                    if line.id in db_line_map:
                        db_line = db_line_map[line.id]
                        if len(db_line.annotations) == 0:
                            db_line.text = line.transcription
                            db_line.np_confidences = get_confidences(line)
                    else:
                        line_id = uuid.uuid4()
                        line.id = str(line_id)
                        text_line = TextLine(id=line_id,
                                             order=order,
                                             np_points=line.polygon,
                                             np_baseline=line.baseline,
                                             np_heights=line.heights,
                                             np_confidences=get_confidences(line),
                                             text=line.transcription,
                                             deleted=False)
                        db_region.textlines.append(text_line)
        db_session.commit()
        page_layout.to_pagexml(xml_path)
        page_layout.save_logits(logits_path)


def get_confidences(line):
    if line.transcription is not None and line.transcription != "":
        char_map = dict([(c, i) for i, c in enumerate(line.characters)])
        c_idx = np.asarray([char_map[c] for c in line.transcription])
        try:
            confidences = get_line_confidence(line, c_idx)
        except ValueError:
            print('ERROR: Known error in get_line_confidence() - Please, fix it. Logit slice has zero length.')
            confidences = np.ones(len(line.transcription)) * 0.5
        return confidences
    return np.asarray([])


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


def set_delete_flag(text_line, delete_flag):
    text_line.deleted = delete_flag
    db_session.commit()


def set_training_flag(text_line, training_flag):
    text_line.for_training = training_flag
    db_session.commit()


def check_document_processed(document):
    for image in document.images:
        for textregion in image.textregions:
            if (len(list(textregion.textlines))):
                return True
    return False


def create_json_from_request(request):
    val = {'id': request.id, 'baseline_id': request.baseline_id, 'ocr_id': request.ocr_id,
           'language_model_id': request.language_model_id, 'document': {'id': request.document.id, 'images': []}}
    for image in request.document.images:
        if not image.deleted:
            val['document']['images'].append(image.id)
    return jsonify(val)


def post_files_to_folder(request, folder):
    files = request.files
    file_names = []
    for file_id in files:
        file = files[file_id]
        path = os.path.join(folder, file.filename)
        file.save(path)
        file_names.append(file.filename)
    return file_names


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


def change_ocr_request_to_fail_and_document_state_to_completed_layout_analysis(request):
    change_ocr_request_and_document_state(request, RequestState.FAILURE, DocumentState.COMPLETED_LAYOUT_ANALYSIS)
    return


def change_ocr_request_to_fail_and_document_state_to_success(request):
    change_ocr_request_and_document_state(request, RequestState.FAILURE, DocumentState.COMPLETED_OCR)
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
    requests = Request.query.filter_by(state=RequestState.PENDING, request_type=RequestType.OCR) \
        .order_by(Request.created_date)
    if False:
        requests = requests.join(Document).join(User).filter(User.trusted > 0)
    return requests.first()
