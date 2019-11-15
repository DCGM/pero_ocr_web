import requests
import sys
import os
import time
import configparser
import shutil
import subprocess
sys.path.insert(1, '../')
from client_helper import get_and_save_request_document_images, get_models
from client_helper import make_post_request_data


def get_post_route(document_id):
    return '/layout_analysis/post_result/{}'.format(document_id)


def check_and_process_request(config):
    base_url = config['SERVER']['base_url']
    request_route = config['SERVER']['layout_analysis_get_request_route']
    models_route = config['SERVER']['layout_analysis_get_models_route']

    r = requests.get('{}{}'.format(base_url, request_route))
    request_json = r.json()

    if 'document' in request_json.keys():
        request_id = request_json['id']
        layout_detector_name = request_json['layout_detector_name']
        document = request_json['document']

        working_dir = os.path.join(config['SETTINGS']['working_directory'], request_id)
        detect_layout_path = config['SETTINGS']['detect_layout_path']

        images_folder = os.path.join(working_dir, 'images')
        output_folder = os.path.join(working_dir, 'output')
        models_folder = os.path.join(working_dir, 'models')
        config_path = os.path.join(models_folder, 'config.ini')

        if os.path.exists(working_dir):
            shutil.rmtree(working_dir)
        os.makedirs(working_dir)
        os.makedirs(images_folder)
        os.makedirs(output_folder)
        os.makedirs(models_folder)

        get_models(base_url, models_route, layout_detector_name, models_folder)

        get_and_save_request_document_images(base_url, images_folder, request_json)

        print(request_id)
        print(document)
        detect_layout_process = subprocess.Popen(['python', detect_layout_path, '-c', config_path], cwd=working_dir)
        detect_layout_process.wait()

        data = make_post_request_data(output_folder, document)
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
