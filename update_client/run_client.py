import os
import time
import shutil
import zipfile
import requests
import subprocess
import configparser

from os import listdir
from lxml import etree

from client_helper import join_url

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


def check_request(r):
    if r.status_code == 200:
        print("SUCCESFUL")
        return True
    else:
        print("FAILED")
        return False


def log_in(config, session):
    r = session.get(join_url(config['SERVER']['base_url'], config['SERVER']['index']))

    if not check_request(r):
        return False

    tree = etree.HTML(r.content)
    csrf = tree.xpath('//input[@name="csrf_token"]/@value')[0]

    payload = {
        'email': config['SETTINGS']['login'],
        'password': config['SETTINGS']['password'],
        'submit': 'Login',
        'csrf_token': csrf
    }

    r = session.post(join_url(config['SERVER']['base_url'], config['SERVER']['authentification']), data=payload)

    if not check_request(r):
        return False
    else:
        return True


def download_xmls(session, config):
    r = session.get(join_url(config['SERVER']['base_url'], config['SERVER'][config['SETTINGS']['type']], config['SETTINGS']['document_id']), stream=True)
    if r.status_code == 200:
        with open(os.path.join(config['SETTINGS']['working_directory'], '{}_xml.zip' .format(config['SETTINGS']['document_id'])), 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    else:
        print("FAILED")
        return False

    with zipfile.ZipFile(os.path.join(config['SETTINGS']['working_directory'], '{}_xml.zip' .format(config['SETTINGS']['document_id'])), 'r') as zip_ref:
        zip_ref.extractall(os.path.join(config['SETTINGS']['working_directory'], "xml"))

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


def check_and_process_update_request(config):
    with requests.Session() as session:
        print()
        print("LOGGING IN")
        print("##############################################################")
        if not log_in(config, session):
            return False
        print("##############################################################")

        print()
        print("CREATING WORK FOLDERS")
        print("##############################################################")
        create_work_folders(config)
        print("##############################################################")

        print()
        print("DOWNLOADING XMLS")
        print("##############################################################")
        if not download_xmls(session, config):
            return False
        print("##############################################################")

        #get page ids
        page_uuids = [f[:-4] for f in listdir(os.path.join(config['SETTINGS']['working_directory'], "xml")) if 'xml' in f]

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
                                            '--output-file', os.path.join(config['SETTINGS']['working_directory'], "changes.json")],
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
    config = configparser.ConfigParser()
    config.read("config.ini")
    while True:
        print("CHECK REQUEST")
        if check_and_process_update_request(config):
            print("REQUEST COMPLETED")
            break
        else:
            print("NO REQUEST")
            time.sleep(2)


if __name__ == '__main__':
    main()
