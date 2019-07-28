from app.db.model import Document, DocumentState
from app.db.general import get_document_by_id, remove_document_by_id, save_document


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
