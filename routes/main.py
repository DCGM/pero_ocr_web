# TEMPORARY CURRENT REFACTORING

import os
from flask import Blueprint, render_template, redirect, url_for, request, abort
from server import db, Base
from flask_login import current_user, login_required
from models.document import Document
from models.user import User
from models.image import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


main = Blueprint('main', __name__)
base_image_path = 'C:/Users/David/Documents/pero_ocr_web/static'




@main.route('/document/<string:id>/collaborators', methods=['POST'])
@login_required
def document_edit_colaborators_post(id):
    request_form = request.form.getlist('collaborators')
    return 'Edit'


@main.route('/document/<string:id>/collaborators', methods=['GET'])
@login_required
def document_edit_colaborators_post_get(id):
    document = Document.query.get(id)
    users = User.query.all()
    users = list(filter(lambda user: user.id != document.user.id, users))
    return render_template('document/edit_collaborators.html', document=document, users=users)


@main.route('/document/<string:id>/upload', methods=['GET'])
@login_required
def document_upload_get(id):
    document = Document.query.get(id)
    engine = create_engine(
        "sqlite:///db/documents/{}.sqlite".format(id))
    Session = sessionmaker(bind=engine)
    session = Session()
    images = session.query(Image.id, Image.filename).all()
    session.close()
    return render_template('document/upload_images.html', document=document, images=images, base_image_url=base_image_path)


@main.route('/document/<string:id>/upload', methods=['POST'])
@login_required
def document_upload_post(id):
    extensions = ('jpg', 'png', 'pdf')
    files = request.files.getlist('document_uploaded_files')
    path = base_image_path + \
        '/upload_images/' + id  # GET DIRECTORY FROM CONFIG
    create_dirs(path)
    engine = create_engine(
        "sqlite:///db/documents/{}.sqlite".format(id))
    Session = sessionmaker(bind=engine)
    session = Session()

    for file in files:
        if file.filename != '' and is_allowed(file, extensions):
            file_path = os.path.join(path, file.filename)
            file.save(file_path)
            image_db = Image(file.filename)
            session.add(image_db)
    session.commit()
    session.close()
    return redirect('/document/{}/upload'.format(id))


def is_allowed(file, extensions):
    if str(file.filename).lower().endswith(extensions):
        return True

    return False


def create_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)
