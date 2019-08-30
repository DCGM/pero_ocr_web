import pickle
import numpy as np
from itertools import count
import sys
from lxml import etree

namespaces = {'t': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}

def get_accuracy_lines(xml_file, logits_file):
    print(xml_file)
    print(logits_file)
    page_xml_tree = etree.parse(xml_file)
    page_xml_root = page_xml_tree.getroot()

    with open(logits_file, 'rb') as f:
        page_logits = pickle.load(f)


    for _, line_logits in page_logits.items():
        blank_char_index = line_logits.shape[1] - 1
        break

    accuracy_lines = {}
    for text_region in page_xml_root[0]:
        for text_line in text_region.findall("t:TextLine", namespaces):

            line_id = text_line.get('id')
            line_text = text_line[2][0].text

            line_logits = page_logits[line_id]
            line_logits = np.array(line_logits.todense())
            line_probs = softmax(line_logits, axis=1)


            #accuracy_lines[line_id] = fce(line_text, line_probs, blank_char_index)






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
