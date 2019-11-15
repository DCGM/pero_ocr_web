import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import argparse
from app.db import Document, Image
import os
from PIL import Image, ImageDraw

def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str, required=True, help="Database.")
    parser.add_argument('-o', '--output', type=str, required=True, help="Output folder for image previews.")
    args = parser.parse_args()
    return args


def main():
    args = parseargs()

    database_url = 'sqlite:///' + args.database
    engine = create_engine(database_url, convert_unicode=True, connect_args={'check_same_thread': False})
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))

    documents = db_session.query(Document).all()
    for document in documents:
        document_path = os.path.join(args.output, str(document.id))
        if not os.path.exists(document_path):
            os.mkdir(document_path)
        for image_db in document.images:
            if os.path.exists(image_db.path):
                image = Image.open(image_db.path)
                image = image.convert('RGB')

                for region in image_db.textregions:
                    points = region.np_points
                    points_new = []
                    for p in points:
                        points_new.append((int(p[1]), int(p[0])))
                    ImageDraw.Draw(image).line(points_new, width=35, fill=(0, 255, 0))
                new_path = os.path.join(document_path, str(image_db.id) + '.jpg')
                scale = (100000.0 / (image.width * image.height)) ** 0.5
                image = image.resize((int(image.width * scale + 0.5), int(image.height * scale + 0.5)),
                                     resample=Image.LANCZOS)
                print(image.width, image.height, scale)
                image.save(new_path)
        print("DOCUMENT PROCESSED.")
    db_session.commit()

if __name__ == '__main__':
    sys.exit(main())



