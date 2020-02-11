from app import db_session
from sqlalchemy import create_engine
from config import *
import sys
from app.document.general import dhash, is_image_duplicate
from PIL import Image as PILImage
from uuid import uuid4

engine = create_engine(database_url, convert_unicode=True, connect_args={'check_same_thread': False})


def init_db():
    from app.db import Base
    Base.metadata.create_all(bind=engine)


def main():
    init_db()
    from app.db.model import Image
    images = Image.query.filter_by( deleted=False).all()
    for image in images:
        if not image.imagehash or image.imagehash == '':
            try:
                img = PILImage.open(image.path)
                img_hash = str(dhash(img))
            except:
                img_hash = str(uuid4())
            image.imagehash = img_hash
            db_session.commit()
            print('Change')
    return 0


if __name__ == '__main__':
    sys.exit(main())





