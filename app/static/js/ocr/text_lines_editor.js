yx = L.latLng;
xy = function (x, y) {
    if (L.Util.isArray(x)) {    // When doing xy([x, y]);
        return yx(x[1], x[0]);
    }
    return yx(y, x);  // When doing xy(x, y);
};

function rgb(r, g, b) {
    return "rgb(" + r + "," + g + "," + b + ")";
}

class TextLinesEditor {
    constructor(container, public_view) {
        this.public_view = public_view;
        this.abort_controller = new AbortController();
        this.container = container;
        this.container.innerHTML = "<div class='editor-map'></div><div class='status'></div>";  // OLD COMPONENT
        this.map_element = this.container.getElementsByClassName("editor-map")[0];  // OLD COMPONENT
        this.active_line = false;
        this.focus_to = null;
        this.focus_fired = false;
        this.animation_in_progress = false;
        this.animation_interrupted = false;
        if(!this.public_view) {
            this.save_btn = document.getElementsByClassName('save-btn');
            this.delete_btn = document.getElementById('deletebutton');
            this.ignore_btn = document.getElementById('ignorebutton');
            this.next_suspect_btn = document.getElementById('nextsucpectline');
            this.compute_scores_btn = document.getElementById('btn-compute-scores');
            for (let btn of this.save_btn) {
                btn.addEventListener('click', this.save_annotations.bind(this));
            }
            this.next_suspect_btn.addEventListener('click', this.show_next_line.bind(this));
            this.delete_btn.addEventListener('click', this.delete_line_btn_action.bind(this, null, 'row'));
            this.ignore_btn.addEventListener('click', this.ignore_line_btn_action.bind(this), true);
        }
        this.show_line_height = document.getElementById('show-line-height');
        this.show_bottom_pad = document.getElementById('show-bottom-pad');
        this.show_line_height.addEventListener('input', this.show_line_change.bind(this));
        this.show_bottom_pad.addEventListener('input', this.show_line_change.bind(this));
        this.text_container = document.getElementById('text-container');
        this.text_container.addEventListener('keypress', this.press_text_container.bind(this));
        if (this.compute_scores_btn != null) {
            this.compute_scores_btn.addEventListener('click', this.compute_scores.bind(this));
        }
        this.worst_confidence = 0;
    }

    swap_ignore_line_button_blueprint(){
        if(this.public_view) {
            return;
        }
        if (this.active_line.for_training_checkbox.checked){
            this.ignore_btn.innerHTML  = '<i class="fas fa-minus-circle"></i> Ignore line';
        }
        else {
            this.ignore_btn.innerHTML  = '<i class="fas fa-minus-circle"></i> Unignore line';
        }
        try {
            this.active_line.container.focus();
        } catch (err) {
        }
    }

    swap_delete_line_button_blueprint(){
        if(this.public_view) {
            return;
        }
        if (this.active_line.valid) {
            this.delete_btn.innerHTML  = '<i class="far fa-trash-alt"></i> Delete line';
            this.delete_btn.className  = 'btn btn-danger';
        }
        else{
            this.delete_btn.innerHTML  = '<i class="fas fa-undo"></i> Restore line';
            this.delete_btn.className  = 'btn btn-primary';
        }
        try {
            this.active_line.container.focus();
        } catch (err) {
        }
    }

    ignore_line_btn_action(button= false) {
        if(this.public_view) {
            return;
        }
        if (this.active_line != false) {
            if (button) {
                this.active_line.for_training_checkbox.checked = !this.active_line.for_training_checkbox.checked;
            }

            let training_flag;
            if (this.active_line.for_training_checkbox.checked) {
                training_flag = 1;
            } else {
                training_flag = 0;
            }

            let text_lines_editor = this;
            let route = Flask.url_for('ocr.training_line', {'line_id': this.active_line.id, 'training_flag': training_flag});
            this.ignore_btn.disabled = true;
            this.active_line.for_training_checkbox.disabled = true;
            $.ajax({
                type: "POST",
                url: route,
                data: {'line_id': this.active_line.id, 'training_flag': training_flag},
                dataType: "json",
                error: function(xhr, ajaxOptions, ThrownError){
                    text_lines_editor.active_line.for_training_checkbox.checked = ! text_lines_editor.active_line.for_training_checkbox.checked;
                    text_lines_editor.swap_ignore_line_button_blueprint();
                    text_lines_editor.ignore_btn.disabled = false;
                    text_lines_editor.active_line.for_training_checkbox.disabled = false;
                    alert('Unable to set training flag. Check your remote connection.');
                },
                success: function (xhr, ajaxOptions) {
                    text_lines_editor.swap_ignore_line_button_blueprint();
                    text_lines_editor.ignore_btn.disabled = false;
                    text_lines_editor.active_line.for_training_checkbox.disabled = false;
                }
            });
        }
    }

