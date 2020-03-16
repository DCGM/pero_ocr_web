import sys
import shutil
import os
import time
import requests
import configparser
import subprocess

from client_helper import join_url
from client_helper import get_and_save_request_document_images_and_xmls, get_config_and_models
from client_helper import make_post_request_data


def check_and_process_request(config):
    base_url = config['SERVER']['base_url']
    request_route = config['SERVER']['ocr_get_request_route']
    ocr_get_config_route = config['SERVER']['ocr_get_config_route']
    ocr_get_baseline_route = config['SERVER']['ocr_get_baseline_route']
    ocr_get_ocr_route = config['SERVER']['ocr_get_ocr_route']
    ocr_get_language_model_route = config['SERVER']['ocr_get_language_model_route']
    ocr_post_result_route = config['SERVER']['ocr_post_result_route']

    r = requests.get(join_url(base_url, request_route))
    request_json = r.json()

    if 'document' in request_json.keys():
        request_id = request_json['id']
        baseline_id = request_json['baseline_id']
        ocr_id = request_json['ocr_id']
        language_model_id = request_json['language_model_id']
        document = request_json['document']

        working_dir = os.path.join(config['SETTINGS']['working_directory'], request_id)
        parse_folder_path = config['SETTINGS']['parse_folder_path']

        images_folder = os.path.join(working_dir, "images")
        xmls_folder = os.path.join(working_dir, "xmls")
        output_folder = os.path.join(working_dir, "output")
        models_folder = os.path.join(working_dir, "models")
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

        get_and_save_request_document_images_and_xmls(base_url, images_folder, xmls_folder, request_json)

        print(request_id)
        print(document)
        parse_folder_process = subprocess.Popen(['python', parse_folder_path, '-c', './models/config.ini'], cwd=working_dir)
        parse_folder_process.wait()

        output_xmls_folder = os.path.join(output_folder, "page")
        output_logits_folder = os.path.join(output_folder, "logits")
        data = make_post_request_data([output_xmls_folder, output_logits_folder], document, ["xml", "logits"])
        requests.post(join_url(base_url, ocr_post_result_route, request_id), files=data)

        return True
    return False


def main():
    config = configparser.ConfigParser()
    config.read("config.ini")
    while True:
        print('Check request')
        if check_and_process_request(config):
            print('Request completed')
        else:
            print('No request')
            time.sleep(2)  # No request so sleep for some time


if __name__ == '__main__':
    sys.exit(main())
