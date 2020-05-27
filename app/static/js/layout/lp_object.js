class LP_object {
    constructor(editor, uuid, deleted, ignore, points, text, polygon, order) {
        var myself = this;
        this.editor = editor;
        this.uuid = uuid;
        this.deleted = deleted;
        this.ignore = ignore;
        this.text = text;
        this.points = [];
        this.centroid = null;
        this.order = order;
        this.prev_order = order;
        this.ordering = false;
        this.show_order = true;
        this.toolTipColor = this.changeToolTipColor('base');

        if (polygon) {
            this.polygon = polygon;
        } else {
            for (var j in points) {
                this.points[j] = xy(points[j][0], -points[j][1]);
            }
            this.polygon = L.polygon(this.points);
        }
        this.polygon.addTo(this.editor.map);
        this.polygon.on('click', this.obj_click.bind(this));
        this.polygon.on("dblclick", this.obj_dblclick.bind(this));
        this.update_style();
        if (this.points.length >= 3){
            this.get_new_centroid(false);

            this.marker = new L.Marker(this.centroid, { opacity: 0.01 });
            this.marker.bindTooltip("1", { permanent: true, direction: 'right', offset: [-18, 25] });
            this.marker.addTo(this.editor.map);
            this.marker._tooltip._container.style.backgroundColor = this.toolTipColor;
            let element = this.marker.getElement();
            element.addEventListener('click', this.obj_click.bind(this));
        }
    }

    change_order(new_order){
        this.prev_order = this.order;
        this.order = new_order;
    }

    prev_order_to_order(){
        this.order = this.prev_order;
    }

    obj_dblclick(){
        if (this.ordering){
            var self = this;
            if (this.editor.previous_object.length == 1){
                this.editor.make_first(self);
            }
            else{
                this.editor.make_append(self);
            }
        }
    }

    obj_click() {
        if (this.deleted || this.ignore) {
            this.deleted = 0;
            this.ignore = 0;
            this.update_style();
        }
        this.editor.unselect_objects();
        this.polygon.toggleEdit();
        if (this.ordering){
            this.editor.reorder_objects(this);
            this.polygon.disableEdit();
        }
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

    get_new_centroid(recompute_order=true){
        this.centroid = this.polygon.getBounds().getCenter();
        if (recompute_order){
            this.get_order();
        }
    }

    get_order(){
         if (this.show_order){
             this.remove_order();
             this.marker = new L.Marker(this.centroid, { opacity: 0.01 });
             this.marker.bindTooltip(String(Number(this.order)+1), { permanent: true, direction: 'right', offset: [-18, 25] });
             this.marker.addTo(this.editor.map);
             this.marker._tooltip._container.style.backgroundColor = this.toolTipColor;
             let element = this.marker.getElement();
             element.addEventListener('click', this.obj_click.bind(this));
         }
         else{
             this.remove_order();
         }
    }

    remove_order(){
        try{
            this.editor.map.removeLayer(this.marker);
        }
        catch (e) {
            ;
        }
    }

    changeToolTipColor(type){
        switch (type) {
            case 'base':
                this.toolTipColor = 'white';
                break;
            case 'last':
                this.toolTipColor = 'deepskyblue';
                break;
            case 'ordered':
                this.toolTipColor = 'skyblue';
                break;
        }
    }

    polygon_colors = {
        good: '#00FF00',
        ignore: '#0000FF',
        deleted: '#C000C0'
    }
}