    set_line_style(line) {
        var conf = (line.line_confidence-this.worst_confidence) / (1 - this.worst_confidence);

        var color = '';
        if (!line.valid) {
            color = rgb(16, 16, 16);
        } else if (line.edited) {
            color = '#ffcc54'
        } else if (line.annotated) {
            color = "#028700";
        } else {
            color = rgb((1 - conf) * 255, 16, conf * 255);
        }
        if (line.focus) {
            line.polygon.setStyle({color: color, opacity: 1, fillColor: color, fillOpacity: 0.15, weight: 2});
        } else {
            line.polygon.setStyle({color: color, opacity: 0.5, fillColor: color, fillOpacity: 0.1, weight: 1});
        }
    }

    delete_line_btn_action(uuid=null, type='row') {
        if(this.public_view){
            return;
        }
        let delete_uuid = uuid? uuid: this.active_line.id;

        if (this.active_line !== false || uuid) {
            if (!uuid)
                this.active_line.valid = !this.active_line.valid;

            let delete_flag;
            if (uuid)
                delete_flag = 1;
            else if (this.active_line.valid)
                delete_flag = 0;
            else
                delete_flag = 1;

            let text_lines_editor = this;
            let route;
            if (type === 'row')
                route = Flask.url_for('ocr.delete_line', {'line_id': delete_uuid, 'delete_flag': delete_flag});
            else
                route = Flask.url_for('ocr.delete_region', {'region_id': delete_uuid, 'delete_flag': delete_flag});


            this.delete_btn.disabled = true;
            $.ajax({
                type: "POST",
                url: route,
                data: {'line_id': delete_uuid, 'delete_flag': delete_flag},
                dataType: "json",
                error: function (xhr, ajaxOptions, ThrownError) {
                    text_lines_editor.active_line.valid = !text_lines_editor.active_line.valid;
                    text_lines_editor.active_line.mutate();
                    text_lines_editor.swap_delete_line_button_blueprint();
                    text_lines_editor.delete_btn.disabled = false;
                    alert('Unable to set delete flag. Check your remote connection.');
                },
                success: function (xhr, ajaxOptions) {
                    if (!uuid) {
                        text_lines_editor.active_line.mutate();
                    }
                    text_lines_editor.swap_delete_line_button_blueprint();
                    text_lines_editor.delete_btn.disabled = false;

                    // Remove line from text_container
                    let to_del = [];
                    for (let line_container of text_lines_editor.text_container.children) {
                        if ($(line_container).attr('data-uuid') === uuid)
                            to_del.push(line_container);
                    }

                    for (let x of to_del)
                        x.remove();
                }
            });
            if (!uuid)
                this.active_line.container.focus();
        }
    }

    change_image(image_id, change_url_callback, line_id) {
        if (typeof this.lines !== 'undefined') {
            let unsaved_lines = false;
            for (let l of this.lines) {
                if (l.edited) {
                    unsaved_lines = true;
                }
            }
            if (unsaved_lines && !this.public_view) {
                if (confirm("Save changes?")) {
                    this.save_annotations();
                }
            }
        }
        this.focus_to = line_id;
        this.get_image(image_id);
        this.swap_delete_line_button_blueprint();
        if(!this.public_view)
            this.ignore_btn.innerHTML = '<i class="fas fa-minus-circle"></i> Ignore line';
        this.change_url = change_url_callback;
    }

