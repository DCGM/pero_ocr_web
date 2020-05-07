import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import argparse
import numpy as np
from app.db import TextLine, TextRegion, Image, Document


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str, required=True, help="Database.")
    args = parser.parse_args()
    return args


def main():
    args = parseargs()

    database_url = 'sqlite:///' + args.database
    engine = create_engine(database_url, convert_unicode=True, connect_args={'check_same_thread': False})
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))

    textlines = db_session.query(TextLine).all()
    number_of_textlines = len(textlines)
    for i, textline in enumerate(textlines):
        textline.score = np.average(textline.np_confidences)
        if (i + 1) % 10000 == 0:
            db_session.commit()
            print("{}/{} DONE".format(i + 1, number_of_textlines))
    db_session.commit()


if __name__ == '__main__':
    sys.exit(main())
