import requests
import sys
import os
from io import open as image_open
import time


base_url = 'http://127.0.0.1:2000'
route = '/layout_analysis/get_request'
folder = '/home/ikohut/projects_new/pero_ocr_web_data/client_images'
output_folder = '/home/ikohut/projects_new/pero_ocr_web_data/client_images_results'
layout_detector_path = '/home/ikohut/projects_new/BP/bp_source/'
layout_detector = layout_detector_path + 'detect_paragraphs.py'


def get_document_images_folder_path(document_id):
    folder_path = os.path.join(folder, document_id)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path


def get_and_save_document_images(document_id, images):
    folder_path = get_document_images_folder_path(document_id)
    for image in images:
        image_request = requests.get("{}/document/get_image/{}/{}".format(base_url, document_id, image))
        file_type = image_request.headers['content-type'].split('/')[-1]
        path = os.path.join(folder_path, '{}.{}'.format(image, file_type))
        if image_request.status_code == 200:
            with image_open(path, 'wb') as file:
                file.write(image_request.content)


def get_and_save_document():
    r = requests. get('{}{}'.format(base_url, route))
    return_json = r.json()
    if 'document' in return_json.keys():
        document = return_json['document']
        get_and_save_document_images(document['id'], document['images'])
        return return_json['id'], document
    return None, None


def make_post_request_data(document):
    document_id = document['id']
    data = dict()
    images = document['images']
    for image in images:
        data[image] = open(os.path.join(output_folder, document_id, "{}.xml".format(image)), 'rb')
    print('Data:', data)
    return data


def get_post_route(document_id):
    return '/layout_analysis/post_result/{}'.format(document_id)


def run_layout_analysis(document):
    document_id = document['id']
    return os.system('python3 {} -o "{}" -i "{}/" -m "{}"'.format(layout_detector, os.path.join(output_folder, document_id), os.path.join(folder, document_id), os.path.join(layout_detector_path, 'model')))


def check_and_process_request():
    request_id, document = get_and_save_document()
    if document:
        status = run_layout_analysis(document)
        if status == 0:
            data = make_post_request_data(document)  # Make post request
            requests.post('{}{}'.format(base_url, get_post_route(request_id)), files=data)  # Send post request
        else:
            # TODO FAILED
            return True
        return True

    return False


def main():
    while True:
        print('Check request')
        if check_and_process_request():
            print('Request completed')
            break
        else:
            print('No request')
            time.sleep(10)  # No request so sleep for some time


if __name__ == '__main__':
    sys.exit(main())
