from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from server import db


class User(UserMixin, db.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String(100))
    password = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    institution = Column(String(300))
    documents = relationship('Document', back_populates="user")

    def __init__(self, email, password, first_name, last_name, institution):
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.institution = institution
