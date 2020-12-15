import configparser
import time
import sys
import requests
import argparse
import traceback

from client_helper import log_in
from layout_client.run_client import check_and_process_layout_request
from ocr_client.run_client import check_and_process_ocr_request


def get_args():
    """
    method for parsing of arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--time-limit", default=-1, type=float, help="Exit when runing longer than time-limit hours.")
    args = parser.parse_args()

    return args


def main():
    args = get_args()
    start_time = time.time()

    layout_config = configparser.ConfigParser()
    layout_config.read("layout_client/config.ini")
    ocr_config = configparser.ConfigParser()
    ocr_config.read("ocr_client/config.ini")
    timeout = 4
    while True:
        if args.time_limit > 0 and args.time_limit * 3600 < time.time() - start_time:
            break
        try:
            with requests.Session() as session:
                if not log_in(session, layout_config['SETTINGS']['login'], layout_config['SETTINGS']['password'],
                              layout_config['SERVER']['base_url'],
                              layout_config['SERVER']['authentification'], layout_config['SERVER']['login_page']):
                    print('Unable to log into server')
                    time.sleep(timeout)

                while True:
                    nothing = True
                    if check_and_process_layout_request(layout_config, session):
                        nothing = False
                    if check_and_process_ocr_request(ocr_config, session):
                        nothing = False
                    if nothing:
                        time.sleep(timeout)
        except:
            print('ERROR exception')
            traceback.print_exc()
            time.sleep(timeout)


if __name__ == '__main__':
    sys.exit(main())
