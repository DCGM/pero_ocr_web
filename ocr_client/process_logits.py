import pickle
import numpy as np
import os
from itertools import count
import sys
from lxml import etree

import sys
sys.path.insert(1, '../../pero/src/')

from confidence_estimation import get_letter_confidence

namespaces = {'t': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}

def save_xml_with_confidences(xml_file, logits_file, chars, output_folder):
    page_xml_tree = etree.parse(xml_file)
    page_xml_root = page_xml_tree.getroot()

    with open(logits_file, 'rb') as f:
        page_logits = pickle.load(f)

    for _, line_logits in page_logits.items():
        blank_char_index = line_logits.shape[1] - 1
        break

    for text_region in page_xml_root[0]:
        for text_line in text_region.findall("t:TextLine", namespaces):

            line_id = text_line.get('id')
            line_text = text_line[2][0].text

            c_idx = []
            for c in line_text:
                c_idx.append(chars.index(c))

            line_logits = page_logits[line_id]
            line_logits = np.array(line_logits.todense())
            #print(line_text)
            #print(c_idx)

            #print(get_letter_confidence(line_logits, c_idx, blank_char_index))

            etree.SubElement(text_line, "Confidences").text = "0.98 0.74 0.69 0.14 0.66"

    xml_string = etree.tostring(page_xml_root, pretty_print=True)
    xml_name = os.path.basename(xml_file)
    xml_output_path = os.path.join(output_folder, xml_name)
    with open(xml_output_path, 'wb') as f:
        f.writelines([xml_string])


