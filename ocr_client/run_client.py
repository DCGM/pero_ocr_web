import sys
sys.path.insert(1, '../')
import shutil
import json

from client_helper import get_and_save_request_document_images_and_xmls, get_models
from client_helper import make_post_request_data
from process_logits import save_xml_with_confidences

import os
import time
import requests
import configparser
import subprocess

def get_post_route(request_id):
    return '/ocr/post_result/{}'.format(request_id)


def check_and_process_request(config):
    base_url = config['SERVER']['base_url']
    request_route = config['SERVER']['ocr_get_request_route']
    models_route = config['SERVER']['document_get_models_route']

    r = requests.get('{}{}'.format(base_url, request_route))
    request_json = r.json()

    if 'document' in request_json.keys():
        request_id = request_json['id']
        ocr_name = request_json['ocr_name']
        document = request_json['document']

        working_dir = os.path.join(config['SETTINGS']['working_directory'], request_id)
        parse_folder_path = config['SETTINGS']['parse_folder_path']

        images_folder = os.path.join(working_dir, 'images')
        xmls_folder = os.path.join(working_dir, 'xmls')
        output_folder = os.path.join(working_dir, 'output')
        xmls_confidences_folder = os.path.join(working_dir, 'xmls_confidences_folder')
        models_folder = os.path.join(working_dir, 'models')
        config_path = os.path.join(models_folder, 'config.ini')

        if os.path.exists(working_dir):
            shutil.rmtree(working_dir)
        os.makedirs(working_dir)
        os.makedirs(images_folder)
        os.makedirs(xmls_folder)
        os.makedirs(output_folder)
        os.makedirs(os.path.join(output_folder, 'page'))
        os.makedirs(xmls_confidences_folder)
        os.makedirs(models_folder)

        get_models(base_url, models_route, ocr_name, models_folder)

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

        with open(os.path.join(models_folder, 'ocr', 'ocr_engine.json'), 'r',  encoding='utf8') as f:
            ocr_config = json.load(f)
        chars = ocr_config['characters']
        output_xmls_folder = os.path.join(output_folder, 'page')
        output_logits_folder = os.path.join(output_folder, 'logits')
        for xml in os.listdir(output_xmls_folder):
            file_name, _ = os.path.splitext(xml)
            xml_path = os.path.join(output_xmls_folder, xml)
            logits_path = os.path.join(output_logits_folder, "{}.logits".format(file_name))
            save_xml_with_confidences(xml_path, logits_path, chars, xmls_confidences_folder)

        data = make_post_request_data(xmls_confidences_folder, document)
        requests.post('{}{}'.format(base_url, get_post_route(request_id)), files=data)

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
            time.sleep(10)  # No request so sleep for some time


if __name__ == '__main__':
    sys.exit(main())
