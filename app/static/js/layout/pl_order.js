
class PL_order {
    constructor(first_centroid, second_centroid, map) {
        this.map = map;
        this.pointList = [first_centroid, second_centroid];

        this.polyline = new L.Polyline(this.pointList, {
            color: 'red',
            weight: 3,
            opacity: 0.8,
            smoothFactor: 1
        });
        this.polyline.addTo(this.map);
    }

    refresh_line(first_centroid, second_centroid){
        this.pointList = [first_centroid, second_centroid];
        this.map.removeLayer(this.polyline);

        this.polyline = new L.Polyline(this.pointList, {
            color: 'red',
            weight: 3,
            opacity: 1,
            smoothFactor: 1
        });
        this.polyline.addTo(this.map);
    }

    remove_line(){
        this.map.removeLayer(this.polyline);
    }
}
