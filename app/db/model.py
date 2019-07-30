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
    images = relationship('Image', secondary='documentimages', lazy='dynamic')
    collaborators = relationship('User', secondary='userdocuments')


class Image(Base):
    __tablename__ = 'images'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    filename = Column(String(100))
    directory = Column(String(255))


class DocumentImage(Base):
    __tablename__ = 'documentimages'
    id = Column(Integer(), primary_key=True)
    document_id = Column(GUID(), ForeignKey('documents.id'), nullable=False)
    image_id = Column(GUID(), ForeignKey('images.id'), nullable=False)


class UserDocument(Base):
    __tablename__ = 'userdocuments'
    id = Column(Integer(), primary_key=True)
    user_id = Column(Integer(), ForeignKey('users.id'), nullable=False)
    document_id = Column(GUID(), ForeignKey('documents.id'), nullable=False)
