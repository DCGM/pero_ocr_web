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


def get_images(session, base_url, document_get_image_route, image_ids, image_folder):
    number_of_images = len(image_ids)
    for i, image_id in enumerate(image_ids):
        print("{}/{} GETTING IMAGE:".format(i + 1, number_of_images), image_id)
        image_response = session.get(join_url(base_url, document_get_image_route, image_id))
        file_type = image_response.headers['content-type'].split('/')[-1]
        path = os.path.join(image_folder, "{}.{}".format(image_id, file_type))
        if image_response.status_code == 200:
            with image_open(path, 'wb') as f:
                f.write(image_response.content)


def add_log_to_request(session, base_url, add_request_to_log_route, request_id, log):
    session.post(join_url(base_url, add_request_to_log_route, request_id), json={"log": "".join(log)})


def post_result(session, base_url, post_result_route, success_route, request_id, image_ids, data_folders, data_types):
    for image_id in image_ids:
        data = dict()
        for data_folder, data_type in zip(data_folders, data_types):
            data["{}.{}".format(image_id, data_type)] = open(os.path.join(data_folder, "{}.{}".format(image_id, data_type)), 'rb')
        session.post(join_url(base_url, post_result_route, image_id), files=data)
    session.post(join_url(base_url, success_route, request_id))


def check_request(r):
    if r.status_code == 200:
        return True
    else:
        return False


def log_in(session, login, password, base_usr, authentification, login_page):
    r = session.get(base_usr)

    if not check_request(r):
        print("FAILED")
        return False

    tree = etree.HTML(r.content)
    csrf = tree.xpath('//input[@name="csrf_token"]/@value')[0]

    payload = {
        'email': login,
        'password': password,
        'submit': 'Login',
        'csrf_token': csrf
    }

    r = session.post(join_url(base_usr, authentification), data=payload)

    if not check_request(r) or login_page not in r.url:
        print("FAILED")
        return False
    else:
        print("SUCCESFUL")
        return True
