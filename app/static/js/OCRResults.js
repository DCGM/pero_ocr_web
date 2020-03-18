yx = L.latLng;
xy = function(x, y) {
    if (L.Util.isArray(x)) {    // When doing xy([x, y]);
        return yx(x[1], x[0]);
    }
    return yx(y, x);  // When doing xy(x, y);
};

function componentToHex(c) {
    var hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

function setColor(front_color, back_color) {
    document.execCommand('styleWithCSS', false, true);
    document.execCommand('foreColor', false, front_color);
    document.execCommand('backColor', false, back_color);
}

function replaceNbsps(str) {
  var re = new RegExp(String.fromCharCode(160), "g");
  return str.replace(re, " ");
}

function get_edited_text(text_line_element){
    return text_line_element.textContent;
}

function post_annotations(annotations, document_id)
{
    console.log(annotations);
    console.log(JSON.stringify(annotations));
    var route = Flask.url_for('ocr.save_annotations', {'document_id': document_id});
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

function set_line_background_to_save(text_line_element)
{
    text_line_element.style.backgroundColor = "#d0ffcf";
    for (let child of text_line_element.childNodes)
    {
        child.style.backgroundColor = "#d0ffcf";
    }
}


class ImageEditor{
    constructor(container) {
        this.container = container;
        this.container.innerHTML = "<div class='editor-map'></div><div class='status'></div>";
        var save_btn = document.getElementById('save-btn')
        save_btn.addEventListener('click', this.save_annotations.bind(this));
    }

    get_image(document_id, image_id) {
        this.document_id = document_id;
        var route = Flask.url_for('ocr.get_lines', {'document_id': document_id, 'image_id': image_id});
        $.get(route, this.new_image_callback.bind(this));
        var text_container = document.getElementById('text-container');
        while (text_container.firstChild) {
            text_container.firstChild.remove();
        }
    }

    new_image_callback(data, status) {
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
        let image = L.imageOverlay(Flask.url_for('document.get_image', {'document_id': this.document_id, 'image_id': this.image_id}), bounds).addTo(this.map);

        //zoom_level = Math.log(annotator_data.width / 256.0) / Math.log(2)
        this.map.fitBounds(bounds);


        for (let i in this.lines) {
            this.add_line_to_map(i, this.lines[i]);
        }
        this.map_element.focus();
        //map_element.onkeydown = this.basic_keypress.bind(this);
    }

    set_confidences_line(text_line_div, line){
        var chars = line.text.split("");
        for(let i in line.np_confidences)
        {
            var char_span = document.createElement('span');
            char_span.setAttribute("style", "font-size: 150%; background: " + rgbToHex(255, Math.floor(line.np_confidences[i] * 255), Math.floor(line.np_confidences[i] * 255)));
            char_span.innerHTML = chars[i];
            text_line_div.appendChild(char_span);
        }
    }

    add_line_to_map(i, line, polygon){
        let points = [];
        if(polygon){
            line.polygon = polygon;
        } else {
            for( let point of line.np_points){
                points.push(xy(point[0], -point[1]));
            }
            line.polygon = L.polygon(points);
            line.polygon.setStyle({ color: "#0059ff", opacity: 1, fillColor: "#0059ff", fillOpacity: 0.1});
        }
        line.polygon.addTo(this.map);
        line.polygon.on('click', this.polygon_click.bind(this, line));
        //this.update_style(position);

        var text_line_div = document.createElement('div');
        text_line_div.setAttribute("contentEditable", "true");
        text_line_div.setAttribute("id", i);
        this.set_confidences_line(text_line_div, line);
        document.getElementById('text-container').appendChild(text_line_div);
        line.text_line_element = text_line_div;
        text_line_div.addEventListener('focus', this.line_click.bind(this, line));
        text_line_div.addEventListener('keypress', this.line_press.bind(this, line));
        if (line.annotated) {
            set_line_background_to_save(text_line_div);
        }
    }

    polygon_click(line){
        line.text_line_element.focus();
    }

    line_click(line){
        for (let l of this.lines)
        {
            l.polygon.setStyle({ color: "#0059ff", opacity: 1, fillColor: "#0059ff", fillOpacity: 0.1});
        }
        var start_x = line.np_textregion_width[0];
        var start_y = line.np_baseline[0][1];
        var end_x = line.np_textregion_width[1];
        var end_y = line.np_baseline[line.np_baseline.length - 1][1];
        var line_length = end_x - start_x;
        var y_pad = line_length / 5;
        this.map.fitBounds([xy(start_x, -start_y + y_pad), xy(end_x, -end_y + y_pad)]);
        line.polygon.setStyle({ color: "#028700", opacity: 1, fillColor: "#028700", fillOpacity: 0.1});
    }

    line_press(line, e){
        for (let child of e.target.childNodes)
        {
            if (child.innerHTML == "")
            {
                e.target.removeChild(child);
            }
        }
        setColor("#028700", "#ffffff");

        if (e.keyCode == 13)
        {
            set_line_background_to_save(line.text_line_element);
            var annotations = [];
            var annotation_dict = {};
            annotation_dict["id"] = line.id;
            annotation_dict["text_original"] = line.text;
            annotation_dict["text_edited"] = get_edited_text(line.text_line_element);
            annotations.push(annotation_dict);
            post_annotations(annotations, this.document_id);
            line.edited = false;
            line.saved = true;
            e.preventDefault();
            var line_number = parseInt(e.target.getAttribute("id"), 10);
            document.getElementById((line_number + 1).toString()).focus();
        }

        if (e.keyCode != 13 && e.keyCode != 9)
        {
            line.text_line_element.style.backgroundColor = "#ffcc54";
            line.edited = true;
            line.saved = false;
        }
    }

    save_annotations(){
        var annotations = [];
        for (let l of this.lines)
        {
            if (l.edited)
            {
                set_line_background_to_save(l.text_line_element);
                var annotation_dict = {};
                annotation_dict["id"] = l.id;
                annotation_dict["text_original"] = l.text;
                annotation_dict["text_edited"] = get_edited_text(l.text_line_element);
                annotations.push(annotation_dict);
                l.edited = false;
                l.saved = true;
            }
        }
        post_annotations(annotations, this.document_id);
    }





    basic_keypress(e) {
        // g - not deleted
        // h - not ignored
        // j - aligner
        // o - reset original object annotation

        // n, s - save

        if(e.key == "o") {
            this.get_image();
        } else if(e.key == "n" || e.key == "s") {
            this.save_objects();
        } else if(e.key == "c"){
            this.create_new_object();
        } else if(e.key == 'g'){
            this.toggle_delete_object();
        } else if(e.key == 'h'){
            this.toggle_ignore_object();
        } else if(e.key == 'j'){
            this.get_image(true)
        }
    }

}


function previous_page() {
    if (image_index > 0)
    {
        image_index -= 1;
        $('.image-item-container[data-index=' + image_index + ']').click();
    }
}


function next_page() {
    if ((image_index + 1) < number_of_images)
    {
        image_index += 1;
        $('.image-item-container[data-index=' + image_index + ']').click();
    }
}


$('.image-item-container').on('click', function (event) {
    let document_id = $(this).data('document');
    let image_id = $(this).data('image');
    image_index = $(this).data('index');
    $('.image-item-active').addClass('d-none');
    $(this).find('.image-item-active').removeClass('d-none');
    document.getElementById('export_page_xml_form').setAttribute("action", Flask.url_for('document.get_page_xml_lines', {'image_id': image_id}))
    document.getElementById('export_alto_xml_form').setAttribute("action", Flask.url_for('document.get_alto_xml', {'image_id': image_id}))
    document.getElementById('export_text_form').setAttribute("action", Flask.url_for('document.get_page_text', {'image_id': image_id}))
    if (typeof image_editor.lines !== 'undefined')
    {
        unsaved_lines = false;
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


var image_editor = new ImageEditor(document.getElementById('map-container'));

var back_btn = document.getElementById('back-btn')
back_btn.addEventListener('click', previous_page);
var next_btn = document.getElementById('next-btn')
next_btn.addEventListener('click', next_page);


let $image_containers = $('.image-item-container');
var number_of_images = $image_containers.length
if (number_of_images) {
    var image_index = 0;
    let $image_container = $($image_containers[0]);
    $image_container.click()
    $image_container.find('.image-item-active').removeClass('d-none');
}