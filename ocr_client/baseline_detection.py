

import sys
sys.path.insert(1, '../../pero/user_scripts/')

import shutil
import os
import configparser
import traceback

sys.path.append(os.path.join(os.path.dirname(__file__), '../../pero/src'))
import engine_line_ocr as ocr

sys.path.append(os.path.join(os.path.dirname(__file__), '../../pero/pero'))
import document_ocr.IO_utils as io
import document_ocr.parser_utils as parser
import document_ocr.crop_engine as cropper
import document_ocr.baseline_engine as detector
import document_ocr.layout as layout

from decoding.decoding_itf import decode_page, get_decoder

from parse_folder import process_file
from parse_folder import save_outputs



def detect_document_baselines(images_folder, xmls_folder, output_folder, document_id, config_path):
    images_path = os.path.join(images_folder, os.listdir(images_folder)[0])
    xmls_path = os.path.join(xmls_folder, os.listdir(xmls_folder)[0])

    config = configparser.ConfigParser()
    config.read(config_path)

    input_path = images_path
    config['INPUTS']['INPUT_PATH'] = input_path
    config['INPUTS']['PAGE_PARAGRAPHS'] = xmls_path
    source_page = config['INPUTS']['SOURCE_PAGE']
    page_lines = config['INPUTS']['PAGE_LINES']
    output_path = os.path.join(output_folder, document_id)
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    os.makedirs(output_path)
    config['OUTPUTS']['OUTPUT_PATH'] = output_path
    combo_model = config['MODELS']['COMBO_MODEL']
    ocr_json = config['MODELS']['OCR_JSON']
    skip = config['SETTINGS'].getboolean('SKIPPING')
    poly = config['SETTINGS'].getint('INTERP')
    line_scale = config['SETTINGS'].getfloat('LINE_SCALE')
    line_height = config['SETTINGS'].getint('LINE_HEIGHT')
    use_cpu = config['SETTINGS'].getboolean('USE_CPU')
    online = config['SETTINGS'].getboolean('ONLINE')

    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # suppress tensorflow warnings on loading models
    ocr_engine = ocr.EngineLineOCR(ocr_json, gpu_id=0)
    decoder = get_decoder(config, ocr_engine.characters)
    crop_engine = cropper.EngineLineCropper(line_height=line_height, poly=poly, scale=line_scale)
    baseline_engine = detector.EngineBaselineDetector(combo_model, use_cpu=use_cpu)


    files_to_process = [f for f in os.listdir(input_path) if (os.path.splitext(f)[1] in ['.jpg', '.jpeg', '.JPG', '.png', '.PNG'])]
    for file in files_to_process:
        try:
            loaded_img_fullsize, page_layout, page_logits = process_file(file, crop_engine, ocr_engine, baseline_engine, config)
            decoder_output = decode_page(page_logits, decoder)
        except:
            print('ERROR: Failed file"{}"'.format(file))
            traceback.print_exc()
        else:
            save_outputs(loaded_img_fullsize, page_layout, page_logits, decoder_output, os.path.splitext(file)[0], config)
