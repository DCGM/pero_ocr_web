
// LINES ANNOTATOR
// #############################################################################

yx = L.latLng;
xy = function(x, y) {
    if (L.Util.isArray(x)) {    // When doing xy([x, y]);
        return yx(x[1], x[0]);
    }
    return yx(y, x);  // When doing xy(x, y);
};


class ImageEditor{
    constructor(container)
    {
        this.container = container;
        this.container.innerHTML = "<div class='editor-map'></div><div class='status'></div>";
        let save_btn = document.getElementById('save-btn')
        save_btn.addEventListener('click', this.save_annotations.bind(this));
    }

    get_image(document_id, image_id)
    {
        this.document_id = document_id;
        let route = Flask.url_for('ocr.get_lines', {'document_id': document_id, 'image_id': image_id});
        $.get(route, this.new_image_callback.bind(this));
        let text_container = document.getElementById('text-container');
        while (text_container.firstChild) {
            text_container.firstChild.remove();
        }
    }

    new_image_callback(data, status)
    {
        this.container.innerHTML = "<div class='editor-map'></div><div class='status'></div>";
        this.document_id = data['document_id'];
        this.image_id = data['image_id'];
        this.width = data['width'];
        this.height = data['height'];
        this.lines = data['lines'];

        for (let l of this.lines)
        {
            l.edited = false;
            l.saved = false;
        }

        this.map_element = this.container.getElementsByClassName("editor-map")[0]

        this.map = L.map(this.map_element, {
            crs: L.CRS.Simple,
            minZoom: -3,
            maxZoom: 3,
            center: [0, 0],
            zoom: 0,
            editable: true,
            fadeAnimation: false,
            zoomAnimation: false,
            zoomSnap: 0.2
        });

        let bounds = [xy(0, -this.height), xy(this.width, 0)];
        this.map.setView(xy(this.width / 2, -this.height / 2), -2);
        L.imageOverlay(Flask.url_for('document.get_image', {'document_id': this.document_id, 'image_id': this.image_id}), bounds).addTo(this.map);
        this.map.fitBounds(bounds);

        for (let i in this.lines)
        {
            this.add_line_to_map(i, this.lines[i]);
        }
        this.map_element.focus();
    }

    add_line_to_map(i, line, polygon)
    {
        let points = [];
        if (polygon)
        {
            line.polygon = polygon;
        }
        else
        {
            for (let point of line.np_points)
            {
                points.push(xy(point[0], -point[1]));
            }
            line.polygon = L.polygon(points);
            line.polygon.setStyle({ color: "#0059ff", opacity: 0.5, fillColor: "#0059ff", fillOpacity: 0.05, weight: 1});
        }
        line.polygon.addTo(this.map);
        line.polygon.on('click', this.polygon_click.bind(this, line));

        let text_line_element = document.createElement('div');
        text_line_element.setAttribute("contentEditable", "true");
        text_line_element.setAttribute("id", i);
        document.getElementById('text-container').appendChild(text_line_element);
        text_line_element.addEventListener('focus', this.line_click.bind(this, line));
        text_line_element.addEventListener('keypress', this.line_press.bind(this, line));
        text_line_element.addEventListener('paste', this.line_paste.bind(this, line));
        set_line_confidences_to_text_line_element(line, text_line_element);
        line.observer = new MutationObserver(this.line_mutated.bind(this, line));
        let config = { attributes: false, childList: true, characterData: true };
        line.observer.observe(text_line_element, config);
        line.text_line_element = text_line_element;

        if (line.annotated)
        {
            set_line_background_to_save(line.text_line_element);
        }
    }

    polygon_click(line){
        line.text_line_element.focus();
    }

    line_click(line)
    {
        for (let l of this.lines)
        {
            l.polygon.setStyle({ color: "#0059ff", opacity: 0.5, fillColor: "#0059ff", fillOpacity: 0.05, weight: 1});
        }
        let start_x = line.np_textregion_width[0];
        let start_y = line.np_baseline[0][1];
        let end_x = line.np_textregion_width[1];
        let end_y = line.np_baseline[line.np_baseline.length - 1][1];
        let line_length = end_x - start_x;
        let y_pad = line_length / 5;
        this.map.fitBounds([xy(start_x, -start_y + y_pad), xy(end_x, -end_y + y_pad)]);
        line.polygon.setStyle({ color: "#028700", opacity: 1, fillColor: "#028700", fillOpacity: 0.1, weight: 2});
    }

    line_mutated(line, e)
    {
        line.edited = true;
        line.saved = false;
        line.text_line_element.style.backgroundColor = "#ffcc54";
    }

    line_press(line, e)
    {
        e.preventDefault();

        if (e.keyCode == 13)
        {
            set_line_background_to_save(line.text_line_element);
            let annotations = [];
            let annotation_dict = {};
            annotation_dict["id"] = line.id;
            annotation_dict["text_original"] = line.text;
            annotation_dict["text_edited"] = line.text_line_element.textContent;
            annotations.push(annotation_dict);
            post_annotations(annotations, this.document_id);
            line.edited = false;
            line.saved = true;
            e.preventDefault();
            let line_number = parseInt(e.target.getAttribute("id"), 10);
            document.getElementById((line_number + 1).toString()).focus();
        }

        if (e.keyCode != 13 && e.keyCode != 9)
        {
            insert_new_char_to_current_position(String.fromCharCode(e.keyCode));
        }
    }

