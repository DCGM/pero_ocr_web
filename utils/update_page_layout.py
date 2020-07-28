import uuid

from app.db import Image, TextRegion, TextLine

from app.ocr.general import get_confidences


def update_page_layout(db_session, db_document, page_layout, image_id, path):
    db_image = db_session.query(Image).filter(Image.id == image_id).first()
    if db_image is None:
        db_image = create_image(page_layout, image_id, path)
        db_document.images.append(db_image)

    db_region_map = dict([(str(region.id), region) for region in db_image.textregions])
    for region_order, region in enumerate(page_layout.regions):
        if region.id in db_region_map:
            db_region = db_region_map[region.id]
            db_region.np_points = region.polygon
        else:
            db_region = create_text_region(region, region_order)
            db_image.textregions.append(db_region)

        db_line_map = dict([(str(line.id), line) for line in db_region.textlines])
        for line_order, line in enumerate(region.lines):
            if line.id in db_line_map:
                db_line = db_line_map[line.id]
                text = db_line.text
                if len(db_line.annotations) == 0:
                    db_line.text = line.transcription
                    db_line.np_confidences = get_confidences(line)
                    if text != db_line.text:
                        print(str(db_line.id), text, db_line.text)
                    else:
                        print(str(db_line.id), "MATCH")
                else:
                    print(str(db_line.id), "ANNOTATED")
            else:
                xml_line_id = line.id
                text_line = create_text_line(line, line_order)
                db_region.textlines.append(text_line)
                print("Created new line: {} {}".format(xml_line_id, str(text_line.id)))

    db_session.commit()

    return db_image


def create_text_line(line, order):
    try:
        line_id = uuid.UUID(line.id, version=4)
    except ValueError:
        line_id = uuid.uuid4()
    text_line = TextLine(id=line_id,
                         order=order,
                         np_points=line.polygon,
                         np_baseline=line.baseline,
                         np_heights=line.heights,
                         np_confidences=get_confidences(line),
                         text=line.transcription,
                         deleted=False)
    return text_line


def create_text_region(region, order):
    try:
        region_id = uuid.UUID(region.id, version=4)
    except ValueError:
        region_id = uuid.uuid4()
    text_region = TextRegion(id=region_id,
                             order=order,
                             np_points=region.polygon,
                             deleted=False)
    return text_region


def create_image(page_layout, image_id, path):
    try:
        image_id = uuid.UUID(image_id, version=4)
    except ValueError:
        image_id = uuid.uuid4()
    image = Image(id=image_id,
                  filename=page_layout.id,
                  path=path,
                  width=page_layout.page_size[1],
                  height=page_layout.page_size[0])
    return image
