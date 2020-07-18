import os
import glob
import json
import shutil
import requests
import argparse
import subprocess
import configparser
import numpy as np

from client_helper import join_url, log_in, check_request
from pero_ocr.document_ocr.layout import PageLayout

def get_args():
    """
    method for parsing of arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", action="store", dest="config", help="config path")
    parser.add_argument("-d", "--document-id", action="store", dest="document_id", help="document id")
    parser.add_argument("-l", "--login", action="store", dest="login", help="username")
    parser.add_argument("-p", "--password", action="store", dest="password", help="password")

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

    if not os.path.isdir(os.path.join(config['SETTINGS']['working_directory'], "other")):
        os.mkdir(os.path.join(config['SETTINGS']['working_directory'], "other"))

    make_empty_folder(config, "xml")
    make_empty_folder(config, "img")

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


def update_baselines(config):
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
        parse_folder_process = subprocess.Popen(['python', config['SETTINGS']['line_fixer_path'],
                                                 '-i', os.path.join(config['SETTINGS']['working_directory'], "img"),
                                                 '-x', os.path.join(config['SETTINGS']['working_directory'], "xml"),
                                                 '-o', config['SETTINGS']['ocr'],
                                                 '--output', os.path.join(config['SETTINGS']['working_directory'], "other"),
                                                 '--output-file', os.path.join(config['SETTINGS']['working_directory'], "changes.json")],
                                                 cwd=config['SETTINGS']['working_directory'])

        parse_folder_process.wait()
        print("SUCCESFUL")
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
                    remove = np.random.randint(1, 4, size=1)[0]
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


def main():
    args = get_args()

    config = configparser.ConfigParser()
    if args.config is not None:
        config.read(args.config)
    else:
        config.read('config_baselines.ini')

    if args.document_id is not None:
        config["SETTINGS"]['document_id'] = args.document_id
    if args.login is not None:
        config["SETTINGS"]['login'] = args.login
    if args.password is not None:
        config["SETTINGS"]['password'] = args.password

    if config["SETTINGS"]['update_type'] == 'confidences':
        if update_confidences(config):
            print("REQUEST COMPLETED")
        else:
            print("REQUEST FAILED")
    elif config["SETTINGS"]['update_type'] == 'baselines':
        if update_baselines(config):
            print("REQUEST COMPLETED")
        else:
            print("REQUEST FAILED")
    elif config["SETTINGS"]['update_type'] == 'restore_baselines':
        if restore_baselines_from_xmls(config):
            print("REQUEST COMPLETED")
        else:
            print("REQUEST FAILED")
    elif config["SETTINGS"]['update_type'] == 'corrupt_baselines':
        if corrupt_baselines(config):
            print("REQUEST COMPLETED")
        else:
            print("REQUEST FAILED")

if __name__ == '__main__':
    main()
