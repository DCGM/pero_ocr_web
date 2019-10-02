import shutil
import os
import configparser


def detect_document_baselines(parse_folder_script, images_folder, xmls_folder, output_folder, document_id, configs_folder, config_path):
    images_path = os.path.join(images_folder, document_id)
    xmls_path = os.path.join(xmls_folder, document_id)

    config = configparser.ConfigParser()
    config.read(os.path.join(configs_folder, config_path))

    config['INPUTS']['INPUT_PATH'] = images_path
    config['INPUTS']['PAGE_PARAGRAPHS'] = xmls_path
    output_path = os.path.join(output_folder, document_id)
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    os.makedirs(output_path)
    config['OUTPUTS']['OUTPUT_PATH'] = output_path


    document_config_path = os.path.join(configs_folder, "document_configs", "{}.ini".format(document_id))

    with open(document_config_path, 'w') as configfile:
        config.write(configfile)

    os.system('python {} -c {}'.format(parse_folder_script, document_config_path))
