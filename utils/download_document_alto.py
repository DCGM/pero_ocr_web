import os
import cgi
import json
import shutil
import requests
import argparse

from client_helper import join_url, log_in


def get_args():
    """
    method for parsing of arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('-u', '--url', action='store', dest='url', help='server web address')
    parser.add_argument("-d", "--document-id", action="store", dest="document_id", help="document id")
    parser.add_argument("-l", "--login", action="store", dest="login", help="username")
    parser.add_argument("-p", "--password", action="store", dest="password", help="password")
    parser.add_argument("-o", "--output-folder", action="store", dest="output_folder", help="output folder path")

    args = parser.parse_args()

    return args


def get_document_ids(session, base_url, document_ids, document_id):
    r = session.get(join_url(base_url, document_ids, document_id), stream=True)
    if r.status_code == 200:
        print("SUCCESFUL")
        return True, json.loads(r.text)
    else:
        print("FAILED")
        return False, None


def download_alto(session, base_url, output_dir, page_uuids):
    for _, uuid in enumerate(page_uuids):
        r = session.get(join_url(base_url, '/document/get_alto_xml', uuid), stream=True)
        if r.status_code == 200:
            with open(os.path.join(output_dir, cgi.parse_header(r.headers['Content-Disposition'])[-1]['filename']), 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print("ERROR {} OCCURED DURING XML {} DOWNLOAD.".format(r.status_code, uuid))


if __name__ == '__main__':
    args = get_args()
    with requests.Session() as session:
        print()
        print("LOGGING IN")
        print("##############################################################")
        if not log_in(session, args.login, args.password, args.url, '/auth/login', '/document/documents'):
            print('ERROR DURING LOGGING IN')
        print("##############################################################")

        print()
        print("GETTING PAGES IDS")
        print("##############################################################")
        done, page_uuids = get_document_ids(session, args.url, '/document/get_document_image_ids', args.document_id)
        if not done:
            print('ERROR DURING GETTING PAGES IDS')
        print("##############################################################")

        print()
        print("DOWNLOADING ALTO")
        print("##############################################################")
        download_alto(session, args.url, args.output_folder, page_uuids)
        print("##############################################################")
