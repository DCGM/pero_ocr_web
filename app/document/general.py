import cv2
import copy
import numpy as np
import hashlib
import sqlalchemy
from sqlalchemy import and_
from app.db.model import DocumentState
from app.db.general import get_document_by_id, remove_document_by_id, save_document, save_image_to_document,\
                           get_user_by_id, is_image_duplicate, get_user_documents
import os
from flask import current_app
from flask import Response
from app import db_session
import uuid
from app.db import Document, Image, TextLine, Annotation, UserDocument, User, TextRegion
import datetime
import pero_ocr.document_ocr.layout as layout
import unicodedata
from werkzeug.urls import url_quote
from pero_ocr.layout_engines.layout_helpers import baseline_to_textline
from pero_ocr.document_ocr.arabic_helper import ArabicHelper


def dhash(image, hash_size=8):
    # Grayscale and shrink the image in one step.
    image = image.convert('L').resize(
        (hash_size + 1, hash_size),
    )

    pixels = list(image.getdata())
    # Compare adjacent pixels.
    difference = []
    for row in range(hash_size):
        for col in range(hash_size):
            pixel_left = image.getpixel((col, row))
            pixel_right = image.getpixel((col + 1, row))
            difference.append(pixel_left > pixel_right)
    # Convert the binary array to a hexadecimal string.
    decimal_value = 0
    hex_string = []
    for index, value in enumerate(difference):
        if value:
            decimal_value += 2 ** (index % 8)
        if (index % 8) == 7:
            hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
            decimal_value = 0
    return ''.join(hex_string)


def create_document(name, user):
    document = Document(
        name=name, user=user, state=DocumentState.NEW)
    save_document(document)
    return document


def check_and_remove_document(document_id, user):
    if is_document_owner(document_id, user):
        remove_document_by_id(document_id)
        return True
    return False


def is_document_owner(document_id, user):
    document = get_document_by_id(document_id)
    if document and document.user.id == user.id:
        return True
    else:
        return False


def is_user_owner_or_collaborator(document_id, user):
    if is_user_trusted(user):
        return True
    document = get_document_by_id(document_id)
    if is_document_owner(document_id, user):
        return True
    if user in document.collaborators:
        return True
    return False


def save_image(file, document_id):
    file_data = file.stream.read()

    img_hash = hashlib.md5(file_data).hexdigest()
    db_image = is_image_duplicate(document_id, img_hash)
    if db_image:
        return f'Image is already uploaded as {db_image.filename}.'

    db_image = db_session.query(Image).filter(Image.document_id == document_id).filter(Image.filename == file.filename).first()
    if db_image != None:
        return f'Image with filename {file.filename} is already uploaded.'

    image = cv2.imdecode(np.frombuffer(file_data, np.uint8), 1)
    if image is None:
        return f'Unable to decode the image. It is corrupted or the type is not supported.'

    original_file_name, extension = os.path.splitext(file.filename)

    #if extension.lower() in ['.jpg', '.jpeg', '.jfif', '.pjpeg', '.pjp']:
    #    exif = exifread.process_file(io.BytesIO(file_data))
    #    if 'Image Orientation' in exif and exif['Image Orientation'].values[0] != 1:
    #        _, file_data = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 92])

    if extension.lower() not in ['.jpg', '.jpeg', '.jfif', '.pjpeg', '.pjp', '.png']:
        _, file_data = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        extension = '.jpg'

    document = get_document_by_id(document_id)
    directory_path = get_and_create_document_image_directory(document_id)

    image_db = Image(id=uuid.uuid4(), filename=original_file_name + extension)
    image_id = str(image_db.id)

    image_name = "{}{}".format(image_id, extension)
    file_path = os.path.join(directory_path, image_name)
    with open(file_path, 'wb') as f:
        f.write(file_data)
        image_db.path = image_name
        image_db.width = image.shape[1]
        image_db.height = image.shape[0]
        image_db.imagehash = img_hash
        save_image_to_document(document, image_db)

    return ''


