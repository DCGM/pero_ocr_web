import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import argparse
from app.db import Image
import os
import dateutil.parser


def parseargs():
    parser = argparse.ArgumentParser(description='Export document texts from database. Can take annotation snapshot from exact time by rolling back user edits.')
    parser.add_argument('-d', '--database', type=str, required=True, help="Database.")
    parser.add_argument('-i', '--document-uuid', type=str, nargs='+', required=True, help="Id of pages to export.")
    parser.add_argument('--datetime', type=str, required=True, help="Time where to roll back text.")
    parser.add_argument('-o', '--output-path', type=str, default='./', help="Time where to roll back text.")
    args = parser.parse_args()
    return args


def main():
    args = parseargs()

    engine = create_engine(args.database, convert_unicode=True, connect_args={})
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    target_datetime = dateutil.parser.isoparse(args.datetime)

    for document_uuid in args.document_uuid:
        print(f'document_uuid {document_uuid}')
        for image_db in db_session.query(Image).filter(Image.document_id == document_uuid).all():
            with open(os.path.join(args.output_path, f'{image_db.filename}.txt'), 'w') as f:
                for region_db in image_db.textregions:
                    for textline_db in region_db.textlines:
                        if textline_db.deleted:
                            continue
                        line_text = textline_db.text
                        for annottation_db in sorted(textline_db.annotations, key=lambda x: x.created_date, reverse=True):
                            if annottation_db.created_date > target_datetime:
                                line_text = annottation_db.text_original
                        print(line_text, file=f)


if __name__ == '__main__':
    sys.exit(main())
