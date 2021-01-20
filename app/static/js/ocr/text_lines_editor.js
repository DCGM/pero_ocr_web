
yx = L.latLng;
xy = function(x, y) {
    if (L.Util.isArray(x)) {    // When doing xy([x, y]);
        return yx(x[1], x[0]);
    }
    return yx(y, x);  // When doing xy(x, y);
};


class TextLinesEditor
{
    constructor(container)
    {
        this.abort_controller = new AbortController();
        this.container = container;
        this.container.innerHTML = "<div class='editor-map'></div><div class='status'></div>";
        this.map_element = this.container.getElementsByClassName("editor-map")[0];
        this.active_line = false;
        this.focused_line = false;
        this.focus_to = null;
        this.save_btn = document.getElementsByClassName('save-btn');
        this.delete_btn = document.getElementById('deletebutton');
        this.ignore_btn = document.getElementById('ignorebutton');
        this.next_suspect_btn = document.getElementById('nextsucpectline');
        this.compute_scores_btn = document.getElementById('btn-compute-scores');
        this.show_line_height = document.getElementById('show-line-height');
        this.show_bottom_pad = document.getElementById('show-bottom-pad');
        for (let btn of this.save_btn)
        {
            btn.addEventListener('click', this.save_annotations.bind(this));
        }
        this.next_suspect_btn.addEventListener('click', this.show_next_line.bind(this));
        this.delete_btn.addEventListener('click', this.delete_line.bind(this));
        this.ignore_btn.addEventListener('click', this.ignore_line.bind(this));
        this.show_line_height.addEventListener('input', this.show_line_change.bind(this));
        this.show_bottom_pad.addEventListener('input', this.show_line_change.bind(this));
        this.text_container = document.getElementById('text-container');
        this.text_container.addEventListener('keypress', this.press_text_container.bind(this));
        if (this.compute_scores_btn != null){
            this.compute_scores_btn.addEventListener('click', this.compute_scores.bind(this));
        }
    }

    ignore_line(){
        if (this.active_line != false){
            this.active_line.for_training_checkbox.checked = ! this.active_line.for_training_checkbox.checked;
            this.active_line.set_training_flag();
            if (this.active_line.for_training_checkbox.checked){
                this.ignore_btn.innerHTML  = '<i class="fas fa-minus-circle"></i> Ignore line';
            }
            else {
                this.ignore_btn.innerHTML  = '<i class="fas fa-minus-circle"></i> Unignore line';
            }
            this.active_line.container.focus();
        }
    }

