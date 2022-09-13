import sys
import shutil
import os
import re
import time
import requests
import configparser
import subprocess
import traceback
import json
import torch
import logging

from client_helper import join_url
from client_helper import unzip_response_to_dir
from client_helper import get_images
from client_helper import post_result
from client_helper import log_in
from client_helper import add_log_to_request

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
module_logger = logging.getLogger('pero_ocr_web.ocr_client')


def check_and_process_ocr_request(config, session, gpu_mode):

    if gpu_mode and not torch.cuda.is_available():
        return False

    base_url = config['SERVER']['base_url']
    ocr_get_request_route = config['SERVER']['ocr_get_request_route']

    r = session.get(join_url(base_url, ocr_get_request_route))

    request_json = r.json()

    # Nothing to process
    if 'document' not in request_json.keys():
        return False

    host_name = config['HOST']['name']
    ocr_get_config_route = config['SERVER']['ocr_get_config_route']
    ocr_get_baseline_route = config['SERVER']['ocr_get_baseline_route']
    ocr_get_ocr_route = config['SERVER']['ocr_get_ocr_route']
    ocr_get_language_model_route = config['SERVER']['ocr_get_language_model_route']
    document_get_image_route = config['SERVER']['document_get_image_route']
    document_get_xml_regions_route = config['SERVER']['document_get_xml_regions_route']
    document_get_xml_lines_route = config['SERVER']['document_get_xml_lines_route']
    document_get_annotated_xml_lines_route = config['SERVER']['document_get_annotated_xml_lines_route']
    ocr_get_document_annotation_statistics_route = config['SERVER']['ocr_get_document_annotation_statistics_route']
    request_add_log_to_request_route = config['SERVER']['request_add_log_route']
    request_increment_processed_pages_route = config['SERVER']['request_increment_processed_pages_route']
    request_update_last_processed_page_route = config['SERVER']['request_update_last_processed_page_route']
    request_get_request_state_route = config['SERVER']['request_get_request_state_route']
    request_change_request_state_to_in_progress_interrupted_route = config['SERVER']['request_change_request_state_to_in_progress_interrupted_route']
    ocr_post_result_route = config['SERVER']['ocr_post_result_route']
    ocr_change_ocr_request_and_document_state_on_success_route = config['SERVER']['ocr_change_ocr_request_and_document_state_on_success_route']

    request_id = request_json['id']
    baseline_id = request_json['baseline_id']
    ocr_id = request_json['ocr_id']
    language_model_id = request_json['language_model_id']
    document = request_json['document']
    document_id = document['id']
    image_ids = document['images']

    module_logger.info("")
    module_logger.info("REQUEST")
    module_logger.info("##############################################################")
    module_logger.info("REQUEST ID: {}".format(request_id))
    module_logger.info("BASELINE ID: {}".format(baseline_id))
    module_logger.info("OCR ID: {}".format(ocr_id))
    module_logger.info("LANGUAGE MODEL ID: {}".format(language_model_id))
    module_logger.info("IMAGES IDS:")
    for image_id in image_ids:
        module_logger.info(image_id)
    module_logger.info("##############################################################")

    working_dir = os.path.join(config['SETTINGS']['working_directory'], request_id)
    parse_folder_path = config['SETTINGS']['parse_folder_path']
    select_embed_id_path = config['SETTINGS']['select_embed_id_path']

    models_folder = os.path.join(working_dir, "models")
    images_folder = os.path.join(working_dir, "images")
    xmls_folder = os.path.join(working_dir, "xmls")
    output_folder = os.path.join(working_dir, "output")

    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    os.makedirs(working_dir)
    os.makedirs(images_folder)
    os.makedirs(xmls_folder)
    os.makedirs(output_folder)
    os.makedirs(os.path.join(output_folder, "page"))
    os.makedirs(models_folder)

    module_logger.info("")
    module_logger.info("GETTING CONFIG AND MODELS")
    module_logger.info("##############################################################")
    get_config_and_models(session, base_url, ocr_get_config_route, ocr_get_baseline_route, ocr_get_ocr_route,
                          ocr_get_language_model_route, baseline_id, ocr_id, language_model_id, models_folder)
    module_logger.info("##############################################################")

    module_logger.info("")
    module_logger.info("GETTING IMAGES")
    module_logger.info("##############################################################")
    get_images(session, base_url, document_get_image_route, image_ids, images_folder)
    number_of_images = len(os.listdir(images_folder))
    module_logger.info("##############################################################")

    if baseline_id is None:
        response = session.get(join_url(base_url, ocr_get_document_annotation_statistics_route, document_id))
        annotated_count = int(response.json()['annotated_count'])
        min_annotated_lines_for_embed_selection = 50
        module_logger.info("")
        module_logger.info("MIN ANNOTATED LINES FOR EMBED SELECTION: {}".format(min_annotated_lines_for_embed_selection))
        module_logger.info("ANNOTATED LINES: {}".format(annotated_count))
        model_config = configparser.ConfigParser()
        model_config.read(os.path.join(working_dir, "models", "config.ini"))
        with open(os.path.join(working_dir, "models", model_config['OCR']['OCR_JSON']), 'r', encoding='utf8') as f:
            ocr_config = json.load(f)
        module_logger.info("EMBED MODEL: {}".format("embed_id" in ocr_config))
        if annotated_count >= min_annotated_lines_for_embed_selection and "embed_id" in ocr_config:
            annotated_xmls_folder = os.path.join(working_dir, "annotated_xmls")
            os.makedirs(annotated_xmls_folder)
            module_logger.info("")
            module_logger.info("GETTING XMLS WITH ANNOTATED LINES")
            module_logger.info("##############################################################")
            get_xmls(session, base_url, document_get_annotated_xml_lines_route, image_ids,
                     annotated_xmls_folder)
            module_logger.info("##############################################################")
            module_logger.info("")
            module_logger.info("STARTING SELECT EMBED ID: {}".format(select_embed_id_path))
            module_logger.info("##############################################################")
            parse_folder_process = subprocess.Popen(['python', '-u', select_embed_id_path, '-c', "./models/config.ini",
                                                     '-i', images_folder, '-x', annotated_xmls_folder],
                                                    cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log = []
            while True:
                line = parse_folder_process.stdout.readline()
                if not line:
                    break
                line = line.decode("utf-8")
                log.append(line)
                # -1 ommits new line
                module_logger.info(line[:-1])
            parse_folder_process.wait()
            module_logger.info("##############################################################")

        module_logger.info("")
        module_logger.info("GETTING XMLS WITH DETECTED LINES")
        module_logger.info("##############################################################")
        get_xmls(session, base_url, document_get_xml_lines_route, image_ids, xmls_folder)
    else:
        module_logger.info("")
        module_logger.info("GETTING XMLS WITH DETECTED LAYOUT")
        module_logger.info("##############################################################")
        get_xmls(session, base_url, document_get_xml_regions_route, image_ids, xmls_folder)
    module_logger.info("##############################################################")

    module_logger.info("")
    module_logger.info("STARTING PARSE FOLDER: {}".format(parse_folder_path))
    module_logger.info("##############################################################")
    parse_folder_process = subprocess.Popen(['python', '-u', parse_folder_path, '-c', "./models/config.ini"],
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

    add_log_to_request(session, base_url, request_add_log_to_request_route, request_id, log)

    canceled_request = False
    r = session.get(join_url(base_url, request_get_request_state_route, request_id))
    rj = r.json()
    if 'state' not in rj.keys() or rj['state'] == 'CANCELED':
        canceled_request = True

    output_xmls_folder = os.path.join(output_folder, "page")
    output_logits_folder = os.path.join(output_folder, "logits")
    no_output = False
    if os.path.isdir(output_xmls_folder) and os.path.isdir(output_logits_folder):
        number_of_xmls = len(os.listdir(output_xmls_folder))
        number_of_logits = len(os.listdir(output_logits_folder))
    else:
        no_output = True

    if canceled_request:
        module_logger.info("REQUEST WAS CANCELED")
    elif not no_output and \
        parse_folder_process.returncode == 0 and \
        number_of_images == number_of_xmls and \
        number_of_images == number_of_logits:
        data_folders = [output_xmls_folder, output_logits_folder]
        data_types = ["xml", "logits"]
        module_logger.info("")
        module_logger.info("POSTING RESULT TO SERVER")
        module_logger.info("##############################################################")
        module_logger.info("XMLS")
        module_logger.info("\n".join(os.listdir(output_xmls_folder)))
        module_logger.info("")
        module_logger.info("LOGITS")
        module_logger.info("\n".join(os.listdir(output_logits_folder)))
        post_result(session, base_url, ocr_post_result_route, request_update_last_processed_page_route,
                    ocr_change_ocr_request_and_document_state_on_success_route, request_id, image_ids, data_folders,
                    data_types)
        module_logger.info("##############################################################")
        module_logger.info("")
    else:
        module_logger.info("PARSE FOLDER FAILED, SETTING REQUEST TO IN PROGRESS INTERRUPTED")
        session.post(join_url(base_url, request_change_request_state_to_in_progress_interrupted_route, request_id))

    return True


def get_config_and_models(session, base_url, ocr_get_config_route, ocr_get_baseline_route, ocr_get_ocr_route,
                          ocr_get_language_model_route, baseline_id, ocr_id, language_model_id, models_folder):
    baseline_route = "none"
    language_model_route = "none"
    if baseline_id is not None:
        baseline_route = baseline_id
    if language_model_id is not None:
        language_model_route = language_model_id
    config_response = session.get(join_url(base_url, ocr_get_config_route, baseline_route, ocr_id,
                                            language_model_route))
    config_path = os.path.join(models_folder, "config.ini")
    with open(config_path, 'wb') as handle:
        handle.write(config_response.content)
    if baseline_id is not None:
        module_logger.info("GETTING BASELINE: {}".format(baseline_id))
        baseline_response = session.get(join_url(base_url, ocr_get_baseline_route, baseline_id))
        unzip_model_response(baseline_response, models_folder)
    module_logger.info("GETTING OCR: {}".format(ocr_id))
    ocr_response = session.get(join_url(base_url, ocr_get_ocr_route, ocr_id))
    unzip_model_response(ocr_response, models_folder)
    if language_model_id is not None:
        module_logger.info("GETTING LANGUAGE MODEL: {}".format(language_model_id))
        language_model_response = session.get(join_url(base_url, ocr_get_language_model_route, language_model_id))
        unzip_model_response(language_model_response, models_folder)


def get_xmls(session, base_url, get_xml_route, image_ids, xmls_folder):
    number_of_images = len(image_ids)
    for i, image_id in enumerate(image_ids):
        module_logger.info("{}/{} GETTING XML: {}".format(i + 1, number_of_images, image_id))
        xml_response = session.get(join_url(base_url, get_xml_route, image_id))
        path = os.path.join(xmls_folder, "{}.xml".format(image_id))
        if xml_response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(xml_response.content)


def unzip_model_response(response, models_folder):
    model_type_folder_name = re.findall("filename=(.+)", response.headers["Content-Disposition"])[0].split('.')[0]
    model_type_folder_name = os.path.join(models_folder, model_type_folder_name)
    os.makedirs(model_type_folder_name)
    unzip_response_to_dir(response, model_type_folder_name)


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
                    if check_and_process_ocr_request(config, session, False):
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

