import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import argparse
import os
from app.db import Image


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str, required=True, help="Database.")
    args = parser.parse_args()
    return args


def main():
    args = parseargs()

    database_url = 'postgres://postgres:pero@localhost:5432/' + args.database
    engine = create_engine(database_url, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    for image_db in db_session.query(Image).all():
        image_db.path = os.path.basename(image_db.path)
    db_session.commit()


if __name__ == '__main__':
    sys.exit(main())
