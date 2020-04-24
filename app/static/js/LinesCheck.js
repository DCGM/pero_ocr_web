
// LINES ANNOTATOR
// #############################################################################

yx = L.latLng;
xy = function(x, y) {
    if (L.Util.isArray(x)) {    // When doing xy([x, y]);
        return yx(x[1], x[0]);
    }
    return yx(y, x);  // When doing xy(x, y);
};

// #############################################################################


// KEYBOARD
// #############################################################################
class Keyboard{
    constructor(container, image_editor) {
        this.container = container;
        this.image_editor = image_editor;
        this.keyboard_btn = document.getElementsByClassName("keyboard-btn");
        for (let btn of this.keyboard_btn)
        {
            btn.addEventListener('click',  this.toogle.bind(this));
        }
        this.selected_layout = "default";
        this.layout_select = document.getElementById('layout-select');
        this.layout_select.addEventListener('change', this.select_layout_change.bind(this, this.layout_select));
        this.layouts = document.getElementById('layouts');
        this.new_letter_input = document.getElementById('new-letter-input');
        this.add_new_letter_btn = document.getElementById('add-new-letter-btn');
        this.add_new_letter_btn.addEventListener('click', this.add_new_letter.bind(this));
        this.remove_custom_letters_btn = document.getElementById('remove-custom-letters-btn');
        this.remove_custom_letters_btn.addEventListener('click', this.remove_custom_letters.bind(this));
        this.custom_letters = {};
        let keyboard_custom_letters_cookie = getCookie("keyboard_custom_letters");
        console.log(keyboard_custom_letters_cookie);
        if (keyboard_custom_letters_cookie)
        {
            this.custom_letters = JSON.parse(keyboard_custom_letters_cookie);
        }

        let route = Flask.url_for('document.get_keyboard');
        $.get(route, this.init.bind(this));
    }

    toogle(e)
    {
        this.container.classList.toggle("d-none");
    }

    init(data, status)
    {
        this.keyboard_dict = data;
        this.init_select();
        this.init_layouts();
    }

    init_select()
    {
        this.layout_select.innerHTML = '';
        for (let key in this.keyboard_dict) {
            let option_element = document.createElement('option');
            if (key == this.selected_layout)
            {
                option_element.setAttribute("selected", "selected");
            }
            option_element.setAttribute("value", key);
            let split_layout_name = key.split("_");
            for (let i in split_layout_name)
            {
                split_layout_name[i] = capitalize_first_letter(split_layout_name[i]);
            }
            option_element.innerHTML = split_layout_name.join(" ");
            this.layout_select.appendChild(option_element);
        }
    }

    init_layouts()
    {
        this.layouts.innerHTML = '';
        for (let key in this.keyboard_dict) {
            let layout_div = document.createElement('div');
            if (key == this.selected_layout)
            {
                layout_div.setAttribute("class", "layout d-flex flex-wrap active");
            }
            else
            {
                layout_div.setAttribute("class", "layout d-none");
            }
            layout_div.setAttribute("layout-name", key);
            let letters = this.keyboard_dict[key];
            if (this.custom_letters[key])
            {
                letters = letters.concat(this.custom_letters[key]);
            }
            for (let letter of letters)
            {
                let letter_div = document.createElement('div');
                letter_div.addEventListener('mousedown', this.letter_mousedown.bind(this, letter[0]));
                letter_div.setAttribute("class", "letter-container text-center mr-2 mb-2");
                if (letter.length > 1)
                {
                    let img_background_div = document.createElement('img');
                    img_background_div.setAttribute("class", "img-fluid");
                    img_background_div.setAttribute("src", "/static/img/letters/" + letter[1]);
                    letter_div.appendChild(img_background_div);
                }
                else
                {
                    let letter_background_div = document.createElement('div');
                    letter_background_div.setAttribute("class", "letter");
                    letter_background_div.innerHTML = letter[0];
                    letter_div.appendChild(letter_background_div);
                }
                layout_div.appendChild(letter_div);
            }
            this.layouts.appendChild(layout_div);
        }
    }

    add_new_letter(e)
    {
        let new_letter = this.new_letter_input.value;
        if (new_letter.length == 1)
        {
            if (this.custom_letters[this.selected_layout])
            {
                this.custom_letters[this.selected_layout].push([new_letter]);
            }
            else
            {
                this.custom_letters[this.selected_layout] = [[new_letter]];
            }
            document.cookie = "keyboard_custom_letters=" + JSON.stringify(this.custom_letters) +"; path=/ ";
            this.init_layouts();
        }
    }

    remove_custom_letters(e)
    {
        delete this.custom_letters[this.selected_layout];
        document.cookie = "keyboard_custom_letters=" + JSON.stringify(this.custom_letters) +"; path=/ ";
        this.init_layouts();
    }

