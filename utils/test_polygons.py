import argparse
from collections import Counter

from app.db import Base, TextRegion, Image, Document
from sqlalchemy.orm import scoped_session, sessionmaker

from sqlalchemy import create_engine, select
from pero_ocr.core.layout import TextLine, guess_line_heights_from_polygon

from app.db.model import str_points2D_to_np, str_points_to_np
from app.db import TextLine as DbTextLine


def get_args():
    """
    method for parsing of arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--database", required=True)

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = get_args()
    round_to = 0

    conn = create_engine('{}' .format(args.database)).connect()
    q = select([DbTextLine])

    proxy = conn.execution_options(stream_results=True).execute(q)
    bad_dictionary = dict()
    bad_dictionary['textlines'] = set()
    bad_dictionary['textregions'] = set()
    bad_dictionary['images'] = set()
    bad_dictionary['documents'] = set()
    bad_textlines = list()
    while 'batch not empty':
        batch = proxy.fetchmany(100000)  # 100,000 rows at a time

        if not batch:
            break

        for row in batch:
            txl = TextLine(id=row.id,
                           baseline=str_points2D_to_np(row.baseline),
                           polygon=str_points2D_to_np(row.points),
                           heights=str_points_to_np(row.heights))
            if not guess_line_heights_from_polygon(txl):
                continue

            db_heights = str_points_to_np(row.heights)
            computed_heights = txl.heights
            if abs(round(db_heights[0], round_to) - round(computed_heights[0], round_to)) > 5 or abs(round(db_heights[1], round_to) - round(computed_heights[1], round_to)) > 5:
                bad_textlines.append(row)
                bad_dictionary['textlines'].add(str(row.id))

    proxy.close()

    engine = create_engine('{}' .format(args.database),
                           convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    Base.query = db_session.query_property()
    Base.metadata.create_all(bind=engine)

    documents = list()
    images = list()
    documents_images = dict()
    for row in bad_textlines:
        image = db_session.query(Image).join(TextRegion).filter(TextRegion.id == row.region_id).first()
        document = db_session.query(Document).join(Image).join(TextRegion).filter(TextRegion.id == row.region_id).first()
        if document != None and image != None:
            documents.append(document.id)
            images.append(image.id)
            try:
                documents_images[document.id].append(tuple((image.id, image.filename)))
            except:
                documents_images[document.id] = [tuple((image.id, image.filename))]

    documents_sorted = Counter(documents).most_common()
    for document in documents_sorted:
        print("Document: {} - errors: {}" .format(document[0], document[1]))
        document_images_sorted = Counter(documents_images[document[0]]).most_common()
        for image in document_images_sorted:
            print("    Image: {} ({}) - errors: {}" .format(image[0][0], image[0][1], image[1]))
