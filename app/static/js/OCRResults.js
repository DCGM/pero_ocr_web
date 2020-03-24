
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
        let save_btn = document.getElementById('save-btn');
        let show_line_height = document.getElementById('show-line-height');
        let show_bottom_pad = document.getElementById('show-bottom-pad');
        save_btn.addEventListener('click', this.save_annotations.bind(this));
        show_line_height.addEventListener('input', this.show_line_change.bind(this));
        show_bottom_pad.addEventListener('input', this.show_line_change.bind(this));
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
        this.active_line = false;

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
            fadeAnimation: true,
            zoomAnimation: true,
            zoomSnap: 0
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
        text_line_element.setAttribute("class", "text-line");
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

    polygon_click(line)
    {
        line.text_line_element.focus();
    }

    line_click(line)
    {
        if (this.active_line)
        {
            this.active_line.polygon.setStyle({ color: "#0059ff", opacity: 0.5, fillColor: "#0059ff", fillOpacity: 0.05, weight: 1});
        }

        let focus_line_points = get_focus_line_points(line);

        this.map.flyToBounds([xy(focus_line_points[0], -focus_line_points[2]), xy(focus_line_points[1], -focus_line_points[2])],
                             {animate: true, duration: 0.5});
        this.active_line = line;
        line.polygon.setStyle({ color: "#028700", opacity: 1, fillColor: "#028700", fillOpacity: 0.1, weight: 2});
    }

    show_line_change()
    {
        if (this.active_line)
        {
            let focus_line_points = get_focus_line_points(this.active_line);
            this.map.flyToBounds([xy(focus_line_points[0], -focus_line_points[2]), xy(focus_line_points[1], -focus_line_points[2])],
                                 {animate: false, duration: 0});
        }
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
            annotation_dict["text_edited"] = get_text_content(line.text_line_element);
            annotations.push(annotation_dict);
            post_annotations(annotations, this.document_id);
            line.edited = false;
            line.saved = true;
            e.preventDefault();
            let line_number = parseInt(e.target.getAttribute("id"), 10);
            document.getElementById((line_number + 1).toString()).focus();
        }

        // Skip
        // TAB (9)
        // ENTER (13)
        // CTRL+S (19)
        // CTRL+Y (25)
        // CTRL+Z (26)
        if (e.keyCode != 9 &&
            e.keyCode != 13 &&
            e.keyCode != 19 &&
            e.keyCode != 25 &&
            e.keyCode != 26)
        {
            insert_new_char_to_current_position(String.fromCharCode(e.keyCode), line.text_line_element);
        }
    }

    line_paste(line, e)
    {
        e.preventDefault();
        let text = (e.originalEvent || e).clipboardData.getData('text/plain');
        for (let i = 0; i < text.length; i++)
        {
            insert_new_char_to_current_position(text.charAt(i), line.text_line_element);
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
                annotation_dict["text_edited"] = get_text_content(l.text_line_element);
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
$('.scrolling-wrapper .figure').on('click', function (event) {
    let document_id = $(this).data('document');
    let image_id = $(this).data('image');
    image_index = $(this).data('index');

    let previous_active_figure = $('.scrolling-wrapper .figure.active');
    if (previous_active_figure.length)
    {
        previous_active_figure.removeClass('active');
        $(previous_active_figure.children()[0]).css('background-color', 'white');
    }
    $(this).addClass('active');
    $($(this).children()[0]).css('background-color', '#ff00f2');

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
let images = $('.scrolling-wrapper .figure');
let number_of_images = images.length;
if (number_of_images)
{
    let first_image = images[image_index];
    $(first_image).click();
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
        $('.scrolling-wrapper .figure[data-index=' + image_index + ']').click();
    }
}
function next_page()
{
    if ((image_index + 1) < number_of_images)
    {
        image_index += 1;
        $('.scrolling-wrapper .figure[data-index=' + image_index + ']').click();
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

function insert_new_char_to_current_position(char, text_line_element)
{
    let empty_text_line_element = !($(text_line_element).has('span').length);
    if (empty_text_line_element)
    {
        $(text_line_element).html('');
    }

    let start_span;
    let end_span;

    // Insert nonbreaking space instead of normal space (more robust)
    if (char == " ")
    {
      char = "&nbsp;";
    }

    let selection = document.getSelection();
    let range = selection.getRangeAt(0);

    // Get span on current caret position
    let caret_element = selection.anchorNode.parentNode;
    if (empty_text_line_element)
    {
        caret_element = text_line_element;
    }

    // If text is selected remove it
    // Removal of selection keeps two empty spans, store them for deletion
    let text_selected = range.startOffset != range.endOffset;
    if (text_selected)
    {
      start_span = range.startContainer.parentNode;
      end_span = range.endContainer.parentNode;
      range.deleteContents();
    }

    // Create new span for new char
    // Set it's content to &#8203; special empty char so caret can be set inside
    let new_span = document.createElement('span');
    new_span.setAttribute("style", "font-size: 150%; background: #ffffff; color: #028700");
    new_span.innerHTML = "&#8203;";

    // If selection begins on the first position in line insert new span before (if line is empty just append span)
    if (range.startOffset == 0)
    {
        if (empty_text_line_element)
        {
            caret_element.appendChild(new_span);
        }
        else
        {
            caret_element.parentNode.insertBefore(new_span, caret_element);
        }
    }
    // Otherwise insert new span after
    else
    {
        caret_element.parentNode.insertBefore(new_span, caret_element.nextSibling);
    }

    // Set range (selection) on content of new span &#8203
    range.selectNodeContents(new_span.childNodes[0]);
    selection.removeAllRanges();
    selection.addRange(range);

    // Replace current range (selection) with char
    document.execCommand("insertHTML", false, char);

    // Usage of &#8203 and execCommand ensures that CTRL+Z and CTRL+Y works
    // properly. After pressing CTRL+Z the char is replaced by &#8203 and after
    // pressing CTRL+Y the &#8203 is replaced with the char.

    // Remove empty spans
    if (text_selected)
    {
      start_span.remove();
      end_span.remove();
    }
}

function get_focus_line_points(line)
{
    let show_line_height = $('#show-line-height').val();
    let show_bottom_pad = $('#show-bottom-pad').val();
    let width_boundary = get_line_width_boundary(line);
    let height_boundary = get_line_height_boundary(line);
    let start_x = width_boundary[0];
    let end_x = width_boundary[1];
    let start_y = height_boundary[0];
    let end_y = height_boundary[1];
    let line_height = end_y - start_y;
    let y = start_y + line_height;
    let line_width = end_x - start_x;
    let container = $('.editor-map');
    let container_width = container.width();
    let container_height = container.height();
    let expected_show_line_height = line_height * (container_width / line_width);
    let new_line_width = (line_height * container_width) / show_line_height;
    if (expected_show_line_height > show_line_height)
    {
        start_x -= (new_line_width - line_width) / 2;
        end_x += (new_line_width - line_width) / 2;
    }
    if (expected_show_line_height < show_line_height)
    {
        end_x -= line_width - new_line_width;
    }
    let show_height_offset = (container_height / 2) - show_bottom_pad;
    let height_offset = (show_height_offset / (container_width / new_line_width));
    return [start_x, end_x, y - height_offset];
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

function get_line_height_boundary(line)
{
    let height_min = 100000000000000000000000;
    let height_max = 0;
    for (let coord of line.np_points)
    {
        if (coord[1] < height_min)
        {
            height_min = coord[1];
        }
        if (coord[1] > height_max)
        {
            height_max = coord[1];
        }
    }
    return [height_min, height_max];
}

function get_line_width_boundary(line)
{
    let width_min = 100000000000000000000000;
    let width_max = 0;
    for (let coord of line.np_points)
    {
        if (coord[0] < width_min)
        {
            width_min = coord[0];
        }
        if (coord[0] > width_max)
        {
            width_max = coord[0];
        }
    }
    return [width_min, width_max];
}

function get_text_content(text_line_element)
{
  let text = text_line_element.textContent;
  let filtered_text = "";
  for (let i = 0; i < text.length; i++)
  {
      let charCode = text.charCodeAt(i);
      if (charCode == 160)
      {
        filtered_text += " ";
      }
      if (charCode != 160 && charCode != 8203)
      {
        filtered_text += text.charAt(i);
      }
  }
  return filtered_text;
}

function componentToHex(c) {
    let hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

// #############################################################################
