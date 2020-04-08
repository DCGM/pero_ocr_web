import json

from app.document import bp
from flask_login import login_required, current_user
from flask import render_template, redirect, url_for, request, send_file, flash, Response
from app.document.general import create_document, check_and_remove_document, save_images, get_image_url, \
    get_collaborators_select_data, save_collaborators, is_document_owner, is_user_owner_or_collaborator,\
    remove_image, get_document_images, get_page_layout, get_page_layout_text, update_confidences, is_user_trusted,\
    is_granted_acces_for_page, is_granted_acces_for_document
from app.db.general import get_user_documents, get_document_by_id
from app.document.forms import CreateDocumentForm
from io import BytesIO
import zipfile
import time


@bp.route('/documents')
@login_required
def documents():
    user_created_documents = get_user_documents(current_user)
    return render_template('document/documents.html', documents=user_created_documents)


@bp.route('/new_document', methods=['GET', 'POST'])
@login_required
def new_document():
    form = CreateDocumentForm()
    if form.validate_on_submit():
        create_document(form.document_name.data, current_user)
        flash(u'Document successfully created!', 'success')
        return redirect(url_for('document.documents'))
    else:
        return render_template('document/new_document.html', form=form)


@bp.route('/delete_document/<string:document_id>')
@login_required
def delete_document(document_id):
    if check_and_remove_document(document_id, current_user):
        flash(u'Document successfully deleted!', 'success')
        return document_id
    else:
        flash(u'You do not have sufficient rights to remove this document!', 'danger')
        return None


@bp.route('/upload_document/<string:document_id>', methods=['GET'])
@login_required
def upload_document_get(document_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to upload images!', 'danger')
        return redirect(url_for('main.index'))

    document = get_document_by_id(document_id)
    images = get_document_images(document)
    return render_template('document/upload_images.html', document=document, images=images)


@bp.route('/upload_document/<string:document_id>', methods=['POST'])
@login_required
def upload_document_post(document_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to upload images!', 'danger')
        return '', 404

    if request.method == 'POST':
        f = request.files.get('file')
        status = save_images(f, document_id)
        if status == '':
            return '', 200
        return status, 409


@bp.route('/get_page_xml_regions/<string:image_id>')
@login_required
def get_page_xml_regions(image_id):
    if not is_granted_acces_for_page(image_id, current_user):
        flash(u'You do not have sufficient rights to download regions!', 'danger')
        return redirect(url_for('main.index'))

    page_layout = get_page_layout(image_id, only_regions=True)
    return Response(page_layout.to_pagexml_string(), mimetype='text/xml')


@bp.route('/get_page_xml_lines/<string:image_id>')
@login_required
def get_page_xml_lines(image_id):
    if not is_granted_acces_for_page(image_id, current_user):
        flash(u'You do not have sufficient rights to download xml!', 'danger')
        return redirect(url_for('main.index'))

    page_layout = get_page_layout(image_id, only_regions=False, only_annotated=False)
    return Response(page_layout.to_pagexml_string(), mimetype='text/xml')


@bp.route('/get_alto_xml/<string:image_id>')
@login_required
def get_alto_xml(image_id):
    if not is_granted_acces_for_page(image_id, current_user):
        flash(u'You do not have sufficient rights to download alto!', 'danger')
        return redirect(url_for('main.index'))

    page_layout = get_page_layout(image_id, only_regions=False, only_annotated=False, alto=True)
    return Response(page_layout.to_altoxml_string(), mimetype='text/xml')


@bp.route('/get_text/<string:image_id>')
@login_required
def get_text(image_id):
    if not is_granted_acces_for_page(image_id, current_user):
        flash(u'You do not have sufficient rights to download text!', 'danger')
        return redirect(url_for('main.index'))

    page_layout = get_page_layout(image_id, only_regions=False, only_annotated=False)
    return Response(get_page_layout_text(page_layout), mimetype='text/plain')


@bp.route('/download_document_pages/<string:document_id>')
def get_document_pages(document_id):
    if not is_granted_acces_for_document(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        document = get_document_by_id(document_id)
        for image in document.images:
            page_layout = get_page_layout(str(image.id), only_regions=False, only_annotated=False)
            page_string = page_layout.to_pagexml_string()
            text_string = get_page_layout_text(page_layout)
            d_page = zipfile.ZipInfo("{}.xml".format(image.id))
            d_page.date_time = time.localtime(time.time())[:6]
            d_page.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(d_page, page_string)
            d_text = zipfile.ZipInfo("{}.txt".format(image.id))
            d_text.date_time = time.localtime(time.time())[:6]
            d_text.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(d_text, text_string)
    memory_file.seek(0)
    return send_file(memory_file, attachment_filename='pages.zip', as_attachment=True)


@bp.route('/get_document_annotated_pages/<string:document_id>')
@bp.route('/download_document_annotated_pages/<string:document_id>')
def get_document_annotated_pages(document_id):
    if not is_granted_acces_for_document(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        document = get_document_by_id(document_id)
        for image in document.images:
            page_layout = get_page_layout(str(image.id), only_regions=False, only_annotated=True)
            xml_string = page_layout.to_pagexml_string()
            d_XML = zipfile.ZipInfo("{}.xml".format(image.id))
            d_XML.date_time = time.localtime(time.time())[:6]
            d_XML.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(d_XML, xml_string)
    memory_file.seek(0)
    return send_file(memory_file, attachment_filename='pages.zip', as_attachment=True)


@bp.route('/get_image/<string:image_id>')
@login_required
def get_image(image_id):
    if not is_granted_acces_for_page(image_id, current_user):
        flash(u'You do not have sufficient rights to download image!', 'danger')
        return redirect(url_for('main.index'))

    image_url = get_image_url(image_id)
    return send_file(image_url)


@bp.route('/remove_image/<string:document_id>/<string:image_id>')
@login_required
def remove_image_get(document_id, image_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to get this image!', 'danger')
        return redirect(url_for('main.index'))
    if remove_image(document_id, image_id):
        flash(u'Image successfully removed!', 'success')
    return redirect(url_for('document.upload_document_get', document_id=document_id))


@bp.route('/collaborators/<string:document_id>', methods=['GET'])
@login_required
def collaborators_get(document_id):
    if not is_document_owner(document_id, current_user):
        flash(u'You do not have sufficient rights to edit collaborators!', 'danger')
        return redirect(url_for('main.index'))
    else:
        document = get_document_by_id(document_id)
        select_data = get_collaborators_select_data(document)
        return render_template('document/edit_collaborators.html', document=document, select_items=select_data)


@bp.route('/collaborators/<string:document_id>', methods=['POST'])
@login_required
def collaborators_post(document_id):
    collaborators_ids = request.form.getlist('collaborators')
    if not is_document_owner(document_id, current_user):
        flash(u'You do not have sufficient rights to edit collaborators!', 'danger')
        return redirect(url_for('main.index'))
    else:
        save_collaborators(document_id, collaborators_ids)
        flash(u'Collaborators saved successfully.', 'success')
        return redirect(url_for('document.collaborators_get', document_id=document_id))


@bp.route('/update_confidences', methods=['POST'])
def update_all_confidences():
    if not is_user_trusted(current_user.id):
        flash(u'You do not have sufficient rights to edit collaborators!', 'danger')
        return redirect(url_for('main.index'))

    file = request.files['data']
    content = file.read()
    changes = json.loads(content)
    update_confidences(changes)

    return redirect(url_for('document.documents'))
