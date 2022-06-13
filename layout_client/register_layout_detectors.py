import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import argparse
from app.db import LayoutDetector


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str, required=True, help="Database to register layout engines.")
    parser.add_argument('-r', '--replace', action="store_true", help="Replace all layout engines.")
    args = parser.parse_args()
    return args


layout_engines = [
    {"name": "NONE", "description": "Don't use any layout detector."},
    {"name": "Whole Page Region", "description": "Set layout as whole page region."},
    {"name": "Simple Threshold Region", "description": "Simple and fast layout detector based on segmentation that works on nice binarized single column pages."},
    {"name": "Complex printed and handwritten layout", "description": "This model is able to segment most documents. It is suitable for most prints (including complex pages such as newspapers) and for most handwritten documents. It may fail on handwritten tables where text lines cross table boundaries."},
    {"name": "Complex printed and handwritten layout (experimental)", "description": "This is experimental version, use at your own risk. This model is able to segment most documents. It is suitable for most prints (including complex pages such as newspapers) and for most handwritten documents. It may fail on handwritten tables where text lines cross table boundaries."},
    {"name": "Printed layout", "description": "Layout detector optimized for a variety of historical printed books and documents including complex layouts such as newspapers and legal documents."}
    ]


def main():
    args = parseargs()

    database_url = 'postgresql://postgres:pero@localhost:5432/' + args.database
    engine = create_engine(database_url, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))

    if args.replace:
        for db_ocr in db_session.query(LayoutDetector).all():
            db_ocr.active = False
        db_session.commit()

    for layout_detector in layout_engines:
        if db_session.query(LayoutDetector).filter(LayoutDetector.name == layout_detector['name']).filter(LayoutDetector.active == True).first() is None:
            db_ocr = LayoutDetector(**layout_detector)
            db_session.add(db_ocr)
            print('ADDED ', layout_detector)
        else:
            print('SKIPPING', layout_detector)

    db_session.commit()


if __name__ == '__main__':
    sys.exit(main())
