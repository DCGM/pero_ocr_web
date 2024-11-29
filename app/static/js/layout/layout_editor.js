
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

        this.show_reading_order_btn = document.querySelector("input[name=show-reading-order-btn]");
        this.show_reading_order_btn.addEventListener('change', this.show_reading_order.bind(this));

        this.set_reading_order_btn = document.querySelector("input[name=set-reading-order-btn]");
        this.set_reading_order_btn.addEventListener('change', this.set_reading_order.bind(this));

        this.map_region = document.getElementById('map-container');
        this.map_region.addEventListener('click', this.redraw_order.bind(this));

        this.leaflet = document.querySelector('body');

        this.previous_object = [];
        this.last_action = null;
    }

    show_reading_order(){
        if (this.show_reading_order_btn.checked){
            let parent_element = this.show_reading_order_btn.parentElement;
            parent_element.children[1].innerText = 'Hide reading order (w)';
        }
        else{
            let parent_element = this.show_reading_order_btn.parentElement;
            parent_element.children[1].innerText = 'Show reading order (w)';
        }
        this.redraw_order();
    }

    set_reading_order(){
        if (this.show_reading_order_btn.checked == false && this.set_reading_order_btn.checked){
            this.disable_set_order();
            this.enable_show_order();
            this.show_reading_order();
            this.enable_set_order();

        }
        if (this.set_reading_order_btn.checked){
            this.enable_set_order();
            this.map.doubleClickZoom.disable();
        }
        else {
            if (this.show_reading_order_btn.checked == true){
                this.disable_set_order();
                this.map.doubleClickZoom.enable();
            }
        }

        this.unselect_objects();
        for (var i in this.objects) {
            this.objects[i].ordering = !this.objects[i].ordering;
        }
        if (this.set_reading_order_btn.checked == false){
            this.previous_object = [];
            for (var i in this.objects){
                this.objects[i].changeToolTipColor('base');
            }
            this.show_reading_order();
        }

        this.last_action = "redraw_order";
    }

    remove_empty(){
        var end = true;
        while (true){
            for (var i in this.objects){
                if (this.objects[i].polygon._latlngs[0].length < 3){
                    this.objects.splice(i, 1);
                    end = false;
                    break;
                }
                end = true;
            }
            if (end){
                break;
            }
        }
    }

    make_first(object){
        this.remove_empty();
        let order = Number(object.order);
        let highest = Number(this.objects[this.objects.length-1].order);
        for (var i in this.objects) {
            if (Number(this.objects[i].order) < order){
                this.objects[i].order = Number(highest) + Number(i) + 1;
            }
        }
        this.objects.sort((a, b) => (Number(a.order)) - (Number(b.order)));
        for (var i in this.objects) {
            this.objects[i].order = i;
        }
        if (this.previous_object[this.previous_object.length - 1].uuid !== object.uuid){
            this.previous_object.push(Object.assign( Object.create( Object.getPrototypeOf(object)), object));
        }
        else{
            this.previous_object[this.previous_object.length-1].order = object.order;
        }
        this.last_action = "reorder_objects";
        this.redraw_order();
    }

    make_append(object){
        this.remove_empty();
        for (var i in this.objects){
            this.objects[i].prev_order_to_order();
        }

        this.objects.sort((a, b) => (Number(a.order)) - (Number(b.order)));
        for (var i in this.objects) {
            this.objects[i].order = i;
        }

        var actual_order = String(object.order);
        this.previous_object.reverse();
        for (var i in this.previous_object){
            if (object.uuid !== this.previous_object[i].uuid){
                var previous_order = String(this.previous_object[i].order);
                break;
            }
        }
        this.previous_object.reverse();
        let highest = Number(this.objects[this.objects.length-1].order);

        if (Number(actual_order) > Number(previous_order)){
                for (var i in this.objects){
                    if (Number(this.objects[i].order) > Number(previous_order) && this.objects[i].order < Number(actual_order)){
                        this.objects[i].order = Number(highest) + Number(i) + 1;
                    }
                    else{
                        if (Number(this.objects[i].order) > Number(actual_order)){
                            this.objects[i].order = Number(previous_order) + Number(i) + 1;
                        }
                    }
                }
        }
        else {
            if (Number(actual_order) < Number(previous_order)){
                for (var i in this.objects) {
                    if (Number(this.objects[i].order) > Number(previous_order)){
                        this.objects[i].order = Number(highest) + Number(i) + 1;
                    }
                }
                for (var i in this.objects){
                    if (Number(this.objects[i].order) >= Number(actual_order) && this.objects[i].order < Number(previous_order)){
                        this.objects[i].order = Number(previous_order) + Number(i) + 1;
                    }
                }
            }
        }
        this.objects.sort((a, b) => (Number(a.order)) - (Number(b.order)));
        for (var i in this.objects) {
            this.objects[i].order = i;
        }
        if (this.previous_object[this.previous_object.length - 1].uuid !== object.uuid){
            this.previous_object.push(Object.assign( Object.create( Object.getPrototypeOf(object)), object));
        }
        else{
            this.previous_object[this.previous_object.length-1].order = object.order;
        }
        this.last_action = "reorder_objects";
        this.redraw_order();
    }

    reorder_objects(object){
        this.last_action = "reorder_objects";
        object.changeToolTipColor('last');
        if (this.previous_object.length == 0){
            this.previous_object.push(object);
        }
        else {
            if (this.previous_object[this.previous_object.length - 1].uuid !== object.uuid){
                this.previous_object[this.previous_object.length - 1].changeToolTipColor('ordered');
                let order = Number(this.previous_object[this.previous_object.length - 1].order) + 1;

                for (var i in this.objects) {
                    if (this.objects[i].order >= Number(order)){
                        this.objects[i].change_order(Number(this.objects[i].order) + 1);
                    }
                    else{
                        this.objects[i].change_order(this.objects[i].order);
                    }
                }
                object.order = order;
            }
            for (var i in this.previous_object){
                if (this.previous_object[i].uuid !== object.uuid){
                    this.previous_object[i].changeToolTipColor('ordered');
                }
            }
        }

        this.objects.sort((a, b) => (Number(a.order)) - (Number(b.order)));
        for (var i in this.objects) {
            this.objects[i].order = Number(i);
        }
        if (this.previous_object[this.previous_object.length - 1].uuid !== object.uuid){
            this.previous_object.push(object);
        }
    }

    redraw_order(){
        if (this.last_action != null){
            if (this.last_action == "redraw_order"){
                if (this.set_reading_order_btn.checked){
                    this.disable_set_order();
                    this.set_reading_order();
                }
            }
            this.last_action = "redraw_order";
        }
        if (this.objects.length > 1){
            for (let i = 0; i < (this.objects.length); i++) {
                if (this.objects[i].polygon._latlngs[0].length >= 3 && this.objects[i].centroid == null) {
                    this.objects[i].get_new_centroid();
                    this.order_lines.push(new PL_order(this.objects[i - 1].centroid, this.objects[i].centroid, this.map));
                }
            }
        }
        for (var i in this.objects){
            this.objects[i].show_order = this.show_reading_order_btn.checked;
            if (this.objects[i].polygon._latlngs[0].length >= 3){
                this.objects[i].get_new_centroid();
            }
        }
        for (let i = 0; i < (this.objects.length-1); i++) {
            if (this.objects[i].polygon._latlngs[0].length >= 3 && this.objects[i + 1].polygon._latlngs[0].length >= 3){
                if (this.show_reading_order_btn.checked) {
                    this.order_lines[i].refresh_line(this.objects[i].centroid, this.objects[i + 1].centroid);
                }
                else{
                    this.order_lines[i].remove_line();
                }
            }
        }
    }

    get_default_order(){
        var highest_current_order = -1;
        var not_ordered = [];
        var hightest_lat = [];
        for (var i in this.objects) {
            if (this.objects[i].order == null){
                not_ordered.push(this.objects[i]);
                let highest = -100000;
                for (var e in this.objects[i].polygon._latlngs[0]){
                    let latitude = layout_editor.objects[i].polygon._latlngs[0][e]["lat"];
                    if (highest < latitude){
                        highest = latitude;
                    }
                }
                hightest_lat.push(highest);
            }
            else{
                if (this.objects[i].order > highest_current_order){
                    highest_current_order = this.objects[i].order;
                }
            }
        }

        var sorted_not_ordered = hightest_lat.map(function(e,i){return i;})
               .sort(function(a,b){return hightest_lat[a] - hightest_lat[b];})
               .map(function(e){return not_ordered[e];});
        sorted_not_ordered = sorted_not_ordered.reverse();

        for (var i in sorted_not_ordered){
            sorted_not_ordered[i].order = highest_current_order + 1;
            sorted_not_ordered[i].prev_order = highest_current_order + 1;
            highest_current_order += 1;
        }
    }

    enable_set_order(){
        $(":checkbox").eq(1).prop('checked', true);
        $('#setOrderWrapper').addClass("active").css({"background-color": "deepskyblue", "border-color": "deepskyblue"});
        this.create_new_object_btn.disabled = true;
        this.toggle_delete_object_btn.disabled = true;
        this.toggle_delete_all_objects_btn.disabled = true;
    }

    disable_set_order(){
        $(":checkbox").eq(1).prop('checked', false);
        $('#setOrderWrapper').removeClass("active").css({"background-color": "", "border-color": ""});
        for (var i in this.objects){
            this.objects[i].changeToolTipColor('base');
        }
        this.previous_object = [];
        this.create_new_object_btn.disabled = false;
        this.toggle_delete_object_btn.disabled = false;
        this.toggle_delete_all_objects_btn.disabled = false;
    }

    enable_show_order(){
        $(":checkbox").eq(0).prop('checked', true);
        $('#showOrderWrapper').addClass("active");
    }

    disable_show_order(){
        $(":checkbox").eq(0).prop('checked', false);
        $('#showOrderWrapper').removeClass("active");
    }

    temp_copy_objects(){
        this.temp_objects = [];
        for (var i in this.objects) {
            this.temp_objects[this.temp_objects.length] = [String(this.objects[i].polygon._latlngs[0]), this.objects[i].deleted, this.objects[i].order];
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
            if (this.objects[i].deleted != this.temp_objects[i][1]){
                return true;
            }
            if (this.objects[i].order != this.temp_objects[i][2]){
                return true;
            }
        }

        return false;
    }

    unselect_objects () {
        for (var i in this.objects) {
            this.objects[i].polygon.disableEdit();
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
        this.disable_set_order();
        this.unselect_objects();
        var order = 0;
        if (this.objects.length > 0){
            order = Number(this.objects[this.objects.length-1].order)+1;
        }
        var poly = this.map.editTools.startPolygon();
        this.objects.push(new LP_object(this, guid(), 0, 0, [], '', poly, order));
    }

    toggle_delete_object() {
        this.disable_set_order();
        let obj = this.get_selected();
        if (obj) {
            obj.deleted = !obj.deleted;
            obj.update_style();
        }
    }

    toggle_delete_all_objects() {
        this.disable_set_order();
        for (let obj of this.objects) {
            if (obj) {
                obj.deleted = !obj.deleted;
                obj.update_style();
            }
        }
    }

    reset_image(){
        if (this.set_reading_order_btn.checked){
            this.disable_set_order();
            this.set_reading_order();
        }
        this.change_image(this.uuid, false);
    }

    change_image(image_id, ask_for_change=true){
        if (ask_for_change){
            if (this.is_changed()){
                if (confirm("Save changes?"))
                {
                    this.save_image();
                }
            }
        }
        this.uuid = image_id;
        this.get_image(image_id);
        this.reload_layout_preview(image_id);
        this.last_action = null;
        if (ask_for_change){
            this.disable_set_order();
        }
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

    new_image_callback(data, status) {
        this.map_region.innerHTML = "<div id='mapid'></div>";
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

        this.map.fitBounds(bounds);

        for (var i in this.objects) {
            this.objects[i] = new LP_object(
                this,
                this.objects[i].uuid,
                this.objects[i].deleted, false,
                this.objects[i].points, '', null,
                this.objects[i].order);
        }
        this.get_default_order();
        this.objects.sort((a, b) => (a.order) - (b.order));
        for (var i in this.objects) {
            this.objects[i].order = i;
        }

        this.order_lines = [];
        if (this.objects.length > 1){
            for (let i = 0; i < (this.objects.length-1); i++) {
                this.order_lines.push(new PL_order(this.objects[i].centroid, this.objects[i+1].centroid, this.map));
            }
        }
        this.redraw_order();

        this.report_status('Got image: ' + data['uuid']);
        this.temp_copy_objects();
    }

    report_status(text) {
        var status_bar = document.getElementById('status');
        status_bar.innerHTML = text;
    }

    reload_layout_preview(uuid){
        try {
          document.querySelector('figure[data-image="'+ uuid +'"]').children[0].attributes['src'].nodeValue = Flask.url_for(
                'document.get_image_preview', {'image_id': uuid}) + '?a=' + String(Math.random()).substr(2);
        }
        catch(err) {
          document.querySelector('figure[data-image="'+ uuid +'"]').children[0].attributes['src'] = Flask.url_for(
                'document.get_image_preview', {'image_id': uuid}) + '?a=' + String(Math.random()).substr(2);
        }
    }

    save_image(){
        if (this.uuid) {
            var obj_to_send = [];
            for (var obj_key in this.objects) {
                var obj = this.objects[obj_key];
                if (obj.polygon._latlngs[0].length >= 3) {
                    var points = [];
                    for (var i in obj.polygon._latlngs[0]) {
                        points[i] = [obj.polygon._latlngs[0][i].lng, -obj.polygon._latlngs[0][i].lat];
                    }

                    obj_to_send[obj_key] = {
                        uuid: obj.uuid,
                        points: points,
                        ignore: obj.ignore,
                        deleted: obj.deleted,
                        order: obj.order
                    };
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
