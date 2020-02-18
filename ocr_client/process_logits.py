import pickle
import numpy as np
import os
from lxml import etree
import numpy as np

import sys
sys.path.insert(1, '../../pero/src/')

from pero_ocr.force_alignment import force_align
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

            if line_text is not None:
                c_idx = []
                for c in line_text:
                    c_idx.append(chars.index(c))

                line_logits = page_logits[line_id]
                line_logits = np.array(line_logits.todense())
                line_logits[line_logits == 0] = -80
                line_probs = softmax(line_logits, axis=1)
                #print(line_text)
                #print(c_idx)

                al_res = force_align(-line_logits, c_idx, blank_char_index)
                con_res = get_letter_confidence(line_logits, al_res, blank_char_index)
                con_str = ""
                for x in np.exp(con_res):
                    if x == 1:
                        con_str += " 1"
                    else:
                        con_str += " {:.3}".format(x)
                etree.SubElement(text_line, "Confidences").text = con_str[1:]
            else:
                etree.SubElement(text_line, "Confidences").text = ""

    xml_string = etree.tostring(page_xml_root, pretty_print=True)
    xml_name = os.path.basename(xml_file)
    xml_output_path = os.path.join(output_folder, xml_name)
    with open(xml_output_path, 'wb') as f:
        f.writelines([xml_string])


def softmax(X, theta=1.0, axis=None):
    """
    Compute the softmax of each element along an axis of X.

    Parameters
    ----------
    X: ND-Array. Probably should be floats.
    theta (optional): float parameter, used as a multiplier
        prior to exponentiation. Default = 1.0
    axis (optional): axis to compute values along. Default is the
        first non-singleton axis.

    Returns an array the same size as X. The result will sum to 1
    along the specified axis.
    """

    # make X at least 2d
    y = np.atleast_2d(X)

    # find axis
    if axis is None:
        axis = next(j[0] for j in enumerate(y.shape) if j[1] > 1)

    # multiply y against the theta parameter,
    if theta != 1:
        y = y * float(theta)

    # subtract the max for numerical stability
    y_max = np.max(y, axis=axis, keepdims=True)
    y = y - y_max

    # exponentiate y
    y = np.exp(y)

    # take the sum along the specified axis
    ax_sum = np.sum(y, axis=axis, keepdims=True)

    # finally: divide elementwise
    p = y / ax_sum

    # flatten if X was 1D
    if len(X.shape) == 1: p = p.flatten()

    return p