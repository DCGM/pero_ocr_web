import os
import json
import shutil
import requests
import argparse
import subprocess
import configparser

from client_helper import join_url, log_in, check_request


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


def download_xmls(session, config, page_uuids):
    for _, uuid in enumerate(page_uuids):
        r = session.get(join_url(config['SERVER']['base_url'], config['SERVER'][config['SETTINGS']['type']], uuid), stream=True)
        if r.status_code == 200:
            with open(os.path.join(config['SETTINGS']['working_directory'], "xml/{}.xml".format(uuid)),
                      'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print("ERROR {} OCCURED DURING XML {} DOWNLOAD.".format(r.status_code, uuid))
            return False

    print("SUCCESFUL")
    return True


def download_images(session, config, page_uuids):
    for _, uuid in enumerate(page_uuids):
        r = session.get(join_url(config['SERVER']['base_url'], config['SERVER']['download_images'], uuid), stream=True)
        if r.status_code == 200:
            with open(os.path.join(config['SETTINGS']['working_directory'], "img/{}.jpg".format(uuid)),
                      'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print("ERROR {} OCCURED DURING IMAGE {} DOWNLOAD.".format(r.status_code, uuid))
            return False

    print("SUCCESFUL")
    return True


def send_data(session, config):
    with open(os.path.join(config['SETTINGS']['working_directory'], "changes.json"), "rb") as f:
        data = f.read()

    r = session.post(join_url(config['SERVER']['base_url'], config['SERVER']['update_all_confidences']),
                     files={'data': ('data.json', data, 'text/plain')})

    if not check_request(r):
        return False
    else:
        return True


def get_document_ids(session, config):
    r = session.get(join_url(config['SERVER']['base_url'], config['SERVER']['document_ids'], config['SETTINGS']['document_id']), stream=True)
    if r.status_code == 200:
        print("SUCCESFUL")
        return True, json.loads(r.text)
    else:
        print("FAILED")
        return False, None


def check_and_process_update_request(config):
    with requests.Session() as session:
        print()
        print("LOGGING IN")
        print("##############################################################")
        if not log_in(config, session):
            print('FAILED')
            return False
        else:
            print('SUCCESFUL')
        print("##############################################################")

        print()
        print("CREATING WORK FOLDERS")
        print("##############################################################")
        create_work_folders(config)
        print("##############################################################")

        print()
        print("GETTING PAGES IDS")
        print("##############################################################")
        done, page_uuids = get_document_ids(session, config)
        if not done:
            return False
        print("##############################################################")

        print()
        print("DOWNLOADING XMLS")
        print("##############################################################")
        if not download_xmls(session, config, page_uuids):
            return False
        print("##############################################################")

        print()
        print("DOWNLOADING IMAGES")
        print("##############################################################")
        if not download_images(session, config, page_uuids):
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
                                            '--threshold', os.path.join(config['SETTINGS']['threshold'])],
                                            cwd=config['SETTINGS']['working_directory'])

        replace_process.wait()
        print("SUCCESFUL")
        print("##############################################################")

        print()
        print("SENDING DATA TO SERVER")
        print("##############################################################")
        if not send_data(session, config):
            return False
        print("##############################################################")

        return True


def main():
    args = get_args()

    config = configparser.ConfigParser()
    if args.config is not None:
        config.read(args.config)
    else:
        config.read('config.ini')

    if args.document_id is not None:
        config["SETTINGS"]['document_id'] = args.document_id
    if args.login is not None:
        config["SETTINGS"]['login'] = args.login
    if args.password is not None:
        config["SETTINGS"]['password'] = args.password

    if check_and_process_update_request(config):
        print("REQUEST COMPLETED")
    else:
        print("REQUEST FAILED")


if __name__ == '__main__':
    main()
