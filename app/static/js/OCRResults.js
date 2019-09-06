yx = L.latLng;
xy = function(x, y) {
    if (L.Util.isArray(x)) {    // When doing xy([x, y]);
        return yx(x[1], x[0]);
    }
    return yx(y, x);  // When doing xy(x, y);
};

class ImageEditor{
    constructor(container) {
        this.container = container;
        this.container.innerHTML = "<div class='editor-map'></div><div class='status'></div>";
        this.polygon_colors = {
            good: '#00FF00',
            ignore: '#0000FF',
            deleted: '#C000C0'
        };
    }

    get_image(document_id, image_id) {
         var route = `/ocr/get_lines/${document_id}/${image_id}`;
        $.get(route, this.new_image_callback.bind(this));
    }

    new_image_callback(data, status) {
        this.container.innerHTML = "<div class='editor-map'></div><div class='status'></div>";
        this.document_id = data['document_id'];
        this.image_id = data['image_id'];
        this.width = data['width'];
        this.height = data['height'];
        this.lines = data['lines'];

        let map_element = this.container.getElementsByClassName("editor-map")[0]

        this.map = L.map(map_element, {
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


        for (let line of this.lines) {
            this.add_line_to_map(line);
        }
        map_element.focus();
        //map_element.onkeydown = this.basic_keypress.bind(this);
    }

    add_line_to_map(line, polygon){
        let points = [];
        if(polygon){
            line.polygon = polygon;
        } else {
            for( let point of line.np_points){
                points.push(xy(point[0], -point[1]));
            }
            line.polygon = L.polygon(points);
        }
        line.polygon.addTo(this.map);
        line.polygon.on('click', this.obj_click.bind(this, line));
        //this.update_style(position);
    }

    obj_click(line){
        console.log(line.text)
    }

    update_style(position){
        let color = this.polygon_colors.good;
        if( position.deleted){
            color = this.polygon_colors.deleted;
        } else if( position.ignore){
            color = this.polygon_colors.ignore;
        }
        position.polygon.setStyle({ color: color, opacity: 1.0, fillColor: color, fillOpacity: 0.1,
            weight: 0.5, radius: 6, clickable: true});
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


