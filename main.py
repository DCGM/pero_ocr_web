from flask import Blueprint, render_template, redirect, url_for, request
from server import db
from flask_login import current_user, login_required
from models.document import Document
from models.user import User
from enums.document_state import DocumentState

main = Blueprint('main', __name__)


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
    documents = Document.query.filter_by(userId=int(current_user.id)).join(
        User, Document.userId == User.id).all()

    return render_template('browser.html', documents=documents)


@main.route('/document/new', methods=['GET', 'POST'])
@login_required
def new_document():
    if request.method == 'POST':
        document_name = request.form.get('documentName')
        new_document = Document(
            name=document_name, userId=current_user.id, state=DocumentState.NEW)
        db.session.add(new_document)
        db.session.commit()
        db.session.refresh(new_document)
        return redirect(url_for('main.browser'))
    else:
        return render_template('new_document.html')


@main.route('/document/<string:id>/edit')
@login_required
def document_edit(id):
    return id
