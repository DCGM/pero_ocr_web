import os
from flask import Blueprint, render_template, redirect, url_for, request, abort
from server import db, Base
from flask_login import current_user, login_required
from models.document import Document
from models.user import User
from models.image import Image
from enums.document_state import DocumentState
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Enum
from sqlalchemy_utils import create_database
from sqlalchemy.orm import sessionmaker
from models.guid import GUID
import uuid


main = Blueprint('main', __name__)
base_image_path = 'C:/Users/David/Documents/pero_ocr_web/static'

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.browser'))
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@main.route('/browser')
@login_required
def browser():
    return render_template('browser.html', documents=current_user.documents)


@main.route('/document/new', methods=['GET', 'POST'])
@login_required
def new_document():
    if request.method == 'POST':
        document_name = request.form.get('documentName')
        new_document = Document(
            name=document_name, user=current_user, state=DocumentState.NEW)
        db.session.add(new_document)
        db.session.commit()
        db.session.refresh(new_document)
        engine = create_engine(
            "sqlite:///db/documents/{}.sqlite".format(new_document.id))
        Base.metadata.create_all(engine)

        return redirect(url_for('main.browser'))
    else:
        return render_template('new_document.html')


@main.route('/document/<string:id>/collaborators')
@login_required
def document_edit(id):
    return 'Collaborators ' + id


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
    return render_template('upload_images.html', document=document, images=images, base_image_url=base_image_path)


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


@main.route('/document/<string:id>/delete')
@login_required
def document_remove(id):
    document = Document.query.get(id)
    if document and document.user.id == current_user.id:
        Document.query.filter_by(id=id).delete()
        db.session.commit()
        return redirect(url_for('main.browser'))
    else:
        return abort(403)


def is_allowed(file, extensions):
    if str(file.filename).lower().endswith(extensions):
        return True

    return False


def create_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)
