import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from pero_ocr.document_ocr.layout import PageLayout
from utils.update_page_layout import update_page_layout
from app.db.model import Document, DocumentState, Image
import argparse
import os
import uuid
from shutil import copyfile


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str, required=True, help="Database.")
    parser.add_argument('-o', '--document-folder', type=str, required=True, help="Folder with xmls and logits (page, logits).")
    parser.add_argument('-n', '--document-name', type=str, help="Document name (will be used if document is not in the database)")
    parser.add_argument('-u', '--uploaded-images-dir', type=str, help="Path to uploaded images")
    parser.add_argument('-l', '--only-layout', action='store_true')
    parser.add_argument('--logits', action='store_true')
    args = parser.parse_args()
    return args


def main():
    args = parseargs()

    database_url = 'postgres://postgres:pero@localhost:5432/' + args.database
    engine = create_engine(database_url, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))

    db_document = None
    for image in os.listdir(os.path.join(args.document_folder, 'images')):
        image_id = image.split('.')[0]
        try:
            image_id = uuid.UUID(image_id, version=4)
            db_image = db_session.query(Image).filter(Image.id == image_id).first()
            if db_image is not None:
                db_document = db_image.document
                if db_document.deleted:
                    print("DELETED DOCUMENT")
                    sys.exit(0)
                else:
                    if args.only_layout:
                        db_document.state = DocumentState.COMPLETED_LAYOUT_ANALYSIS
                    else:
                        db_document.state = DocumentState.COMPLETED_OCR
        except ValueError:
            break
        break

    if db_document is None:
        if args.only_layout:
            document_state = DocumentState.COMPLETED_LAYOUT_ANALYSIS
        else:
            document_state = DocumentState.COMPLETED_OCR
        db_document = Document(id=uuid.uuid4(),
                               name=args.document_name,
                               state=document_state,
                               user_id=622)
        db_session.add(db_document)
        print("NEW DOCUMENT WAS CREATED.")
    else:
        print("DOCUMENT ALREADY EXISTS, UPDATING IMAGES.")
    print(db_document.id)
    print(db_document.name)

    uploaded_images_dir = os.path.join(args.uploaded_images_dir, str(db_document.id))
    if not os.path.exists(uploaded_images_dir):
        os.makedirs(uploaded_images_dir)

    for image in os.listdir(os.path.join(args.document_folder, 'images')):
        image_ext = image.split('.')[1]
        break

    for image in os.listdir(os.path.join(args.document_folder, 'xmls')):
        image_id = image.split('.')[0]

        page_layout = PageLayout()

        xml_path = os.path.join(args.document_folder, 'xmls', image)
        page_layout.from_pagexml(xml_path)

        if not args.only_layout and args.logits:
            logits_path = os.path.join(args.document_folder, 'output', 'logits', "{}.logits".format(image_id))
            page_layout.load_logits(logits_path)

        image_name = "{}.{}".format(image_id, image_ext)
        copy_image_from_path = os.path.join(args.document_folder, 'images', image_name)
        copy_image_to_path = os.path.join(uploaded_images_dir, image_name)

        db_image = update_page_layout(db_session=db_session, db_document=db_document, page_layout=page_layout,
                                      image_id=image_id, path=copy_image_to_path)

        if not os.path.exists(db_image.path):
            copyfile(copy_image_from_path, db_image.path)
            print("CP {} {}".format(copy_image_from_path, db_image.path))

        print("IMG {} ADDED/UPDATED TO DB.".format(image_id))


if __name__ == '__main__':
    sys.exit(main())