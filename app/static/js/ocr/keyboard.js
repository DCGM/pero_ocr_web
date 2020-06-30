
class Keyboard{
    constructor(container, text_lines_editor) {
        this.container = container;
        this.text_lines_editor = text_lines_editor;
        this.keyboard_btn = document.getElementsByClassName("keyboard-btn");
        for (let btn of this.keyboard_btn)
        {
            btn.addEventListener('click',  this.toogle.bind(this));
            btn.addEventListener('mousedown', this.prevent_focus.bind(this))
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

    prevent_focus(e)
    {
        e.preventDefault()
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
        if (this.text_lines_editor.focused_line)
        {
            this.text_lines_editor.active_line.insert_new_char_to_current_position(char);
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

function getCookie(cname)
{
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

function capitalize_first_letter(string)
{
  return string.charAt(0).toUpperCase() + string.slice(1);
}