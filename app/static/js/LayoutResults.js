var loaded_json = "";

annotator_data = {
    uuid: '', past_uuid: [], future_uuid: [],
    unselect_objects: function () {
        for (var i in this.objects) {
            this.objects[i].polygon.disableEdit()
        }
    },
    get_selected: function () {
        for (var i in this.objects) {
            if (this.objects[i].polygon.editEnabled()) {
                return this.objects[i];
            }
        }
        return null;
    },
    history: [],
    future: [],
    selected_id: 0
};

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

dispatchForKeyCode = function (event, callback) {
    var code;
    if (event.key !== undefined) {
        code = event.key;
    } else if (event.keyIdentifier !== undefined) {
        code = event.keyIdentifier;
    } else if (event.keyCode !== undefined) {
        code = event.keyCode;
    }
    callback(code);
};

function report_status(text) {
    var status_bar = document.getElementById('status');
    status_bar.innerHTML = text;
}

function create_new_object() {
    annotator_data.unselect_objects();
    var poly = annotator_data.map.editTools.startPolygon()
    annotator_data.objects.push(new LP_object(guid(), 0, 0, [], '', poly));
}

function toggle_delete_object() {
    obj = annotator_data.get_selected();
    if (obj) {
        obj.deleted = !obj.deleted;
        obj.update_style();
    }
}

function toggle_ignore_object() {
    obj = annotator_data.get_selected();
    if (obj) {
        obj.ignore = !obj.ignore;
        obj.update_style();
    }
}

function editor_keypress(e) {
    // g - not deleted
    // h - not ignored
    // o - reset original object annotation

    // n - save and next forward
    // x - discard and next forward
    // b - backward
    // s - save

    // r - previous annotated??
    // t - next annotated
    var k = e.key = e.key.toLowerCase()
    if (k == "r") {
        get_image(annotator_data.uuid)
    } else if (k == "c") {
        create_new_object();
    } else if (k == 'g') {
        toggle_delete_object();
    } else if (k == 's') {
        save_image();
    } else if(k == 'n') {
        save_image();
        next_image();
    } else if(k == 'b'){
        save_image();
        previous_image();
    }
}

function save_image() {
    if (annotator_data.uuid) {
        var obj_to_send = [];
        for (var obj_key in annotator_data.objects) {
            var obj = annotator_data.objects[obj_key]
            if (obj.polygon._latlngs[0].length > 3) {
                var points = []
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
        var imageId = annotator_data.uuid;
        $.ajax("/layout_analysis/edit_layout/" + imageId, {
            data: data,
            contentType: 'application/json', type: 'POST'
        }).done(function () {
            let $image = $(`.image-item-container[data-image="${imageId}"]`).find('img');
            let src = $image.attr('src') + "?" + new Date().getTime();
            $image.attr('src', src);
        })
    }
}

class LP_object {
    constructor(uuid, deleted, ignore, points, text, polygon) {
        var myself = this;
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
        this.polygon.addTo(annotator_data.map);
        this.polygon.on('click', function () {
            myself.obj_click()
        });
        this.update_style();
    }

    obj_click() {
        if (this.deleted || this.ignore) {
            this.deleted = 0;
            this.ignore = 0;
            this.update_style();
        }
        annotator_data.unselect_objects();
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

function next_image() {
    if (annotator_data.uuid) {
        var index = imagesId.indexOf(annotator_data.uuid);
        if(index < imagesId.length - 1){
            $(`.image-item-container[data-image="${imagesId[index + 1]}"]`).trigger('click');
        }
    }
}

function previous_image() {
    if (annotator_data.uuid) {
        var index = imagesId.indexOf(annotator_data.uuid);
        if(index > 0){
            $(`.image-item-container[data-image="${imagesId[index - 1]}"]`).trigger('click');
        }
    }
}

function new_image_callback(data, status) {
    var map_region = document.getElementById('map-container');
    map_region.innerHTML = "<div id='mapid'></div>";
    annotator_data.uuid = data['uuid'];
    annotator_data.width = data['width'];
    annotator_data.height = data['height'];
    annotator_data.objects = data['objects'];

    annotator_data.map = L.map('mapid', {
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

    var bounds = [xy(0, -annotator_data.height), xy(annotator_data.width, 0)];
    annotator_data.map.setView(xy(annotator_data.width / 2, -annotator_data.height / 2), -2);
    var image = L.imageOverlay(`/document/get_image/${document_id}/${annotator_data.uuid}`, bounds).addTo(annotator_data.map);

    //zoom_level = Math.log(annotator_data.width / 256.0) / Math.log(2)
    annotator_data.map.fitBounds(bounds);

    for (var i in annotator_data.objects) {
        annotator_data.objects[i] = new LP_object(
            annotator_data.objects[i].uuid,
            annotator_data.objects[i].deleted, false,
            annotator_data.objects[i].points, '');
    }

    report_status('Got image: ' + data['uuid'])
}

function get_image(image_uuid) {
    annotator_data.uuid = null;
    annotator_data.objects = null;
    try {
        if(annotator_data.map){
            annotator_data.map.remove();
            annotator_data.map = null;
        }
    } catch (e) {
        console.log(e);
    }

    var url = `/layout_analysis/get_image_result/${document_id}/${image_uuid}`;

    $.get(url, report_status('FAILED: Did not get next image.'),
        new_image_callback);
}

function get_map_zoom() {
    console.log(map.getZoom());
}

function load_image() {
    var d = 100;
    for (x = 0; x < 1655; x += d * 1.5) {
        for (y = 0; y < 2340; y += d * 1.5) {
            var poly = L.polygon([
                [
                    xy(x, y),
                    xy(x + d, y),
                    xy(x + d, y + d),
                    xy(x, y + d),
                ]
            ]).addTo(map);
            poly.enableenableEdit();
        }
    }
}

function resize2x() {
    for (var obj_key in annotator_data.objects) {
        var obj = annotator_data.objects[obj_key]
        for (var i in obj.polygon._latlngs[0]) {
            obj.polygon._latlngs[0][i].lng *= 2;
            obj.polygon._latlngs[0][i].lat *= 2;
        }
        obj.polygon.redraw();
    }
}

function fix_ar() {
    for (var obj_key in annotator_data.objects) {
        var obj = annotator_data.objects[obj_key]
        for (var i in obj.polygon._latlngs[0]) {
            obj.polygon._latlngs[0][i].lat /= 2;
        }
        obj.polygon.redraw();
    }
}

get_image(first_image)

$('.image-item-container').on('click', function (event) {
    let old_image_id = $('.current-result-container').data('image');
    let document_id = $(this).data('document');
    let image_id = $(this).data('image');

    if (old_image_id !== image_id) {
        $('.current-result-container').data('document', document_id);
        $('.current-result-container').data('image', image_id);
        get_image(image_id);
        $('.image-item-active').addClass('d-none');
        $(`[data-image="${image_id}"] .image-item-active`).removeClass('d-none')
    }
});

let $image_containers = $('.image-item-container');
if ($image_containers.length) {
    let $image_container = $($image_containers[0]);
    $image_container.find('.image-item-active').removeClass('d-none');
}
