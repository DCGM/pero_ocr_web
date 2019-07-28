from app.db import db_session
from app.db.user import User
from app.db.model import Document


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
    return user.documents.filter_by(deleted=False)


def remove_document_by_id(document_id):
    document = get_document_by_id(document_id)
    document.deleted = True
    db_session.commit()


def save_document(document):
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document
