import sys
from sqlalchemy import create_engine
import argparse
from app.db import Base


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-db', type=str, help="Database.")
    parser.add_argument('--dest-db', type=str, help="Database.")
    args = parser.parse_args()
    return args


def main():
    args = parseargs()

    src = create_engine(args.source_db, convert_unicode=True)

    dst = create_engine(args.dest_db, convert_unicode=True)

    tables = Base.metadata.tables
    table_order = ['users', 'documents', 'userdocuments', 'images', 'textregions', 'textlines', 'annotations',
              'layout_detectors', 'ocr', 'baseline', 'language_model', 'requests']
    for tbl in table_order:
        print('##################################')
        print(tbl, type(tbl))
        print(tables[tbl].select())
        data = src.execute(tables[tbl].select()).fetchall()
        if data:
            dst.execute(tables[tbl].insert(), data)

    print('done')


if __name__ == '__main__':
    sys.exit(main())



