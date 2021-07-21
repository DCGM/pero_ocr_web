import os
import cgi
import json
import shutil
import requests
import argparse

from client_helper import join_url, log_in


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', default='https://pero-ocr.fit.vutbr.cz/', help='Web app url.   ')
    parser.add_argument("-d", "--document-id", required=True, help="Document UUID (e.g. from server url).")
    parser.add_argument("-l", "--login", required=True, help="username")
    parser.add_argument("-p", "--password", required=True, help="password")
    parser.add_argument("-o", "--output-path", action="store", help="output folder path")
    parser.add_argument('--alto', action='store_true', help='Download results in ALTO XML format.')
    parser.add_argument('--page', action='store_true', help='Download results in PAGE XML format.')
    parser.add_argument('--txt', action='store_true', help='Download results in plain text format.')
    parser.add_argument('--image', action='store_true', help='Download image.')
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


def download_results(page_uuid, session, server_url, output_path, alto, page, txt, image):
    requested_formats = []

    if alto:
        requested_formats.append(
            (join_url(server_url, '/document/get_alto_xml', page_uuid), '_alto.xml'))
    if page:
        requested_formats.append(
            (join_url(server_url, '/document/get_page_xml_lines', page_uuid), '_page.xml'))
    if txt:
        requested_formats.append(
            (join_url(server_url, '/document/get_text', page_uuid), '.txt'))
    if image:
        requested_formats.append(
            (join_url(server_url, '/document/get_image', page_uuid), '.jpg'))

    for url, extension in requested_formats:
        r = session.get(url, stream=True)
        if r.status_code != 200:
            print(f"ERROR {r.status_code} OCCURED DURING XML {page_uuid} DOWNLOAD. URL {url}")
            continue

        output_file_name, _ = os.path.splitext(cgi.parse_header(r.headers['Content-Disposition'])[-1]['filename'])
        output_file_name += extension

        with open(os.path.join(output_path, output_file_name), 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)


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
        print("DOWNLOADING PAGES")
        print("##############################################################")
        for i, page_uuid in enumerate(page_uuids):
            print('Downloading page', i, page_uuid)
            download_results(page_uuid, session, args.url, args.output_path, args.alto, args.page, args.txt, args.image)
        print("##############################################################")