    async get_image(image_id) {
        this.abort_controller.abort();
        this.abort_controller = new AbortController();
        let abort_signal = this.abort_controller.signal;
        await new Promise(resolve => setTimeout(resolve, 150));
        if (abort_signal.aborted) {
            return;
        }

        let route = '';
        if(this.public_view)
            route = Flask.url_for('ocr.get_public_lines', {'image_id': image_id});
        else
            route = Flask.url_for('ocr.get_lines', {'image_id': image_id});

        while (this.text_container.firstChild)
        {
            this.text_container.firstChild.remove();
        }
        let response = fetch(route, {
            signal: abort_signal,
        }).then(res => res.json());

        let data = await response;
        if (data['image_id'] != image_id) {
            return;
        }

        this.image_id = data['image_id'];
        this.width = data['width'];
        this.height = data['height'];
        this.active_line = false;
        this.lines = [];

        // Init map  // OLD COMPONENT
        if (this.map) {
            this.map.off();
            this.map.remove();
        }
        this.map = L.map(this.map_element, {
            crs: L.CRS.Simple,
            minZoom: -3,
            maxZoom: 3,
            center: [this.width / 2, this.height / 2],
            zoom: 0,
            editable: true,
            fadeAnimation: false,
            zoomAnimation: true,
            zoomSnap: 0
        });

        let bounds = [xy(0, -this.height), xy(this.width, 0)];
        this.map.setView(xy(this.width / 2, -this.height / 2), -2);  // OLD COMPONENT
        this.map.fitBounds(bounds);  // OLD COMPONENT

        /** Get background image url **/
        let image_url;
        if(this.public_view) {
            image_url = Flask.url_for('document.get_public_image', {'image_id': this.image_id});
        } else {
            image_url = Flask.url_for('document.get_image', {'image_id': this.image_id});
        }
        L.imageOverlay(image_url, bounds).addTo(this.map);  // OLD COMPONENT
        if (abort_signal.aborted) {
            return;
        }
        let self = this;
        let observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (m) {
                self.set_line_style(self.lines[m.target.id]);
            });
        });

        let i = 0;
        let debug_line_container = document.getElementById('debug-line-container');
        let debug_line_container_2 = document.getElementById('debug-line-container-2');
        let focused = false;

        // Add annotations to map
        for (let l of data['lines']) {
            let line = new TextLine(l.id, l.annotated, l.text, l.np_confidences, l.ligatures_mapping, l.arabic,
                                    l.for_training, debug_line_container, debug_line_container_2, !self.public_view,
                                    this);
            line.np_points = l.np_points;
            line.np_heights = l.np_heights;
            line.focus = false;
            this.add_line_to_map(i, line);
            this.lines.push(line);
            if (l.id == this.focus_to) {
                line.focus = true;
                this.line_focus(line);
                this.polygon_click(line);
                focused = true;
            }
            observer.observe(line.container, {attributes: true});
            i += 1;
            if (i % 50 == 49) {
                await new Promise(resolve => setTimeout(resolve, 0));
                if (abort_signal.aborted) {
                    return;
                }
            }

        }
        this.worst_confidence = 0.95;
        for (let l of this.lines) {
            this.worst_confidence = Math.min(this.worst_confidence, l.line_confidence);
        }
        for (let l of this.lines) {
            this.set_line_style(l, false);
        }

        if (this.focus_to != null) {
            this.focus_to = null;
        } else {
            this.map_element.focus();
        }

        this.map.addEventListener('zoomend', this.zoomend.bind(this));
        this.map.addEventListener('zoomstart', this.zoomstart.bind(this));
    }

    zoomstart()
    {
        this.animation_in_progress = true;
    }

    zoomend()
    {
        if (!this.animation_interrupted)
        {
            this.set_line_height();
        }
        this.animation_interrupted = false;
        this.animation_in_progress = false;
    }

    set_line_height()
    {
        if (this.active_line)
        {
            let view_port_line_height = this.active_line.np_heights[0] + this.active_line.np_heights[1];
            let view_port_y0 = this.map.getBounds()._northEast.lat;
            let view_port_y1 = this.map.getBounds()._southWest.lat;
            let view_port_height = - view_port_y1 + view_port_y0;
            let container = $('.editor-map');
            let container_height = container.height();
            let current_line_container_height = (view_port_line_height / view_port_height) * container_height;
            current_line_container_height = current_line_container_height.toFixed(0);
            let show_line_height = $('#show-line-height').val();
            if (!(this.map._zoom >= this.map.getMaxZoom() && current_line_container_height < show_line_height))
            {
                $('#show-line-height').val(current_line_container_height);
            }
        }
    }

    add_line_to_map(i, line) {
        let points = [];

        for (let point of line.np_points) {
            points.push(xy(point[0], -point[1]));
        }
        line.polygon = L.polygon(points);

        line.polygon.addTo(this.map);  // OLD COMPONENT
        line.polygon.on('click', this.polygon_click.bind(this, line));

        line.container.setAttribute("id", i);

        line.container.addEventListener('focus', () => {
            /** Select line (old) **/
            this.line_focus(line);
        });

        line.container.addEventListener('focusout', this.line_focus_out.bind(this, line));
        line.container.addEventListener('keyup', this.keyup_text_line_container.bind(this, line));
        line.container.addEventListener('click', this.click_text_line_container.bind(this, line));

        line.checkbox_span.addEventListener('click', this.line_focus_from_checkbox.bind(this, line));
        line.for_training_checkbox.addEventListener('click', this.ignore_action_from_checkbox.bind(this, line));

        this.text_container.appendChild(line.checkbox_span);
        this.text_container.appendChild(line.container);
    }

    line_focus_from_checkbox(line) {
        this.line_focus(line);
        line.container.focus();
    }

    ignore_action_from_checkbox(line) {
        if(this.public_view){
            return;
        }

        this.line_focus_from_checkbox(line);
        this.ignore_line_btn_action();
    }

    press_text_container(e) {
        if (e.keyCode == 13) {
            let line_number = parseInt(this.active_line.container.getAttribute("id"), 10);
            try {
                document.getElementById((line_number + 1).toString()).focus();
            }
            catch (e) {

            }
        }
    }

    keyup_text_line_container(line, e) {
        if (!this.focus_fired && !this.animation_in_progress)
        {
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
                this.move_view_port_according_to_caret_position(line);
            }
        }
        else
        {
            this.focus_fired = false;
        }
    }

    click_text_line_container(line, e) {
        if (!this.focus_fired && !this.animation_in_progress)
        {
            this.move_view_port_according_to_caret_position(line);
        }
        else
        {
            this.focus_fired = false;
        }
    }

    polygon_click(line) {
        line.container.focus();
    }

    line_focus(line) {
        this.focus_fired = true;
        if (this.active_line) {
            this.active_line.focus = false;
            this.set_line_style(this.active_line);
        }

        // OLD COMPONENT
        //let view_port_x0 = this.map.getBounds()._southWest.lng;
        //let view_port_y0 = this.map.getBounds()._northEast.lat;
        //let view_port_x1 = this.map.getBounds()._northEast.lng;
        //let view_port_y1 = this.map.getBounds()._southWest.lat;

        //let width_boundary = get_line_width_boundary(line);
        //let line_x0 = width_boundary[0];
        //let line_x1 = width_boundary[1];
        //let line_width = line_x1 - line_x0;
        //let view_port_width = view_port_x1 - view_port_x0;
        //if (line_width < view_port_width)
        //{
        //    view_port_x0 = line_x0 + line_width / 2  - view_port_width / 2;
        //    view_port_x1 = view_port_x0 + view_port_width;
        //}
        //else
        //{
        //    view_port_x0 = line_x0;
        //    view_port_x1 = line_x0 + view_port_width;
        //}

        //let height_boundary = get_line_height_boundary(line);
        //let line_y0 = height_boundary[0];
        //let line_y1 = height_boundary[1];
        //let container = $('.editor-map');
        //let container_bottom_pad = $('#show-bottom-pad').val();
        //let container_height = container.height();
        //let view_port_height = - view_port_y1 + view_port_y0;
        //let view_port_bottom_pad = (view_port_height / container_height) * container_bottom_pad
        //view_port_y0 = - (line_y1 + view_port_bottom_pad - view_port_height);
        //view_port_y1 = - (line_y1 + view_port_bottom_pad);
        let focus_line_points = get_focus_line_points(line);
        let view_port_x0 = focus_line_points[0];
        let view_port_y0 = -focus_line_points[2];
        let view_port_x1 = focus_line_points[1];
        let view_port_y1 = -focus_line_points[2];
        if (this.animation_in_progress)
        {
            this.animation_interrupted = true;
            this.map.stop();
        }
        this.map.flyToBounds([xy(view_port_x0, view_port_y0),
                              xy(view_port_x1, view_port_y1)],
                              {animate: true, duration: 0.5});
        this.active_line = line;
        line.focus = true;
        this.set_line_style(line);

        this.swap_delete_line_button_blueprint();
        this.swap_ignore_line_button_blueprint();

        this.change_url(this.active_line.id);
    }

    line_focus_out(line) {
        this.set_line_style(line)
    }

    move_view_port_according_to_caret_position(line) {
        let focus_line_points = get_focus_line_points(line);

        let view_port_x0 = this.map.getBounds()._southWest.lng;
        let view_port_y0 = this.map.getBounds()._northEast.lat;
        let view_port_x1 = this.map.getBounds()._northEast.lng;
        let view_port_y1 = this.map.getBounds()._southWest.lat;

        let width_boundary = get_line_width_boundary(line);
        let line_x0 = width_boundary[0];
        let line_x1 = width_boundary[1];

        // line in view port
        if ((view_port_x0 <= line_x0) && (view_port_x1 >= line_x1))
        {
            return;
        }

        let line_width = line_x1 - line_x0;
        let normalized_caret_position = line.get_normalized_caret_position();
        let image_caret_position = line_x0 + line_width * normalized_caret_position;

        let view_port_width = view_port_x1 - view_port_x0;
        let half_view_port_width = view_port_width / 2;
        let offset = view_port_width / 8;
        let current_focus = view_port_x0 + half_view_port_width;

        let container = $('.editor-map');
        let container_x_pad = 25;
        let view_port_x_pad = (container_x_pad / container.width()) * view_port_width;

        let new_focus = current_focus;
        // center focus according to caret position
        if ((image_caret_position > current_focus + half_view_port_width - offset) ||
            (image_caret_position < current_focus - half_view_port_width + offset))
        {
            new_focus = image_caret_position;
        }
        // clip focus
        if (new_focus + half_view_port_width > line_x1)
        {
            new_focus = line_x1 - half_view_port_width + view_port_x_pad;
        }
        if (new_focus - half_view_port_width < line_x0)
        {
            new_focus = line_x0 + half_view_port_width - view_port_x_pad;
        }
        // refocus
        if (new_focus != current_focus)
        {
            if (this.animation_in_progress)
            {
                this.animation_interrupted = true;
                this.map.stop();
            }
            this.map.flyToBounds([xy(new_focus - half_view_port_width, view_port_y0),
                                  xy(new_focus + half_view_port_width, view_port_y1)],
                                  {animate: true, duration: 0.5});
        }
    }

    show_line_change() {
        if (this.active_line) {
            let focus_line_points = get_focus_line_points(this.active_line);
            if (this.animation_in_progress)
            {
                this.animation_interrupted = true;
                this.map.stop();
            }
            this.map.flyToBounds([xy(focus_line_points[0], -focus_line_points[2]), xy(focus_line_points[1], -focus_line_points[2])],
                {animate: false, duration: 0});
        }
    }

    show_next_line() {
        var focused = false;
        if (this.active_line.id == undefined) {
            for (let line of this.lines) {
                if (Math.min.apply(Math, line.confidences) < 0.8 && line.text_line_element.style.backgroundColor != 'rgb(208, 255, 207)') {
                    this.line_focus(line);
                    this.polygon_click(line);
                    focused = true;
                    break;
                }

                if (focused) {
                    break;
                }
            }
        } else {
            let index = this.lines.findIndex(x => x.id === this.active_line.id);
            let rest_of_lines = this.lines.slice(index + 1);
            if (rest_of_lines.length != 0) {
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
            } else {
                next_page();
            }
        }
    }

    save_annotations() {
        if(this.public_view){
            return;
        }

        for (let l of this.lines) {
            if (l.edited) {
                l.save();
            }
        }
    }

    compute_scores(){
        if(this.public_view){
            return;
        }

        let route_ = Flask.url_for('document.compute_scores', {'document_id': document.querySelector('#document-id').textContent});
        $.get(route_);
    }
}


