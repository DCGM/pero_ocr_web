from app.document import bp
from flask_login import login_required, current_user
from flask import render_template, redirect, url_for, request, send_file, flash, Response
from app.document.general import create_document, check_and_remove_document, save_images, get_image_url, \
    get_collaborators_select_data, save_collaborators, is_document_owner, is_user_owner_or_collaborator,\
    remove_image, get_document_images
from app.db.general import get_user_documents, get_document_by_id, get_image_by_id
from app.document.forms import CreateDocumentForm
import xml.etree.ElementTree as ET
from os import path


@bp.route('/documents')
@login_required
def documents():
    user_created_documents = get_user_documents(current_user)
    return render_template('document/documents.html', documents=user_created_documents)


@bp.route('/document/new', methods=['GET', 'POST'])
@login_required
def new_document():
    form = CreateDocumentForm()
    if form.validate_on_submit():
        create_document(form.document_name.data, current_user)
        flash(u'Document successfully created!', 'success')
        return redirect(url_for('document.documents'))
    else:
        return render_template('document/new_document.html', form=form)


@bp.route('/document/<string:document_id>/delete')
@login_required
def document_remove(document_id):
    if check_and_remove_document(document_id, current_user):
        flash(u'Document successfully deleted!', 'success')
        return document_id
    else:
        flash(u'You do not have sufficient rights to remove this document!', 'danger')
        return None


@bp.route('/document/<string:document_id>/upload', methods=['GET'])
@login_required
def document_upload_get(document_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to upload images!', 'danger')
        return redirect(url_for('main.index'))

    document = get_document_by_id(document_id)
    images = get_document_images(document)
    return render_template('document/upload_images.html', document=document, images=images)


@bp.route('/document/<string:document_id>/upload', methods=['POST'])
@login_required
def document_upload_post(document_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to upload images!', 'danger')
        return redirect(url_for('main.index'))
    files = request.files.getlist('document_uploaded_files')
    all_correct = save_images(files, document_id)
    if all_correct:
        flash(u'Images successfully uploaded!', 'success')
    else:
        flash(u'Some images were not successfully uploaded!', 'danger')
    return redirect('/document/{}/upload'.format(document_id))


@bp.route('/document/<string:document_id>/image/<string:image_id>/delete', methods=['GET'])
def document_remove_image(document_id, image_id):
    return redirect('/document/{}/upload'.format(document_id))


@bp.route('/get_xml/<string:document_id>/<string:image_id>')
def get_xml(document_id, image_id):
    image = get_image_by_id(image_id)
    root = ET.Element('PcGts')
    root.set('xmlns', 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15')

    page_element = ET.SubElement(root, 'Page',
                                 {"imageFilename": path.splitext(image.filename)[0], "imageWidth": str(image.width), "imageHeight": str(image.height)})
    region_index = 1
    for text_region in image.textregions:
        text_region_element = ET.SubElement(page_element, 'TextRegion', {"id": "r{}".format(region_index)})
        ET.SubElement(text_region_element, 'Coords', {"points": text_region.points})
        region_index += 1

    xml_string = ET.tostring(root, encoding='utf-8')
    return Response(xml_string, mimetype='text/xml')

@bp.route('/get_image/<string:document_id>/<string:image_id>')
# @login_required
def get_image(document_id, image_id):
    # if not is_user_owner_or_collaborator(document_id, current_user):
    #     flash(u'You do not have sufficient rights to get this image!', 'danger')
    #     return redirect(url_for('main.index'))
    image_url = get_image_url(document_id, image_id)
    return send_file(image_url)


@bp.route('/remove_image/<string:document_id>/<string:image_id>')
@login_required
def remove_image_get(document_id, image_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to get this image!', 'danger')
        return redirect(url_for('main.index'))
    if remove_image(document_id, image_id):
        flash(u'Image successfully removed!', 'success')
    return redirect('/document/{}/upload'.format(document_id))


@bp.route('/document/<string:document_id>/collaborators', methods=['GET'])
@login_required
def document_edit_collaborators_get(document_id):
    if not is_document_owner(document_id, current_user):
        flash(u'You do not have sufficient rights to edit collaborators!', 'danger')
        return redirect(url_for('main.index'))
    else:
        document = get_document_by_id(document_id)
        select_data = get_collaborators_select_data(document)
        return render_template('document/edit_collaborators.html', document=document, select_items=select_data)


@bp.route('/document/<string:document_id>/collaborators', methods=['POST'])
@login_required
def document_edit_collaborators_post(document_id):
    collaborators_ids = request.form.getlist('collaborators')
    if not is_document_owner(document_id, current_user):
        flash(u'You do not have sufficient rights to edit collaborators!', 'danger')
        return redirect(url_for('main.index'))
    else:
        save_collaborators(document_id, collaborators_ids)
        flash(u'Collaborators saved successfully.', 'success')
        return redirect('/document/{}/collaborators'.format(document_id))
