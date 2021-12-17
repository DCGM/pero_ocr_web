import os
from flask import request, abort, jsonify
from app.ocr_api import bp
from functools import wraps
from app.db.general import get_user_by_email
from app.document.general import create_document, get_document_by_id, save_image, get_document_images, get_page_layout, \
    get_page_layout_text, create_string_response, check_and_remove_document, save_collaborators


def require_user_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_string = request.headers.get('api-key')
        if not api_string:
            abort(401, f'Missing api KEY as header "api-key".')
        try:
            name, key = api_string.split('_')
        except:
            abort(401, f'API key {api_string} is not valid.')

        name = 'API-ONLY-USER_' + name
        db_user = get_user_by_email(name)
        if db_user and db_user.password == key:
            return f(db_user, *args, **kwargs)
        else:
            abort(401, f'API key {api_string} is not valid.')
    return decorated


# curl  $SERVER_URL/ocr_api/new_document/test_document/someone@somewhere.com,someone@somewhere.com' --request POST --header "api-key: $API_KEY"
@bp.route('/new_document/<string:document_name>/<string:user_list>', methods=['POST'])
@require_user_api_key
def new_document(db_user, document_name, user_list):
    db_document = create_document(document_name, db_user)

    assigned_collaborators = []
    unknown_collaborators = []
    collaborator_ids = []
    for collaborator_name in user_list.split(','):
        db_collaborator = get_user_by_email(collaborator_name)
        if db_collaborator:
            collaborator_ids.append(db_collaborator.id)
            assigned_collaborators.append(collaborator_name)
        else:
            unknown_collaborators.append(collaborator_name)

    if collaborator_ids:
        save_collaborators(db_document.id, collaborator_ids)

    result = {
        'document_id': db_document.id,
        'assigned_collaborators': assigned_collaborators,
        'unknown_collaborators': unknown_collaborators
    }
    return jsonify(result), 200


# curl $SERVER_URL/ocr_api/upload_image/cf8473d0-1a20-4f8e-9f2f-ce70dd5e4d08 --request POST --header "api-key: $API_KEY" -F file=@00000003.xml
@bp.route('/upload_image/<string:document_id>', methods=['POST'])
@require_user_api_key
def upload_image(db_user, document_id):
    db_document = get_document_by_id(document_id)
    if not db_document or db_document.user_id != db_user.id:
        abort(401, f'The api KEY does not own the document.')

    f = request.files.get('file')
    if not f:
        return 'File was not attached.', 409

    status = save_image(f, document_id)
    if status == '':
        return '', 200
    return status, 409


# curl $SERVER_URL/ocr_api/list_documents --request GET --header "api-key: $API_KEY"
@bp.route('/list_documents', methods=['GET'])
@require_user_api_key
def list_documents(db_user):
    db_documents = db_user.documents.filter_by(deleted=False).all()
    results = [{'name': d.name, 'id': d.id, 'created': d.created_date} for d in db_documents]
    return jsonify(results), 200


# curl $SERVER_URL/ocr_api/document_images/cf8473d0-1a20-4f8e-9f2f-ce70dd5e4d08 --request GET --header "api-key: $API_KEY"
@bp.route('/document_images/<string:document_id>', methods=['GET'])
@require_user_api_key
def document_images(db_user, document_id):
    db_document = get_document_by_id(document_id)
    if not db_document or db_document.user_id != db_user.id:
        abort(401, f'The api KEY does not own the document.')

    image_ids = [i.id for i in get_document_images(db_document)]

    results = {
        'document_id': document_id,
        'images': [image_ids]
    }
    return jsonify(results), 200


# curl  $SERVER_URL/ocr_api/get_results/text/cf8473d0-1a20-4f8e-9f2f-ce70dd5e4d08/8e4939a3-e295-4017-9df2-9084103c17ad --request GET --header "api-key: $API_KEY"
# curl  $SERVER_URL/ocr_api/get_results/page/cf8473d0-1a20-4f8e-9f2f-ce70dd5e4d08/8e4939a3-e295-4017-9df2-9084103c17ad --request GET --header "api-key: $API_KEY"
# curl  $SERVER_URL/ocr_api/get_results/alto/cf8473d0-1a20-4f8e-9f2f-ce70dd5e4d08/8e4939a3-e295-4017-9df2-9084103c17ad --request GET --header "api-key: $API_KEY"
@bp.route('/get_results/<string:output_type>/<string:document_id>/<string:image_id>', methods=['GET'])
@require_user_api_key
def get_results(db_user, output_type, document_id, image_id):
    db_document = get_document_by_id(document_id)
    if not db_document or db_document.user_id != db_user.id:
        abort(401, f'The api KEY does not own the document.')

    db_image = db_document.images.filter_by(id=image_id, deleted=False).first()
    if not db_image:
        abort(404, f'Image {image_id} does not exist in document {document_id}.')

    try:
        page_layout = get_page_layout(db_image, alto=(output_type.lower() == 'alto'))
    except FileNotFoundError:
        abort(409, f'Image {image_id} from document {document_id} has not yet been processed with OCR.')

    if output_type.lower() == 'text':
        file_sufix = 'txt'
        mime_type = 'text/plain'
        output_string = get_page_layout_text(page_layout)
    elif output_type.lower() == 'page':
        file_sufix = 'xml'
        mime_type = 'text/xml'
        output_string = page_layout.to_pagexml_string(validate_id=True)
    elif output_type.lower() == 'alto':
        file_sufix = 'xml'
        mime_type = 'text/xml'
        output_string = page_layout.to_altoxml_string(page_uuid=image_id)
    else:
        abort(404, f'The requested format {output_type} is not supported. Possible formats are text, page, alto.')

    file_name = f"{format(os.path.splitext(page_layout.id)[0])}.{file_sufix}"
    return create_string_response(file_name, output_string, minetype=mime_type)


# curl  $SERVER_URL/ocr_api/delete_document/cf8473d0-1a20-4f8e-9f2f-ce70dd5e4d08 --request POST --header "api-key: $API_KEY"
@bp.route('/delete_document/<string:document_id>', methods=['POST'])
@require_user_api_key
def delete_document(db_user, document_id):
    if check_and_remove_document(document_id, db_user):
        return '', 200
    else:
        return f'The api-key does not own document {document_id}', 401
