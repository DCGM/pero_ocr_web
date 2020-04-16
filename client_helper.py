import requests
import os
from io import open as image_open
import zipfile
from lxml import etree


def join_url(*paths):
    final_paths = []
    first_path = paths[0].strip()
    if first_path[-1] == '/':
        first_path = first_path[:-1]
    final_paths.append(first_path)
    for path in paths[1:]:
        final_paths.append(path.strip().strip('/'))
    return '/'.join(final_paths)


def unzip_response_to_dir(response, dir):
    tmp_zip_path = os.path.join(dir, "tmp.zip")
    with open(tmp_zip_path, 'wb') as handle:
        handle.write(response.content)
    with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
        zip_ref.extractall(dir)
    os.remove(tmp_zip_path)


def get_images(base_url, document_get_image_route, image_ids, image_folder):
    number_of_images = len(image_ids)
    for i, image_id in enumerate(image_ids):
        print("{}/{} GETTING IMAGE:".format(i + 1, number_of_images), image_id)
        image_response = requests.get(join_url(base_url, document_get_image_route, image_id))
        file_type = image_response.headers['content-type'].split('/')[-1]
        path = os.path.join(image_folder, "{}.{}".format(image_id, file_type))
        if image_response.status_code == 200:
            with image_open(path, 'wb') as f:
                f.write(image_response.content)


def post_result(base_url, post_result_route, request_id, image_ids, data_folders, data_types):
    data = dict()
    for image_id in image_ids:
        for data_folder, data_type in zip(data_folders, data_types):
            data["{}.{}".format(image_id, data_type)] = open(os.path.join(data_folder, "{}.{}".format(image_id, data_type)), 'rb')
    requests.post(join_url(base_url, post_result_route, request_id), files=data)


def check_request(r, verbose=False):
    if r.status_code == 200:
        if verbose:
            print("SUCCESFUL")
        return True
    else:
        if verbose:
            print("FAILED")
        return False


def log_in(config, session, verbose=True):
    r = session.get(join_url(config['SERVER']['base_url']))

    if not check_request(r, verbose=False):
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

    if not check_request(r, verbose=False) or config['SERVER']['login_page'] not in r.url:
        return False
    else:
        return True
