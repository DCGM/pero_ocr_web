

class LineEditor {
    constructor(document_id) {
        this.lines = [];
        this.image_index = 0;
        this.document_id = document_id;

        let route_ = Flask.url_for('document.get_lines', {'document_id': this.document_id});

        $.get(route_, this.parse_lines.bind(this));

        this.back_btn = document.getElementById('back-btn');
        this.next_btn = document.getElementById('next-btn');
        this.skip_btn = document.getElementById('skip-btn');
        this.save_next_btn = document.getElementById('save-next-btn');
        this.line_image = document.getElementById('line-img');
        this.text_container = document.getElementById('text-container');
    }

    parse_lines(data){
        let lines_json = data['lines'];
        for (let i = 0; i < lines_json.length; i++) {
            this.lines.push(new TextLine(lines_json[i].id, lines_json[i].text, lines_json[i].np_confidences));
        }

        this.line_image.setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': this.lines[this.image_index].id}));
        this.text_container.appendChild(this.lines[this.image_index].container);

        this.back_btn.addEventListener('click', this.previous_line.bind(this));
        this.next_btn.addEventListener('click', this.next_line.bind(this));
        this.skip_btn.addEventListener('click', this.skip_line.bind(this));
        this.save_next_btn.addEventListener('click', this.save_next_line.bind(this));

    }

    previous_line() {
        if (this.image_index > 0) {
            this.image_index -= 1;
            this.line_image.setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': this.lines[this.image_index].id}));
            let text_container = document.getElementById('text-container');
            while (text_container.firstChild) {
                text_container.firstChild.remove();
            }
            this.text_container.appendChild(this.lines[this.image_index].container);
        }
    }

    next_line() {
        if ((this.image_index + 1) < this.lines.length) {
            this.image_index += 1;
            this.line_image.setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': this.lines[this.image_index].id}));
            let text_container = document.getElementById('text-container');
            while (text_container.firstChild) {
                text_container.firstChild.remove();
            }
            this.text_container.appendChild(this.lines[this.image_index].container);
        }
    }

    skip_line() {
        if ((this.image_index + 1) < this.lines.length) {
            this.lines[this.image_index].skip();
            this.image_index += 1;
            this.line_image.setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': this.lines[this.image_index].id}));
            let text_container = document.getElementById('text-container');
            while (text_container.firstChild) {
                text_container.firstChild.remove();
            }
            this.text_container.appendChild(this.lines[this.image_index].container);
            this.lines.splice(this.image_index-1, 1);
            this.image_index -= 1;
        }
    }

    save_next_line() {
        if ((this.image_index + 1) < this.lines.length) {
            this.lines[this.image_index].save();
            this.image_index += 1;
            this.line_image.setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': this.lines[this.image_index].id}));
            let text_container = document.getElementById('text-container');
            while (text_container.firstChild) {
                text_container.firstChild.remove();
            }
            this.text_container.appendChild(this.lines[this.image_index].container);
        }
    }
}

function componentToHex(c) {
    let hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}
