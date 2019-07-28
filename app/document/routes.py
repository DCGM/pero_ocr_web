from app.document import bp
from flask_login import login_required, current_user
from flask import render_template, redirect, url_for, abort
from app.document.general import create_document, check_and_remove_document
from app.db.general import get_user_documents
from app.document.forms import CreateDocumentForm


@bp.route('/documents')
@login_required
def documents():
    return render_template('document/documents.html', documents=get_user_documents(current_user))


@bp.route('/document/new', methods=['GET', 'POST'])
@login_required
def new_document():
    form = CreateDocumentForm()
    if form.validate_on_submit():
        create_document(form.document_name.data, current_user)
        return redirect(url_for('document.documents'))
    else:
        return render_template('document/new_document.html', form=form)


@bp.route('/document/<string:document_id>/delete')
@login_required
def document_remove(document_id):
    if check_and_remove_document(document_id, current_user):
        return redirect(url_for('document.documents'))
    else:
        return abort(403)
