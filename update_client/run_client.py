import os
import shutil
import zipfile
import argparse
import requests

from os import listdir
from lxml import etree

from client_helper import join_url

def get_args():
    """
    method for parsing of arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", action="store", dest="server",
                        help="server address in format \"pchradis-stud.fit.vutbr.cz:2001\"")
    parser.add_argument("--temp", action="store", dest="temp", help="folder for temporal files")
    parser.add_argument("--login", action="store", dest="login", help="user login")
    parser.add_argument("--password", action="store", dest="password", help="user password")
    parser.add_argument("--doc-uuid", action="store", dest="doc_uuid", help="uuid for requested document")

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = get_args()

    #creating work folders
    if not os.path.isdir(args.temp):
        os.mkdir(args.temp)
    if not os.path.isdir(os.path.join(args.temp, "xml_all")):
        os.mkdir(os.path.join(args.temp, "xml_all"))
    if not os.path.isdir(os.path.join(args.temp, "xml_annotated")):
        os.mkdir(os.path.join(args.temp, "xml_annotated"))
    if not os.path.isdir(os.path.join(args.temp, "img_pages")):
        os.mkdir(os.path.join(args.temp, "img_pages"))

    with requests.Session() as s:
        r = s.get(join_url(args.server, 'index'))

        #get csfd token
        tree = etree.HTML(r.content)
        csrf = tree.xpath('//input[@name="csrf_token"]/@value')[0]

        payload = {
            'email': args.login,
            'password': args.password,
            'submit': 'Login',
            'csrf_token': csrf
        }

        #authentification
        p = s.post(join_url(args.server, 'auth/login'), data=payload)

        #download all pages
        r = s.get(join_url(args.server, 'document/download_document_pages', args.doc_uuid), stream=True)
        if r.status_code == 200:
            with open(os.path.join(args.temp, '{}_all_pages_xml.zip' .format(args.doc_uuid)), 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print("Error {} occured during all pages download." .format(r.status_code))
            exit()

        with zipfile.ZipFile(os.path.join(args.temp, '{}_all_pages_xml.zip' .format(args.doc_uuid)), 'r') as zip_ref:
            zip_ref.extractall(os.path.join(args.temp, "xml_all"))

        #download annotations
        r = s.get(join_url(args.server, 'document/get_document_annotated_pages', args.doc_uuid), stream=True)
        if r.status_code == 200:
            with open(os.path.join(args.temp, '{}_annotated_pages_xml.zip' .format(args.doc_uuid)), 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print("Error {} occured during annotations download." .format(r.status_code))
            exit()

        with zipfile.ZipFile(os.path.join(args.temp, '{}_annotated_pages_xml.zip' .format(args.doc_uuid)), 'r') as zip_ref:
            zip_ref.extractall(os.path.join(args.temp, "xml_annotated"))

        #get page ids
        page_uuid = [f[:-4] for f in listdir(os.path.join(args.temp, "xml_all")) if 'xml' in f]

        #removing useless .txt files
        for filename in page_uuid:
            try:
                os.remove(os.path.join(args.temp, "xml_all", "{}.txt" .format(filename)))
            except:
                pass

        #download images
        for _, uuid in enumerate(page_uuid):
            r = s.get(join_url(args.server, 'document/get_image', uuid))
            if r.status_code == 200:
                with open(os.path.join(args.temp, "img_pages/{}.jpg" .format(uuid)), 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
            else:
                print("Error {} occured during image {} download.".format(r.status_code, uuid))

        #postprocess part
        #load model
        #compute logits
        #update xml
        #upload new confidences
        """
        line_cropper = EngineLineCropper(poly=2)
        xml_annotated = [f[:-4] for f in listdir(os.path.join(args.temp, "xml_annotated")) if 'xml' in f]

        dataset_file = ""
        os.mkdir(os.path.join(args.temp, "img_lines"))
        for i, uuid in enumerate(xml_annotated):
            page_layout = PageLayout()

            # load page image
            page = cv2.imread(os.path.join(args.temp, "img_pages/{}.jpg" .format(uuid)))

            # load page xml
            page_layout.from_pagexml(os.path.join(args.temp, "xml_annotated/{}.xml" .format(uuid)))

            # crop lines
            for r, region in enumerate(page_layout.regions):
                for l, line in enumerate(region.lines):
                    line_img = line_cropper.crop(page, line.baseline, line.heights, return_mapping=False)
                    dataset_file = dataset_file + "{}.jpg {}\n" .format(line.id, line.transcription)
                    cv2.imwrite(os.path.join(args.temp, "img_lines/{}.jpg" .format(line.id)), line_img)

        file = codecs.open(os.path.join(args.temp, "dataset.txt"), "w", "utf-8")
        file.write(dataset_file)
        file.close()
        """

        p = s.post(join_url(args.server, 'document/update_document_all_pages', 'id'),
                   files={'data': ('readme.txt', '{ \"name\":\"John\", \"age\":30, \"car\":null }', 'text/plain')})
