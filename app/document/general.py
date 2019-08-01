from app.db.model import Document, DocumentState, Image
from app.db.general import get_document_by_id, remove_document_by_id, save_document, save_image_to_document,\
    get_all_users, get_user_by_id
import os
from flask import current_app as app
from app.db import db_session
import uuid


def create_document(name, user):
    document = Document(
        name=name, user=user, state=DocumentState.NEW)
    save_document(document)
    return document


def check_and_remove_document(document_id, user):
    document = get_document_by_id(document_id)
    if document and document.user.id == user.id:
        remove_document_by_id(document_id)
        return True
    return False


def save_images(files, document_id):
    document = get_document_by_id(document_id)
    directory_path = get_and_create_document_image_directory(document_id)

    for file in files:
        if is_allowed_file(file):
            image_id = str(uuid.uuid4())
            extension = os.path.splitext(file.filename)[1]
            file_path = os.path.join(directory_path, "{}{}".format(image_id, extension))
            file.save(file_path)
            image_db = Image(id=image_id, filename=file.filename, path=file_path)
            save_image_to_document(document, image_db)


def get_and_create_document_image_directory(document_id):
    directory_path = app.config['UPLOAD_IMAGE_FOLDER'] + document_id
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


def get_image_url(document_id, image_id):
    document = get_document_by_id(document_id)
    image = document.images.filter_by(id=image_id).first()
    return image.path


def get_possible_collaborators(document):
    users = get_all_users()
    return list(filter(lambda user: user.id != document.user.id, users))


class UserSelectItem:
    def __init__(self, user, is_selected=False):
        self.user = user
        self.is_selected = is_selected


def get_collaborators_select_data(document):
    select_items = []
    possible_collaborators = get_possible_collaborators(document)

    for user in possible_collaborators:
        is_selected = is_user_collaborator(document, user)
        user_select_item = UserSelectItem(user=user, is_selected=is_selected)
        select_items.append(user_select_item)
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
    if user in document.collaborators:
        return True
    return False