// HELPER FUNCTIONS
// #############################################################################


function componentToHex(c) {
    let hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}


// #############################################################################
// Annotator component helper functions

/**
 * Converts raw data annotations to desired format
 * @param raw_data {}
 * @param type str row/region
 * @returns annotations [{*}]
 */
function get_annotations(raw_data, type) {
    if (type === 'row') {
        return raw_data.lines.map(raw_row => {
            return {
                uuid: raw_row.id,
                region_annotation_uuid: raw_row.region_id, // FK to parent region uuid
                points: raw_row.np_points.map(point => {
                    return {x: point[0], y: point[1]}
                }),
                baseline: raw_row.np_baseline.map(point => {
                    return {x: point[0], y: point[1]}
                }),
                heights: {up: raw_row.np_heights[0], down: raw_row.np_heights[1]},
                state: '', // active/ignored/edited
                text: raw_row.text,
                order: 0,
                confidence: get_confidence(raw_row.np_confidences),

                // Statuses
                edited: false,
                annotated: raw_row.annotated,
                is_valid: true
            }
        });
    }
    else if (type === 'region') {
        return raw_data.regions.map(raw_region => {
            return {
                uuid: raw_region.uuid,
                points: raw_region.np_points.map(point => {
                    return {x: point[0], y: point[1]}
                }),
            }
        });
    }
}

