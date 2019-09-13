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


base_url = 'http://127.0.0.1:2000'
route = '/ocr/get_request'

images_folder = "/home/ikohut/projects_new/pero_ocr_web_new/ocr_client/images"
xmls_folder = "/home/ikohut/projects_new/pero_ocr_web_new/ocr_client/xmls"
output_folder = "/home/ikohut/projects_new/pero_ocr_web_new/ocr_client/output"
logits_folder = "/home/ikohut/projects_new/pero_ocr_web_new/ocr_client/output/logits"
pages_folder = "/home/ikohut/projects_new/pero_ocr_web_new/ocr_client/output/page"
xmls_confidences_folder = "/home/ikohut/projects_new/pero_ocr_web_new/ocr_client/xmls_confidences_folder"

config_path = "/home/ikohut/projects_new/pero_ocr_web_new/ocr_client/config.ini"
ocr_json = "/home/ikohut/projects_new/pero_ocr_web_new/ocr_client/models/ocr/IMPACT_2019-03-18/ocr_engine.json"


def get_post_route(request_id):
    return '/ocr/post_result/{}'.format(request_id)


def check_and_process_request():
    request_id, document = get_and_save_document_images_and_xmls(images_folder, xmls_folder, base_url, route)

    if document:
        document_id = document['id']

        print(request_id)
        print(document)


        detect_document_baselines(images_folder, xmls_folder, output_folder, document_id, config_path)
        
        xmls_confidences_folder_doc = os.path.join(xmls_confidences_folder, document_id)
        if os.path.exists(xmls_confidences_folder_doc):
            shutil.rmtree(xmls_confidences_folder_doc)
        os.makedirs(xmls_confidences_folder_doc)
        with open(ocr_json, 'r',  encoding='utf8') as f:
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
    '''
        # CALL LAYOUT ANALYSIS
        data = make_post_request_data(document)  # Make post request
        requests.post('{}{}'.format(base_url, get_post_route(request_id)), files=data)  # Send post request
        return True
    '''
    return False


def main():
    while True:
        print('Check request')
        if check_and_process_request():
            print('Request completed')
            break  # Only for development
        else:
            print('No request')
            time.sleep(10)  # No request so sleep for some time


if __name__ == '__main__':
    sys.exit(main())
