import _thread
import sqlalchemy
from app.document import bp
from flask_login import login_required, current_user
from flask import render_template, redirect, url_for, request, send_file, flash, jsonify
from flask import current_app
from app.document.general import create_document, check_and_remove_document, save_image, \
    get_collaborators_select_data, save_collaborators, is_document_owner, is_user_owner_or_collaborator,\
    remove_image, get_document_images, get_page_layout, get_page_layout_text, update_confidences, is_user_trusted,\
    is_granted_acces_for_page, is_granted_acces_for_document, get_line_image_by_id, get_sucpect_lines_ids, \
    compute_scores_of_doc, skip_textline, get_line, is_granted_acces_for_line, create_string_response, \
    update_baselines, make_image_preview, find_textlines, get_documents_with_granted_acces

from werkzeug.exceptions import NotFound

from app.db.general import get_requests

from app.db.general import get_user_documents, get_document_by_id, get_user_by_email, get_all_documents,\
                           get_previews_for_documents, get_image_by_id
from app.document.forms import CreateDocumentForm
from app.document.annotation_statistics import get_document_annotation_statistics, get_user_annotation_statistics, get_document_annotation_statistics_by_day
from io import BytesIO
import dateutil.parser
import zipfile
import time
import os
import json
import re


@bp.route('/documents')
@login_required
def documents():
    if is_user_trusted(current_user):
       user_documents = get_all_documents()
    else:
       user_documents = get_user_documents(current_user)

    document_ids = [d.id for d in user_documents]
    previews = dict([(im.document_id, im) for im in get_previews_for_documents(document_ids)])

    for d in user_documents:
        if d.id not in previews:
            previews[d.id] = ""

    return render_template('document/documents.html', documents=user_documents, previews=previews)


@bp.route('/annotation_statistics/<string:document_id>')
@login_required
def annotation_statistics(document_id):
    if not (is_user_owner_or_collaborator(document_id, current_user) or is_user_trusted(current_user)):
        flash(u'You do not have sufficient rights to view statistics for this document!', 'danger')
        return redirect(url_for('main.index'))

    document = get_document_by_id(document_id)
    statistics = get_document_annotation_statistics(document)

    return render_template('document/annotation_statistics.html', statistics=statistics, header_name=document.name)


@bp.route('/annotation_statistics')
@login_required
def annotation_statistics_global():
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to view global statistics!', 'danger')
        return redirect(url_for('main.index'))

    statistics = get_document_annotation_statistics()

    return render_template('document/annotation_statistics.html', statistics=statistics, header_name='All documents')


@bp.route('/user_annotation_statistics/<string:user_email>')
@login_required
def user_annotation_statistics(user_email):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to view statistics for other users!', 'danger')
        return redirect(url_for('main.index'))

    user = get_user_by_email(user_email)
    statistics = get_user_annotation_statistics(user)

    return render_template('document/annotation_statistics.html',
                           statistics=statistics, header_name=f'{user.first_name} {user.last_name}')


@bp.route('/user_annotation_statistics')
@login_required
def user_annotation_statistics_current_user():
    statistics = get_user_annotation_statistics(current_user)

    return render_template('document/annotation_statistics.html',
                           statistics=statistics, header_name=f'{current_user.first_name} {current_user.last_name}')


@bp.route('/user_annotation_statistics_global')
@login_required
def user_annotation_statistics_global():
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to view statistics for other users!', 'danger')
        return redirect(url_for('main.index'))

    statistics = get_user_annotation_statistics()

    return render_template('document/annotation_statistics.html', statistics=statistics, header_name='All users')


@bp.route('/requests')
@login_required
def requests():
    if is_user_trusted(current_user):
       user_documents = get_all_documents()
    else:
       user_documents = get_user_documents(current_user)

    document_ids = [d.id for d in user_documents]
    requests = get_requests(document_ids)

    return render_template('requests/request_list.html', requests=requests)


