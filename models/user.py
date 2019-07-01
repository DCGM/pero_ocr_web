from main import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    institution = db.Column(db.String(300))

    def __init__(self, email, password, first_name, last_name, institution):
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.institution = institution