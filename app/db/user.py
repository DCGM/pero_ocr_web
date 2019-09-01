from app.db import Base
from flask_login import UserMixin
from sqlalchemy import Column, String, Integer
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship


class User(UserMixin, Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(100))
    password = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    institution = Column(String(300))

    documents = relationship('Document', back_populates="user", lazy='dynamic')
    collaborator_documents = relationship('Document', secondary='userdocuments', lazy='dynamic')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)