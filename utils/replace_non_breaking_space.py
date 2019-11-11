import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import argparse
from app.db import TextLine, Annotation


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
    for textline in textlines:
        if textline.text is not None:
            if u"\u00A0" in textline.text:
                print(textline.text)
                textline.text = textline.text.replace(u"\u00A0", ' ')
    db_session.commit()

    annotations = db_session.query(Annotation).all()
    for annotation in annotations:
        if annotation.text_original is not None:
            if u"\u00A0" in annotation.text_original:
                print(annotation.text_original)
                annotation.text_original = annotation.text_original.replace(u"\u00A0", ' ')
        if annotation.text_edited is not None:
            if u"\u00A0" in annotation.text_edited:
                print(annotation.text_edited)
                annotation.text_edited = annotation.text_edited.replace(u"\u00A0", ' ')
    db_session.commit()

if __name__ == '__main__':
    sys.exit(main())
