from app.db.model import Document, DocumentState, Image
from app.db.general import get_document_by_id, remove_document_by_id, save_document, save_image_to_document,\
    get_all_users, get_user_by_id, get_image_by_id, is_image_duplicate
import os
from flask import current_app as app
from app import db_session
from PIL import Image as PILImage
import uuid
from lxml import etree as ET
from app.db import Document, Image, TextLine, Annotation


def dhash(image, hash_size=8):
    # Grayscale and shrink the image in one step.
    image = image.convert('L').resize(
        (hash_size + 1, hash_size),
    )

    pixels = list(image.getdata())
    # Compare adjacent pixels.
    difference = []
    for row in range(hash_size):
        for col in range(hash_size):
            pixel_left = image.getpixel((col, row))
            pixel_right = image.getpixel((col + 1, row))
            difference.append(pixel_left > pixel_right)
    # Convert the binary array to a hexadecimal string.
    decimal_value = 0
    hex_string = []
    for index, value in enumerate(difference):
        if value:
            decimal_value += 2 ** (index % 8)
        if (index % 8) == 7:
            hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
            decimal_value = 0
    return ''.join(hex_string)


def create_document(name, user):
    document = Document(
        name=name, user=user, state=DocumentState.NEW)
    save_document(document)
    return document


def check_and_remove_document(document_id, user):
    if is_document_owner(document_id, user):
        remove_document_by_id(document_id)
        return True
    return False


def is_document_owner(document_id, user):
    document = get_document_by_id(document_id)
    if document and document.user.id == user.id:
        return True
    else:
        return False


def is_user_owner_or_collaborator(document_id, user):
    document = get_document_by_id(document_id)
    if is_document_owner(document_id, user):
        return True
    if user in document.collaborators:
        return True
    return False


def save_images(file, document_id):
    document = get_document_by_id(document_id)
    directory_path = get_and_create_document_image_directory(document_id)

    if is_allowed_file(file):
        image_db = Image(id=uuid.uuid4(), filename=file.filename)
        image_id = str(image_db.id)
        extension = os.path.splitext(file.filename)[1]
        file_path = os.path.join(directory_path, "{}{}".format(image_id, extension))
        file.save(file_path)
        img = PILImage.open(file_path)
        img_hash = str(dhash(img))
        if is_image_duplicate(document_id, img_hash):
            return 'Image is already uploaded.'
        width, height = img.size
        image_db.path = file_path
        image_db.width = width
        image_db.height = height
        image_db.imagehash = img_hash
        save_image_to_document(document, image_db)
    else:
        return 'Not allowed extension.'
    return ''


def get_and_create_document_image_directory(document_id):
    directory_path = os.path.join(app.config['UPLOAD_IMAGE_FOLDER'], document_id)
    create_dirs(directory_path)
    return directory_path


def is_allowed_file(file):
    if file.filename != '' and is_allowed_extension(file, app.config['EXTENSIONS']):
        return True
    return False


def is_allowed_extension(file, allowed_extensions):
    if str(file.filename).lower().endswith(allowed_extensions):
        return True
    return False


def create_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_image_url(image_id):
    image = get_image_by_id(image_id)
    return image.path


def remove_image(document_id, image_id):
    document = get_document_by_id(document_id)
    image = document.images.filter_by(id=image_id, deleted=False).first()
    if image:
        image.deleted = True
        db_session.commit()
        return True
    return False


def get_possible_collaborators(document):
    users = get_all_users()
    return list(filter(lambda user: user.id != document.user.id, users))


class UserSelectItem:
    def __init__(self, user, is_selected=False):
        self.user = user
        self.is_selected = is_selected


def get_collaborators_select_data(document):
    select_items = []
    possible_collaborators = get_possible_collaborators(document)

    for user in possible_collaborators:
        is_selected = is_user_collaborator(document, user)
        user_select_item = UserSelectItem(user=user, is_selected=is_selected)
        select_items.append(user_select_item)
    return select_items


def save_collaborators(document_id, collaborators_ids):
    document = get_document_by_id(document_id)

    for old_collaborator in document.collaborators:
        if str(old_collaborator.id) not in collaborators_ids:
            document.collaborators.remove(old_collaborator)

    for collaborator_id in collaborators_ids:
        user = get_user_by_id(collaborator_id)
        if user not in document.collaborators:
            document.collaborators.append(user)
    db_session.commit()


def is_user_collaborator(document, user):
    if user in document.collaborators:
        return True
    return False


def get_document_images(document):
    return document.images.filter_by(deleted=False)


def get_region_xml_root(image_id):
    image = get_image_by_id(image_id)
    root = ET.Element('PcGts')
    root.set('xmlns', 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15')

    page_element = ET.SubElement(root, 'Page',
                                 {"imageFilename": os.path.splitext(image.filename)[0], "imageWidth": str(image.width),
                                  "imageHeight": str(image.height)})

    for text_region in image.textregions:
        if not text_region.deleted:
            text_region_element = ET.SubElement(page_element, 'TextRegion', {"id": str(text_region.id)})
            ET.SubElement(text_region_element, 'Coords', {"points": text_region.points})
    return root


def get_page_xml_root(image_id, only_annotated=False):
    print(image_id)
    text = ""
    image = get_image_by_id(image_id)
    root = ET.Element("PcGts")
    root.set("xmlns", "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15")

    page_element = ET.SubElement(root, "Page")
    page_element.set("imageFilename", os.path.splitext(image.filename)[0])
    page_element.set("imageWidth", str(image.width))
    page_element.set("imageHeight", str(image.height))

    skip_textregion_sorting = False
    for tr in image.textregions:
        if tr.order is None:
            skip_textregion_sorting = True
    if not skip_textregion_sorting:
        textregions = sorted(list(image.textregions), key=lambda x: x.order)
    else:
        textregions = image.textregions
    for text_region in textregions:
        if not text_region.deleted:
            text_region_element = ET.SubElement(page_element, "TextRegion")
            text_region_element.set("id", str(text_region.id))
            coords = ET.SubElement(text_region_element, "Coords")
            coords.set("points", text_region.points)

            textlines = TextLine.query.filter_by(region_id=text_region.id).distinct()
            if only_annotated:
                textlines = textlines.join(Annotation)
            textlines = textlines.order_by(TextLine.order)
            textlines = textlines.all()
            for text_line in textlines:
                if not text_line.deleted:
                    text_line_element = ET.SubElement(text_region_element, "TextLine")
                    text_line_element.set("id", str(text_line.id))
                    heights = text_line.np_heights
                    text_line_element.set("custom", "heights {" + str(int(heights[0])) + ", " + str(int(heights[1])) + "}")

                    coords_element = ET.SubElement(text_line_element, "Coords")
                    points = text_line.np_points
                    points = ["{},{}".format(int(x[0]), int(x[1])) for x in points]
                    points = " ".join(points)
                    coords_element.set("points", points)

                    baseline_element = ET.SubElement(text_line_element, "Baseline")
                    points = text_line.np_baseline
                    points = ["{},{}".format(int(x[0]), int(x[1])) for x in points]
                    points = " ".join(points)
                    baseline_element.set("points", points)

                    text_element = ET.SubElement(text_line_element, "TextEquiv")
                    text_element = ET.SubElement(text_element, "Unicode")
                    text_tmp = ""
                    if text_line.text is not None:
                        text_tmp = text_line.text
                    text_element.text = text_tmp
                    text += text_tmp + '\n'

    return root, text

