import requests
import sys
import os
import time
import configparser
import shutil
import subprocess

from client_helper import join_url
from client_helper import unzip_response_to_dir
from client_helper import get_images
from client_helper import post_result


def check_and_process_request(config):
    base_url = config['SERVER']['base_url']
    layout_analysis_get_request_route = config['SERVER']['layout_analysis_get_request_route']
    layout_analysis_get_layout_detector_route = config['SERVER']['layout_analysis_get_layout_detector_route']
    document_get_image_route = config['SERVER']['document_get_image_route']
    layout_analysis_post_result_route = config['SERVER']['layout_analysis_post_result_route']

    r = requests.get(join_url(base_url, layout_analysis_get_request_route))
    request_json = r.json()

    if 'document' in request_json.keys():
        request_id = request_json['id']
        layout_detector_id = request_json['layout_detector_id']
        document = request_json['document']
        image_ids = document['images']

        working_dir = os.path.join(config['SETTINGS']['working_directory'], request_id)
        parse_folder_path = config['SETTINGS']['parse_folder_path']

        images_folder = os.path.join(working_dir, "images")
        output_folder = os.path.join(working_dir, "output")
        layout_detector_folder = os.path.join(working_dir, "layout_detector")
        config_path = os.path.join(layout_detector_folder, "config.ini")

        if os.path.exists(working_dir):
            shutil.rmtree(working_dir)
        os.makedirs(working_dir)
        os.makedirs(images_folder)
        os.makedirs(output_folder)
        os.makedirs(layout_detector_folder)

        get_layout_detector(base_url, layout_analysis_get_layout_detector_route, layout_detector_id,
                            layout_detector_folder)
        get_images(base_url, document_get_image_route, image_ids, images_folder)

        print(request_id)
        print(document)
        parse_folder_process = subprocess.Popen(['python', parse_folder_path, '-c', config_path],
                                                cwd=working_dir)
        parse_folder_process.wait()

        output_xmls_folder = os.path.join(output_folder, "page")
        data_folders = [output_xmls_folder]
        data_types = ["xml"]
        post_result(base_url, layout_analysis_post_result_route, request_id, image_ids, data_folders, data_types)

        return True

    return False


def get_layout_detector(base_url, layout_analysis_get_layout_detector_route, layout_detector_id, layout_detector_folder):
    layout_detector_response = requests.get(join_url(base_url, layout_analysis_get_layout_detector_route,
                                                     layout_detector_id))
    unzip_response_to_dir(layout_detector_response, layout_detector_folder)


def main():
    config = configparser.ConfigParser()
    config.read("config.ini")
    while True:
        print('Check request')
        if check_and_process_request(config):
            print('Request completed')
        else:
            print('No request')
            time.sleep(2)


if __name__ == '__main__':
    sys.exit(main())