    delete_line(){
        if (this.active_line.valid){
            this.active_line.valid = false;
        }
        else{
            this.active_line.valid = true;
        }

        this.active_line.mutate();

        if (this.active_line.valid){
            this.delete_btn.innerHTML  = '<i class="far fa-trash-alt"></i> Delete line';
            this.delete_btn.className  = 'btn btn-danger';
        }
        else{
            this.delete_btn.innerHTML  = '<i class="fas fa-undo"></i> Restore line';
            this.delete_btn.className  = 'btn btn-primary';
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
                if (text_lines_editor.active_line.valid){
                    text_lines_editor.delete_btn.innerHTML  = '<i class="far fa-trash-alt"></i> Delete line';
                    text_lines_editor.delete_btn.className  = 'btn btn-danger';
                }
                else{
                    text_lines_editor.delete_btn.innerHTML  = '<i class="fas fa-undo"></i> Restore line';
                    text_lines_editor.delete_btn.className  = 'btn btn-primary';
                }
                alert('Unable to set delete flag. Check your remote connection.');
            }
        });
        this.active_line.container.focus();
    }

    change_image(image_id, change_url_callback, line_id)
    {
        if (typeof this.lines !== 'undefined')
        {
            let unsaved_lines = false;
            for (let l of this.lines)
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
                    this.save_annotations();
                }
            }
        }
        this.focus_to = line_id;
        this.get_image(image_id);
        this.delete_btn.innerHTML  = '<i class="far fa-trash-alt"></i> Delete line';
        this.delete_btn.className  = 'btn btn-danger';
        this.ignore_btn.innerHTML  = '<i class="fas fa-minus-circle"></i> Ignore line';
        this.change_url = change_url_callback;
    }

    async get_image(image_id)
    {
        this.abort_controller.abort();
        this.abort_controller = new AbortController();
        let abort_signal = this.abort_controller.signal;
        await new Promise(resolve => setTimeout(resolve, 150));
        if( abort_signal.aborted){ return;}

        let route = Flask.url_for('ocr.get_lines', {'image_id': image_id});
        while (this.text_container.firstChild)
        {
            this.text_container.firstChild.remove();
        }
        let response = fetch(route, {
            signal: abort_signal,})
            .then(res => res.json());

        if (this.map)
        {
            this.map.off();
            this.map.remove();
        }
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

        let data = await response;

        if( data['image_id'] != image_id){
            return;
        }

        this.image_id = data['image_id'];
        this.width = data['width'];
        this.height = data['height'];
        this.active_line = false;
        this.lines = [];

        let bounds = [xy(0, -this.height), xy(this.width, 0)];
        L.imageOverlay(Flask.url_for('document.get_image', {'image_id': this.image_id}), bounds).addTo(this.map);
        this.map.setView(xy(this.width / 2, -this.height / 2), -2);
        this.map.fitBounds(bounds);
        if( abort_signal.aborted){ return;}

        let i = 0;
        let debug_line_container = document.getElementById('debug-line-container');
        let debug_line_container_2 = document.getElementById('debug-line-container-2');
        let focused = false;
        for (let l of data['lines'])
        {
            let line = new TextLine(l.id, l.annotated, l.text, l.np_confidences, l.ligatures_mapping, l.arabic, l.for_training,
                                    debug_line_container, debug_line_container_2)
            line.np_points = l.np_points;
            line.np_heights = l.np_heights;
            this.add_line_to_map(i, line);
            this.lines.push(line);
            if (l.id == this.focus_to){
                this.line_focus(line);
                this.polygon_click(line);
                focused = true;
            }
            i += 1;
            if(i % 50 == 49){
                await new Promise(resolve => setTimeout(resolve, 0));
                if( abort_signal.aborted){return;}
            }
        }
        if (this.focus_to != null){
            this.focus_to = null;
        }
        else{
            this.map_element.focus();
        }
    }

    add_line_to_map(i, line)
    {
        let points = [];

        for (let point of line.np_points)
        {
            points.push(xy(point[0], -point[1]));
        }
        line.polygon = L.polygon(points);
        line.polygon.setStyle({ color: "#0059ff", opacity: 0.5, fillColor: "#0059ff", fillOpacity: 0.05, weight: 1});

        line.polygon.addTo(this.map);
        line.polygon.on('click', this.polygon_click.bind(this, line));

        line.container.setAttribute("id", i);

        line.container.addEventListener('focus', this.line_focus.bind(this, line));
        line.container.addEventListener('focusout', this.line_focus_out.bind(this));

        line.checkbox_span.addEventListener('click', this.line_focus_from_checkbox.bind(this, line));

        this.text_container.appendChild(line.checkbox_span);
        this.text_container.appendChild(line.container);
    }

    line_focus_from_checkbox(line) {
        this.line_focus(line);
        line.container.focus();
    }

    press_text_container(e)
    {
        if (e.keyCode == 13)
        {
            let line_number = parseInt(this.active_line.container.getAttribute("id"), 10);
            document.getElementById((line_number + 1).toString()).focus();
        }
    }

    polygon_click(line)
    {
        line.container.focus();
    }

    line_focus(line)
    {
        this.focused_line = true;
        if (this.active_line)
        {
            this.active_line.polygon.setStyle({ color: "#0059ff", opacity: 0.5, fillColor: "#0059ff", fillOpacity: 0.05, weight: 1});
        }

        let focus_line_points = get_focus_line_points(line);

        this.map.flyToBounds([xy(focus_line_points[0], -focus_line_points[2]), xy(focus_line_points[1], -focus_line_points[2])],
                             {animate: true, duration: 0.5});
        this.active_line = line;
        line.polygon.setStyle({ color: "#028700", opacity: 1, fillColor: "#028700", fillOpacity: 0.1, weight: 2});

        if (this.active_line.valid){
            this.delete_btn.innerHTML  = '<i class="far fa-trash-alt"></i> Delete line';
            this.delete_btn.className  = 'btn btn-danger';
        }
        else{
            this.delete_btn.innerHTML  = '<i class="fas fa-undo"></i> Restore line';
            this.delete_btn.className  = 'btn btn-primary';
        }
        if (this.active_line.for_training_checkbox.checked){
            this.ignore_btn.innerHTML  = '<i class="fas fa-minus-circle"></i> Ignore line';
        }
        else {
            this.ignore_btn.innerHTML  = '<i class="fas fa-minus-circle"></i> Unignore line';
        }
        this.change_url(this.active_line.id);
    }

    line_focus_out()
    {
        this.focused_line = false;
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

    show_next_line()
    {
        var focused = false;
        if (this.active_line.id == undefined){
            for (let line of this.lines){
                if (Math.min.apply(Math, line.confidences) < 0.8 && line.text_line_element.style.backgroundColor != 'rgb(208, 255, 207)') {
                    this.line_focus(line);
                    this.polygon_click(line);
                    focused = true;
                    break;
                }

                if (focused){
                    break;
                }
            }
        }
        else {
            let index = this.lines.findIndex(x => x.id === this.active_line.id);
            let rest_of_lines = this.lines.slice(index+1);
            if (rest_of_lines.length != 0){
                for (let line of rest_of_lines) {
                    if (Math.min.apply(Math, line.confidences) < 0.8 && line.container.style.backgroundColor != 'rgb(208, 255, 207)') {
                        this.line_focus(line);
                        this.polygon_click(line);
                        focused = true;
                        break;
                    }

                    if (focused) {
                        break;
                    }
                }
            }
            else{
                next_page();
            }
        }
    }

    save_annotations()
    {
        for (let l of this.lines)
        {
            if (l.edited)
            {
                l.save();
            }
        }
    }

    compute_scores(){
        let route_ = Flask.url_for('document.compute_scores', {'document_id': document.querySelector('#document-id').textContent});
        $.get(route_);
    }
}


// HELPER FUNCTIONS
// #############################################################################

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
    let line_height = line.np_heights[0] + line.np_heights[1];
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

function componentToHex(c) {
    let hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}


// #############################################################################