/**
 * Get line confidence
 * @param confidences
 * @returns {number}
 */
function get_confidence(confidences) {
    let line_confidence = 0;
    if (confidences.length > 0){
        let power_const = 5;
        for (let c of confidences)
            line_confidence += (1 - c) ** power_const;
        line_confidence = 1 - (line_confidence / confidences.length) ** (1.0/power_const)
    }
    return line_confidence;
}



function get_focus_line_points(line) {
    let show_line_height = $('#show-line-height').val();
    let show_bottom_pad = $('#show-bottom-pad').val();
    let width_boundary = get_line_width_boundary(line);
    let height_boundary = get_line_height_boundary(line);
    let start_x = width_boundary[0];
    let end_x = width_boundary[1];
    let start_y = height_boundary[0];
    let end_y = height_boundary[1];
    let line_height = line.np_heights[0] + line.np_heights[1];
    let line_width = end_x - start_x;
    let container = $('.editor-map');
    let container_width = container.width();
    let container_height = container.height();
    let expected_show_line_height = line_height * (container_width / line_width);
    let new_line_width = (line_height * container_width) / show_line_height;
    if (expected_show_line_height > show_line_height) {
        start_x -= (new_line_width - line_width) / 2;
        end_x += (new_line_width - line_width) / 2;
    }
    if (expected_show_line_height < show_line_height) {
        let container_left_pad = 25;
        let left_pad = (line_height * container_left_pad) / show_line_height;
        start_x -= left_pad;
        end_x -= line_width - new_line_width + left_pad;
    }
    let view_port_container_height = (line_height * container_height) / show_line_height;
    let bottom_pad = (line_height * show_bottom_pad) / show_line_height;
    let y = end_y - view_port_container_height / 2 + bottom_pad;
    return [start_x, end_x, y];
}

function get_line_height_boundary(line) {
    let height_min = 100000000000000000000000;
    let height_max = 0;
    for (let coord of line.np_points) {
        if (coord[1] < height_min) {
            height_min = coord[1];
        }
        if (coord[1] > height_max) {
            height_max = coord[1];
        }
    }
    return [height_min, height_max];
}

function get_line_width_boundary(line) {
    let width_min = 100000000000000000000000;
    let width_max = 0;
    for (let coord of line.np_points) {
        if (coord[0] < width_min) {
            width_min = coord[0];
        }
        if (coord[0] > width_max) {
            width_max = coord[0];
        }
    }
    return [width_min, width_max];
}
