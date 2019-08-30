import pickle
import numpy as np
from itertools import count
import sys
from lxml import etree

namespaces = {'t': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}

def get_xml_prop(xml_file):
    page_xml_tree = etree.parse(xml_file)
    page_xml_root = page_xml_tree.getroot()

    line_ids = []
    coords = []
    texts = []
    for text_region in page_xml_root[0]:
        for text_line in text_region.findall("t:TextLine", namespaces):
            line_id = text_line.get('id')
            line_points = text_line[0].get('points')
            line_text = text_line[2][0].text
            line_ids.append(line_id)
            coords.append(line_points)
            texts.append(line_text)
    return (line_ids, coords, texts)
