import os
import shutil
import zipfile
import requests
import subprocess
import configparser

from os import listdir
from lxml import etree

from client_helper import join_url

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("config.ini")

    #creating work folders
    if not os.path.isdir(config['SETTINGS']['working_directory']):
        os.mkdir(config['SETTINGS']['working_directory'])
    if not os.path.isdir(os.path.join(config['SETTINGS']['working_directory'], "xml_all")):
        os.mkdir(os.path.join(config['SETTINGS']['working_directory'], "xml_all"))
    if not os.path.isdir(os.path.join(config['SETTINGS']['working_directory'], "xml_annotated")):
        os.mkdir(os.path.join(config['SETTINGS']['working_directory'], "xml_annotated"))
    if not os.path.isdir(os.path.join(config['SETTINGS']['working_directory'], "img_pages")):
        os.mkdir(os.path.join(config['SETTINGS']['working_directory'], "img_pages"))
    if not os.path.isdir(os.path.join(config['SETTINGS']['working_directory'], "other")):
        os.mkdir(os.path.join(config['SETTINGS']['working_directory'], "other"))

    with requests.Session() as s:
        r = s.get(join_url(config['SERVER']['base_url'], config['SERVER']['index']))

        #get csfd token
        tree = etree.HTML(r.content)
        csrf = tree.xpath('//input[@name="csrf_token"]/@value')[0]

        payload = {
            'email': config['SETTINGS']['login'],
            'password': config['SETTINGS']['password'],
            'submit': 'Login',
            'csrf_token': csrf
        }

        #authentification
        p = s.post(join_url(config['SERVER']['base_url'], config['SERVER']['authentification']), data=payload)

        #download all pages
        r = s.get(join_url(config['SERVER']['base_url'], config['SERVER']['download_all_xmls'], config['SETTINGS']['document_id']), stream=True)
        if r.status_code == 200:
            with open(os.path.join(config['SETTINGS']['working_directory'], '{}_all_pages_xml.zip' .format(config['SETTINGS']['document_id'])), 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print("Error {} occured during all pages download." .format(r.status_code))
            exit()

        with zipfile.ZipFile(os.path.join(config['SETTINGS']['working_directory'], '{}_all_pages_xml.zip' .format(config['SETTINGS']['document_id'])), 'r') as zip_ref:
            zip_ref.extractall(os.path.join(config['SETTINGS']['working_directory'], "xml_all"))

        #download annotations
        r = s.get(join_url(config['SERVER']['base_url'], config['SERVER']['download_annotated_xmls'], config['SETTINGS']['document_id']), stream=True)
        if r.status_code == 200:
            with open(os.path.join(config['SETTINGS']['working_directory'], '{}_annotated_pages_xml.zip' .format(config['SETTINGS']['document_id'])), 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print("Error {} occured during annotations download." .format(r.status_code))
            exit()

        with zipfile.ZipFile(os.path.join(config['SETTINGS']['working_directory'], '{}_annotated_pages_xml.zip' .format(config['SETTINGS']['document_id'])), 'r') as zip_ref:
            zip_ref.extractall(os.path.join(config['SETTINGS']['working_directory'], "xml_annotated"))

        #get page ids
        page_uuid = [f[:-4] for f in listdir(os.path.join(config['SETTINGS']['working_directory'], "xml_all")) if 'xml' in f]

        #removing useless .txt files
        for filename in page_uuid:
            try:
                os.remove(os.path.join(config['SETTINGS']['working_directory'], "xml_all", "{}.txt" .format(filename)))
            except:
                pass

        #download images
        for _, uuid in enumerate(page_uuid):
            r = s.get(join_url(config['SERVER']['base_url'], config['SERVER']['download_images'], uuid), stream=True)
            if r.status_code == 200:
                with open(os.path.join(config['SETTINGS']['working_directory'], "img_pages/{}.jpg" .format(uuid)), 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
            else:
                print("Error {} occured during image {} download.".format(r.status_code, uuid))

        parse_folder_process = subprocess.Popen(['python', config['SETTINGS']['parse_folder_path'],
                                                 '-c', config['SETTINGS']['parse_folder_config_path']],
                                                 cwd=config['SETTINGS']['working_directory'])
        parse_folder_process.wait()

        processed_logits_folder = os.path.join(config['SETTINGS']['working_directory'], "output_logits")

        replace_process = subprocess.Popen(['python', config['SETTINGS']['replace_script_path'],
                                            '--substig', config['SETTINGS']['substitution_file_path'],
                                            '--xml', os.path.join(config['SETTINGS']['working_directory'], "xml_all"),
                                            '--logits', processed_logits_folder,
                                            '--images', os.path.join(config['SETTINGS']['working_directory'], "img_pages"),
                                            '--output-img', os.path.join(config['SETTINGS']['working_directory'], "other"),
                                            '--output-xml', os.path.join(config['SETTINGS']['working_directory'], "other"),
                                            '--output-file', os.path.join(config['SETTINGS']['working_directory'], "changes.json")],
                                            cwd=config['SETTINGS']['working_directory'])

        replace_process.wait()

        with open(os.path.join(config['SETTINGS']['working_directory'], "changes.json"), "rb") as f:
            data = f.read()

        p = s.post(join_url(config['SERVER']['base_url'], config['SETTINGS']['type'], 'id'),
                   files={'data': ('readme.txt', data, 'text/plain')})
