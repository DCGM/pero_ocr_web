

class LineEditor {
    constructor(document_id) {
        this.mode = 'all';
        this.focused_line = false;
        this.active_line = null;
        this.lines = [];
        this.annotated_in_session = [];
        this.image_index = 0;
        this.document_id = document_id;

        this.line_image = document.getElementById('line-img');
        this.line_image.setAttribute("src", "/static/img/loading.gif");

        this.back_btn = document.getElementById('back-btn');
        this.next_btn = document.getElementById('next-btn');
        this.skip_btn = document.getElementById('skip-btn');
        this.save_next_btn = document.getElementById('save-next-btn');
        this.go_to_line_btn = document.getElementById("go-to-line-btn");
        this.text_container = document.getElementById('text-container');
        this.back_btn.addEventListener('click', this.previous_line.bind(this));
        this.next_btn.addEventListener('click', this.next_line.bind(this));
        this.skip_btn.addEventListener('click', this.skip_line.bind(this));
        this.save_next_btn.addEventListener('click', this.save_next_line.bind(this));
        this.go_to_line_btn.addEventListener('click', this.go_to_line.bind(this));

        this.actual_line_container = document.getElementById('actual-line');
        this.lines_total_container = document.getElementById('lines-total');

        let route_ = Flask.url_for('document.get_all_lines', {'document_id': this.document_id});
        $.get(route_, this.parse_lines.bind(this));

        $("#line_options input[name='line_type']").click(this.change_mode.bind(this));
    }

    line_focus(){

        this.focused_line = true;
    }

    line_focus_out(){
        this.focused_line = false;
    }

    parse_lines(data){
        this.lines = [];
        let lines_json = data['lines'];
        for (let i = 0; i < lines_json.length; i++) {
            this.lines.push([lines_json[i].id, lines_json[i].annotated]);
            this.annotated_in_session.push(false);
        }

        this.change_line_index();

        let route_ = Flask.url_for('document.get_line_info', {'line_id': this.lines[this.image_index][0]});
        $.get(route_, this.get_line.bind(this));
    }

    change_line_index(){
        this.actual_line_container.value = this.image_index;
        this.actual_line_container.max = String(this.lines.length-1);
        this.lines_total_container.textContent = String(this.lines.length-1);
        this.actual_line_container.style.width = String(document.getElementsByClassName("input-group-append")[0].offsetWidth+20) + 'px';
    }

    get_line(data){
        let line_json = data;
        this.active_line = new TextLine(line_json['id'], line_json['text'], line_json['np_confidences']);
        while (this.text_container.firstChild) {
                this.text_container.firstChild.remove();
        }
        this.line_image.setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': this.active_line.id}));
        this.text_container.appendChild(this.active_line.container);
        this.text_container.children[0].focus();
        this.line_focus();
        if (this.annotated_in_session[this.image_index] || this.lines[this.image_index][1]){
            this.active_line.set_background_to_annotated()
        }
        this.text_container.children[0].addEventListener('focus', this.line_focus.bind(this));
        this.text_container.children[0].addEventListener('focusout', this.line_focus_out.bind(this));
    }

    previous_line() {
        if (this.image_index > 0) {
            this.image_index -= 1;
            this.actual_line_container.value = this.image_index;
            this.line_image.setAttribute("src", "/static/img/loading.gif");
            let route_ = Flask.url_for('document.get_line_info', {'line_id': this.lines[this.image_index][0]});
            $.get(route_, this.get_line.bind(this));
        }
    }

    next_line() {
        if ((this.image_index + 1) < this.lines.length) {
            this.image_index += 1;
            this.actual_line_container.value = this.image_index;
            this.line_image.setAttribute("src", "/static/img/loading.gif");
            let route_ = Flask.url_for('document.get_line_info', {'line_id': this.lines[this.image_index][0]});
            $.get(route_, this.get_line.bind(this));
        }
    }

    go_to_line(){
        if (Number(this.actual_line_container.value) > Number(this.actual_line_container.max)){
            this.actual_line_container.value = this.actual_line_container.max;
        }
        if (Number(this.actual_line_container.value) < Number(this.actual_line_container.min)){
            this.actual_line_container.value = this.actual_line_container.min;
        }
        this.image_index = Number(this.actual_line_container.value);
        this.line_image.setAttribute("src", "/static/img/loading.gif");
        let route_ = Flask.url_for('document.get_line_info', {'line_id': this.lines[this.image_index][0]});
        $.get(route_, this.get_line.bind(this));
    }

    skip_line() {
        if ((this.image_index + 1) < this.lines.length) {
            this.active_line.skip();
            this.image_index += 1;
            this.line_image.setAttribute("src", "/static/img/loading.gif");
            let route_ = Flask.url_for('document.get_line_info', {'line_id': this.lines[this.image_index][0]});
            $.get(route_, this.get_line.bind(this));
            this.lines.splice(this.image_index-1, 1);
            this.annotated_in_session.splice(this.image_index-1, 1);
            this.actual_line_container.max = String(this.lines.length-1);
            this.lines_total_container.textContent = String(this.lines.length-1);
            this.image_index -= 1;
        }
        else {
            this.active_line.skip();
            this.image_index -= 1;
            this.line_image.setAttribute("src", "/static/img/loading.gif");
            let route_ = Flask.url_for('document.get_line_info', {'line_id': this.lines[this.image_index][0]});
            $.get(route_, this.get_line.bind(this));
            this.lines.splice(this.lines.length-1, 1);
            this.annotated_in_session.splice(this.lines.length-1, 1);
            this.actual_line_container.max = String(this.lines.length-1);
            this.actual_line_container.value = String(this.lines.length-1);
            this.lines_total_container.textContent = String(this.lines.length-1);
            this.image_index -= 1;
        }
    }

    save_next_line(save=true) {
        if ((this.image_index + 1) < this.lines.length) {
            if (save){
                this.active_line.save();
            }
            this.active_line.skip();
            this.annotated_in_session[this.image_index] = true;
            this.image_index += 1;
            this.line_image.setAttribute("src", "/static/img/loading.gif");
            let route_ = Flask.url_for('document.get_line_info', {'line_id': this.lines[this.image_index][0]});
            $.get(route_, this.get_line.bind(this));
        }
        else{
            this.active_line.save();
            this.active_line.skip();
            this.annotated_in_session[this.image_index] = true;
        }
    }

    change_mode(){
        this.mode = $('input:radio[name=line_type]:checked').val();
        this.image_index = 0;
        this.line_image.setAttribute("src", "/static/img/loading.gif");
        switch(this.mode) {
          case 'all':
            var route_ = Flask.url_for('document.get_all_lines', {'document_id': this.document_id});
            break;
          case 'annotated':
            var route_ = Flask.url_for('document.get_annotated_lines', {'document_id': this.document_id});
            break;
          case 'not_annotated':
            var route_ = Flask.url_for('document.get_not_annotated_lines', {'document_id': this.document_id});
            break;
        }
        $.get(route_, this.parse_lines.bind(this));
    }
}

function componentToHex(c) {
    let hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}