@bp.route('/document_history/<string:document_id>')
@login_required
def document_history(document_id):
    if not (is_user_owner_or_collaborator(document_id, current_user) or is_user_trusted(current_user)):
        flash(u'You do not have sufficient rights to view statistics for this document!', 'danger')
        return redirect(url_for('main.index'))

    db_requests = get_requests(document_ids=[document_id])
    db_document = get_document_by_id(document_id)

    ann_stats = get_document_annotation_statistics_by_day(db_document.id)

    import altair as alt
    data = [{'x': str(date), 'y': count, 'u': f'{user1} {user2}'} for date, user1, user2, count in ann_stats]
    data = alt.Data(values=data)
    chart = alt.Chart(data).mark_bar().encode(
            x='x:T',  # specify ordinal data
            y='sum(y):Q',  # specify quantitative data
            color='u:N'
        ).properties(width='container', height=300)

    return render_template('document/document_history.html',
                           requests=db_requests, document=db_document, graph_json=chart.to_json(indent=0))



@bp.route('/new_document', methods=['GET', 'POST'])
@login_required
def new_document():
    form = CreateDocumentForm()
    if form.validate_on_submit():
        document = create_document(form.document_name.data, current_user)
        flash(u'Document successfully created!', 'success')
        return redirect(url_for('document.upload_images_to_document', document_id=document.id))
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


