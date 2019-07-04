from server import db
from sqlalchemy import Column, Integer, String, ForeignKey

class Document(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    userId = Column(Integer, ForeignKey('user.id'))
    state = Column(Integer)

    def __init__(self, name, userId):
        self.name = name
        self.userId = userId