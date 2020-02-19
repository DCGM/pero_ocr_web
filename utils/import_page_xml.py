import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import argparse
from app.db import Document, Image, TextRegion, TextLine
from app.db.guid import GUID
import glob
import os
import uuid
from pero_ocr.document_ocr import PageLayout
from app.document.general import dhash, get_and_create_document_image_directory
from shutil import copyfile
from PIL import Image as PILImage
import numpy as np

import re



def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=str, required=True, help="Database.")
    parser.add_argument('-x', '--xml-path', type=str, required=True, help="XML path.")
    parser.add_argument('-i', '--image-path', type=str, required=True, help="Image path.")
    parser.add_argument('-d', '--document', type=str, required=True, help="Image path.")
    parser.add_argument('-p', '--upload_path', type=str, required=True, help="Image path.")

    args = parser.parse_args()
    return args


def has_text(layout):
    has_transcript = False
    for region in layout.regions:
        for line in region.lines:
            if line.transcription:
                has_transcript = True
    return has_transcript


def create_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


replace_rules = [
    [re.compile(r'([^\[])J([^\]])'), r'\g<1>G\g<2>'],      #J  g
    [re.compile(r'([^\[])j([^\]])'), r'\g<1>g\g<2>'],      #j  g
    [re.compile(r'í'), r'j'],                                #í  j
    [re.compile(r'š'), r'ſſ'],                               #š  ſſ
    [re.compile(r's\B'), r'ſ'],  #s  ſ
    [re.compile(r'\bu'), r'v'],                 # u v
    [re.compile(r'\[J\]'), r'J'],                           #[J]    j
    [re.compile(r'\]j\]'), r'j'],                           #[j]    j
    ];

weird_characters = ['š', 'ſ', 's', 'v', 'j', 'J', 'g', 'G']

def apply_rules(text, rules, weird_characters):
    for reg, repl in rules:
        text = re.sub(reg, repl, text)

    confidences = [0.5 if c in weird_characters else 1 for c in text]
    return text, confidences

def main():
    args = parseargs()

    database_url = 'sqlite:///' + args.database
    engine = create_engine(database_url, convert_unicode=True, connect_args={'check_same_thread': False})
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))

    document = db_session.query(Document).filter(Document.name == args.document).one()
    document_directory_path = os.path.join(args.upload_path, str(document.id))
    create_dirs(document_directory_path)

    for xml_file in glob.glob(args.xml_path + '/*.xml'):
        print(xml_file)
        layout = PageLayout(id=xml_file)
        layout.from_pagexml(xml_file)
        if not has_text(layout):
            continue

        image_file_id, _ = os.path.splitext(os.path.basename(xml_file))
        image_file = os.path.join(args.image_path, image_file_id + '.jpg')

        image_uid = uuid.uuid4()
        image_id = str(image_uid)
        file_path = os.path.join(document_directory_path, "{}{}".format(image_id, '.jpg'))
        try:
            copyfile(image_file, file_path)
        except:
            print('Image does not exist', image_file, xml_file)
            continue

        db_image = Image(id=image_uid, filename=image_file_id)

        img = PILImage.open(file_path)
        width, height = img.size
        db_image.path = file_path
        db_image.width = width
        db_image.height = height
        db_image.imagehash = str(dhash(img))
        document.images.append(db_image)
        print(image_file, xml_file, layout.page_size)
        scale = width / layout.page_size[1]

        for region_order, region in enumerate(layout.regions):
            region.polygon = (region.polygon * scale).astype(np.int32)
            db_region = TextRegion(order=region_order, np_points=region.polygon)
            db_image.textregions.append(db_region)

            for line_order, line in enumerate(region.lines):
                #line.transcription = line.transcription  + ' sssss uuuu  asdf[J] [j] [J]an uragan guragan test šaty sauna tugras'
                print(line.transcription)
                if not line.transcription:
                    line.transcription = ''
                    confidences = []
                else:
                    pass
                    line.transcription, confidences = apply_rules(line.transcription, replace_rules, weird_characters)
                print(line.transcription)

                try:
                    line.polygon = np.asarray(line.polygon)[:, ::-1] * scale
                    line.baseline = np.asarray(line.baseline)[:, ::-1] * scale

                    db_line = TextLine(order=line_order)
                    db_line.np_points = line.polygon
                    db_line.np_baseline = line.baseline
                    line_height = abs(line.polygon[0][1] - line.polygon[-1][1])
                    db_line.np_heights = [0.7*line_height, 0.3*line_height]
                    db_line.confidences = ' '.join([str(x) for x in confidences])
                    db_line.text = line.transcription
                    db_region.textlines.append(db_line)
                except:
                    print('Line Failed')
                    print('polygon', line.polygon)
                    print('polygon', line.baseline)



        db_session.commit()
    print('done')


if __name__ == '__main__':
    sys.exit(main())



