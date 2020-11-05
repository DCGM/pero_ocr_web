"""
not tested
"""
import os
import argparse
import requests
import subprocess
import configparser
from pathlib import Path

from client_helper import log_in
from update_client.update_line_size import download_data, send_data


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", required=True, help="Config path.")
    parser.add_argument("-d", "--document-id", help="Process document with this ID.")
    parser.add_argument("-l", "--login", help="Username of superuser on remote server.")
    parser.add_argument("-p", "--password", help="Password of superuser on remote server.")
    parser.add_argument("--working-directory", help="Work in this directory. All downloded and resultsing files will be here.")

    args = parser.parse_args()

    return args


def update_confidences(config, config_path):
    parse_folder_process = subprocess.Popen(['python', config['SETTINGS']['parse_folder_path'],
                                             '-c', config_path],
                                            cwd=config['SETTINGS']['working_directory'])

    parse_folder_process.wait()
    if parse_folder_process.returncode != 0:
        print(f'ERROR: Error during parse_folder_process process.')
        exit(-1)

    replace_process = subprocess.Popen(['python', config['SETTINGS']['replace_script_path'],
                                        '--substig', config['SETTINGS']['substitution_file_path'],
                                        '--xml', os.path.join(config['SETTINGS']['working_directory'], "page_xml"),
                                        '--logits',
                                        os.path.join(config['SETTINGS']['working_directory'], "logits"),
                                        '--images', os.path.join(config['SETTINGS']['working_directory'], "images"),
                                        '--output-img', os.path.join(config['SETTINGS']['working_directory'], "other"),
                                        '--output-xml', os.path.join(config['SETTINGS']['working_directory'], "other"),
                                        '--output-file',
                                        os.path.join(config['SETTINGS']['working_directory'], "changes.json"),
                                        '--threshold', config['SETTINGS']['threshold'],
                                        '--max-confidence', config['SETTINGS']['max_confidence'],
                                        '--computation-type', config['SETTINGS']['computation_type']],
                                       cwd=config['SETTINGS']['working_directory'])

    replace_process.wait()
    if replace_process.returncode != 0:
        print(f'ERROR: Error during replace_process process.')
        exit(-1)

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
                         update_path=config['SERVER']['update_path']):
            print(f'ERROR: Error during uploading.')
            exit(-1)


def main():
    args = get_args()

    if not os.path.isfile(args.config):
        print(f'Error: Config file does not exist "{args.config}"')
        exit(-1)

    config = configparser.ConfigParser()
    config.read(args.config)

    if args.document_id:
        config["SETTINGS"]['document_id'] = args.document_id
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
    Path(os.path.join(config["SETTINGS"]['working_directory'], 'other')).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(config["SETTINGS"]['working_directory'], 'images')).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(config["SETTINGS"]['working_directory'], 'logits')).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(config["SETTINGS"]['working_directory'], 'page_xml')).mkdir(parents=True, exist_ok=True)

    download_data(config)
    update_confidences(config, args.config)


if __name__ == '__main__':
    main()
