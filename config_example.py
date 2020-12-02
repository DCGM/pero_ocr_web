
database_url = 'sqlite:////home/kohutjan/data/pero_ocr_web_data/db.sqlite'


class Config(object):
    DEBUG = False
    UPLOADED_IMAGES_FOLDER = '/home/kohutjan/data/pero_ocr_web_data/uploaded_images/'
    PREVIEW_IMAGES_FOLDER = '/home/kohutjan/data/pero_ocr_web_data/uploaded_images/'
    LAYOUT_RESULTS_FOLDER = '/home/kohutjan/data/pero_ocr_web_data/layout_analysis_results/'
    OCR_RESULTS_FOLDER = '/home/kohutjan/data/pero_ocr_web_data/ocr_results/'
    MODELS_FOLDER = '/home/kohutjan/data/pero_ocr_web_data/models'
    LAYOUT_DETECTORS_FOLDER = '/home/kohutjan/data/pero_ocr_web_data/layout_detectors'
    KEYBOARD_FOLDER = '/home/kohutjan/data/pero_ocr_web_data/keyboard'
    EXTENSIONS = ('jpg', 'png', 'pdf', 'jpeg')
    SECRET_KEY = '35q0HKGItx35FvnC4G3uUrXXXzH8RBZ3'
    JSONIFY_PRETTYPRINT_REGULAR = False
    JSON_SORT_KEYS = False

