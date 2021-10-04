from app import db_session
from app.db import User, Document, Request, Image, TextRegion, TextLine, LayoutDetector, Baseline, OCR, LanguageModel, \
    Annotation
from sqlalchemy import distinct, func


def save_user(user):
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def get_document_by_id(document_id):
    return Document.query.filter_by(id=document_id).first()


def get_image_annotation_statistics_db(image_id):
    line_count = db_session.query(func.count(TextLine.id)).filter(TextLine.deleted == False).join(TextRegion).join(Image).filter(Image.id == image_id).one()[0]
    annotated_count = db_session.query(func.count(distinct(TextLine.id))).filter(TextLine.deleted == False).filter(TextLine.annotated == True).join(TextRegion).join(Image).filter(Image.id == image_id).one()[0]
    return line_count, annotated_count


def get_document_annotation_statistics_db(document_id):
    annotated_count = db_session.query(func.count(distinct(TextLine.id))).filter(TextLine.deleted == False).join(TextRegion).join(Image).join(Document).join(Annotation).filter(Document.id == document_id).one()[0]
    return annotated_count


def get_all_documents():
    all_documents = Document.query.filter_by(deleted=False).order_by(Document.created_date).all()
    return all_documents


def get_user_documents(user):
    user_created_documents = user.documents.filter_by(deleted=False).order_by(Document.created_date).all()
    collaborators_documents = user.collaborator_documents.filter_by(deleted=False).order_by(Document.created_date).all()
    return user_created_documents + collaborators_documents


def get_requests(document_ids=None):
    db_requests = db_session.query(Request)
    if document_ids is not None:
        db_requests = db_requests.join(Document).filter(Document.id.in_(document_ids))

    db_requests = db_requests.order_by(Request.created_date)
    db_requests = db_requests.all()[::-1]

    return db_requests


def get_previews_for_documents(document_ids: list):
    images = Image.query.filter(Image.deleted == False).filter(Image.document_id.in_(document_ids))
    images = images.distinct(Image.document_id)
    images = images.all()
    return images


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
    return Image.query.filter_by(id=image_id, deleted=False).one()


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
