from server import db, create_app
# from models.user import *

db.create_all(app=create_app()) # pass the create_app result so Flask-SQLAlchemy gets the configuration.