    letter_mousedown(char, e)
    {
        e.preventDefault();
        if (this.image_editor.focused_line)
        {
            insert_new_char_to_current_position(char, this.image_editor.active_line.text_line_element);
        }
    }

    select_layout_change(layout_select, e)
    {
        this.selected_layout = layout_select.options[layout_select.selectedIndex].value;
        let active_layout_element = document.getElementsByClassName("layout active")[0];
        let selected_layout_element = $("[layout-name=" + this.selected_layout + "]")[0];
        active_layout_element.setAttribute("class", "layout d-none");
        selected_layout_element.setAttribute("class", "layout d-flex flex-wrap active");
    }
}

//let keyboard = new Keyboard(document.getElementById('keyboard'), image_editor);

// #############################################################################


// PAGE CHANGE EVENT
// #############################################################################

// #############################################################################


// PAGE NAVIGATION
// #############################################################################
var image_index = 0;
var number_of_images;
let document_id = document.getElementById('document-id').textContent;
let route_ = Flask.url_for('document.get_lines', {'document_id': document_id});

var lines;
$.get(route_, function(data){
    lines = data['lines'];
    document.getElementById('line-img').setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': lines[image_index].id}));
    number_of_images = lines.length;

    let text_line_element = document.createElement('div');
    text_line_element.setAttribute("class", "text-line");
    text_line_element.setAttribute("contentEditable", "true");
    text_line_element.style.lineHeight = "220%";
    document.getElementById('text-container').appendChild(text_line_element);
    set_line_confidences_to_text_line_element(lines[image_index], text_line_element);
});

let back_btn = document.getElementById('back-btn')
back_btn.addEventListener('click', previous_page);
let next_btn = document.getElementById('next-btn')
next_btn.addEventListener('click', next_page);

