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
from client_helper import log_in
from client_helper import add_log_to_request


def check_and_process_layout_request(config):
    with requests.Session() as session:
        if not log_in(session, config['SETTINGS']['login'], config['SETTINGS']['password'], config['SERVER']['base_url'],
                      config['SERVER']['authentification'], config['SERVER']['login_page']):
            return False

        base_url = config['SERVER']['base_url']
        layout_analysis_get_request_route = config['SERVER']['layout_analysis_get_request_route']
        layout_analysis_change_layout_request_and_document_state_on_success_route = config['SERVER']['layout_analysis_change_layout_request_and_document_state_on_success_route']
        layout_analysis_change_layout_request_to_fail_and_document_state_to_new_route = config['SERVER']['layout_analysis_change_layout_request_to_fail_and_document_state_to_new_route']

        try:
            r = session.get(join_url(base_url, layout_analysis_get_request_route))
        except:
            return False

        request_json = r.json()

        if 'document' in request_json.keys():
            layout_analysis_get_layout_detector_route = config['SERVER']['layout_analysis_get_layout_detector_route']
            document_get_image_route = config['SERVER']['document_get_image_route']
            main_add_log_to_request_route = config['SERVER']['main_add_log_to_request_route']
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
            get_layout_detector(session, base_url, layout_analysis_get_layout_detector_route, layout_detector_id,
                                layout_detector_folder)

            print()
            print("GETTING IMAGES")
            print("##############################################################")
            get_images(session, base_url, document_get_image_route, image_ids, images_folder)
            number_of_images = len(os.listdir(images_folder))
            print("##############################################################")

            print()
            print("STARTING PARSE FOLDER:", parse_folder_path)
            print("##############################################################")
            parse_folder_process = subprocess.Popen(['python', parse_folder_path, '-c', "./layout_detector/config.ini"],
                                                    cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log = []
            while True:
                line = parse_folder_process.stdout.readline()
                if not line:
                    break
                line = line.decode("utf-8")
                log.append(line)
                print(line, end='')
            parse_folder_process.wait()
            print("##############################################################")

            output_xmls_folder = os.path.join(output_folder, "page")
            no_output = False
            if os.path.isdir(output_xmls_folder):
                number_of_xmls = len(os.listdir(output_xmls_folder))
            else:
                no_output = True

            add_log_to_request(session, base_url, main_add_log_to_request_route, request_id, log)

            if not no_output and parse_folder_process.returncode == 0 and number_of_images == number_of_xmls:
                data_folders = [output_xmls_folder]
                data_types = ["xml"]
                print()
                print("POSTING RESULT TO SERVER")
                print("##############################################################")
                print("XMLS")
                print("\n".join(os.listdir(output_xmls_folder)))
                post_result(session, base_url, layout_analysis_post_result_route,
                            layout_analysis_change_layout_request_and_document_state_on_success_route, request_id,
                            image_ids, data_folders, data_types)
                print("##############################################################")
                print()
            else:
                print("PARSE FOLDER FAILED, SETTING REQUEST TO FAILED")
                session.post(join_url(base_url, layout_analysis_change_layout_request_to_fail_and_document_state_to_new_route, request_id))
            return True

        return False


def get_layout_detector(session, base_url, layout_analysis_get_layout_detector_route, layout_detector_id, layout_detector_folder):
    layout_detector_response = session.get(join_url(base_url, layout_analysis_get_layout_detector_route,
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
