from server import db
from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from models.guid import GUID
from enums.document_state import DocumentState
import uuid


class Document(db.Model):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    userId = Column(Integer, ForeignKey('user.id'))
    state = Column(Enum(DocumentState))

    def __init__(self, name, userId, state):
        self.name = name
        self.userId = userId
        self.state = state
