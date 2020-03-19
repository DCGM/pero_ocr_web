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


def check_and_process_layout_request(config):
    base_url = config['SERVER']['base_url']
    layout_analysis_get_request_route = config['SERVER']['layout_analysis_get_request_route']

    try:
        r = requests.get(join_url(base_url, layout_analysis_get_request_route))
    except:
        return False

    request_json = r.json()

    if 'document' in request_json.keys():
        layout_analysis_get_layout_detector_route = config['SERVER']['layout_analysis_get_layout_detector_route']
        document_get_image_route = config['SERVER']['document_get_image_route']
        layout_analysis_post_result_route = config['SERVER']['layout_analysis_post_result_route']

        request_id = request_json['id']
        layout_detector_id = request_json['layout_detector_id']
        document = request_json['document']
        image_ids = document['images']

        print()
        print("REQUEST")
        print("##############################################################")
        print("REQUEST ID:", request_id)
        print("LAYOUT DETECTOR ID:", layout_detector_id)
        print("IMAGES IDS:")
        print("\n".join(image_ids))
        print("##############################################################")

        working_dir = os.path.join(config['SETTINGS']['working_directory'], request_id)
        parse_folder_path = config['SETTINGS']['parse_folder_path']

        images_folder = os.path.join(working_dir, "images")
        output_folder = os.path.join(working_dir, "output")
        layout_detector_folder = os.path.join(working_dir, "layout_detector")

        if os.path.exists(working_dir):
            shutil.rmtree(working_dir)
        os.makedirs(working_dir)
        os.makedirs(images_folder)
        os.makedirs(output_folder)
        os.makedirs(layout_detector_folder)

        print()
        print("GETTING LAYOUT DETECTOR:", layout_detector_id)
        get_layout_detector(base_url, layout_analysis_get_layout_detector_route, layout_detector_id,
                            layout_detector_folder)

        print()
        print("GETTING IMAGES")
        print("##############################################################")
        get_images(base_url, document_get_image_route, image_ids, images_folder)
        print("##############################################################")

        print()
        print("STARTING PARSE FOLDER:", parse_folder_path)
        print("##############################################################")
        parse_folder_process = subprocess.Popen(['python', parse_folder_path, '-c', "./layout_detector/config.ini"],
                                                cwd=working_dir)
        parse_folder_process.wait()
        print("##############################################################")

        output_xmls_folder = os.path.join(output_folder, "page")
        data_folders = [output_xmls_folder]
        data_types = ["xml"]
        print()
        print("POSTING RESULT TO SERVER")
        print("##############################################################")
        print("XMLS")
        print("\n".join(os.listdir(output_xmls_folder)))
        post_result(base_url, layout_analysis_post_result_route, request_id, image_ids, data_folders, data_types)
        print("##############################################################")
        print()
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
        print("CHECK REQUEST")
        if check_and_process_layout_request(config):
            print("REQUEST COMPLETED")
        else:
            print("NO REQUEST")
            time.sleep(2)


if __name__ == '__main__':
    sys.exit(main())
