from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from models.guid import GUID
import uuid
from server import Base


class Image(Base):
    __tablename__ = 'image'
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    filename = Column(String(100))

    def __init__(self, name):
        self.name = name
