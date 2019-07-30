from app.document import bp
from flask_login import login_required, current_user
from flask import render_template, redirect, url_for, abort, request, send_file
from app.document.general import create_document, check_and_remove_document, save_images, get_image_url, \
    get_possible_collaborators
from app.db.general import get_user_documents, get_document_by_id
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


@bp.route('/document/<string:document_id>/upload', methods=['GET'])
@login_required
def document_upload_get(document_id):
    # TODO check user document permission
    document = get_document_by_id(document_id)
    return render_template('document/upload_images.html', document=document, images=document.images)


@bp.route('/document/<string:document_id>/upload', methods=['POST'])
@login_required
def document_upload_post(document_id):
    # TODO check user document permission
    files = request.files.getlist('document_uploaded_files')
    save_images(files, document_id)
    return redirect('/document/{}/upload'.format(document_id))


@bp.route('/get_image/<string:document_id>/<string:image_id>')
@login_required
def get_image(document_id, image_id):
    # TODO check user document permission
    image_url = get_image_url(document_id, image_id)
    return send_file(image_url)


@bp.route('/document/<string:document_id>/collaborators', methods=['GET'])
@login_required
def document_edit_collaborators_post_get(document_id):
    document = get_document_by_id(document_id)
    users = get_possible_collaborators(document)
    return render_template('document/edit_collaborators.html', document=document, users=users)
