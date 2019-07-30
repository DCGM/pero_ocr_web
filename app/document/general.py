from app.db.model import Document, DocumentState, Image
from app.db.general import get_document_by_id, remove_document_by_id, save_document, save_image_to_document,\
    get_all_users
import os
from flask import current_app as app


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
            file_path = os.path.join(directory_path, file.filename)
            file.save(file_path)
            image_db = Image(filename=file.filename, directory=directory_path)
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
    return os.path.join(image.directory, image.filename)


def get_possible_collaborators(document):
    users = get_all_users()
    return list(filter(lambda user: user.id != document.user.id, users))
