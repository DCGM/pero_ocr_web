import sys
import shutil
import os
import re
import time
import requests
import configparser
import subprocess

from client_helper import join_url
from client_helper import unzip_response_to_dir
from client_helper import get_images
from client_helper import post_result


def check_and_process_ocr_request(config):
    base_url = config['SERVER']['base_url']
    ocr_get_request_route = config['SERVER']['ocr_get_request_route']
    ocr_get_config_route = config['SERVER']['ocr_get_config_route']
    ocr_get_baseline_route = config['SERVER']['ocr_get_baseline_route']
    ocr_get_ocr_route = config['SERVER']['ocr_get_ocr_route']
    ocr_get_language_model_route = config['SERVER']['ocr_get_language_model_route']
    document_get_image_route = config['SERVER']['document_get_image_route']
    document_get_xml_regions_route = config['SERVER']['document_get_xml_regions_route']
    document_get_xml_lines_route = config['SERVER']['document_get_xml_lines_route']
    ocr_post_result_route = config['SERVER']['ocr_post_result_route']

    r = requests.get(join_url(base_url, ocr_get_request_route))
    request_json = r.json()

    if 'document' in request_json.keys():
        request_id = request_json['id']
        baseline_id = request_json['baseline_id']
        ocr_id = request_json['ocr_id']
        language_model_id = request_json['language_model_id']
        document = request_json['document']
        image_ids = document['images']

        working_dir = os.path.join(config['SETTINGS']['working_directory'], request_id)
        parse_folder_path = config['SETTINGS']['parse_folder_path']

        models_folder = os.path.join(working_dir, "models")
        config_path = os.path.join(models_folder, "config.ini")
        images_folder = os.path.join(working_dir, "images")
        xmls_folder = os.path.join(working_dir, "xmls")
        output_folder = os.path.join(working_dir, "output")
        config_path = os.path.join(models_folder, "config.ini")

        if os.path.exists(working_dir):
            shutil.rmtree(working_dir)
        os.makedirs(working_dir)
        os.makedirs(images_folder)
        os.makedirs(xmls_folder)
        os.makedirs(output_folder)
        os.makedirs(os.path.join(output_folder, "page"))
        os.makedirs(models_folder)

        get_config_and_models(base_url, ocr_get_config_route, ocr_get_baseline_route, ocr_get_ocr_route,
                              ocr_get_language_model_route, baseline_id, ocr_id, language_model_id, models_folder)

        if document['processed']:
            config = configparser.ConfigParser()
            config.optionxform = str
            config.read(config_path)
            config['PAGE_PARSER']['RUN_LINE_PARSER'] = "no"
            with open(config_path, 'w') as f:
                config.write(f)

        get_images(base_url, document_get_image_route, image_ids, images_folder)
        if document['processed']:
            get_xmls(base_url, document_get_xml_lines_route, image_ids, xmls_folder)
        else:
            get_xmls(base_url, document_get_xml_regions_route, image_ids, xmls_folder)

        print(request_id)
        print(document)
        parse_folder_process = subprocess.Popen(['python', parse_folder_path, '-c', config_path],
                                                cwd=working_dir)
        parse_folder_process.wait()

        output_xmls_folder = os.path.join(output_folder, "page")
        output_logits_folder = os.path.join(output_folder, "logits")
        data_folders = [output_xmls_folder, output_logits_folder]
        data_types = ["xml", "logits"]
        post_result(base_url, ocr_post_result_route, request_id, image_ids, data_folders, data_types)

        return True

    return False


def get_config_and_models(base_url, ocr_get_config_route, ocr_get_baseline_route, ocr_get_ocr_route,
                          ocr_get_language_model_route, baseline_id, ocr_id, language_model_id, models_folder):
    config_response = requests.get(join_url(base_url, ocr_get_config_route, baseline_id, ocr_id, language_model_id))
    config_path = os.path.join(models_folder, "config.ini")
    with open(config_path, 'wb') as handle:
        handle.write(config_response.content)
    baseline_response = requests.get(join_url(base_url, ocr_get_baseline_route, baseline_id))
    unzip_model_response(baseline_response, models_folder)
    ocr_response = requests.get(join_url(base_url, ocr_get_ocr_route, ocr_id))
    unzip_model_response(ocr_response, models_folder)
    language_model_response = requests.get(join_url(base_url, ocr_get_language_model_route, language_model_id))
    unzip_model_response(language_model_response, models_folder)


def get_xmls(base_url, get_xml_route, image_ids, xmls_folder):
    for image_id in image_ids:
        xml_response = requests.get(join_url(base_url, get_xml_route, image_id))
        path = os.path.join(xmls_folder, "{}.xml".format(image_id))
        if xml_response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(xml_response.content)


def unzip_model_response(response, models_folder):
    model_type_folder_name = re.findall("filename=(.+)", response.headers["Content-Disposition"])[0].split('.')[0]
    model_type_folder_name = os.path.join(models_folder, model_type_folder_name)
    os.makedirs(model_type_folder_name)
    unzip_response_to_dir(response, model_type_folder_name)


def main():
    config = configparser.ConfigParser()
    config.read("config.ini")
    while True:
        print('Check request')
        if check_and_process_ocr_request(config):
            print('Request completed')
        else:
            print('No request')
            time.sleep(2)


if __name__ == '__main__':
    sys.exit(main())