    line_paste(line, e)
    {
        e.preventDefault();
        let text = (e.originalEvent || e).clipboardData.getData('text/plain');
        for (let i = 0; i < text.length; i++)
        {
            insert_new_char_to_current_position(text.charAt(i));
        }
    }

    save_annotations()
    {
        let annotations = [];
        for (let l of this.lines)
        {
            if (l.edited)
            {
                set_line_background_to_save(l.text_line_element);
                let annotation_dict = {};
                annotation_dict["id"] = l.id;
                annotation_dict["text_original"] = l.text;
                annotation_dict["text_edited"] = l.text_line_element.textContent;
                annotations.push(annotation_dict);
                l.edited = false;
                l.saved = true;
            }
        }
        post_annotations(annotations, this.document_id);
    }
}

let image_editor = new ImageEditor(document.getElementById('map-container'));

// #############################################################################


// PAGE CHANGE EVENT
// #############################################################################
$('.image-item-container').on('click', function (event) {
    let document_id = $(this).data('document');
    let image_id = $(this).data('image');
    image_index = $(this).data('index');
    $('.image-item-active').addClass('d-none');
    $(this).find('.image-item-active').removeClass('d-none');
    document.getElementById('btn-export-page-xml').setAttribute("href", Flask.url_for('document.get_page_xml_lines', {'image_id': image_id}))
    document.getElementById('btn-export-alto-xml').setAttribute("href", Flask.url_for('document.get_alto_xml', {'image_id': image_id}))
    document.getElementById('btn-export-text').setAttribute("href", Flask.url_for('document.get_text', {'image_id': image_id}))
    if (typeof image_editor.lines !== 'undefined')
    {
        let unsaved_lines = false;
        for (let l of image_editor.lines)
        {
            if (l.edited)
            {
                unsaved_lines = true;
            }
        }
        if (unsaved_lines)
        {
            if (confirm("Save changes?"))
            {
                image_editor.save_annotations();
            }
        }
    }
    image_editor.get_image(document_id, image_id)
});
// #############################################################################


// PAGE NAVIGATION
// #############################################################################
let image_index = 0;
let image_containers = $('.image-item-container');
let number_of_images = image_containers.length;
if (number_of_images)
{
    let first_image_container = image_containers[image_index];
    $(first_image_container).click();
    $(first_image_container).find('.image-item-active').removeClass('d-none');
}
let back_btn = document.getElementById('back-btn')
back_btn.addEventListener('click', previous_page);
let next_btn = document.getElementById('next-btn')
next_btn.addEventListener('click', next_page);
function previous_page()
{
    if (image_index > 0)
    {
        image_index -= 1;
        $('.image-item-container[data-index=' + image_index + ']').click();
    }
}
function next_page()
{
    if ((image_index + 1) < number_of_images)
    {
        image_index += 1;
        $('.image-item-container[data-index=' + image_index + ']').click();
    }
}
// #############################################################################


// POST ANNOTATION TO SERVER
// #############################################################################

function post_annotations(annotations, document_id)
{
    console.log(annotations);
    console.log(JSON.stringify(annotations));
    let route = Flask.url_for('ocr.save_annotations', {'document_id': document_id});
    $.ajax({
        type: "POST",
        url: route,
        data: {annotations: JSON.stringify(annotations)},
        dataType: "json",
        success: function(data, textStatus) {
            if (data.status == 'redirect') {
                // data.redirect contains the string URL to redirect to
                window.location.href = data.href;
            }
        },
        error: function(xhr, ajaxOptions, ThrownError){
            alert('Unable to save annotation. Check your remote connection. ');
        }
    });
}

// #############################################################################


// HELPER FUNCTIONS
// #############################################################################

function set_line_confidences_to_text_line_element(line, text_line_element)
{
    let chars = line.text.split("");
    for (let i in line.np_confidences)
    {
        let char_span = document.createElement('span');
        char_span.setAttribute("style", "font-size: 150%; background: " + rgbToHex(255, Math.floor(line.np_confidences[i] * 255), Math.floor(line.np_confidences[i] * 255)));
        char_span.innerHTML = chars[i];
        text_line_element.appendChild(char_span);
    }
}

function insert_new_char_to_current_position(char)
{
    let selection = document.getSelection();
    let caret_span = selection.anchorNode.parentNode;
    let new_span = document.createElement('span');
    new_span.setAttribute("style", "font-size: 150%; background: #ffffff; color: #028700");
    if (char == " ")
    {
        char = "&nbsp;"
    }
    new_span.innerHTML = char;
    caret_span.parentNode.insertBefore(new_span, caret_span.nextSibling);
    let range = selection.getRangeAt(0);
    range.collapse(false);
    range.selectNodeContents(new_span.childNodes[0]);
    range.collapse(false);
    selection.removeAllRanges();
    selection.addRange(range);
}

function set_line_background_to_save(text_line_element)
{
    text_line_element.style.backgroundColor = "#d0ffcf";
    let descendents = text_line_element.getElementsByTagName('*');
    for (let child of descendents)
    {
        child.style.backgroundColor = "#d0ffcf";
    }
}

function componentToHex(c) {
    let hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

// #############################################################################