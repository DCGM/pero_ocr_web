import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import argparse
import os
from app.db import Image, Document


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str, required=True, help="Database.")
    args = parser.parse_args()
    return args


def main():
    args = parseargs()

    database_url = 'postgresql://postgres:pero@localhost:5432/' + args.database
    engine = create_engine(database_url, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    for document_db in db_session.query(Document).all():
        if document_db.user.email == "#revert_OCR_backup#":
            print()
            print(document_db.name)
            orig_doc_name = document_db.name[14:]
            candidate_orig_docs = db_session.query(Document).filter(Document.name == orig_doc_name).all()
            print([x.name for x in candidate_orig_docs])
            print()
        for image_db in document_db.images:
            if os.path.basename(image_db.path) != image_db.path:
                image_db.path = os.path.join(*image_db.path.split('/')[-2:]).strip()
            else:
                if document_db.user.email == "#revert_OCR_backup#":
                    candidate_found = False
                    for candidate_orig_doc in candidate_orig_docs:
                        if not candidate_found:
                            for candidate_image in candidate_orig_doc.images:
                                if os.path.basename(candidate_image.path).strip() == image_db.path.strip():
                                    print("FOUND")
                                    print(image_db.path)
                                    image_db.path = os.path.join(candidate_orig_doc.id, image_db.path).strip()
                                    print(image_db.path)
                                    print()
                                    candidate_found = True
                                    break
                        else:
                            break
                    if not candidate_found:
                        print("NOT FOUND")
                        print(image_db.path)
                        image_db.path = os.path.join(image_db.document.id, image_db.path).strip()
                        print(image_db.path)
                        print()
                else:
                    image_db.path = os.path.join(image_db.document.id, image_db.path).strip()

    db_session.commit()


if __name__ == '__main__':
    sys.exit(main())
