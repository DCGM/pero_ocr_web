import configparser
import time
import sys

from layout_client.run_client import check_and_process_layout_request
from ocr_client.run_client import check_and_process_ocr_request


def main():
    layout_config = configparser.ConfigParser()
    layout_config.read("layout_client/config.ini")
    ocr_config = configparser.ConfigParser()
    ocr_config.read("ocr_client/config.ini")
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



if __name__ == '__main__':
    sys.exit(main())