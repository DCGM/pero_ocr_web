class LP_object {
    constructor(editor, uuid, deleted, ignore, points, text, polygon) {
        var myself = this;
        this.editor = editor;
        this.uuid = uuid;
        this.deleted = deleted;
        this.ignore = ignore;
        this.text = text;
        this.points = [];

        if (polygon) {
            this.polygon = polygon;
        } else {
            for (var j in points) {
                this.points[j] = xy(points[j][0], -points[j][1])
            }
            this.polygon = L.polygon(this.points);
        }
        this.polygon.addTo(this.editor.map);
        this.polygon.on('click', function () {
            myself.obj_click()
        });
        this.update_style();
    }

    obj_click() {
        this.editor.edited = true;
        if (this.deleted || this.ignore) {
            this.deleted = 0;
            this.ignore = 0;
            this.update_style();
        }
        this.editor.unselect_objects();
        this.polygon.toggleEdit();
    }

    update_style() {
        var color = this.polygon_colors.good;
        if (this.deleted) {
            color = this.polygon_colors.deleted;
        } else if (this.ignore) {
            color = this.polygon_colors.ignore;
        }
        this.polygon.setStyle({
            color: color, opacity: 1.0, fillColor: color, fillOpacity: 0.1,
            radius: 6, clickable: true
        });
    }

    polygon_colors = {
        good: '#00FF00',
        ignore: '#0000FF',
        deleted: '#C000C0'
    }
}