def make_image_preview(image_db):
    if image_db is not None:
        image_path = os.path.join(current_app.config['UPLOADED_IMAGES_FOLDER'], str(image_db.document_id), image_db.path)
        image_id = str(image_db.id)
        image = cv2.imread(image_path, 1)
        if image is None:
            image = np.zeros([image_db.height, image_db.width, 3], dtype=np.uint8)

        # Fix historicaly swapped image width and height
        if image.shape[0] != image_db.height or image.shape[1] != image_db.width:
            image_db.height = image.shape[0]
            image_db.width = image.shape[1]
            db_session.commit()

        scale = (100000.0 / (image.shape[0] * image.shape[1]))**0.5
        image = cv2.resize(image, (0,0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        if image_db.textregions:
            regions = [(region.np_points * scale).astype(np.int32) for region in image_db.textregions if not region.deleted]
            cv2.polylines(image, regions, isClosed=True, thickness=4, color=(0,255,0))

        new_dir = os.path.join(current_app.config['PREVIEW_IMAGES_FOLDER'], str(image_db.document_id))
        if not os.path.exists(new_dir):
            os.makedirs(new_dir, exist_ok=True) # exist_ok=True is needed due to multi-processing
        cv2.imwrite(os.path.join(new_dir, str(image_id) + '.jpg'), image)


def get_and_create_document_image_directory(document_id):
    directory_path = os.path.join(current_app.config['UPLOADED_IMAGES_FOLDER'], str(document_id))
    create_dirs(directory_path)
    return directory_path


def is_allowed_file(file):
    if file.filename != '' and is_allowed_extension(file, current_app.config['EXTENSIONS']):
        return True
    return False


def is_allowed_extension(file, allowed_extensions):
    if str(file.filename).lower().endswith(allowed_extensions):
        return True
    return False


def create_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)  # exist_ok=True is needed due to multi-processing


def remove_image(document_id, image_id):
    document = get_document_by_id(document_id)
    image = document.images.filter_by(id=image_id, deleted=False).first()
    if image:
        image.deleted = True
        db_session.commit()
        return True
    return False


class UserSelectItem:
    def __init__(self, user, is_selected=None):
        self.user = user
        self.is_selected = is_selected


def get_collaborators_select_data(document):
    users = db_session.query(User, UserDocument.document_id)\
            .outerjoin(UserDocument, and_(UserDocument.document_id == document.id, UserDocument.user_id == User.id))\
            .filter(User.id != document.user.id)\
            .filter(User.email != '#revert_OCR_backup#')\
            .all()

    select_items = [UserSelectItem(user=user, is_selected=selected) for user, selected in users]

    return select_items


def save_collaborators(document_id, collaborators_ids):
    document = get_document_by_id(document_id)

    for old_collaborator in list(document.collaborators):
        if str(old_collaborator.id) not in collaborators_ids:
            document.collaborators.remove(old_collaborator)

    for collaborator_id in collaborators_ids:
        user = get_user_by_id(collaborator_id)
        if user not in document.collaborators:
            document.collaborators.append(user)
    db_session.commit()


def is_user_collaborator(document, user):
    if is_user_trusted(user):
        return True
    if user in document.collaborators:
        return True
    return False


def get_document_images(document):
    return document.images.filter_by(deleted=False)


def get_page_layout(image, only_regions=False, only_annotated=False, alto=False, from_time: datetime.datetime=None,
                    active_ignoring=False):
    page_layout = layout.PageLayout()
    page_layout.id = image.filename
    page_layout.page_size = (image.height, image.width)

    text_regions = sort_text_regions(list(image.textregions))

    for text_region in text_regions:
        if not text_region.deleted:
            region_layout = layout.RegionLayout(id=str(text_region.id), polygon=text_region.np_points)
            page_layout.regions.append(region_layout)

            if not only_regions:
                text_lines = TextLine.query.filter_by(region_id=text_region.id).distinct()
                if only_annotated:
                    text_lines = text_lines.join(Annotation)
                    if from_time:
                        text_lines = text_lines.filter(Annotation.created_date > from_time)
                text_lines = text_lines.order_by(TextLine.order)
                text_lines = text_lines.all()

                for text_line in text_lines:
                    if not text_line.deleted:
                        if not active_ignoring or (active_ignoring and text_line.for_training):
                            transcription_confidence = None
                            if text_line.np_confidences != []:
                                transcription_confidence = np.quantile(text_line.np_confidences, .50)
                            region_layout.lines.append(layout.TextLine(id=str(text_line.id),
                                                                       baseline=text_line.np_baseline,
                                                                       polygon=text_line.np_points,
                                                                       heights=text_line.np_heights,
                                                                       transcription=text_line.text,
                                                                       transcription_confidence=transcription_confidence))
    if alto:
        logits_path = os.path.join(current_app.config['OCR_RESULTS_FOLDER'], str(image.document.id), "{}.logits".format(image.id))
        page_layout.load_logits(logits_path)

    return page_layout


def create_string_response(filename, string, minetype):
    r = Response(string, mimetype=minetype)

    try:
        filename = filename.encode('latin-1')
    except UnicodeEncodeError:
        filenames = {
            'filename': unicodedata.normalize('NFKD', filename).encode('latin-1', 'ignore'),
            'filename*': "UTF-8''{}".format(url_quote(filename)),
        }
    else:
        filenames = {'filename': filename}

    r.headers.set('Content-Disposition', 'attachment', **filenames)
    return r


def get_page_layout_text(page_layout):
    text = ""
    for line in page_layout.lines_iterator():
        text += "{}\n".format(line.transcription)
    return text


def sort_text_regions(text_regions):
    skip_text_region_sorting = False
    for tr in text_regions:
        if tr.order is None:
            skip_text_region_sorting = True
    if not skip_text_region_sorting:
        text_regions = sorted(text_regions, key=lambda x: x.order)
    return text_regions


def update_confidences(changes):
    for _, uuid in enumerate(changes.keys()):
        changed_line = changes[uuid]
        transcription = changed_line[0]
        confidences = changed_line[1]
        if len(changed_line) > 2:
            score = changed_line[2]
        else:
            score = None

        line = TextLine.query.filter_by(id=uuid.replace("-", "")).first()

        if confidences is not None:
            conf_string = ' '.join(str(round(x, 3)) for x in confidences)
            line.confidences = conf_string
            #line.confidences = conf_string.replace('1.0', '1') --- this is dangerous

        if score is None:
            line_conf = line.np_confidences
            line.score = 1 - (np.sum((1 - line_conf) ** 2) / (line_conf.shape[0] + 2))
        else:
            line.score = score

        if transcription is not None:
            line.text = transcription

    db_session.commit()


def update_baselines(changes):
    for uuid in changes.keys():
        baseline = changes[uuid][0]
        heights = changes[uuid][1]
        line = TextLine.query.filter_by(id=uuid.replace("-", "")).first()
        line.np_baseline = baseline
        line.np_points = baseline_to_textline(np.array(baseline), np.array(heights))
    db_session.commit()


def is_user_trusted(user):
    user = User.query.filter_by(id=user.id).first()
    if user.trusted == 1:
        return True
    else:
        return False


def is_page_from_doc(image_id, user):
    document_id = Image.query.filter_by(id=image_id).first().document_id
    if is_user_owner_or_collaborator(document_id, user):
        return True
    else:
        return False


def is_line_from_doc(line_id, user):
    document_id = Image.query.join(TextRegion).join(TextLine).filter(TextLine.id==line_id).first().document_id
    if is_user_owner_or_collaborator(document_id, user):
        return True
    else:
        return False


def is_granted_acces_for_page(image_id, user):
    if is_user_trusted(user):
        return True
    elif is_page_from_doc(image_id, user):
        return True
    else:
        return False


def is_granted_acces_for_line(line_id, user):
    if is_user_trusted(user):
        return True
    elif is_line_from_doc(line_id, user):
        return True
    else:
        return False


def is_granted_acces_for_document(document_id, user):
    if is_user_trusted(user):
        return True
    elif is_user_owner_or_collaborator(document_id, user):
        return True
    else:
        return False


def get_line_image_by_id(line_id):
    line = TextLine.query.filter_by(id=line_id).first()
    region = TextRegion.query.filter_by(id=line.region_id).first()
    image = cv2.imread(region.image.path)

    # coords
    min_x = int(np.min(line.np_points[:,0])) - 15
    min_y = int(np.min(line.np_points[:,1]))
    max_x = int(np.max(line.np_points[:,0])) + 15
    max_y = int(np.max(line.np_points[:,1]))
    min_y -= int(0.1 * (max_y - min_y) + 5.5)
    min_y = max(min_y, 0)
    min_x = max(min_x, 0)

    # crop
    crop_img = image[min_y:max_y, min_x:max_x]
    image = cv2.imencode(".jpg", crop_img, [cv2.IMWRITE_JPEG_QUALITY, 98])[1].tobytes()

    return image


def is_score_computed(document_id):
    text_lines = TextLine.query.join(TextRegion).join(Image).filter(and_(Image.document_id == document_id, TextLine.score != None)).all()
    if len(text_lines) > 0:
        return True
    else:
        return False


def get_sucpect_lines_ids(document_ids, type, show_ignored_lines, threshold=0.95):
    if type == "all":
        text_lines = TextLine.query.join(TextRegion).join(Image).filter(Image.document_id.in_(document_ids)).filter(TextLine.for_training != show_ignored_lines).order_by(TextLine.score.asc())[:2000]
    elif type == "annotated":
        text_lines = TextLine.query.join(TextRegion).join(Image).filter(Image.document_id.in_(document_ids), TextLine.annotations.any()).filter(TextLine.for_training != show_ignored_lines).order_by(TextLine.score.asc())[:2000]
    elif type == "not_annotated":
        text_lines = TextLine.query.join(TextRegion).join(Image).filter(Image.document_id.in_(document_ids), ~TextLine.annotations.any()).filter(TextLine.for_training != show_ignored_lines).order_by(TextLine.score.asc())[:2000]

    lines_dict = {'document_ids': document_ids, 'lines': []}
    for line in text_lines:
        if not line.deleted:
            lines_dict['lines'].append({
            'id': line.id,
            'annotated': True if len(line.annotations) > 0 else False
        })

    return lines_dict


def get_line(line_id):
    text_line = TextLine.query.filter_by(id=line_id).first()

    line_dict = dict()

    line_dict['id'] = text_line.id
    text = text_line.text if text_line.text is not None else ""

    if len(text_line.annotations) > 0:
        line_dict['annotated'] = True
    else:
        line_dict['annotated'] = False

    arabic_helper = ArabicHelper()
    arabic = False
    if arabic_helper.is_arabic_line(text_line.text):
        arabic = True
        text_to_detect_ligatures = arabic_helper._reverse_transcription(copy.deepcopy(text))
    else:
        text_to_detect_ligatures = text

    ligatures_mapping = []

    for i, c in enumerate(text_to_detect_ligatures):
        if unicodedata.combining(c) and i:
            ligatures_mapping[-1].append(i)
        else:
            ligatures_mapping.append([i])

    line_dict['arabic'] = arabic
    line_dict['for_training'] = text_line.for_training
    line_dict['ligatures_mapping'] = ligatures_mapping
    line_dict['np_confidences'] = text_line.np_confidences.tolist()
    line_dict['text'] = text_line.text if text_line.text is not None else ""

    return line_dict


def compute_scores_of_doc(document_id):
    lines = TextLine.query.join(TextRegion).join(Image).filter_by(document_id=document_id)
    for line in lines:
        line_conf = line.np_confidences
        line.score = 1 - (np.sum((1 - line_conf) ** 2) / (line_conf.shape[0] + 2))

    db_session.commit()


def skip_textline(line_id):
    line = TextLine.query.filter_by(id=line_id).first()
    line.score = 10

    db_session.commit()


def document_exists(document_id):
    try:
        document = Document.query.filter_by(id=document_id).first()
    except sqlalchemy.exc.StatementError:
        return False
    if document is not None:
        return True
    else:
        return False


def document_in_allowed_state(document_id, state):
    document = Document.query.filter_by(id=document_id).first()
    if document.state == state:
        return True
    else:
        return False


def find_textlines(query, user, document_ids):
    if document_ids == []:
        documents = get_user_documents(user)
        document_ids = [document.id for document in documents]

    query_words = query.split(' ')[:10]

    db_query = db_session.query(Document.id, Image.id, TextLine).filter(Document.id.in_(document_ids)) \
                         .outerjoin(Image, Image.document_id == Document.id)\
                         .outerjoin(TextRegion, TextRegion.image_id == Image.id)\
                         .outerjoin(TextLine, TextLine.region_id == TextRegion.id)

    for word in query_words:
        db_query = db_query.filter(TextLine.text.like('%{}%' .format(word)))

    text_lines = db_query.limit(200).all()

    lines = []
    for line in text_lines:
         lines.append({"id": line[2].id, "document_id": line[0], "image_id": line[1], "text": line[2].text})

    return lines


def get_documents_with_granted_acces(document_ids, user):
    granted_acces = []
    for document_id in document_ids:
        if is_granted_acces_for_document(document_id, user):
            granted_acces.append(document_id)

    return granted_acces
