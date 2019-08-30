from app.db import Base
from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Boolean, DateTime
from app.db.guid import GUID
import enum
from sqlalchemy.orm import relationship
import uuid
import datetime


class DocumentState(enum.Enum):
    NEW = 'New'
    WAITING_LAYOUT_ANALYSIS = 'Waiting on start of layout analysis'
    RUNNING_LAYOUT_ANALYSIS = 'Running layout analysis'
    COMPLETED_LAYOUT_ANALYSIS = 'Layout analysis completed'
    WAITING_OCR = 'Waiting on start of OCR'


class RequestState(enum.Enum):
    PENDING = 0
    IN_PROGRESS = 1
    SUCCESS = 2
    FAILURE = 3
    CANCELED = 4


class RequestType(enum.Enum):
    LAYOUT_ANALYSIS = 0
    OCR = 1


class Document(Base):
    __tablename__ = 'documents'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    state = Column(Enum(DocumentState))
    deleted = Column(Boolean(), default=False)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="documents")
    images = relationship('Image', back_populates="document", lazy='dynamic')
    collaborators = relationship('User', secondary='userdocuments')
    requests = relationship('Request', back_populates="document", lazy='dynamic')


class Image(Base):
    __tablename__ = 'images'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    filename = Column(String(100))
    path = Column(String(255))
    width = Column(Integer())
    height = Column(Integer())
    deleted = Column(Boolean(), default=False)

    document_id = Column(GUID(), ForeignKey('documents.id'))
    document = relationship('Document', back_populates="images")
    textregions = relationship('TextRegion', back_populates="image", lazy='dynamic')


class UserDocument(Base):
    __tablename__ = 'userdocuments'
    id = Column(Integer(), primary_key=True)
    user_id = Column(Integer(), ForeignKey('users.id'), nullable=False)
    document_id = Column(GUID(), ForeignKey('documents.id'), nullable=False)


class Request(Base):
    __tablename__ = 'requests'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    request_type = Column(Enum(RequestType))
    state = Column(Enum(RequestState))

    document_id = Column(GUID(), ForeignKey('documents.id'))
    document = relationship('Document', back_populates="requests")

class TextRegion(Base):
    __tablename__ = 'textregions'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    points = Column(String())
    deleted = Column(Boolean())

    image_id = Column(GUID(), ForeignKey('images.id'))
    image = relationship('Image', back_populates="textregions")

