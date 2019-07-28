from db import Base
from flask_login import UserMixin
from sqlalchemy import Column, String, Integer


class User(UserMixin, Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(100))
    password = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    institution = Column(String(300))
