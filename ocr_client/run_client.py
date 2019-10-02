import sys
sys.path.insert(1, '../')
import shutil
import json

from client_helper import get_and_save_document_images_and_xmls
from client_helper import make_post_request_data
from baseline_detection import detect_document_baselines
from process_logits import save_xml_with_confidences

import os
import time
import requests
import configparser


def get_post_route(request_id):
    return '/ocr/post_result/{}'.format(request_id)


def check_and_process_request(config):
    base_url = config['SERVER']['base_url']
    route = config['SERVER']['ocr_get_request_route']

    images_folder = config['OCR']['images_folder']
    xmls_folder = config['OCR']['xmls_folder']
    output_folder = config['OCR']['output_folder']
    xmls_confidences_folder = config['OCR']['xmls_confidences_folder']

    models_path = config['PARSE_FOLDER']['models_path']
    parse_folder_configs_path = config['PARSE_FOLDER']['parse_folder_configs_path']
    parse_folder_path = config['PARSE_FOLDER']['parse_folder_path']

    request_id, parse_folder_config_path, ocr_json_path, document = get_and_save_document_images_and_xmls(images_folder, xmls_folder, base_url, route)

    if document:
        document_id = document['id']

        print(request_id)
        print(document)

        detect_document_baselines(parse_folder_path, images_folder, xmls_folder, output_folder, document_id, parse_folder_configs_path, parse_folder_config_path)
        
        xmls_confidences_folder_doc = os.path.join(xmls_confidences_folder, document_id)
        if os.path.exists(xmls_confidences_folder_doc):
            shutil.rmtree(xmls_confidences_folder_doc)
        os.makedirs(xmls_confidences_folder_doc)
        with open(os.path.join(models_path, "ocr", ocr_json_path), 'r',  encoding='utf8') as f:
            ocr_config = json.load(f)
        chars = ocr_config['characters']
        output_xmls_folder = os.path.join(output_folder, document_id, 'page')
        output_logits_folder = os.path.join(output_folder, document_id, 'logits')
        for xml in os.listdir(output_xmls_folder):
            file_name, _ = os.path.splitext(xml)
            xml_path = os.path.join(output_xmls_folder, xml)
            logits_path = os.path.join(output_logits_folder, "{}.logits".format(file_name))
            save_xml_with_confidences(xml_path, logits_path, chars, xmls_confidences_folder_doc)

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
            break  # Only for development
        else:
            print('No request')
            time.sleep(10)  # No request so sleep for some time


if __name__ == '__main__':
    sys.exit(main())
