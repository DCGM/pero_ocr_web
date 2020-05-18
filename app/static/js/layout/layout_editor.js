
var uid = getCookie('uid');
uid = guid();
setCookie('uid', uid, 360);

yx = L.latLng;
xy = function (x, y) {
    if (L.Util.isArray(x)) {    // When doing xy([x, y]);
        return yx(x[1], x[0]);
    }
    return yx(y, x);  // When doing xy(x, y);
};


class LayoutEditor{
    constructor(){
        this.uuid = '';
        this.map = null;
        this.objects = [];
        this.temp_objects = [];
        this.order_lines = [];

        this.create_new_object_btn = document.getElementById('create-new-object-btn');
        this.create_new_object_btn.addEventListener('click', this.create_new_object.bind(this));

        this.toggle_delete_object_btn = document.getElementById('toggle-delete-object-btn');
        this.toggle_delete_object_btn.addEventListener('click', this.toggle_delete_object.bind(this));

        this.toggle_delete_all_objects_btn = document.getElementById('toggle-delete-all-objects-btn');
        this.toggle_delete_all_objects_btn.addEventListener('click', this.toggle_delete_all_objects.bind(this));

        this.reset_btn = document.getElementById('reset-btn');
        this.reset_btn.addEventListener('click', this.reset_image.bind(this));

        this.save_image_btn = document.getElementById('save-image-btn');
        this.save_image_btn.addEventListener('click', this.save_image.bind(this));
    }

    temp_copy_objects(){
        this.temp_objects = [];
        for (var i in this.objects) {
            this.temp_objects[this.temp_objects.length] = [String(this.objects[i].points), this.objects[i].deleted];
        }
    }

    is_changed(){
        if (this.temp_objects.length != this.objects.length){
            return true;
        }

        for (var i in this.objects) {
            if (String(this.objects[i].polygon._latlngs[0]) != this.temp_objects[i][0]){
                return true;
            }
        }

        for (var i in this.objects) {
            if (this.objects[i].deleted != this.temp_objects[i][1]){
                return true;
            }
        }

        return false;
    }

    unselect_objects () {
        for (var i in this.objects) {
            this.objects[i].polygon.disableEdit()
        }
    }

    get_selected() {
        for (var i in this.objects) {
            if (this.objects[i].polygon.editEnabled()) {
                return this.objects[i];
            }
        }
        return null;
    }

    create_new_object() {
        this.unselect_objects();
        var poly = this.map.editTools.startPolygon()
        this.objects.push(new LP_object(this, guid(), 0, 0, [], '', poly));
    }

    toggle_delete_object() {
        let obj = this.get_selected();
        if (obj) {
            obj.deleted = !obj.deleted;
            obj.update_style();
        }
    }

    toggle_delete_all_objects() {
        for (let obj of this.objects) {
            if (obj) {
                obj.deleted = !obj.deleted;
                obj.update_style();
            }
        }
    }

    reset_image(){
        this.change_image(this.uuid)
    }

    change_image(image_id){
        if (this.is_changed()){
            if (confirm("Save changes?"))
            {
                this.save_image();
            }
        }
        this.uuid = image_id;
        this.get_image(image_id);
        this.reload_layout_preview(image_id);
    }

    get_image(image_uuid) {
        this.uuid = null;
        this.objects = null;
        try {
            if (this.map){
                this.map.remove();
                this.map = null;
            }
        } catch (e) {
            console.log(e);
        }

        var url = `/layout_analysis/get_image_result/${image_uuid}`;

        $.get(url, this.report_status('FAILED: Did not get next image.'),
            this.new_image_callback.bind(this));
    }

    recompute_order(){
        if (this.objects.length > 1){
            for (var i in this.objects){
                this.objects[i].get_new_centroid();
            }

            for (let i = 0; i < (this.objects.length-1); i++) {
                this.order_lines[i].refresh_line(this.objects[i].centroid, this.objects[i+1].centroid);
            }
        }
    }

    new_image_callback(data, status) {
        this.map_region = document.getElementById('map-container');

        this.map_region.innerHTML = "<div id='mapid'></div>";
        this.map_region.addEventListener('click', this.recompute_order.bind(this));
        this.uuid = data['uuid'];
        this.width = data['width'];
        this.height = data['height'];
        this.objects = data['objects'];

        this.map = L.map('mapid', {
            crs: L.CRS.Simple,
            minZoom: -3,
            maxZoom: 3,
            center: [0, 0],
            zoom: 0,
            editable: true,
            fadeAnimation: false,
            zoomAnimation: false,
            zoomSnap: 0.25
        });

        var bounds = [xy(0, -this.height), xy(this.width, 0)];
        this.map.setView(xy(this.width / 2, -this.height / 2), -2);
        var image = L.imageOverlay(`/document/get_image/${this.uuid}`, bounds).addTo(this.map);

        //zoom_level = Math.logthis.width / 256.0) / Math.log(2)
        this.map.fitBounds(bounds);

        for (var i in this.objects) {
            this.objects[i] = new LP_object(
                this,
                this.objects[i].uuid,
                this.objects[i].deleted, false,
                this.objects[i].points, '');
        }

        if (this.objects.length > 1){
            for (let i = 0; i < (this.objects.length-1); i++) {
                this.order_lines.push(new PL_order(this.objects[i].centroid, this.objects[i+1].centroid, this.map));
            }
        }

        this.report_status('Got image: ' + data['uuid']);
        this.temp_copy_objects();
    }

    report_status(text) {
        var status_bar = document.getElementById('status');
        status_bar.innerHTML = text;
    }

    reload_layout_preview(uuid){
        document.querySelector('figure[data-image="'+ uuid +'"]').children[0].attributes[1].nodeValue = Flask.url_for(
                'layout_analysis.get_result_preview', {'image_id': uuid});
    }

    save_image(){
        if (this.uuid) {
            var obj_to_send = [];
            for (var obj_key in this.objects) {
                var obj = this.objects[obj_key];
                if (obj.polygon._latlngs[0].length > 3) {
                    var points = [];
                    for (var i in obj.polygon._latlngs[0]) {
                        points[i] = [obj.polygon._latlngs[0][i].lng, -obj.polygon._latlngs[0][i].lat];
                    }

                    obj_to_send[obj_key] = {
                        uuid: obj.uuid,
                        points: points,
                        ignore: obj.ignore,
                        deleted: obj.deleted,
                    }
                }
            }
            console.log(obj_to_send);
            var data = JSON.stringify(obj_to_send);
            var imageId = this.uuid;
            $.ajax("/layout_analysis/edit_layout/" + imageId, {
                data: data,
                contentType: 'application/json', type: 'POST'
            }).done(this.reload_layout_preview.bind(this, this.uuid));
            this.temp_copy_objects();
        }
    }
}

// HELPER FUNCTIONS
// #############################################################################

function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    var expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + "; " + expires;
}

function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return '';
}

function guid() {
    function randomDigit() {
        if (crypto && crypto.getRandomValues) {
            var rands = new Uint8Array(1);
            crypto.getRandomValues(rands);
            return (rands[0] % 16).toString(16);
        } else {
            return ((Math.random() * 16) | 0).toString(16);
        }
    }

    var crypto = window.crypto || window.msCrypto;
    return 'xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx'.replace(/x/g, randomDigit);
}
