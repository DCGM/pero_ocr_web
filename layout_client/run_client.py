import requests
import sys
import os
import time
import configparser
import shutil
import subprocess
import traceback
import torch
import logging

from client_helper import join_url
from client_helper import unzip_response_to_dir
from client_helper import get_images
from client_helper import post_result
from client_helper import log_in
from client_helper import add_log_to_request


logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
module_logger = logging.getLogger('pero_ocr_web.layout_client')


def check_and_process_layout_request(config, session, gpu_mode):

    if gpu_mode and not torch.cuda.is_available():
        return False

    base_url = config['SERVER']['base_url']
    layout_analysis_get_request_route = config['SERVER']['layout_analysis_get_request_route']
    layout_analysis_change_layout_request_and_document_state_on_success_route = config['SERVER']['layout_analysis_change_layout_request_and_document_state_on_success_route']

    r = session.get(join_url(base_url, layout_analysis_get_request_route))

    request_json = r.json()

    if 'document' not in request_json.keys():
        return False
    host_name = config['HOST']['name']
    layout_analysis_get_layout_detector_route = config['SERVER']['layout_analysis_get_layout_detector_route']
    document_get_image_route = config['SERVER']['document_get_image_route']
    request_add_log_route = config['SERVER']['request_add_log_route']
    request_increment_processed_pages_route = config['SERVER']['request_increment_processed_pages_route']
    request_update_last_processed_page_route = config['SERVER']['request_update_last_processed_page_route']
    request_get_request_state_route = config['SERVER']['request_get_request_state_route']
    request_change_request_state_to_in_progress_interrupted_route = config['SERVER']['request_change_request_state_to_in_progress_interrupted_route']
    layout_analysis_post_result_route = config['SERVER']['layout_analysis_post_result_route']

    request_id = request_json['id']
    layout_detector_id = request_json['layout_detector_id']
    document = request_json['document']
    image_ids = document['images']

    module_logger.info("")
    module_logger.info("REQUEST")
    module_logger.info("##############################################################")
    module_logger.info("REQUEST ID: {}".format(request_id))
    module_logger.info("LAYOUT DETECTOR ID: {}".format(layout_detector_id))
    module_logger.info("IMAGES IDS:")
    for image_id in image_ids:
        module_logger.info(image_id)
    module_logger.info("##############################################################")

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

    module_logger.info("")
    module_logger.info("GETTING LAYOUT DETECTOR: {}".format(layout_detector_id))
    get_layout_detector(session, base_url, layout_analysis_get_layout_detector_route, layout_detector_id,
                        layout_detector_folder)

    module_logger.info("")
    module_logger.info("GETTING IMAGES")
    module_logger.info("##############################################################")
    get_images(session, base_url, document_get_image_route, image_ids, images_folder)
    number_of_images = len(os.listdir(images_folder))
    module_logger.info("##############################################################")

    module_logger.info("")
    module_logger.info("STARTING PARSE FOLDER: {}".format(parse_folder_path))
    module_logger.info("##############################################################")
    parse_folder_process = subprocess.Popen(['python', '-u', parse_folder_path, '-c', "./layout_detector/config.ini"],
                                            cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = []
    log.append("HOST NAME: {}\n\n".format(host_name))
    while True:
        line = parse_folder_process.stdout.readline()
        if not line:
            break
        line = line.decode("utf-8")
        if line.startswith("DONE "):
            session.post(join_url(base_url, request_increment_processed_pages_route, request_id))
        log.append(line)
        # -1 ommits new line
        module_logger.info(line[:-1])
    parse_folder_process.wait()
    module_logger.info("##############################################################")

    add_log_to_request(session, base_url, request_add_log_route, request_id, log)

    canceled_request = False
    r = session.get(join_url(base_url, request_get_request_state_route, request_id))
    rj = r.json()
    if 'state' not in rj.keys() or rj['state'] == 'CANCELED':
        canceled_request = True

    output_xmls_folder = os.path.join(output_folder, "page")
    no_output = False
    if os.path.isdir(output_xmls_folder):
        number_of_xmls = len(os.listdir(output_xmls_folder))
    else:
        no_output = True

    if canceled_request:
        module_logger.info("REQUEST WAS CANCELED")
    elif not no_output and parse_folder_process.returncode == 0 and number_of_images == number_of_xmls:
        data_folders = [output_xmls_folder]
        data_types = ["xml"]
        module_logger.info("")
        module_logger.info("POSTING RESULT TO SERVER")
        module_logger.info("##############################################################")
        module_logger.info("XMLS")
        for xml in sorted(os.listdir(output_xmls_folder)):
            module_logger.info(xml)
        module_logger.info("")
        post_result(session, base_url, layout_analysis_post_result_route, request_update_last_processed_page_route,
                    layout_analysis_change_layout_request_and_document_state_on_success_route, request_id,
                    image_ids, data_folders, data_types)
        module_logger.info("##############################################################")
        module_logger.info("")
    else:
        module_logger.info("PARSE FOLDER FAILED, SETTING REQUEST TO IN PROGRESS INTERRUPTED")
        session.post(join_url(base_url, request_change_request_state_to_in_progress_interrupted_route, request_id))

    return True


def get_layout_detector(session, base_url, layout_analysis_get_layout_detector_route, layout_detector_id, layout_detector_folder):
    layout_detector_response = session.get(join_url(base_url, layout_analysis_get_layout_detector_route,
                                                    layout_detector_id))
    unzip_response_to_dir(layout_detector_response, layout_detector_folder)


def main():
    config = configparser.ConfigParser()
    config.read("config.ini")
    timeout = 4
    while True:
        try:
            with requests.Session() as session:
                if not log_in(session, config['SETTINGS']['login'], config['SETTINGS']['password'],
                              config['SERVER']['base_url'],
                              config['SERVER']['authentification'], config['SERVER']['login_page']):
                    module_logger.error('Unable to log into server')
                    time.sleep(timeout)
                    continue

                while True:
                    module_logger.info("CHECK REQUEST")
                    if check_and_process_layout_request(config, session, False):
                        module_logger.info("REQUEST COMPLETED")
                    else:
                        module_logger.info("NO REQUEST")
                        time.sleep(timeout)
        except:
            module_logger.error('ERROR exception')
            traceback.print_exc()
            time.sleep(timeout)


if __name__ == '__main__':
    sys.exit(main())

