import configparser
import time
import sys
import requests
import traceback

from client_helper import log_in
from layout_client.run_client import check_and_process_layout_request
from ocr_client.run_client import check_and_process_ocr_request


def main():
    layout_config = configparser.ConfigParser()
    layout_config.read("layout_client/config.ini")
    ocr_config = configparser.ConfigParser()
    ocr_config.read("ocr_client/config.ini")
    timeout = 4
    while True:
        try:
            with requests.Session() as session:
                if not log_in(session, layout_config['SETTINGS']['login'], layout_config['SETTINGS']['password'],
                              layout_config['SERVER']['base_url'],
                              layout_config['SERVER']['authentification'], layout_config['SERVER']['login_page']):
                    print('Unable to log into server')
                    time.sleep(timeout)

                while True:
                    print()
                    print("CHECK LAYOUT REQUEST")
                    if check_and_process_layout_request(layout_config):
                        print("LAYOUT REQUEST COMPLETED")
                    else:
                        print("NO LAYOUT REQUEST")
                    print()
                    print("CHECK OCR REQUEST")
                    if check_and_process_ocr_request(ocr_config):
                        print("OCR REQUEST COMPLETED")
                    else:
                        print("NO OCR REQUEST")
                        time.sleep(2)
        except:
            print('ERROR exception')
            traceback.print_exc()
            time.sleep(timeout)


if __name__ == '__main__':
    sys.exit(main())
