import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from app.db.model import TextLine, Annotation
import argparse
import uuid


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str, required=True, help="Database.")
    parser.add_argument('-a', '--annotations_file', type=str, required=True, help="text_line_id text_original text_edited")
    args = parser.parse_args()
    return args


def main():
    args = parseargs()

    database_url = 'sqlite:///' + args.database
    engine = create_engine(database_url, convert_unicode=True, connect_args={'check_same_thread': False})
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))

    doc_ann_counter = {}

    with open(args.annotations_file) as f:
        ann = f.readlines()

    for i in range(len(ann) // 4):
        text_line_id = ann[i * 4].strip()
        text_original = ann[i * 4 + 1].strip()
        text_edited = ann[i * 4 + 2].strip()
        annotation_time = ann[i * 4 + 3].strip()
        db_text_line = db_session.query(TextLine).filter(TextLine.text == text_original).first()
        if db_text_line is not None:
            print("TEXT LINE ID:", str(db_text_line.id))
            db_text_line.text = text_edited
            db_text_line.confidences = ' '.join([str(1) for _ in text_edited])
            ann_uuid = uuid.uuid4()
            db_annotation = Annotation(id=ann_uuid, text_original=text_original, text_edited=text_edited,
                                       deleted=False, user_id=db_text_line.region.image.document.user_id)
            db_text_line.annotations.append(db_annotation)
            doc = db_text_line.region.image.document
            doc_id = str(doc.id)
            print("NEW ANNOTATIONS", str(ann_uuid), "TEXT ORIGINAL:", text_original, "TEXT_EDITED:", text_edited)
            if doc_id in doc_ann_counter:
                doc_ann_counter[doc_id]['counter'] += 1
            else:
                doc_ann_counter[doc_id] = {"name": doc.name, "counter": 1}
            db_session.commit()
            db_session.refresh(db_text_line)
        else:
            print("TEXT LINE NOT FOUND IN DB FOR TEXT-ORIGINAL:", text_original)

    print()
    print("DOC STATS")
    print()

    doc_ann_counter = list(doc_ann_counter.items())
    doc_ann_counter.sort(key=lambda x: x[1]['counter'], reverse=True)
    for c in doc_ann_counter:
        print(c[0], c[1]['name'], c[1]['counter'])



if __name__ == '__main__':
    sys.exit(main())
