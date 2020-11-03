import os
import cv2
import glob
import json
import shutil
import requests
import argparse
import subprocess
import configparser
import numpy as np
import traceback

from client_helper import join_url, log_in, check_request
from pero_ocr.document_ocr.layout import PageLayout
from pero_ocr.document_ocr.page_parser import PageParser


def get_args():
    """
    method for parsing of arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", required=True, help="Config path.")
    parser.add_argument("--parse-folder-config", help="Config for parse_folder.py used when changing heights.")
    parser.add_argument("-d", "--document-id", help="Process document with this ID.")
    parser.add_argument("-l", "--login", help="Username of superuser on remote server.")
    parser.add_argument("-p", "--password", help="Password of superuser on remote server.")
    parser.add_argument("-u", "--upload-result", action='store_true', help="Upload results to server.")

    args = parser.parse_args()

    return args


def remove_files(config, folder_name):
    list_of_files = os.listdir(os.path.join(config['SETTINGS']['working_directory'], folder_name))
    for _, file in enumerate(list_of_files):
        os.remove(os.path.join(config['SETTINGS']['working_directory'], folder_name, file))


def make_empty_folder(config, folder_name):
    if not os.path.isdir(os.path.join(config['SETTINGS']['working_directory'], folder_name)):
        os.mkdir(os.path.join(config['SETTINGS']['working_directory'], folder_name))
    else:
        remove_files(config, folder_name)


def create_work_folders(config):
    if not os.path.isdir(config['SETTINGS']['working_directory']):
        os.mkdir(config['SETTINGS']['working_directory'])

    make_empty_folder(config, "xml")
    make_empty_folder(config, "img")
    make_empty_folder(config, "other")

    print("SUCCESFUL")


def download_xmls(session, base_url, type, working_directory, page_uuids):
    for _, uuid in enumerate(page_uuids):
        r = session.get(join_url(base_url, type, uuid), stream=True)
        if r.status_code == 200:
            with open(os.path.join(working_directory, "xml/{}.xml".format(uuid)),
                      'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print("ERROR {} OCCURED DURING XML {} DOWNLOAD.".format(r.status_code, uuid))
            return False

    print("SUCCESFUL")
    return True


def download_images(session, base_url, download_images, working_directory, page_uuids):
    for _, uuid in enumerate(page_uuids):
        r = session.get(join_url(base_url, download_images, uuid), stream=True)
        if r.status_code == 200:
            with open(os.path.join(working_directory, "img/{}.jpg".format(uuid)),
                      'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print("ERROR {} OCCURED DURING IMAGE {} DOWNLOAD.".format(r.status_code, uuid))
            return False

    print("SUCCESFUL")
    return True


def send_data(session, working_directory, base_url, update_all_confidences, file="changes.json"):
    with open(os.path.join(working_directory, file), "rb") as f:
        data = f.read()

    r = session.post(join_url(base_url, update_all_confidences),
                     files={'data': ('data.json', data, 'text/plain')})

    if not check_request(r):
        print("FAILED")
        return False
    else:
        print("SUCCESFUL")
        return True


def get_document_ids(session, base_url, document_ids, document_id):
    r = session.get(join_url(base_url, document_ids, document_id), stream=True)
    if r.status_code == 200:
        print("SUCCESFUL")
        return True, json.loads(r.text)
    else:
        print("FAILED")
        return False, None


def update_confidences(config):
    with requests.Session() as session:
        print()
        print("LOGGING IN")
        print("##############################################################")
        if not log_in(session, config['SETTINGS']['login'], config['SETTINGS']['password'], config['SERVER']['base_url'],
                      config['SERVER']['authentification'], config['SERVER']['login_page']):
            return False
        print("##############################################################")

        print()
        print("CREATING WORK FOLDERS")
        print("##############################################################")
        create_work_folders(config)
        print("##############################################################")

        print()
        print("GETTING PAGES IDS")
        print("##############################################################")
        done, page_uuids = get_document_ids(session, config['SERVER']['base_url'], config['SERVER']['document_ids'], config['SETTINGS']['document_id'])
        if not done:
            return False
        print("##############################################################")

        print()
        print("DOWNLOADING XMLS")
        print("##############################################################")
        if not download_xmls(session, config['SERVER']['base_url'], config['SERVER'][config['SETTINGS']['type']], config['SETTINGS']['working_directory'], page_uuids):
            return False
        print("##############################################################")

        print()
        print("DOWNLOADING IMAGES")
        print("##############################################################")
        if not download_images(session, config['SERVER']['base_url'], config['SERVER']['download_images'], config['SETTINGS']['working_directory'], page_uuids):
            return False
        print("##############################################################")

        print()
        print("PARSE FOLDER PROCESS")
        print("##############################################################")
        parse_folder_process = subprocess.Popen(['python', config['SETTINGS']['parse_folder_path'],
                                                 '-c', config['SETTINGS']['parse_folder_config_path']],
                                                 cwd=config['SETTINGS']['working_directory'])

        parse_folder_process.wait()
        print("SUCCESFUL")
        print("##############################################################")

        print()
        print("DATASET REPLACE PROCESS")
        print("##############################################################")
        replace_process = subprocess.Popen(['python', config['SETTINGS']['replace_script_path'],
                                            '--substig', config['SETTINGS']['substitution_file_path'],
                                            '--xml', os.path.join(config['SETTINGS']['working_directory'], "xml"),
                                            '--logits', os.path.join(config['SETTINGS']['working_directory'], "output_logits"),
                                            '--images', os.path.join(config['SETTINGS']['working_directory'], "img"),
                                            '--output-img', os.path.join(config['SETTINGS']['working_directory'], "other"),
                                            '--output-xml', os.path.join(config['SETTINGS']['working_directory'], "other"),
                                            '--output-file', os.path.join(config['SETTINGS']['working_directory'], "changes.json"),
                                            '--threshold', config['SETTINGS']['threshold'],
                                            '--max-confidence', config['SETTINGS']['max_confidence'],
                                            '--computation-type', config['SETTINGS']['computation_type']],
                                            cwd=config['SETTINGS']['working_directory'])

        replace_process.wait()
        print("SUCCESFUL")
        print("##############################################################")

        print()
        print("SENDING DATA TO SERVER")
        print("##############################################################")
        if not send_data(session, config['SETTINGS']['working_directory'], config['SERVER']['base_url'], config['SERVER']['update_path']):
            return False
        print("##############################################################")

        return True


def compute_baselines(config):
    with requests.Session() as session:
        print()
        print("LOGGING IN")
        print("##############################################################")
        if not log_in(session, config['SETTINGS']['login'], config['SETTINGS']['password'], config['SERVER']['base_url'],
                      config['SERVER']['authentification'], config['SERVER']['login_page']):
            return False
        print("##############################################################")

        print()
        print("CREATING WORK FOLDERS")
        print("##############################################################")
        create_work_folders(config)
        print("##############################################################")

        print()
        print("GETTING PAGES IDS")
        print("##############################################################")
        done, page_uuids = get_document_ids(session, config['SERVER']['base_url'], config['SERVER']['document_ids'], config['SETTINGS']['document_id'])
        if not done:
            return False
        print("##############################################################")

        print()
        print("DOWNLOADING XMLS")
        print("##############################################################")
        if not download_xmls(session, config['SERVER']['base_url'], config['SERVER'][config['SETTINGS']['type']], config['SETTINGS']['working_directory'], page_uuids):
            return False
        print("##############################################################")

        print()
        print("DOWNLOADING IMAGES")
        print("##############################################################")
        if not download_images(session, config['SERVER']['base_url'], config['SERVER']['download_images'], config['SETTINGS']['working_directory'], page_uuids):
            return False
        print("##############################################################")

        print()
        print("LINE FIXER PROCESS")
        print("##############################################################")
        line_fixer_process = subprocess.Popen(['python', config['SETTINGS']['line_fixer_path'],
                                                 '-m', config['SETTINGS']['extension_mode'],
                                                 '-i', os.path.join(config['SETTINGS']['working_directory'], "img"),
                                                 '-x', os.path.join(config['SETTINGS']['working_directory'], "xml"),
                                                 '-o', config['SETTINGS']['ocr'],
                                                 '--output', os.path.join(config['SETTINGS']['working_directory'], "other"),
                                                 '--output-file', os.path.join(config['SETTINGS']['working_directory'], "changes.json"),
                                                 '--extend-by', config['SETTINGS']['automatic_extension_by'],
                                                 '--ocr-start-offset', config['SETTINGS']['ocr_start_offset'],
                                                 '--ocr-end-offset', config['SETTINGS']['ocr_end_offset']],
                                                 cwd=config['SETTINGS']['working_directory'])

        line_fixer_process.wait()
        print("SUCCESFUL")
        print("##############################################################")

        print()
        print("PARSE FOLDER PROCESS")
        print("##############################################################")
        parse_folder_process = subprocess.Popen(['python', config['SETTINGS']['parse_folder_path'],
                                                 '-c', config['SETTINGS']['parse_folder_config_path']],
                                                 cwd=config['SETTINGS']['working_directory'])

        parse_folder_process.wait()
        print("SUCCESFUL")
        print("##############################################################")

        return True


def upload_baselines(config):
    with requests.Session() as session:
        print()
        print("LOGGING IN")
        print("##############################################################")
        if not log_in(session, config['SETTINGS']['login'], config['SETTINGS']['password'],
                        config['SERVER']['base_url'],
                      config['SERVER']['authentification'], config['SERVER']['login_page']):
            return False
        print("##############################################################")

        print()
        print("SENDING DATA TO SERVER")
        print("##############################################################")
        if not send_data(session, config['SETTINGS']['working_directory'], config['SERVER']['base_url'], config['SERVER']['update_path']):
            return False
        print("##############################################################")

        return True


def restore_baselines_from_xmls(config):
    with requests.Session() as session:
        print()
        print("LOGGING IN")
        print("##############################################################")
        if not log_in(session, config['SETTINGS']['login'], config['SETTINGS']['password'], config['SERVER']['base_url'],
                      config['SERVER']['authentification'], config['SERVER']['login_page']):
            return False
        print("##############################################################")

        print()
        print("RESTORING ORIGINAL BASELINES")
        print("##############################################################")
        xmls = os.listdir(os.path.join(config['SETTINGS']['working_directory'], "xml"))
        correction = dict()
        for xml in xmls:
            page_layout = PageLayout(file=os.path.join(config['SETTINGS']['working_directory'], "xml", xml))
            for line in page_layout.lines_iterator():
                correction[line.id] = [np.int_(line.baseline).tolist(), np.int_(line.heights).tolist()]

        with open(os.path.join(config['SETTINGS']['working_directory'], "correction.json"), 'w') as handle:
            json.dump(correction, handle)
        print("SUCCESFUL")
        print("##############################################################")

        print()
        print("SENDING DATA TO SERVER")
        print("##############################################################")
        if not send_data(session, config['SETTINGS']['working_directory'], config['SERVER']['base_url'], config['SERVER']['update_path'], file='correction.json'):
            return False
        print("##############################################################")

        return True


def corrupt_baselines(config):
    with requests.Session() as session:
        print()
        print("LOGGING IN")
        print("##############################################################")
        if not log_in(session, config['SETTINGS']['login'], config['SETTINGS']['password'], config['SERVER']['base_url'],
                      config['SERVER']['authentification'], config['SERVER']['login_page']):
            return False
        print("##############################################################")

        print()
        print("CREATING WORK FOLDERS")
        print("##############################################################")
        create_work_folders(config)
        print("##############################################################")

        print()
        print("GETTING PAGES IDS")
        print("##############################################################")
        done, page_uuids = get_document_ids(session, config['SERVER']['base_url'], config['SERVER']['document_ids'],
                                            config['SETTINGS']['document_id'])
        if not done:
            return False
        print("##############################################################")

        print()
        print("DOWNLOADING XMLS")
        print("##############################################################")
        if not download_xmls(session, config['SERVER']['base_url'], config['SERVER'][config['SETTINGS']['type']],
                             config['SETTINGS']['working_directory'], page_uuids):
            return False
        print("##############################################################")

        print()
        print("CORRUPTING BASELINES")
        print("##############################################################")
        xmls = os.listdir(os.path.join(config['SETTINGS']['working_directory'], "xml"))
        print(xmls)
        corruption = dict()
        for xml in xmls:
            page_layout = PageLayout(file=os.path.join(config['SETTINGS']['working_directory'], "xml", xml))
            for line in page_layout.lines_iterator():
                if np.random.randint(2, size=1)[0]:
                    remove = 2#np.random.randint(1, 4, size=1)[0]
                    baseline = np.int_(line.baseline).tolist()
                    if remove < len(baseline):
                        if np.random.randint(2, size=1)[0]:
                            corruption[line.id] = [baseline[remove:], np.int_(line.heights).tolist()]
                        else:
                            corruption[line.id] = [baseline[:-remove], np.int_(line.heights).tolist()]
        with open(os.path.join(config['SETTINGS']['working_directory'], "corruption.json"), 'w') as handle:
            json.dump(corruption, handle)
        print("SUCCESFUL")
        print("##############################################################")

        print()
        print("SENDING DATA TO SERVER")
        print("##############################################################")
        if not send_data(session, config['SETTINGS']['working_directory'], config['SERVER']['base_url'], config['SERVER']['update_path'], file='corruption.json'):
            return False
        print("##############################################################")

        return True


def update_heights(config):
    with requests.Session() as session:
        print()
        print("LOGGING IN")
        print("##############################################################")
        if not log_in(session, config['SETTINGS']['login'], config['SETTINGS']['password'], config['SERVER']['base_url'],
                      config['SERVER']['authentification'], config['SERVER']['login_page']):
            return False
        print("##############################################################")

        print()
        print("CREATING WORK FOLDERS")
        print("##############################################################")
        create_work_folders(config)
        print("##############################################################")

        print()
        print("GETTING PAGES IDS")
        print("##############################################################")
        done, page_uuids = get_document_ids(session, config['SERVER']['base_url'], config['SERVER']['document_ids'], config['SETTINGS']['document_id'])
        if not done:
            return False
        print("##############################################################")

        print()
        print("DOWNLOADING XMLS")
        print("##############################################################")
        if not download_xmls(session, config['SERVER']['base_url'], config['SERVER'][config['SETTINGS']['type']], config['SETTINGS']['working_directory'], page_uuids):
            return False
        print("##############################################################")

        print()
        print("DOWNLOADING IMAGES")
        print("##############################################################")
        if not download_images(session, config['SERVER']['base_url'], config['SERVER']['download_images'], config['SETTINGS']['working_directory'], page_uuids):
            return False
        print("##############################################################")

        print()
        print("FIXING HEIGHTS")
        print("##############################################################")
        page_parser = PageParser(config)
        xmls = os.listdir(os.path.join(config['SETTINGS']['working_directory'], "xml"))
        height_fix = dict()
        for xml in xmls:
            page_layout = PageLayout(file=os.path.join(config['SETTINGS']['working_directory'], "xml", xml))
            image = cv2.imread(os.path.join(config['SETTINGS']['working_directory'], "img", xml[:-4]+'.jpg'))
            page_layout = page_parser.process_page(image, page_layout)
            for line in page_layout.lines_iterator():
                baseline = np.int_(line.baseline).tolist()
                height_fix[line.id] = [baseline, np.int_(line.heights).tolist()]

        with open(os.path.join(config['SETTINGS']['working_directory'], "height_fix.json"), 'w') as handle:
            json.dump(height_fix, handle)
        print("SUCCESFUL")
        print("##############################################################")

        print()
        print("SENDING DATA TO SERVER")
        print("##############################################################")
        if not send_data(session, config['SETTINGS']['working_directory'], config['SERVER']['base_url'], config['SERVER']['update_path'], file='height_fix.json'):
            return False
        print("##############################################################")

        return True


def download_data(config):
    pass

def upload_data(config):
    pass


def main():
    args = get_args()

    if not args.parse_folder_config:
        args.parse_folder_config = args.config

    if not os.path.isfile(args.config):
        print(f'Error: Config file does not exist "{args.config}"')
        exit(-1)
    if not os.path.isfile(args.parse_folder_config):
        print(f'Error: Config file does not exist "{args.parse_folder_config}"')
        exit(-1)

    config = configparser.ConfigParser()
    config.read(args.config)

    if args.document_id:
        config["SETTINGS"]['document_id'] = args.document_id
    if args.login:
        config["SETTINGS"]['login'] = args.login
    if args.password:
        config["SETTINGS"]['password'] = args.password


    download_data(config)

    update_type = config["SETTINGS"]['update_type']
    print(f'STARTING PROCESSING "{update_type}"')
    try:
        if update_type == 'confidences':
            update_confidences(config)
        elif update_type == 'baselines_compute':
            compute_baselines(config)
        elif update_type == 'restore_baselines':
            restore_baselines_from_xmls(config)
        elif update_type == 'corrupt_baselines':
            corrupt_baselines(config)
        elif update_type == 'update_heights':
            update_heights(config)
        else:
            print(f'ERROR: Unknow update_type "{update_type}"')
            exit(-1)
    except:
        print(f'ERROR: Processing failed with exception.')
        raise

    upload_data(config)


if __name__ == '__main__':
    main()
