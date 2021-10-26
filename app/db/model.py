from app.db import Base
from sqlalchemy import Column, Enum, ForeignKey, Integer, Float, String, Boolean, DateTime
from app.db.guid import GUID
import enum
from sqlalchemy.orm import relationship
import uuid
import datetime
import numpy as np
import Levenshtein


class DocumentState(enum.Enum):
    NEW = 'New'
    WAITING_LAYOUT_ANALYSIS = 'Waiting on start of layout analysis.'
    RUNNING_LAYOUT_ANALYSIS = 'Running layout analysis.'
    COMPLETED_LAYOUT_ANALYSIS = 'Layout analysis completed.'
    WAITING_OCR = 'Waiting on start of OCR.'
    RUNNING_OCR = 'Running OCR.'
    COMPLETED_OCR = 'OCR completed.'


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
    name = Column(String())
    state = Column(Enum(DocumentState), index=True)
    deleted = Column(Boolean(), default=False)
    line_count = Column(Integer(), default=0)
    annotated_line_count = Column(Integer(), default=0)
    created_date = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    is_public = Column(Boolean(), default=False, index=True)

    #preview_image_id = Column(GUID(), ForeignKey('documents.id'), nullable=True, index=True)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="documents")
    images = relationship('Image', back_populates="document", lazy='dynamic')
    collaborators = relationship('User', secondary='userdocuments')
    requests = relationship('Request', back_populates="document", lazy='dynamic')
    requests_lazy = relationship('Request', order_by="Request.created_date")


class Image(Base):
    __tablename__ = 'images'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    filename = Column(String())
    path = Column(String())
    width = Column(Integer())
    height = Column(Integer())
    deleted = Column(Boolean(), default=False)
    imagehash = Column(String())
    document_id = Column(GUID(), ForeignKey('documents.id'), index=True)

    document = relationship('Document', back_populates="images")
    textregions = relationship('TextRegion', back_populates="image", lazy='dynamic')


class UserDocument(Base):
    __tablename__ = 'userdocuments'
    id = Column(Integer(), primary_key=True)
    user_id = Column(Integer(), ForeignKey('users.id'), nullable=False, index=True)
    document_id = Column(GUID(), ForeignKey('documents.id'), nullable=False, index=True)


class Request(Base):
    __tablename__ = 'requests'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    layout_id = Column(GUID(), ForeignKey('layout_detectors.id'))
    baseline_id = Column(GUID(), ForeignKey('baseline.id'))
    ocr_id = Column(GUID(), ForeignKey('ocr.id'))
    language_model_id = Column(GUID(), ForeignKey('language_model.id'))
    created_date = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    request_type = Column(Enum(RequestType))
    state = Column(Enum(RequestState))
    log = Column(String())
    document_id = Column(GUID(), ForeignKey('documents.id'), index=True)

    document = relationship('Document', back_populates="requests")
    ocr = relationship('OCR')
    layout_detector = relationship('LayoutDetector')
    baseline = relationship('Baseline')
    language_model = relationship('LanguageModel')


class TextRegion(Base):
    __tablename__ = 'textregions'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    order = Column(Integer())
    points = Column(String())
    deleted = Column(Boolean(), default=False)
    image_id = Column(GUID(), ForeignKey('images.id'), index=True)

    image = relationship('Image', back_populates="textregions")
    textlines = relationship('TextLine')

    @property
    def np_points(self):
        return str_points2D_to_np(self.points)

    @np_points.setter
    def np_points(self, ps):
        self.points = points2D_to_str(ps)


class TextLine(Base):
    __tablename__ = 'textlines'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    region_id = Column(GUID(), ForeignKey('textregions.id'), index=True)
    order = Column(Integer())
    points = Column(String())
    baseline = Column(String())
    heights = Column(String())
    confidences = Column(String())
    deleted = Column(Boolean(), default=False)
    annotated = Column(Boolean(), default=False)
    for_training = Column(Boolean(), default=True)
    text = Column(String())
    score = Column(Float(), index=True)

    region = relationship('TextRegion')
    annotations = relationship('Annotation', cascade="all, delete-orphan")

    @property
    def np_points(self):
        return str_points2D_to_np(self.points)

    @np_points.setter
    def np_points(self, ps):
       self.points = points2D_to_str(ps)

    @property
    def np_baseline(self):
        return str_points2D_to_np(self.baseline)

    @np_baseline.setter
    def np_baseline(self, bs):
        self.baseline = points2D_to_str(bs)

    @property
    def np_heights(self):
        return str_points_to_np(self.heights)

    @np_heights.setter
    def np_heights(self, hs):
        self.heights = points_to_str(hs)

    @property
    def np_confidences(self):
        return str_points_to_np(self.confidences)

    @np_confidences.setter
    def np_confidences(self, cs):
        self.confidences = confidences_to_str(cs)


def init_character_change_count(context):
    return Levenshtein.distance(context.get_current_parameters()['text_original'], context.get_current_parameters()['text_edited'])

def init_character_count(context):
    return len(context.get_current_parameters()['text_edited'])


class Annotation(Base):
    __tablename__ = 'annotations'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    text_line_id = Column(GUID(), ForeignKey('textlines.id'), index=True)
    text_original = Column(String())
    text_edited = Column(String())
    created_date = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    deleted = Column(Boolean())
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    character_change_count = Column(Integer, default=init_character_change_count)
    character_count = Column(Integer, default=init_character_count)

    text_line = relationship('TextLine')
    user = relationship('User')


class LayoutDetector(Base):
    __tablename__ = 'layout_detectors'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(), nullable=False)
    description = Column(String())
    active = Column(Boolean(), default=True, nullable=False)
    order = Column(Integer())

    requests = relationship('Request')


class OCR(Base):
    __tablename__ = 'ocr'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(), nullable=False)
    description = Column(String())
    active = Column(Boolean(), default=True, nullable=False)
    order = Column(Integer())

    requests = relationship('Request')


class OCRTrainingDocuments(Base):
    __tablename__ = 'ocr_training_documents'
    document_id = Column(GUID(), ForeignKey('documents.id'), primary_key=True)
    ocr_id = Column(GUID(), ForeignKey('ocr.id'), primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class Baseline(Base):
    __tablename__ = 'baseline'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(), nullable=False)
    description = Column(String())
    active = Column(Boolean(), default=True, nullable=False)
    order = Column(Integer())

    requests = relationship('Request')


class LanguageModel(Base):
    __tablename__ = 'language_model'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(), nullable=False)
    description = Column(String())
    active = Column(Boolean(), default=True, nullable=False)
    order = Column(Integer())

    requests = relationship('Request')


def str_points2D_to_np(str_points):
    return np.asarray([[float(x) for x in point.split(',')] for point in str_points.split()])


def points2D_to_str(points):
    return ' '.join(['{:.1f},{:.1f}'.format(point[0], point[1]) for point in points])


def str_points_to_np(str_heights):
    if str_heights is None:
        return np.asarray([])
    return np.asarray([float(x) for x in str_heights.split()])


def points_to_str(heights):
    return ' '.join(['{:.1f}'.format(x) for x in heights])


def confidences_to_str(cs):
    con_str = ""
    for x in cs:
        if x == 1:
            con_str += " 1"
        else:
            con_str += " {:.3}".format(x)
    return con_str[1:]
