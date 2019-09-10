yx = L.latLng;
xy = function(x, y) {
    if (L.Util.isArray(x)) {    // When doing xy([x, y]);
        return yx(x[1], x[0]);
    }
    return yx(y, x);  // When doing xy(x, y);
};

function componentToHex(c) {
    var hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

function setColor(color) {
    document.execCommand('styleWithCSS', false, true);
    document.execCommand('foreColor', false, color);
}

class ImageEditor{
    constructor(container) {
        this.container = container;
        this.container.innerHTML = "<div class='editor-map'></div><div class='status'></div>";
        var save_btn = document.getElementById('save-btn')
        save_btn.addEventListener('click', this.save_lines.bind(this));
    }

    get_image(document_id, image_id) {
         var route = Flask.url_for('ocr.get_lines', {'document_id': document_id, 'image_id': image_id});
        $.get(route, this.new_image_callback.bind(this));
    }

    new_image_callback(data, status) {
        this.container.innerHTML = "<div class='editor-map'></div><div class='status'></div>";
        this.document_id = data['document_id'];
        this.image_id = data['image_id'];
        this.width = data['width'];
        this.height = data['height'];
        this.lines = data['lines'];
        this.edited = false;

        this.map_element = this.container.getElementsByClassName("editor-map")[0]

        this.map = L.map(this.map_element, {
            crs: L.CRS.Simple,
            minZoom: -3,
            maxZoom: 3,
            center: [0, 0],
            zoom: 0,
            editable: true,
            fadeAnimation: false,
            zoomAnimation: false,
            zoomSnap: 0.2
        });

        let bounds = [xy(0, -this.height), xy(this.width, 0)];
        this.map.setView(xy(this.width / 2, -this.height / 2), -2);
        let image = L.imageOverlay(Flask.url_for('document.get_image', {'document_id': this.document_id, 'image_id': this.image_id}), bounds).addTo(this.map);

        //zoom_level = Math.log(annotator_data.width / 256.0) / Math.log(2)
        this.map.fitBounds(bounds);


        for (let i in this.lines) {
            this.add_line_to_map(i, this.lines[i]);
        }
        this.map_element.focus();
        //map_element.onkeydown = this.basic_keypress.bind(this);
    }

    set_confidences_line(text_line_div, line){
        var chars = line.text.split("");
        for(let i in line.np_confidences)
        {
            var char_span = document.createElement('span');
            char_span.setAttribute("style", "background: " + rgbToHex(255, Math.floor(line.np_confidences[i] * 255), Math.floor(line.np_confidences[i] * 255)));
            char_span.innerHTML = chars[i];
            text_line_div.appendChild(char_span);
        }
    }

    add_line_to_map(i, line, polygon){
        let points = [];
        if(polygon){
            line.polygon = polygon;
        } else {
            for( let point of line.np_points){
                points.push(xy(point[0], -point[1]));
            }
            line.polygon = L.polygon(points);
            line.polygon.setStyle({ color: "#0059ff", opacity: 1, fillColor: "#0059ff", fillOpacity: 0.1});
        }
        line.polygon.addTo(this.map);
        line.polygon.on('click', this.polygon_click.bind(this, line));
        //this.update_style(position);

        var text_line_div = document.createElement('div');
        text_line_div.setAttribute("contentEditable", "true");
        text_line_div.setAttribute("id", i);
        this.set_confidences_line(text_line_div, line);
        document.getElementById('text-container').appendChild(text_line_div);
        line.text_line_element = text_line_div;
        text_line_div.addEventListener('focus', this.line_click.bind(this, line));
        text_line_div.addEventListener('keypress', this.line_press.bind(this, line));
    }

    polygon_click(line){
        for (let l of this.lines)
        {
            l.polygon.setStyle({ color: "#0059ff", opacity: 1, fillColor: "#0059ff", fillOpacity: 0.1});
        }
        line.polygon.setStyle({ color: "#028700", opacity: 1, fillColor: "#028700", fillOpacity: 0.1});
        line.text_line_element.focus();
    }

    line_click(line){
        for (let l of this.lines)
        {
            l.polygon.setStyle({ color: "#0059ff", opacity: 1, fillColor: "#0059ff", fillOpacity: 0.1});
        }
        var start_x = line.np_baseline[0][0];
        var start_y = line.np_baseline[0][1];
        var end_x = line.np_baseline[line.np_baseline.length - 1][0];
        var end_y = line.np_baseline[line.np_baseline.length - 1][1];
        var line_length = end_x - start_x;
        var y_pad = line_length / 10;
        var middle_x = start_x + line_length / 2;
        var middle_y = (start_y + end_y) / 2;
        this.map.fitBounds([xy(start_x, -start_y + y_pad), xy(end_x, -end_y + y_pad)]);
        line.polygon.setStyle({ color: "#028700", opacity: 1, fillColor: "#028700", fillOpacity: 0.1});
    }

    line_press(line, e){
        for (let child of e.target.childNodes)
        {
            if (child.innerHTML == "")
            {
                e.target.removeChild(child);
            }
        }
        setColor("#028700");

        if (e.keyCode == 13)
        {
            e.preventDefault();
            var line_number = parseInt(e.target.getAttribute("id"), 10);
            document.getElementById((line_number + 1).toString()).focus();
        }

        if (e.keyCode != 13 && e.keyCode != 9)
        {
            line.edited = true;
        }
    }

    save_lines(){
        var edited_lines = [];
        for (let l of this.lines)
        {
            if (l.edited)
            {
                var line_text = "";
                for (let child of l.text_line_element.childNodes)
                {
                    if (child.childNodes.length > 1)
                    {
                        if (child.childNodes[0].childNodes.length > 0)
                        {
                            line_text += child.childNodes[0].innerHTML;
                            line_text += child.childNodes[1].textContent;
                        }
                        else
                        {
                            line_text += child.childNodes[0].textContent;
                            line_text += child.childNodes[1].innerHTML;
                        }
                    }
                    else
                    {
                        line_text += child.innerHTML;
                    }
                }
                var line_dict = {};
                line_dict["id"] = l.id;
                line_dict["text"] = line_text;
                edited_lines.push(line_dict);
                console.log(l.id, line_text);
            }
        }
        console.log(edited_lines);
        console.log(JSON.stringify(edited_lines));
        var route = Flask.url_for('ocr.save_lines', {});
        console.log(route);
        $.post(route, {lines: JSON.stringify(edited_lines)}, function(data, status) {});
    }





    basic_keypress(e) {
        // g - not deleted
        // h - not ignored
        // j - aligner
        // o - reset original object annotation

        // n, s - save

        if(e.key == "o") {
            this.get_image();
        } else if(e.key == "n" || e.key == "s") {
            this.save_objects();
        } else if(e.key == "c"){
            this.create_new_object();
        } else if(e.key == 'g'){
            this.toggle_delete_object();
        } else if(e.key == 'h'){
            this.toggle_ignore_object();
        } else if(e.key == 'j'){
            this.get_image(true)
        }
    }

}

var image_editor = new ImageEditor(document.getElementById('map-container'));

$('.image-item-container').on('click', function (event) {
    let document_id = $(this).data('document');
    let image_id = $(this).data('image');
    image_editor.get_image(document_id, image_id)
});


