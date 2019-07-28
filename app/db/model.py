from app.db import Base
from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Boolean
from app.db.guid import GUID
import enum
from sqlalchemy.orm import relationship
import uuid


class DocumentState(enum.Enum):
    NEW = 'New'
    UPLOADED_IMAGES = 'Uploaded images'


class Document(Base):
    __tablename__ = 'documents'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    state = Column(Enum(DocumentState))
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="documents")
    deleted = Column(Boolean(), default=False)


class Image(Base):
    __tablename__ = 'images'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    filename = Column(String(100))
