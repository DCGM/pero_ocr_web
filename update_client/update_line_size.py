import os
import cv2
import json
import shutil
import requests
import argparse
import subprocess
import numpy as np
import configparser
from os import listdir
from pathlib import Path
from shutil import copyfile
from os.path import isfile, join

from client_helper import join_url, log_in, check_request
from pero_ocr.core.layout import PageLayout
from pero_ocr.document_ocr.page_parser import PageParser


def get_args():
    """
    method for parsing of arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", required=True, help="Config path.")
    parser.add_argument("--parse-folder-config", help="Config for parse_folder.py used when changing heights.")
    parser.add_argument("-d", "--document-id", help="Process document with this ID.")
    parser.add_argument("--update-type", choices=["baselines_compute", "restore_baselines", "update_heights"], help="Update method.")
    parser.add_argument("-l", "--login", help="Username of superuser on remote server.")
    parser.add_argument("-p", "--password", help="Password of superuser on remote server.")
    parser.add_argument("--working-directory", help="Work in this directory. All downloaded and resulting files will be here.")
    parser.add_argument("-r", "--render", default=True, type=bool, help="Render original page_xml and output page_xml as images.")
    parser.add_argument("-u", "--upload-results", action='store_true', help="Upload results to server. No processing is done in this case.")

    args = parser.parse_args()

    return args


def download_xmls(session, base_url, type, working_directory, page_uuids):
    for _, uuid in enumerate(page_uuids):
        r = session.get(join_url(base_url, type, uuid), stream=True)
        if r.status_code == 200:
            with open(os.path.join(working_directory, "page_xml/{}.xml".format(uuid)), 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print("ERROR {} OCCURRED DURING XML {} DOWNLOAD.".format(r.status_code, uuid))
            return False

    return True


def download_images(session, base_url, download_images, working_directory, page_uuids):
    for _, uuid in enumerate(page_uuids):
        r = session.get(join_url(base_url, download_images, uuid), stream=True)
        if r.status_code == 200:
            with open(os.path.join(working_directory, "images/{}.jpg".format(uuid)), 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print("ERROR {} OCCURRED DURING IMAGE {} DOWNLOAD.".format(r.status_code, uuid))
            return False

    return True


def send_data(session, working_directory, base_url, update_path, file="changes.json"):
    with open(os.path.join(working_directory, file), "rb") as f:
        data = f.read()

    r = session.post(join_url(base_url, update_path),
                     files={'data': ('data.json', data, 'text/plain')})

    if not check_request(r):
        return False
    else:
        return True


def get_document_ids(session, base_url, document_ids, document_id):
    r = session.get(join_url(base_url, document_ids, document_id), stream=True)
    if r.status_code == 200:
        return True, json.loads(r.text)
    else:
        return False, None


def update_baselines(config):
    line_fixer_process = subprocess.Popen(['python', config['SETTINGS']['line_fixer_path'],
                                           '-m', config['SETTINGS']['extension_mode'],
                                           '-i', os.path.join(config['SETTINGS']['working_directory'], "images"),
                                           '-x', os.path.join(config['SETTINGS']['working_directory'], "page_xml_results"),
                                           '-o', config['SETTINGS']['ocr'],
                                           '--output', os.path.join(config['SETTINGS']['working_directory'], "page_xml_results"),
                                           '--extend-by', config['SETTINGS']['automatic_extension_by'],
                                           '--ocr-start-offset', config['SETTINGS']['ocr_start_offset'],
                                           '--ocr-end-offset', config['SETTINGS']['ocr_end_offset']],
                                          cwd=config['SETTINGS']['working_directory'])

    line_fixer_process.wait()
    if line_fixer_process.returncode != 0:
        print(f'ERROR: Error during line_fixer process.')
        exit(-1)


def restore_originals(config):
    """
    Move ./page_xml to ./page_xml_results.

    :param config:
    :return:
    """
    page_xml_path = os.path.join(config["SETTINGS"]['working_directory'], 'page_xml')
    page_xml_files = [f for f in listdir(page_xml_path) if isfile(join(page_xml_path, f))]
    for file in page_xml_files:
        copyfile(os.path.join(config["SETTINGS"]['working_directory'], 'page_xml', file),
                 os.path.join(config["SETTINGS"]['working_directory'], 'page_xml_results', file))


def update_heights(config, parse_folder_config_path):
    parse_folder_config = configparser.ConfigParser()
    parse_folder_config.read(parse_folder_config_path)

    page_parser = PageParser(parse_folder_config)
    xmls = os.listdir(os.path.join(config['SETTINGS']['working_directory'], "page_xml_results"))
    for xml in xmls:
        page_layout = PageLayout(file=os.path.join(config['SETTINGS']['working_directory'], "page_xml_results", xml))
        image = cv2.imread(os.path.join(config['SETTINGS']['working_directory'], "images", xml[:-4] + '.jpg'))
        page_layout = page_parser.process_page(image, page_layout)
        page_layout.to_pagexml(os.path.join(config['SETTINGS']['working_directory'], "page_xml_results", xml))

    return True


def render_pages(config):
    """
    Render from ./page_xml as *_orig.jpg and from ./page_xml_results as *_new.jpg.

    :param config:
    :return:
    """
    page_parser = PageParser(config)
    page_xml_path = os.path.join(config["SETTINGS"]['working_directory'], 'page_xml')
    page_xml_files = [f for f in listdir(page_xml_path) if isfile(join(page_xml_path, f))]
    for xml in page_xml_files:
        # page_xml
        image = cv2.imread(os.path.join(config['SETTINGS']['working_directory'], "images", xml[:-4] + '.jpg'))
        page_layout = PageLayout(file=os.path.join(config['SETTINGS']['working_directory'], "page_xml", xml))
        page_layout = page_parser.process_page(image, page_layout)
        page_layout.render_to_image(image)
        cv2.imwrite(os.path.join(config["SETTINGS"]['working_directory'], 'render', xml[:-4] + '_orig.jpg'), image, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        # page_xml_results
        image = cv2.imread(os.path.join(config['SETTINGS']['working_directory'], "images", xml[:-4] + '.jpg'))
        page_layout = PageLayout(file=os.path.join(config['SETTINGS']['working_directory'], "page_xml_results", xml))
        page_layout = page_parser.process_page(image, page_layout)
        page_layout.render_to_image(image)
        cv2.imwrite(os.path.join(config["SETTINGS"]['working_directory'], 'render', xml[:-4] + '_new.jpg.jpg'), image, [int(cv2.IMWRITE_JPEG_QUALITY), 70])


def download_data(config):
    """
    Download data if working directories do not exist. (./images ./page_xml ./page_xml_results)

    :param config:
    :return:
    """
    page_xml_path = os.path.join(config["SETTINGS"]['working_directory'], 'page_xml')
    page_xml_files = [f for f in listdir(page_xml_path) if isfile(join(page_xml_path, f))]
    if len(page_xml_files) == 0:
        with requests.Session() as session:
            if not log_in(session=session,
                          login=config['SETTINGS']['login'],
                          password=config['SETTINGS']['password'],
                          base_usr=config['SERVER']['base_url'],
                          authentification=config['SERVER']['authentification'],
                          login_page=config['SERVER']['login_page']):
                print(f'ERROR: Error during logging in.')
                exit(-1)

            done, page_uuids = get_document_ids(session=session,
                                                base_url=config['SERVER']['base_url'],
                                                document_ids=config['SERVER']['document_ids'],
                                                document_id=config['SETTINGS']['document_id'])
            if not done:
                print(f'ERROR: Error during getting document ids.')
                exit(-1)

            if not download_xmls(session=session,
                                 base_url=config['SERVER']['base_url'],
                                 type=config['SERVER'][config['SETTINGS']['type']],
                                 working_directory=config['SETTINGS']['working_directory'],
                                 page_uuids=page_uuids):
                print(f'ERROR: Error during downloading xmls.')
                exit(-1)

            if not download_images(session=session,
                                   base_url=config['SERVER']['base_url'],
                                   download_images=config['SERVER']['download_images'],
                                   working_directory=config['SETTINGS']['working_directory'],
                                   page_uuids=page_uuids):
                print(f'ERROR: Error during downloading images.')
                exit(-1)

    if os.path.isdir(os.path.join(config["SETTINGS"]['working_directory'], 'page_xml_results')):
        page_xml_results_path = os.path.join(config["SETTINGS"]['working_directory'], 'page_xml_results')
        page_xml_results_files = [f for f in listdir(page_xml_results_path) if isfile(join(page_xml_results_path, f))]
        if len(page_xml_results_files) == 0:
            for file in page_xml_files:
                copyfile(os.path.join(config["SETTINGS"]['working_directory'], 'page_xml', file),
                         os.path.join(config["SETTINGS"]['working_directory'], 'page_xml_results', file))


def upload_data(config):
    """
    If ./page_xml_results exists, upload differences to server (with respect to ./page_xml)

    :param config:
    :return:
    """
    page_xml_path = os.path.join(config["SETTINGS"]['working_directory'], 'page_xml')
    page_xml_files = [f for f in listdir(page_xml_path) if isfile(join(page_xml_path, f))]

    page_xml_results_path = os.path.join(config["SETTINGS"]['working_directory'], 'page_xml_results')
    page_xml_results_files = [f for f in listdir(page_xml_results_path) if isfile(join(page_xml_results_path, f))]

    if len(page_xml_files) != 0 and len(page_xml_files) != len(page_xml_results_files):
        print(f'ERROR: XML in folders ./page_xml_results and ./page_xml don\'t match.')
        exit(-1)

    update = dict()
    for file in page_xml_files:
        page_layout_orig = PageLayout(file=os.path.join(config['SETTINGS']['working_directory'], "page_xml", file))
        page_layout_new = PageLayout(file=os.path.join(config['SETTINGS']['working_directory'], "page_xml_results", file))
        for line_orig, line_new in zip(page_layout_orig.lines_iterator(), page_layout_new.lines_iterator()):
            line_orig_baseline = np.int_(line_orig.baseline).tolist()
            line_orig_heights = np.int_(line_orig.heights).tolist()

            line_new_baseline = np.int_(line_new.baseline).tolist()
            line_new_heights = np.int_(line_new.heights).tolist()

            if line_orig_baseline != line_new_baseline or line_orig_heights != line_new_heights:
                update[line_new.id] = [np.int_(line_new.baseline).tolist(), np.int_(line_new.heights).tolist()]

    with open(os.path.join(config['SETTINGS']['working_directory'], "data.json"), 'w') as handle:
        json.dump(update, handle)

    with requests.Session() as session:
        if not log_in(session=session,
                      login=config['SETTINGS']['login'],
                      password=config['SETTINGS']['password'],
                      base_usr=config['SERVER']['base_url'],
                      authentification=config['SERVER']['authentification'],
                      login_page=config['SERVER']['login_page']):
            print(f'ERROR: Error during logging in.')
            exit(-1)

        if not send_data(session=session,
                         working_directory=config['SETTINGS']['working_directory'],
                         base_url=config['SERVER']['base_url'],
                         update_path=config['SERVER']['update_path'],
                         file='data.json'):
            print(f'ERROR: Error during uploading.')
            exit(-1)


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
    if args.update_type:
        config["SETTINGS"]['update_type'] = args.update_type
    if args.login:
        config["SETTINGS"]['login'] = args.login
    if args.password:
        config["SETTINGS"]['password'] = args.password
    if args.working_directory:
        config["SETTINGS"]['working_directory'] = args.working_directory
    else:
        config["SETTINGS"]['working_directory'] = \
            os.path.join(config["SETTINGS"].get('working_directory', fallback=''), config["SETTINGS"]['document_id'])

    Path(config["SETTINGS"]['working_directory']).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(config["SETTINGS"]['working_directory'], 'images')).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(config["SETTINGS"]['working_directory'], 'page_xml')).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(config["SETTINGS"]['working_directory'], 'page_xml_results')).mkdir(parents=True, exist_ok=True)

    if args.upload_results:
        upload_data(config)
    else:
        download_data(config)

        update_type = config["SETTINGS"]['update_type']
        print(f'STARTING PROCESSING "{update_type}"')
        try:
            if update_type == 'update_baselines':
                update_baselines(config)
            elif update_type == 'update_heights':
                update_heights(config, args.parse_folder_config)
            elif update_type == 'restore_originals':
                restore_originals(config)
            else:
                print(f'ERROR: Unknown update_type "{update_type}"')
                exit(-1)
        except:
            print(f'ERROR: Processing failed with exception.')
            raise

        if args.render:
            Path(os.path.join(config["SETTINGS"]['working_directory'], 'render')).mkdir(parents=True, exist_ok=True)
            render_pages(config)


if __name__ == '__main__':
    main()
