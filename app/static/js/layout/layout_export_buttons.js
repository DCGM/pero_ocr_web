
class LayoutExportButtons
{
    constructor()
    {

    }

    change_image(image_id)
    {
        document.getElementById('btn-export-page-xml').setAttribute("href", Flask.url_for('document.get_page_xml_lines', {'image_id': image_id}));
        document.getElementById('btn-export-img').setAttribute("href", Flask.url_for('document.get_image', {'image_id': image_id}));
    }
}