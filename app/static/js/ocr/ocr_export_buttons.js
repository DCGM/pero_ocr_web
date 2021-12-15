
class OCRExportButtons
{
    constructor()
    {

    }

    change_image(image_id)
    {
        document.getElementById('btn-export-page-xml').setAttribute("href", Flask.url_for('document.get_page_xml_lines', {'image_id': image_id, 'valid': 1}));
        document.getElementById('btn-export-alto-xml').setAttribute("href", Flask.url_for('document.get_alto_xml', {'image_id': image_id}));
        document.getElementById('btn-export-text').setAttribute("href", Flask.url_for('document.get_text', {'image_id': image_id}));
        document.getElementById('btn-export-img').setAttribute("href", Flask.url_for('document.get_image', {'image_id': image_id}));
    }
}