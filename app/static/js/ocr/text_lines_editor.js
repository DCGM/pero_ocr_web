
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
        this.container = container;
        this.active_line = false;
        this.focused_line = false;
        let save_btn = document.getElementsByClassName('save-btn');
        let next_suspect_btn = document.getElementById('nextsucpectline');
        let show_line_height = document.getElementById('show-line-height');
        let show_bottom_pad = document.getElementById('show-bottom-pad');
        for (let btn of save_btn)
        {
            btn.addEventListener('click', this.save_annotations.bind(this));
        }
        next_suspect_btn.addEventListener('click', this.show_next_line.bind(this));
        show_line_height.addEventListener('input', this.show_line_change.bind(this));
        show_bottom_pad.addEventListener('input', this.show_line_change.bind(this));
    }

    change_image(image_id)
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
        this.get_image(image_id)
    }

    get_image(image_id)
    {
        let route = Flask.url_for('ocr.get_lines', {'image_id': image_id});
        $.get(route, this.new_image_callback.bind(this));
        let text_container = document.getElementById('text-container');
        text_container.addEventListener('keypress', this.press_text_container.bind(this));
        while (text_container.firstChild)
        {
            text_container.firstChild.remove();
        }
    }

    new_image_callback(data, status)
    {
        this.container.innerHTML = "<div class='editor-map'></div><div class='status'></div>";
        this.image_id = data['image_id'];
        this.width = data['width'];
        this.height = data['height'];
        this.active_line = false;
        this.lines = [];

        for (let l of this.lines)
        {
            l.edited = false;
            l.saved = false;
        }

        this.map_element = this.container.getElementsByClassName("editor-map")[0];

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
        L.imageOverlay(Flask.url_for('document.get_image', {'image_id': this.image_id}), bounds).addTo(this.map);
        this.map.fitBounds(bounds);

        let i = 0;
        for (let l of data['lines'])
        {
            let line = new TextLine(l.id, l.text, l.np_confidences)
            line.np_points = l.np_points;
            line.annotated = l.annotated;
            this.add_line_to_map(i, line);
            this.lines.push(line);
            i += 1;
        }
        this.map_element.focus();
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

        document.getElementById('text-container').appendChild(line.container);

        if (line.annotated)
        {
            line.set_background_to_annotated();
        }
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
            }
            else{
                next_page();
            }
        }
    }

    save_annotations()
    {
        let annotations = [];
        for (let l of this.lines)
        {
            if (l.edited)
            {
                l.save();
                l.edited = false;
                l.saved = true;
            }
        }
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
