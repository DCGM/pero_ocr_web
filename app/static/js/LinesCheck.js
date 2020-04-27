

class LineEditor {
    constructor(document_id) {
        this.lines = [];
        this.image_index = 0;
        this.document_id = document_id;

        let route_ = Flask.url_for('document.get_lines', {'document_id': this.document_id});

        $.get(route_, this.parse_lines.bind(this));

        this.back_btn = document.getElementById('back-btn');
        this.back_btn.addEventListener('click', this.previous_page.bind(this));
        this.next_btn = document.getElementById('next-btn');
        this.next_btn.addEventListener('click', this.next_page.bind(this));
    }

    parse_lines(data){
        let lines_json = data['lines'];
        for (let i = 0; i < lines_json.length; i++) {
            this.lines.push(new TextLine(lines_json[i].id, lines_json[i].text, lines_json[i].np_confidences));
        }

        document.getElementById('line-img').setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': this.lines[this.image_index].id}));
        document.getElementById('text-container').appendChild(this.lines[this.image_index].container);
    }

    previous_page() {
        if (this.image_index > 0) {
            this.lines[this.image_index].save();
            this.image_index -= 1;
            document.getElementById('line-img').setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': this.lines[this.image_index].id}));
            let text_container = document.getElementById('text-container');
            while (text_container.firstChild) {
                text_container.firstChild.remove();
            }
            document.getElementById('text-container').appendChild(this.lines[this.image_index].container);
        }
    }

    next_page() {
        if ((this.image_index + 1) < this.lines.length) {
            this.lines[this.image_index].save();
            this.image_index += 1;
            document.getElementById('line-img').setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': this.lines[this.image_index].id}));
            let text_container = document.getElementById('text-container');
            while (text_container.firstChild) {
                text_container.firstChild.remove();
            }
            document.getElementById('text-container').appendChild(this.lines[this.image_index].container);
        }
    }
}


let document_id = document.getElementById('document-id').textContent;
let line_editor = new LineEditor(document_id);


function componentToHex(c) {
    let hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

