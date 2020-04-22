import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import argparse
from app.db import Document
import os


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str, required=True, help="Database.")
    parser.add_argument('-i', '--document-id', type=str, required=True, help="Id of document.")
    args = parser.parse_args()
    return args


def main():
    args = parseargs()

    database_url = 'sqlite:///' + args.database
    engine = create_engine(database_url, convert_unicode=True, connect_args={'check_same_thread': False})
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))

    document = db_session.query(Document).filter(Document.id == args.document_id).first()
    for image in document.images:
        extension = os.path.splitext(image.filename)[1]
        print(image.filename, "{}{}".format(image.id, extension))


if __name__ == '__main__':
    sys.exit(main())
