from app import db_session
from app.db import User, Document, Request, Image, TextRegion, TextLine, LayoutDetector, Baseline, OCR, LanguageModel


def save_user(user):
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def get_document_by_id(document_id):
    return Document.query.filter_by(id=document_id, deleted=False).first()


def get_all_documents():
    all_documents = Document.query.filter_by(deleted=False).all()
    return all_documents


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


def get_layout_detector_by_id(id):
    return LayoutDetector.query.get(id)


def get_text_line_by_id(id):
    try:
        return TextLine.query.get(id)
    except:
        return None


def get_baseline_by_id(id):
    return Baseline.query.get(id)


def get_ocr_by_id(id):
    return OCR.query.get(id)


def get_language_model_by_id(id):
    return LanguageModel.query.get(id)


def is_image_duplicate(document_id, imagehash):
    image_db = Image.query.filter_by(imagehash=imagehash, deleted=False, document_id=document_id).first()
    return image_db
