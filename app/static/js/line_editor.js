

class LineEditor {
    constructor(document_id) {
        this.mode = 'all';
        this.focused_line = false;
        this.active_line = null;
        this.lines = [];
        this.annotated_in_session = [];
        this.image_index = 0;
        this.document_id = document_id;
        this.deleted_lines = new Set();

        this.line_image = document.getElementById('line-img');
        this.line_image.setAttribute("src", "/static/img/loading.gif");

        this.back_btn = document.getElementById('back-btn');
        this.next_btn = document.getElementById('next-btn');
        this.skip_btn = document.getElementById('skip-btn');
        this.save_next_btn = document.getElementById('save-next-btn');
        this.go_to_line_btn = document.getElementById("go-to-line-btn");
        this.delete_btn = document.getElementById("deletebutton");
        this.ignore_btn = document.getElementById("ignorebutton");
        this.text_container = document.getElementById('text-container');
        this.show_ignored_lines_btn = document.getElementById("show-ignored-lines-btn");
        this.back_btn.addEventListener('click', this.previous_line.bind(this));
        this.next_btn.addEventListener('click', this.next_line.bind(this));
        this.skip_btn.addEventListener('click', this.skip_line.bind(this));
        this.save_next_btn.addEventListener('click', this.save_next_line.bind(this));
        this.go_to_line_btn.addEventListener('click', this.go_to_line.bind(this));
        this.delete_btn.addEventListener('click', this.delete_line.bind(this));
        this.ignore_btn.addEventListener('click', this.ignore_line.bind(this));
        this.show_ignored_lines_btn.addEventListener('change', this.ignored_lines_switch.bind(this));

        this.actual_line_container = document.getElementById('actual-line');
        this.lines_total_container = document.getElementById('lines-total');

        $.ajaxSetup({
           headers:{
              'show-ignored-lines': this.show_ignored_lines_btn.checked
           }
        });
        let route_ = Flask.url_for('document.get_all_lines', {'document_id': this.document_id});
        $.get(route_, this.parse_lines.bind(this));

        $("#line_options input[name='line_type']").click(this.change_mode.bind(this));
    }

    ignored_lines_switch(){
        this.change_mode();
    }

    delete_line(){
        if (this.active_line.valid){
            this.active_line.valid = false;
            this.deleted_lines.add(this.active_line.id);
        }
        else{
            this.active_line.valid = true;
            this.deleted_lines.delete(this.active_line.id);
        }

        this.active_line.mutate();

        if (this.active_line.valid){
            this.delete_btn.innerHTML  = '<i class="far fa-trash-alt"></i>&nbsp;&nbsp;Delete line (Alt+B)';
            this.delete_btn.className  = 'btn btn-danger  mb-2';
        }
        else{
            this.delete_btn.innerHTML  = '<i class="far fa-trash-alt"></i>&nbsp;&nbsp;Restore line (Alt+B)';
            this.delete_btn.className  = 'btn btn-primary  mb-2';
        }

        let delete_flag;
        if (this.active_line.valid){
            delete_flag = 0;
        }
        else{
            delete_flag = 1;
        }

        let text_lines_editor = this;
        let route = Flask.url_for('ocr.delete_line', {'line_id': this.active_line.id, 'delete_flag': delete_flag});
        $.ajax({
            type: "POST",
            url: route,
            data: {'line_id': this.active_line.id, 'delete_flag': delete_flag},
            dataType: "json",
            error: function(xhr, ajaxOptions, ThrownError){
                text_lines_editor.active_line.valid = ! text_lines_editor.active_line.valid;
                text_lines_editor.active_line.mutate();
                if (this.active_line.valid){
                    this.delete_btn.innerHTML  = '<i class="far fa-trash-alt"></i>&nbsp;&nbsp;Delete line (Alt+B)';
                    this.delete_btn.className  = 'btn btn-danger  mb-2';
                }
                else{
                    this.delete_btn.innerHTML  = '<i class="far fa-trash-alt"></i>&nbsp;&nbsp;Restore line (Alt+B)';
                    this.delete_btn.className  = 'btn btn-primary  mb-2';
                }
                alert('Unable to set delete flag. Check your remote connection.');
            }
        });
        this.active_line.container.focus();
    }

