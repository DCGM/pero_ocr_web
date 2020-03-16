import requests
import os
from io import open as image_open
import zipfile
import re


def get_document_folder_path(folder, document_id):
    folder_path = os.path.join(folder, document_id)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path


def get_and_save_images(folder, base_url, images):
    for image in images:
        image_request = requests.get("{}/document/get_image/{}".format(base_url, image))
        file_type = image_request.headers['content-type'].split('/')[-1]
        path = os.path.join(folder, '{}.{}'.format(image, file_type))
        if image_request.status_code == 200:
            with image_open(path, 'wb') as f:
                f.write(image_request.content)


def get_and_save_xmls(folder, base_url, document_processed, images):
    for image in images:
        if document_processed:
            xml_request = requests.get("{}/document/get_page_xml/{}".format(base_url, image))
        else:
            xml_request = requests.get("{}/document/get_region_xml/{}".format(base_url, image))
        path = os.path.join(folder, '{}.xml'.format(image))
        print("Saving", path)
        if xml_request.status_code == 200:
            with open(path, 'wb') as f:
                f.write(xml_request.content)


def get_and_save_document_images(folder, base_url, route):
    r = requests. get('{}{}'.format(base_url, route))
    return_json = r.json()
    if 'document' in return_json.keys():
        document = return_json['document']
        get_and_save_images(folder, base_url, document['images'])
        return return_json['id'], document
    return None, None


def get_and_save_request_document_images(base_url, folder, request_json):
    if 'document' in request_json.keys():
        document = request_json['document']
        get_and_save_images(folder, base_url, document['images'])


def get_and_save_document_xmls(folder, base_url, route):
    r = requests. get('{}{}'.format(base_url, route))
    return_json = r.json()
    if 'document' in return_json.keys():
        document = return_json['document']
        get_and_save_xmls(folder, base_url, document['images'])
        return return_json['id'], document
    return None, None


def get_and_save_document_images_and_xmls(images_folder, xmls_folder, base_url, route):
    r = requests. get('{}{}'.format(base_url, route))
    request_json = r.json()
    if 'document' in request_json.keys():
        document = request_json['document']
        get_and_save_images(images_folder, base_url, document['images'])
        get_and_save_xmls(xmls_folder, base_url, document['processed'], document['images'])
        return request_json['id'], request_json['parse_folder_config_path'], request_json['ocr_json_path'], document
    return None, None, None, None


def get_and_save_request_document_images_and_xmls(base_url, images_folder, xmls_folder, request_json):
    if 'document' in request_json.keys():
        document = request_json['document']
        get_and_save_images(images_folder, base_url, document['images'])
        get_and_save_xmls(xmls_folder, base_url, document['processed'], document['images'])


def make_post_request_data(data_folders, document, data_types):
    data = dict()
    images = document['images']
    for image in images:
        for data_folder, data_type in zip(data_folders, data_types):
            data[image] = open(os.path.join(data_folder, "{}.{}".format(image, data_type)), 'rb')
    print('Data:', data)
    return data


def get_layout_detector(base_url, route, layout_detector_id, models_folder):
    r = requests.get('{}{}{}'.format(base_url, route, layout_detector_id))
    tmp_zip_path = os.path.join(models_folder, "tmp.zip")
    with open(tmp_zip_path, 'wb') as handle:
        handle.write(r.content)
    with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
        zip_ref.extractall(models_folder)
    os.remove(tmp_zip_path)


def get_config_and_models(base_url, ocr_get_config_route, ocr_get_baseline_route, ocr_get_ocr_route,
                          ocr_get_language_model_route, baseline_id, ocr_id, language_model_id, models_folder):
    config_response = requests.get('{}{}{}/{}/{}'.format(base_url, ocr_get_config_route, baseline_id, ocr_id,
                                                         language_model_id))
    config_path = os.path.join(models_folder, "config.ini")
    with open(config_path, 'wb') as handle:
        handle.write(config_response.content)
    baseline_response = requests.get('{}{}{}'.format(base_url, ocr_get_baseline_route, baseline_id))
    unzip_response(baseline_response, models_folder)
    ocr_response = requests.get('{}{}{}'.format(base_url, ocr_get_ocr_route, ocr_id))
    unzip_response(ocr_response, models_folder)
    language_model_response = requests.get('{}{}{}'.format(base_url, ocr_get_language_model_route, language_model_id))
    unzip_response(language_model_response, models_folder)


def unzip_response(response, models_folder):
    model_type_folder_name = re.findall("filename=(.+)", response.headers["Content-Disposition"])[0].split('.')[0]
    model_type_folder_name = os.path.join(models_folder, model_type_folder_name)
    os.makedirs(model_type_folder_name)
    tmp_zip_path = os.path.join(model_type_folder_name, "tmp.zip")
    with open(tmp_zip_path, 'wb') as handle:
        handle.write(response.content)
    with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
        zip_ref.extractall(model_type_folder_name)
    os.remove(tmp_zip_path)


def join_url(*paths):
    final_paths = []
    first_path = paths[0].strip()
    if first_path[-1] == '/':
        first_path = first_path[:-1]
    final_paths.append(first_path)
    for path in paths[1:]:
        final_paths.append(path.strip().strip('/'))
    return '/'.join(final_paths)





