import requests
import sys
import os
from io import open as image_open

base_url = 'http://127.0.0.1:5000'
route = '/layout_analysis/get_request'
folder = 'C:\\Users\\rykk0\\OneDrive\\Dokumenty\\client_images'


def main():
    r = requests.get('{}{}'.format(base_url, route))
    return_json = r.json()
    document = return_json['document']
    for image in document['images']:
        image_request = requests.get("{}/get_image/{}/{}".format(base_url, document['id'], image))
        folder_path = '{}\\{}'.format(folder, document['id'])
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_type = image_request.headers['content-type'].split('/')[-1]
        path = '{}\\{}.{}'.format(folder_path, image, file_type)
        if image_request.status_code == 200:
            with image_open(path, 'wb') as file:
                file.write(image_request.content)
    return 0


if __name__ == '__main__':
    sys.exit(main())
