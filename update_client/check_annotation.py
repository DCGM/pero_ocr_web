import os
import json
import shutil
import requests
import argparse
import subprocess
import configparser
import numpy as np
import cv2

from client_helper import join_url, log_in

from pero_ocr.document_ocr.layout import PageLayout
from pero_ocr.document_ocr.page_parser import PageParser
from datasets.charset import get_chars_mapping
from utils.line_fixer import align_text, get_loss


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", action="store", dest="config", help="config path")
    parser.add_argument("-d", "--document-id", action="store", dest="document_id", help="document id")
    parser.add_argument("-l", "--login", action="store", dest="login", help="username")
    parser.add_argument("-p", "--password", action="store", dest="password", help="password")
    args = parser.parse_args()
    return args


def get_document_ids(session, base_url, document_ids, document_id):
    r = session.get(join_url(base_url, document_ids, document_id), stream=True)
    if r.status_code == 200:
        print("SUCCESFUL")
        return True, json.loads(r.text)
    else:
        print("FAILED", document_id)
        return False, None


def get_line_confidence(line, original_transcription, translation):
    labels = np.asarray([ord(x) for x in original_transcription.translate(translation)], dtype=np.int64)
    log_probs = line.get_full_logprobs()
    logits = line.get_dense_logits()

    orig_loss, orig_log_probs = get_loss(logits[np.newaxis, ...], original_transcription, translation)
    new_loss, new_log_probs = get_loss(logits[np.newaxis, ...], line.transcription, translation)

    #print(np.max(labels), original_transcription, translation)
    alignment = align_text(-log_probs, labels, log_probs.shape[1] - 1)
    alignment = np.concatenate([alignment, [1000]])

    probs = np.exp(log_probs)
    last_border = 0
    confidences = np.zeros(labels.shape[0])
    for i, label in enumerate(labels):
        label_prob = probs[alignment[i], label]
        next_border = (alignment[i] + 1 + alignment[i+1]) // 2
        pos_probs = probs[last_border: next_border]
        masked_probs = np.copy(pos_probs)
        masked_probs[:, label] = 0
        other_prob = masked_probs[:, :-1].max()
        confidences[i] = label_prob - other_prob
        last_border = next_border

    confidences = confidences / 2 + 0.5
    return confidences, orig_loss[0], new_loss[0]

def send_data(session, base_url, update_all_confidences, payload):
    payload = json.dumps(payload)

    r = session.post(join_url(base_url, update_all_confidences),
                     files={'data': ('data.json', payload, 'text/plain')})

    if r.status_code == 200:
        return True
    else:
        return False

def check_and_process_update_request(config, page_parser):
    with requests.Session() as session:
        print()
        print("LOGGING IN")
        print("##############################################################")
        if not log_in(session, config['SETTINGS']['login'], config['SETTINGS']['password'], config['SERVER']['base_url'],
                      config['SERVER']['authentification'], config['SERVER']['login_page']):
            return False
        print("##############################################################")

        print()
        print("GETTING PAGES IDS")
        print("##############################################################")
        done, page_uuids = get_document_ids(session, config['SERVER']['base_url'], config['SERVER']['document_ids'], config['SETTINGS']['document_id'])
        if not done:
            return False
        print("##############################################################")

        base_url = config['SERVER']['base_url']
        download_images = config['SERVER']['download_images']

        for page_uuid in page_uuids:
            r = session.get(join_url(base_url, config['SERVER'][config['SETTINGS']['type']], page_uuid), stream=True)
            if r.status_code != 200:
                print("ERROR {} OCCURED DURING XML {} DOWNLOAD.".format(r.status_code, page_uuid))
                continue
            page_layout = PageLayout(id=page_uuid, file=r.raw)
            orig_transcriptions = dict([(line.id, line.transcription) for line in page_layout.lines_iterator()])
            if len(orig_transcriptions) == 0:
                continue

            r = session.get(join_url(base_url, download_images, page_uuid), stream=True)
            if r.status_code != 200:
                print("ERROR {} OCCURED DURING XML {} DOWNLOAD.".format(r.status_code, page_uuid))
                continue

            nparr = np.frombuffer(r.content, np.uint8)
            image = cv2.imdecode(nparr, 1)

            page_layout = page_parser.process_page(image, page_layout)

            from_char, to_char = get_chars_mapping(
                ''.join([t for t in orig_transcriptions.values()]),
                next(page_layout.lines_iterator()).characters)
            translation = str.maketrans(''.join(from_char), ''.join(to_char))

            updates = {}
            for line in page_layout.lines_iterator():
                if orig_transcriptions[line.id] and line.transcription:
                    confidences, orig_loss, new_loss = get_line_confidence(line, orig_transcriptions[line.id], translation)
                    updates[line.id] = [None, confidences.tolist(), 2**(0.1*(-2*orig_loss + new_loss))]
                    if orig_loss > new_loss:
                        print(orig_loss, new_loss, ' '.join([f'{c:.2}' for c in confidences]))
                        print(line.transcription)
                        print(orig_transcriptions[line.id])
            if updates:
                if not send_data(session, config['SERVER']['base_url'], config['SERVER']['update_all_confidences'], updates):
                    print('SEND FAILED')

    return True


def main():
    args = get_args()

    config = configparser.ConfigParser()
    if args.config is not None:
        config.read(args.config)
    else:
        config.read('config.ini')

    if args.document_id is not None:
        config["SETTINGS"]['document_id'] = args.document_id
    if args.login is not None:
        config["SETTINGS"]['login'] = args.login
    if args.password is not None:
        config["SETTINGS"]['password'] = args.password

    page_parser = PageParser(config, config_path=os.path.dirname(args.config))

    if check_and_process_update_request(config, page_parser):
        print("REQUEST COMPLETED")
    else:
        print("REQUEST FAILED")


if __name__ == '__main__':
    main()
