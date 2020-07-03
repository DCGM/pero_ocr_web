import cv2
import numpy as np
import hashlib
import io
import exifread
from sqlalchemy import and_, or_
from app.db.model import Document, DocumentState, Image
from app.db.general import get_document_by_id, remove_document_by_id, save_document, save_image_to_document,\
    get_all_users, get_user_by_id, get_image_by_id, is_image_duplicate
import os
from flask import current_app as app
from flask import Response
from app import db_session
import uuid
from app.db import Document, Image, TextLine, Annotation, UserDocument, User, TextRegion
import datetime
import pero_ocr.document_ocr.layout as layout
import unicodedata
from werkzeug.urls import url_quote


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

    file_path = os.path.join(directory_path, "{}{}".format(image_id, extension))
    with open(file_path, 'wb') as f:
        f.write(file_data)
        image_db.path = file_path
        image_db.width = image.shape[1]
        image_db.height = image.shape[0]
        image_db.imagehash = img_hash
        save_image_to_document(document, image_db)

    return ''


def get_and_create_document_image_directory(document_id):
    directory_path = os.path.join(app.config['UPLOAD_IMAGE_FOLDER'], document_id)
    create_dirs(directory_path)
    return directory_path


def is_allowed_file(file):
    if file.filename != '' and is_allowed_extension(file, app.config['EXTENSIONS']):
        return True
    return False


def is_allowed_extension(file, allowed_extensions):
    if str(file.filename).lower().endswith(allowed_extensions):
        return True
    return False


def create_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


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

    for old_collaborator in document.collaborators:
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


def get_page_layout(image_id, only_regions=False, only_annotated=False, alto=False, from_time: datetime.datetime=None):
    image = get_image_by_id(image_id)
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
                        region_layout.lines.append(layout.TextLine(id=str(text_line.id),
                                                                   baseline=text_line.np_baseline,
                                                                   polygon=text_line.np_points,
                                                                   heights=text_line.np_heights,
                                                                   transcription=text_line.text))
    if alto:
        logits_path = os.path.join(app.config['OCR_RESULTS_FOLDER'], str(image.document.id), "{}.logits".format(image.id))
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

        line = TextLine.query.filter_by(id=uuid.replace("-", "")).first()

        conf_string = ' '.join(str(round(x, 3)) for x in confidences)
        line.confidences = conf_string.replace('1.0', '1')
        line_conf = line.np_confidences
        line.score = 1 - (np.sum((1 - line_conf) ** 2) / (line_conf.shape[0] + 2))

        line.text = transcription

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


def get_sucpect_lines_ids(document_id, type, threshold=0.95):
    if type == "all":
        text_lines = TextLine.query.join(TextRegion).join(Image).filter(Image.document_id == document_id).order_by(TextLine.score.asc())[:2000]
    elif type == "annotated":
        text_lines = TextLine.query.join(TextRegion).join(Image).filter(Image.document_id == document_id, TextLine.annotations.any()).order_by(TextLine.score.asc())[:2000]
    elif type == "not_annotated":
        text_lines = TextLine.query.join(TextRegion).join(Image).filter(Image.document_id == document_id, ~TextLine.annotations.any()).order_by(TextLine.score.asc())[:2000]

    lines_dict = {'document_id': document_id, 'lines': []}
    lines_dict['lines'] += [{
        'id': line.id,
        'annotated': True if len(line.annotations) > 0 else False
    } for line in text_lines]

    return lines_dict


def get_line(line_id):
    text_line = TextLine.query.filter_by(id=line_id).first()

    line_dict = dict()
    line_dict['id'] = text_line.id
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
    except:
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
