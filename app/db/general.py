from app.db import db_session
from app.db.user import User
from app.db.model import Document, Request, Image, TextRegion


def save_user(user):
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def get_document_by_id(document_id):
    return Document.query.filter_by(id=document_id, deleted=False).first()


def get_user_documents(user):
    user_created_documents = user.documents.filter_by(deleted=False).all()
    collaborators_documents = user.collaborator_documents.filter_by(deleted=False).all()
    return user_created_documents + collaborators_documents


def get_user_by_id(id):
    return User.query.get(int(id))


def remove_document_by_id(document_id):
    document = get_document_by_id(document_id)
    document.deleted = True
    db_session.commit()


def save_document(document):
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


def save_image_to_document(document, image):
    document.images.append(image)
    db_session.commit()


def get_all_users():
    return User.query.all()


def get_request_by_id(request_id):
    return Request.query.filter_by(id=request_id).first()


def get_image_by_id(image_id):
    return Image.query.filter_by(id=image_id, deleted=False).first()


def get_text_region_by_id(id):
    return TextRegion.query.get(id)