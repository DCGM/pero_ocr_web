import sys
sys.path.insert(1, '../')
from client_helper import get_and_save_document_images_and_xmls
from baseline_detection import detect_document_baselines

import os
import time


base_url = 'http://127.0.0.1:5000'
route = '/ocr/get_request'

images_folder = "/home/ikohut/projects_new/pero_ocr_web/ocr_client/images"
xmls_folder = "/home/ikohut/projects_new/pero_ocr_web/ocr_client/xmls"
output_folder = "/home/ikohut/projects_new/pero_ocr_web/ocr_client/output"
logits_folder = "/home/ikohut/projects_new/pero_ocr_web/ocr_client/output/logits"
pages_folder = "/home/ikohut/projects_new/pero_ocr_web/ocr_client/output/page"

config_path = "/home/ikohut/projects_new/pero_ocr_web/ocr_client/config.ini"
ocr_json = "/home/ikohut/projects_new/pero_ocr_web/ocr_client/models/ocr/IMPACT_2019-03-18/ocr_engine.json"


def get_post_route(document_id):
    return '/ocr/{}/post_result'.format(document_id)


def check_and_process_request():
    request_id, document = get_and_save_document_images_and_xmls(images_folder, xmls_folder, base_url, route)


    if document:
        print(request_id)
        print(document)

        detect_document_baselines(images_folder, xmls_folder, output_folder, config_path)
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
