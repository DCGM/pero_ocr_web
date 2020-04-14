import sys
import shutil
import os
import re
import time
import requests
import configparser
import subprocess

from client_helper import join_url
from client_helper import unzip_response_to_dir
from client_helper import get_images
from client_helper import post_result
from client_helper import log_in


def check_and_process_ocr_request(config):
    with requests.Session() as session:
        if not log_in(config, session, verbose=False):
            return False

        base_url = config['SERVER']['base_url']
        ocr_get_request_route = config['SERVER']['ocr_get_request_route']

        try:
            r = requests.get(join_url(base_url, ocr_get_request_route))
        except:
            return False

        request_json = r.json()

        if 'document' in request_json.keys():
            ocr_get_config_route = config['SERVER']['ocr_get_config_route']
            ocr_get_baseline_route = config['SERVER']['ocr_get_baseline_route']
            ocr_get_ocr_route = config['SERVER']['ocr_get_ocr_route']
            ocr_get_language_model_route = config['SERVER']['ocr_get_language_model_route']
            document_get_image_route = config['SERVER']['document_get_image_route']
            document_get_xml_regions_route = config['SERVER']['document_get_xml_regions_route']
            document_get_xml_lines_route = config['SERVER']['document_get_xml_lines_route']
            ocr_post_result_route = config['SERVER']['ocr_post_result_route']

            request_id = request_json['id']
            baseline_id = request_json['baseline_id']
            ocr_id = request_json['ocr_id']
            language_model_id = request_json['language_model_id']
            document = request_json['document']
            image_ids = document['images']

            print()
            print("REQUEST")
            print("##############################################################")
            print("REQUEST ID:", request_id)
            print("BASELINE ID:", baseline_id)
            print("OCR ID:", ocr_id)
            print("LANGUAGE MODEL ID:", language_model_id)
            print("IMAGES IDS:")
            print("\n".join(image_ids))
            print("##############################################################")

            working_dir = os.path.join(config['SETTINGS']['working_directory'], request_id)
            parse_folder_path = config['SETTINGS']['parse_folder_path']

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

            print()
            print("GETTING CONFIG AND MODELS")
            print("##############################################################")
            get_config_and_models(base_url, ocr_get_config_route, ocr_get_baseline_route, ocr_get_ocr_route,
                                  ocr_get_language_model_route, baseline_id, ocr_id, language_model_id, models_folder)
            print("##############################################################")

            print()
            print("GETTING IMAGES")
            print("##############################################################")
            get_images(base_url, document_get_image_route, image_ids, images_folder)
            print("##############################################################")

            print()
            if baseline_id is None:
                print("GETTING XMLS WITH DETECTED LINES")
                print("##############################################################")
                get_xmls(base_url, document_get_xml_lines_route, image_ids, xmls_folder)
            else:
                print("GETTING XMLS WITH DETECTED LAYOUT")
                print("##############################################################")
                get_xmls(base_url, document_get_xml_regions_route, image_ids, xmls_folder)
            print("##############################################################")

            print()
            print("STARTING PARSE FOLDER:", parse_folder_path)
            print("##############################################################")
            parse_folder_process = subprocess.Popen(['python', parse_folder_path, '-c', "./models/config.ini"],
                                                    cwd=working_dir)
            parse_folder_process.wait()
            print("##############################################################")

            output_xmls_folder = os.path.join(output_folder, "page")
            output_logits_folder = os.path.join(output_folder, "logits")
            data_folders = [output_xmls_folder, output_logits_folder]
            data_types = ["xml", "logits"]
            print()
            print("POSTING RESULT TO SERVER")
            print("##############################################################")
            print("XMLS")
            print("\n".join(os.listdir(output_xmls_folder)))
            print()
            print("LOGITS")
            print("\n".join(os.listdir(output_logits_folder)))
            post_result(base_url, ocr_post_result_route, request_id, image_ids, data_folders, data_types)
            print("##############################################################")
            print()
            return True

        return False


def get_config_and_models(base_url, ocr_get_config_route, ocr_get_baseline_route, ocr_get_ocr_route,
                          ocr_get_language_model_route, baseline_id, ocr_id, language_model_id, models_folder):
    baseline_route = "none"
    language_model_route = "none"
    if baseline_id is not None:
        baseline_route = baseline_id
    if language_model_id is not None:
        language_model_route = language_model_id
    config_response = requests.get(join_url(base_url, ocr_get_config_route, baseline_route, ocr_id,
                                            language_model_route))
    config_path = os.path.join(models_folder, "config.ini")
    with open(config_path, 'wb') as handle:
        handle.write(config_response.content)
    if baseline_id is not None:
        print("GETTING BASELINE:", baseline_id)
        baseline_response = requests.get(join_url(base_url, ocr_get_baseline_route, baseline_id))
        unzip_model_response(baseline_response, models_folder)
    print("GETTING OCR:", ocr_id)
    ocr_response = requests.get(join_url(base_url, ocr_get_ocr_route, ocr_id))
    unzip_model_response(ocr_response, models_folder)
    if language_model_id is not None:
        print("GETTING LANGUAGE MODEL:", language_model_id)
        language_model_response = requests.get(join_url(base_url, ocr_get_language_model_route, language_model_id))
        unzip_model_response(language_model_response, models_folder)


def get_xmls(base_url, get_xml_route, image_ids, xmls_folder):
    number_of_images = len(image_ids)
    for i, image_id in enumerate(image_ids):
        print("{}/{} GETTING XML:".format(i + 1, number_of_images), image_id)
        xml_response = requests.get(join_url(base_url, get_xml_route, image_id))
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
    while True:
        print("CHECK REQUEST")
        if check_and_process_ocr_request(config):
            print("REQUEST COMPLETED")
        else:
            print("NO REQUEST")
            time.sleep(2)


if __name__ == '__main__':
    sys.exit(main())