@bp.route('/upload_images_to_document/<string:document_id>', methods=['GET'])
@login_required
def upload_images_to_document(document_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to upload images!', 'danger')
        return redirect(url_for('main.index'))

    document = get_document_by_id(document_id)
    images = get_document_images(document)
    return render_template('document/upload_images_to_document.html', document=document, images=images)


@bp.route('/upload_image_to_document/<string:document_id>', methods=['POST'])
@login_required
def upload_image_to_document(document_id):
    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to upload images!', 'danger')
        return '', 404

    if request.method == 'POST':
        f = request.files.get('file')
        status = save_image(f, document_id)
        if status == '':
            return '', 200
        return status, 409


@bp.route('/get_image_preview/<string:image_id>')
@bp.route('/get_image_preview/')
@login_required
def get_image_preview(image_id=None):
    if image_id is None:
        return send_file('static/img/missing_page.png', cache_timeout=10000000)

    try:
        db_image = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404

    document_id = db_image.document_id
    if not is_granted_acces_for_document(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    image_preview_path = os.path.join(current_app.config['PREVIEW_IMAGES_FOLDER'], str(document_id), str(image_id) + '.jpg')
    if not os.path.isfile(image_preview_path):
        make_image_preview(db_image)
    return send_file(image_preview_path, cache_timeout=0)


@bp.route('/get_document_image_ids/<string:document_id>')
@login_required
def get_document_image_ids(document_id):
    if not is_granted_acces_for_document(document_id, current_user):
        flash(u'You do not have sufficient rights to document!', 'danger')
        return redirect(url_for('main.index'))

    document = get_document_by_id(document_id)
    return jsonify([str(x.id) for x in document.images if not x.deleted])


@bp.route('/get_page_xml_regions/<string:image_id>')
@login_required
def get_page_xml_regions(image_id):
    try:
        db_image = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404

    if not is_granted_acces_for_page(image_id, current_user):
        flash(u'You do not have sufficient rights to download regions!', 'danger')
        return redirect(url_for('main.index'))

    page_layout = get_page_layout(db_image, only_regions=True)
    filename = "{}.xml".format(os.path.splitext(page_layout.id)[0])
    return create_string_response(filename, page_layout.to_pagexml_string(), minetype='text/xml')


@bp.route('/get_page_xml_lines/<string:image_id>')
@login_required
def get_page_xml_lines(image_id):
    try:
        db_image = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404

    if not is_granted_acces_for_page(image_id, current_user):
        flash(u'You do not have sufficient rights to download xml!', 'danger')
        return redirect(url_for('main.index'))

    page_layout = get_page_layout(db_image, only_regions=False)
    filename = "{}.xml".format(os.path.splitext(page_layout.id)[0])
    return create_string_response(filename, page_layout.to_pagexml_string(), minetype='text/xml')


@bp.route('/get_annotated_page_xml_lines/<string:image_id>')
@bp.route('/get_annotated_page_xml_lines/<string:image_id>/<string:from_time>/')
@login_required
def get_annotated_page_xml_lines(image_id, from_time=None):
    try:
        db_image = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404

    if not is_granted_acces_for_page(image_id, current_user):
        flash(u'You do not have sufficient rights to download xml!', 'danger')
        return redirect(url_for('main.index'))

    if from_time:
        try:
            from_time = dateutil.parser.parse(from_time)
        except:
            return 'ERROR: Could not parse from_time argument.', 400

    page_layout = get_page_layout(db_image, only_regions=False, only_annotated=True, from_time=from_time,
                                  active_ignoring=True)
    filename = "{}.xml".format(os.path.splitext(page_layout.id)[0])
    return create_string_response(filename, page_layout.to_pagexml_string(), minetype='text/xml')


@bp.route('/get_alto_xml/<string:image_id>')
@login_required
def get_alto_xml(image_id):
    try:
        db_image = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404

    if not is_granted_acces_for_page(image_id, current_user):
        flash(u'You do not have sufficient rights to download alto!', 'danger')
        return redirect(url_for('main.index'))

    page_layout = get_page_layout(db_image, only_regions=False, only_annotated=False, alto=True)
    filename = "{}.xml".format(os.path.splitext(page_layout.id)[0])
    return create_string_response(filename, page_layout.to_altoxml_string(page_uuid=image_id), minetype='text/xml')


@bp.route('/get_text/<string:image_id>')
@login_required
def get_text(image_id):
    try:
        db_image = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404

    if not is_granted_acces_for_page(image_id, current_user):
        flash(u'You do not have sufficient rights to download text!', 'danger')
        return redirect(url_for('main.index'))


    page_layout = get_page_layout(db_image, only_regions=False, only_annotated=False)
    file_name = "{}.txt".format(os.path.splitext(page_layout.id)[0])
    return create_string_response(file_name, get_page_layout_text(page_layout), minetype='text/plain')


@bp.route('/get_image/<string:image_id>')
@login_required
def get_image(image_id):
    try:
        image_db = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404

    if not is_granted_acces_for_page(image_id, current_user):
        flash(u'You do not have sufficient rights to download image!', 'danger')
        return redirect(url_for('main.index'))

    image_path = os.path.join(current_app.config['UPLOADED_IMAGES_FOLDER'], str(image_db.document_id), image_db.path)
    if not os.path.isfile(image_path):
        print('ERRPR: Could not find image on disk', image_id, image_path)
        raise NotFound()

    return send_file(image_path, as_attachment=True, attachment_filename=image_db.filename)


@bp.route('/download_document_pages/<string:document_id>')
@login_required
def get_document_pages(document_id):
    if not is_granted_acces_for_document(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        document = get_document_by_id(document_id)
        for image in document.images:
            page_layout = get_page_layout(image, only_regions=False, only_annotated=False)
            page_string = page_layout.to_pagexml_string()
            text_string = get_page_layout_text(page_layout)
            d_page = zipfile.ZipInfo("{}.xml".format(os.path.splitext(page_layout.id)[0]))
            d_page.date_time = time.localtime(time.time())[:6]
            d_page.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(d_page, page_string)
            d_text = zipfile.ZipInfo("{}.txt".format(os.path.splitext(page_layout.id)[0]))
            d_text.date_time = time.localtime(time.time())[:6]
            d_text.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(d_text, text_string)
    memory_file.seek(0)
    return send_file(memory_file, attachment_filename='pages.zip', as_attachment=True)


@bp.route('/get_document_annotated_pages/<string:document_id>')
@bp.route('/download_document_annotated_pages/<string:document_id>')
@login_required
def get_document_annotated_pages(document_id):
    if not is_granted_acces_for_document(document_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        document = get_document_by_id(document_id)
        for image in document.images:
            page_layout = get_page_layout(image, only_regions=False, only_annotated=True)
            xml_string = page_layout.to_pagexml_string()
            d_XML = zipfile.ZipInfo("{}.xml".format(os.path.splitext(page_layout.id)[0]))
            d_XML.date_time = time.localtime(time.time())[:6]
            d_XML.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(d_XML, xml_string)
    memory_file.seek(0)
    return send_file(memory_file, attachment_filename='pages.zip', as_attachment=True)


@bp.route('/remove_image/<string:document_id>/<string:image_id>')
@login_required
def remove_image_get(document_id, image_id):
    try:
        db_image = get_image_by_id(image_id)
    except sqlalchemy.exc.StatementError:
        return "Image does not exist.", 404

    if not is_user_owner_or_collaborator(document_id, current_user):
        flash(u'You do not have sufficient rights to get this image!', 'danger')
        return redirect(url_for('main.index'))
    if remove_image(document_id, image_id):
        flash(u'Image successfully removed!', 'success')
    return redirect(url_for('document.upload_images_to_document', document_id=document_id))


@bp.route('/collaborators/<string:document_id>', methods=['GET'])
@login_required
def collaborators_get(document_id):
    if not is_document_owner(document_id, current_user) and not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to edit collaborators!', 'danger')
        return redirect(url_for('main.index'))
    else:
        document = get_document_by_id(document_id)
        collaborators = get_collaborators_select_data(document)
        reg = re.compile('@.*')
        for collaborator in collaborators:
            collaborator.email_an = re.sub(reg, '@...', collaborator.user.email)

        return render_template('document/edit_collaborators.html', document=document, collaborators=collaborators)


@bp.route('/collaborators/<string:document_id>', methods=['POST'])
@login_required
def collaborators_post(document_id):
    collaborators_ids = request.form.getlist('collaborators')
    if not is_document_owner(document_id, current_user) and not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to edit collaborators!', 'danger')
        return redirect(url_for('main.index'))
    else:
        save_collaborators(document_id, collaborators_ids)
        flash(u'Collaborators saved successfully.', 'success')
        return redirect(url_for('document.collaborators_get', document_id=document_id))


@bp.route('/get_keyboard', methods=['GET'])
@login_required
def get_keyboard():
    keyboard_dict = {}

    for keyboard_layout in os.listdir(current_app.config['KEYBOARD_FOLDER']):
        keyboard_layout_name = os.path.splitext(keyboard_layout)[0]
        keyboard_layout_path = os.path.join(current_app.config['KEYBOARD_FOLDER'], keyboard_layout)
        with open(keyboard_layout_path) as f:
            keyboard_dict[keyboard_layout_name] = json.load(f)

    return jsonify(keyboard_dict)


@bp.route('/update_confidences', methods=['POST'])
@login_required
def update_all_confidences():
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    file = request.files['data']
    content = file.read()
    changes = json.loads(content)
    update_confidences(changes)

    return redirect(url_for('document.documents'))


@bp.route('/update_baselines', methods=['POST'])
@login_required
def update_all_baselines():
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    file = request.files['data']
    content = file.read()
    changes = json.loads(content)
    update_baselines(changes)

    return redirect(url_for('document.documents'))


@bp.route('/lines_check', methods=['GET', 'POST'])
@bp.route('/lines_check/<string:document_id>', methods=['GET',  'POST'])
@login_required
def lines_check(document_id=None):
    if is_user_trusted(current_user):
       user_documents = get_all_documents()
    else:
       user_documents = get_user_documents(current_user)

    selected = [False for _ in user_documents]

    if document_id is not None:
        for i, document in enumerate(user_documents):
            if document_id == str(document.id):
                selected[i] = True

    if request.method == 'POST':
        selected = [False for _ in user_documents]
        document_ids = request.form.getlist('documents')
        for i, document in enumerate(user_documents):
            if document_ids != []:
                if str(document.id) in document_ids:
                    selected[i] = True

    return render_template('document/lines_check.html', documents=enumerate(user_documents), selected=selected)


@bp.route('/get_all_lines', methods=['GET'])
@login_required
def get_all_lines():
    show_ignored_lines = request.headers.get('show-ignored-lines')
    document_ids = json.loads(request.headers.get('documents'))
    document_ids = get_documents_with_granted_acces(document_ids, current_user)

    if show_ignored_lines == 'true':
        show_ignored_lines = True
    elif show_ignored_lines == 'false':
        show_ignored_lines = False

    lines = get_sucpect_lines_ids(document_ids, 'all', show_ignored_lines)

    return jsonify(lines)


@bp.route('/get_annotated_lines', methods=['GET'])
@login_required
def get_annotated_lines():
    show_ignored_lines = request.headers.get('show-ignored-lines')
    document_ids = json.loads(request.headers.get('documents'))
    document_ids = get_documents_with_granted_acces(document_ids, current_user)

    if show_ignored_lines == 'true':
        show_ignored_lines = True
    elif show_ignored_lines == 'false':
        show_ignored_lines = False

    lines = get_sucpect_lines_ids(document_ids, 'annotated', show_ignored_lines)

    return jsonify(lines)


@bp.route('/get_not_annotated_lines', methods=['GET'])
@login_required
def get_not_annotated_lines():
    show_ignored_lines = request.headers.get('show-ignored-lines')
    document_ids = json.loads(request.headers.get('documents'))
    document_ids = get_documents_with_granted_acces(document_ids, current_user)

    if show_ignored_lines == 'true':
        show_ignored_lines = True
    elif show_ignored_lines == 'false':
        show_ignored_lines = False

    lines = get_sucpect_lines_ids(document_ids, 'not_annotated', show_ignored_lines)

    return jsonify(lines)


@bp.route('/get_cropped_image/<string:line_id>')
@login_required
def get_cropped_image(line_id):
    if not is_granted_acces_for_line(line_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    image = get_line_image_by_id(line_id)

    return send_file(BytesIO(image), attachment_filename='{}.jpeg' .format(line_id), mimetype='image/jpeg', as_attachment=True)


@bp.route('/compute_scores/<string:document_id>')
@login_required
def compute_scores(document_id):
    if not is_user_trusted(current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    _thread.start_new_thread( compute_scores_of_doc, (document_id, ) )

    flash(u'Computing scores!', 'info')

    return jsonify('success')


@bp.route('/skip_line/<string:line_id>')
@login_required
def skip_line(line_id):
    if not is_granted_acces_for_line(line_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))
    skip_textline(line_id)

    return jsonify({'status': 'success'})


@bp.route('/get_line_info/<string:line_id>')
@login_required
def get_line_info(line_id):
    if not is_granted_acces_for_line(line_id, current_user):
        flash(u'You do not have sufficient rights to this document!', 'danger')
        return redirect(url_for('main.index'))

    lines = get_line(line_id)

    return jsonify(lines)


@bp.route('/search', methods=['GET', 'POST'])
def search_bar():
    query = ""
    lines = []
    if is_user_trusted(current_user):
       user_documents = get_all_documents()
    else:
       user_documents = get_user_documents(current_user)

    selected = [False for _ in user_documents]

    if request.method == 'POST':
        query = request.form['query']
        document_ids = request.form.getlist('documents')
        user_document_ids = []
        for i, document in enumerate(user_documents):
            if document_ids != []:
                if str(document.id) in document_ids:
                    selected[i] = True
                    user_document_ids.append(str(document.id))
            else:
                user_document_ids.append(str(document.id))

        lines = find_textlines(query, current_user, user_document_ids)

    return render_template('document/search_lines.html', query=query, lines=lines, documents=enumerate(user_documents), selected=selected)


