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
    {"name": "NONE", "description": "Skip layout analysis."},
    {"name": "layout_coloraug_degrade_bnorm", "description": "Basic layout detector."},
    {"name": "simple_threshold_region", "description": "Works on single column pages."}
]


def main():
    args = parseargs()

    database_url = 'sqlite:///' + args.database
    engine = create_engine(database_url, convert_unicode=True, connect_args={'check_same_thread': False})
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