function previous_page()
{
    console.log('prev');
    if (image_index > 0)
    {
        image_index -= 1;
        document.getElementById('line-img').setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': lines[image_index].id}));
        let text_container = document.getElementById('text-container');
        while (text_container.firstChild) {
            text_container.firstChild.remove();
        }
        let text_line_element = document.createElement('div');
        text_line_element.setAttribute("class", "text-line");
        text_line_element.setAttribute("contentEditable", "true");
        text_line_element.style.lineHeight = "220%";
        document.getElementById('text-container').appendChild(text_line_element);
        set_line_confidences_to_text_line_element(lines[image_index], text_line_element);
    }
}
function next_page()
{
    if ((image_index + 1) < number_of_images)
    {
        image_index += 1;
        document.getElementById('line-img').setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': lines[image_index].id}));
        let text_container = document.getElementById('text-container');
        while (text_container.firstChild) {
            text_container.firstChild.remove();
        }
        let text_line_element = document.createElement('div');
        text_line_element.setAttribute("class", "text-line");
        text_line_element.setAttribute("contentEditable", "true");
        text_line_element.style.lineHeight = "220%";
        document.getElementById('text-container').appendChild(text_line_element);
        set_line_confidences_to_text_line_element(lines[image_index], text_line_element);
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

    // Insert nonbreaking space instead of normal space (more robust)
    if (char == " ")
    {
      char = "&nbsp;";
    }

    let selection = document.getSelection();
    let range = selection.getRangeAt(0);
    let text_selected = range.cloneContents().children.length;

    let start_span;
    let end_span;

    let caret_element;
    let caret_before_first_span = false;

    if (empty_text_line_element)
    {
        caret_element = text_line_element;
    }
    else
    {
        caret_element = get_caret_span();
        caret_before_first_span = check_caret_before_first_span(caret_element);

        // If text is selected remove it
        // Removal of selection keeps two empty spans, store them for deletion
        if (text_selected)
        {
            start_span = range.startContainer.parentNode;
            end_span = range.endContainer.parentNode;
            range.deleteContents();
        }
    }

    // Create new span for new char
    // Set it's content to &#8203; special empty char so caret can be set inside
    let new_span = document.createElement('span');
    new_span.setAttribute("style", "font-size: 150%; background: #ffffff; color: #028700");
    new_span.innerHTML = "&#8203;";

    if (empty_text_line_element)
    {
        caret_element.appendChild(new_span);
    }
    else
    {
        if (caret_before_first_span)
        {
            caret_element.parentNode.insertBefore(new_span, caret_element);
        }
        else
        {
            caret_element.parentNode.insertBefore(new_span, caret_element.nextSibling);
        }
    }


    // Set range (selection) on content of new span &#8203
    range.selectNodeContents(new_span.childNodes[0]);
    selection.removeAllRanges();
    selection.addRange(range);

    let isFirefox = typeof InstallTrigger !== 'undefined';
    if (isFirefox)
    {
        new_span = document.createElement('span');
        new_span.setAttribute("style", "font-size: 150%; background: #ffffff; color: #028700");
        new_span.innerHTML = char;

        // Replace current span with new span
        document.execCommand("insertHTML", false, new_span.outerHTML);
    }
    else
    {
        // Replace the content (&#8203) of current new span
        document.execCommand("insertHTML", false, char);
    }

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

function skip_all_empty_spans_to_the_left()
{
    let caret_span = get_caret_span();
    let previous_span = caret_span;
    while (previous_span)
    {
        let skip_span = ((previous_span.innerHTML.charCodeAt(0) == 8203) || (previous_span.innerHTML == ""));

        if (skip_span)
        {
            if (previous_span.previousSibling)
            {
                previous_span = previous_span.previousSibling;
            }
            else
            {
                break;
            }
        }
        else
        {
            break;
        }
    }
    let selection = document.getSelection();
    let range = selection.getRangeAt(0);
    if (previous_span.previousSibling)
    {
        if (previous_span.previousSibling.childNodes.length)
        {
            range.selectNodeContents(previous_span.previousSibling.childNodes[0]);
            range.collapse(false);
        }
        else
        {
            range.selectNodeContents(previous_span.previousSibling);
            range.collapse(false);
        }
    }
    else
    {
        if (previous_span.childNodes.length)
        {
            range.selectNodeContents(previous_span.childNodes[0]);
        }
        else
        {
            range.selectNodeContents(previous_span);
        }
        range.collapse(true);
    }
    selection.removeAllRanges();
    selection.addRange(range);
}

function skip_all_empty_spans_to_the_right()
{
    let caret_span = get_caret_span();
    let caret_before_first_span = check_caret_before_first_span(caret_span);
    let valid_current_span = false;
    if (caret_before_first_span)
    {
        valid_current_span = ((caret_span.innerHTML.charCodeAt(0) != 8203) && (caret_span.innerHTML != ""));
    }
    let next_span = caret_span;
    if (caret_span.nextSibling && !valid_current_span)
    {
        next_span = caret_span.nextSibling;
        while (next_span)
        {
            let skip_span = ((next_span.innerHTML.charCodeAt(0) == 8203) || (next_span.innerHTML == ""));
            if (skip_span)
            {
                next_span = next_span.nextSibling;
            }
            else
            {
                break;
            }
        }
    }
    let selection = document.getSelection();
    let range = selection.getRangeAt(0);
    if (next_span.childNodes.length)
    {
        range.selectNodeContents(next_span.childNodes[0]);
    }
    else
    {
        range.selectNodeContents(next_span);
    }
    range.collapse(false);
    selection.removeAllRanges();
    selection.addRange(range);
}

function set_caret_before_actual_char()
{
    let caret_span = get_caret_span();
    let caret_before_first_span = check_caret_before_first_span(caret_span);
    let previous_span = caret_span;
    let valid_span_char = false;
    while (previous_span)
    {
        let skip_span = ((previous_span.innerHTML.charCodeAt(0) == 8203) || (previous_span.innerHTML == ""));

        if (skip_span)
        {
            if (previous_span.previousSibling)
            {
                previous_span = previous_span.previousSibling;
            }
            else
            {
                break;
            }
        }
        else
        {
            valid_span_char = true;
            break;
        }
    }
    let selection = document.getSelection();
    let range = selection.getRangeAt(0);
    if (valid_span_char && !caret_before_first_span)
    {
        range.selectNodeContents(previous_span.childNodes[0]);
        range.collapse(false);
        selection.removeAllRanges();
        selection.addRange(range);
        return true;
    }
    else
    {
        return false;
    }
}

function get_caret_span()
{
    let selection = document.getSelection();
    let caret_span = selection.anchorNode;
    //Firefox bug, doesn't delete span after pressing backspace
    if (caret_span.tagName != "SPAN")
    {
        caret_span = caret_span.parentNode;
    }
    // Anchor offset should be always 1 apart from caret on first position
    if (selection.anchorOffset == 0)
    {
        // Firefox bug, anchor offset is 0 but caret element is not the first element
        if (caret_span.previousSibling)
        {
            caret_span = caret_span.previousSibling;
        }
    }
    return caret_span;
}

function check_caret_before_first_span(caret_span)
{
    let selection = document.getSelection();
    if (selection.anchorOffset == 0)
    {
        if (!caret_span.previousSibling)
        {
            return true;
        }
    }
    return false;
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

function set_line_background_to_annotated(text_line_element)
{
    text_line_element.style.backgroundColor = "#d0ffcf";
}

function set_line_background_to_save(text_line_element)
{
    set_line_background_to_annotated(text_line_element)
    let descendents = text_line_element.getElementsByTagName('*');
    for (let child of descendents)
    {
        child.style.backgroundColor = "#ffffff";
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

function getCookie(cname) {
  var name = cname + "=";
  var decodedCookie = decodeURIComponent(document.cookie);
  var ca = decodedCookie.split(';');
  for(var i = 0; i <ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

function capitalize_first_letter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

// #############################################################################