    ignore_line(){
        if (this.active_line != false){
            this.active_line.for_training_checkbox.checked = ! this.active_line.for_training_checkbox.checked;
            this.active_line.set_training_flag();
        if (this.active_line.for_training_checkbox.checked){
            this.ignore_btn.innerHTML  = '<i class="fas fa-minus-circle"></i>&nbsp;&nbsp;Ignore line (Alt+N)';
        }
        else {
            this.ignore_btn.innerHTML  = '<i class="fas fa-minus-circle"></i>&nbsp;&nbsp;Unignore line (Alt+N)';
        }
            this.active_line.container.focus();
        }
    }

    line_focus(){
        this.focused_line = true;
        if (this.active_line.valid){
            this.delete_btn.innerHTML  = '<i class="far fa-trash-alt"></i>&nbsp;&nbsp;Delete line (Alt+B)';
            this.delete_btn.className  = 'btn btn-danger  mb-2';
        }
        else{
            this.delete_btn.innerHTML  = '<i class="far fa-trash-alt"></i>&nbsp;&nbsp;Restore line (Alt+B)';
            this.delete_btn.className  = 'btn btn-primary  mb-2';
        }
        if (this.active_line.for_training_checkbox.checked){
            this.ignore_btn.innerHTML  = '<i class="fas fa-minus-circle"></i>&nbsp;&nbsp;Ignore line (Alt+N)';
        }
        else {
            this.ignore_btn.innerHTML  = '<i class="fas fa-minus-circle"></i>&nbsp;&nbsp;Unignore line (Alt+N)';
        }
        this.active_line.container.focus();
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
        this.active_line = new TextLine(line_json['id'], line_json['annotated'], line_json['text'], line_json['np_confidences'],
                                        line_json['ligatures_mapping'], line_json['arabic'], line_json['for_training']);
        while (this.text_container.firstChild) {
                this.text_container.firstChild.remove();
        }
        this.line_image.setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': this.active_line.id}));
        this.text_container.appendChild(this.active_line.checkbox_span);
        this.text_container.appendChild(this.active_line.container);
        this.text_container.children[0].focus();
        this.line_focus();
        if (this.annotated_in_session[this.image_index] || this.lines[this.image_index][1]){
            this.active_line.set_background_to_annotated()
        }
        this.text_container.children[0].addEventListener('focus', this.line_focus.bind(this));
        this.text_container.children[0].addEventListener('focusout', this.line_focus_out.bind(this));
        this.active_line.checkbox_span.addEventListener('click', this.line_focus_from_checkbox.bind(this));
        if (this.deleted_lines.has(this.active_line.id)){
            this.active_line.valid = false;
            this.active_line.mutate();
            if (this.active_line.valid){
                this.delete_btn.innerHTML  = '<i class="far fa-trash-alt"></i>&nbsp;&nbsp;Delete line (Alt+B)';
                this.delete_btn.className  = 'btn btn-danger  mb-2';
            }
            else{
                this.delete_btn.innerHTML  = '<i class="far fa-trash-alt"></i>&nbsp;&nbsp;Restore line (Alt+B)';
                this.delete_btn.className  = 'btn btn-primary  mb-2';
            }
        }
    }

    line_focus_from_checkbox(){
        this.line_focus();
    }

    previous_line() {
        if (this.image_index > 0) {
            this.image_index -= 1;
            this.actual_line_container.value = this.image_index;
            this.line_image.setAttribute("src", "/static/img/loading.gif");
            let route_ = Flask.url_for('document.get_line_info', {'line_id': this.lines[this.image_index][0]});
            $.get(route_, this.get_line.bind(this));
            this.line_focus();
        }
    }

    next_line() {
        if ((this.image_index + 1) < this.lines.length) {
            this.image_index += 1;
            this.actual_line_container.value = this.image_index;
            this.line_image.setAttribute("src", "/static/img/loading.gif");
            let route_ = Flask.url_for('document.get_line_info', {'line_id': this.lines[this.image_index][0]});
            $.get(route_, this.get_line.bind(this));
            this.line_focus();
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
        this.line_focus();
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
        this.line_focus();
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
        this.line_focus();
    }

    change_mode(){
        this.mode = $('input:radio[name=line_type]:checked').val();
        this.image_index = 0;
        this.line_image.setAttribute("src", "/static/img/loading.gif");

        $.ajaxSetup({
           headers:{
              'show-ignored-lines': this.show_ignored_lines_btn.checked
           }
        });

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
        this.line_focus();
    }
}

function componentToHex(c) {
    let hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}
