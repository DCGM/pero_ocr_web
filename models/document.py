from server import db
from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from models.guid import GUID
from enums.document_state import DocumentState
import uuid


class Document(db.Model):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    userId = Column(Integer, ForeignKey('user.id'))
    state = Column(Enum(DocumentState))
    user = relationship("User", back_populates="documents")

    def __init__(self, name, user, state):
        self.name = name
        self.user = user
        self.state = state
