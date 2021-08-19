/**
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
**/

import {v4 as uuidv4} from 'uuid';


/**
 * Emit edit event
 * @param annotation_type
 * @param annotation
 */
export function emitAnnotationEditedEvent(annotation) {
    let annotation_type = annotation.hasOwnProperty('text')? 'row': 'region';
    annotation.view.path = setPathColor(annotation.view.path, annotation_type, annotation);
    this.$emit(annotation_type+'-edited-event', this.serializeAnnotation(annotation));
}

/**
 * Load annotations (regions/rows) into canvas
 * this: annotator_component
 * @param annotations - list of regions/rows objects
 */
export function loadAnnotations(annotations) {
    for (let annotation of annotations) {
        let type = annotation.hasOwnProperty('order')? 'rows': 'regions';
        annotation.view = this.createAnnotationView(annotation, type);
        this.annotations[type].push(annotation);
    }
}

/**
 * Get all annotation from canvas
 * @returns - {regions:[], rows:[]}
 */
export function getAnnotations() {
    let annotations = {regions:[], rows:[]};
    for (let type of ['regions', 'rows'])
        for (let annotation of this.annotations[type])
            annotations[type].push(serializeAnnotation(annotation));
    console.log(annotations);
    return annotations;
}

/**
 * Serialize annotation (gets points from view, remove view...)
 * @param annotation
 * @returns serialized region/row object
 */
export function serializeAnnotation(annotation) {
    let copy = Object.assign({}, annotation);
    copy.points = getPathPoints(copy.view.path);
    if (annotation.hasOwnProperty('text'))
        copy.text = copy.view.text.content;
    delete copy.view;
    return copy;
}

/**
 * Get points from path
 * @param path
 * @returns [{x,y}]
 */
export function getPathPoints(path) {
    return path.getSegments().map((item) => _.pick(item.point, ['x', 'y']));
}

/**
 * Remove annotation from canvas by UUID
 * this: annotator_component
 * @param uuid - annotation uuid
 */
export function removeAnnotation(uuid) {
    // Delete regions
    let region_idx = this.annotations.regions.findIndex((item) => item.uuid === uuid);
    if (region_idx !== -1) {
        // Emit event
        this.$emit('region-deleted-event', serializeAnnotation(this.annotations.regions[region_idx]));

        // Disable active region
        if (this.annotations.regions[region_idx] === this.active_region)
            this.active_region = null;

        this.annotations.regions[region_idx].view.group.remove();
        this.annotations.regions.splice(region_idx, 1)

        // Delete region rows
        let row_idx;
        while ((row_idx = this.annotations.rows.findIndex((item) => item.region_annotation_uuid === uuid)) !== -1) {
            // Emit event
            this.$emit('row-deleted-event', serializeAnnotation(this.annotations.rows[row_idx]));

            // Disable active row
            if (this.annotations.rows[row_idx] === this.active_row)
                this.active_row = null;

            this.annotations.rows[row_idx].view.group.remove();
            this.annotations.rows.splice(row_idx, 1);
        }
    }

    // Delete rows
    let row_idx = this.annotations.rows.findIndex((item) => item.uuid === uuid);
    if (row_idx !== -1) {
        // Check if parent region has only one row => delete entire region
        let parent_region_uuid = this.annotations.rows[row_idx].region_annotation_uuid;
        if (parent_region_uuid) {
            /** Delete region **/
            let rows = this.annotations.rows.filter(item => item.region_annotation_uuid === parent_region_uuid);
            if (rows.length === 1)
                this.removeAnnotation(parent_region_uuid);
        }

        row_idx = this.annotations.rows.findIndex((item) => item.uuid === uuid);
        // Emit event
        this.$emit('row-deleted-event', serializeAnnotation(this.annotations.rows[row_idx]));

        // Disable active row
        if (this.annotations.rows[row_idx] === this.active_row)
            this.active_row = null;

        this.annotations.rows[row_idx].view.group.remove();
        this.annotations.rows.splice(row_idx, 1);
    }
}

export function removeAnnotationSegm() {
    if (this.last_segm) {
        this.last_segm.remove();
        this.last_segm = null;
        this.emitAnnotationEditedEvent(this.last_active_annotation);
    }
}

/**
 * Set path's color
 * @param path
 * @param annotation_type
 * @param annotation
 */
function setPathColor(path, annotation_type, annotation) {
    if (annotation_type === 'row' || annotation_type === 'rows') {
        path.strokeWidth = 2;
        path.strokeColor = 'rgba(34,43,68,0.8)';
        // path.strokeColor = 'rgb(162,160,146)';
        // path.fillColor = 'rgba(219,200,28, 0.1)';

        // Set background color
        let worst_confidence = 0.394;
        let conf = (annotation.confidence - worst_confidence) / (1 - worst_confidence);
        let color = `rgba(${(1 - conf) * 255}, ${16}, ${conf * 255}, 0.1)`;

        if (!annotation.is_valid)
            color = 'rgba(16, 16, 16, 0.1)';
        else if (annotation.edited)
            color = 'rgba(255,204,84,0.1)'
        else if (annotation.annotated)
            color = "rgba(2,135,0,0.1)";

        path.fillColor = color;

        // OLD
        // if (line.focus)
        //     line.polygon.setStyle({color: color, opacity: 1, fillColor: color, fillOpacity: 0.15, weight: 2});
        // else
        //     line.polygon.setStyle({color: color, opacity: 0.5, fillColor: color, fillOpacity: 0.1, weight: 1});

    }
    else { // Region
        path.strokeWidth = 3;
        path.strokeColor = 'rgba(34,43,68, 0.9)';
        // path.fillColor = 'rgba(34,43,68,1)';
        // path.fillColor = 'rgba(34,43,68,0.2)';
    }
    return path;
}

/**
 * Create new annotation
 * this: annotator_component
 * @param view
 * @param type
 * @param parent_region_uuid
 * @returns {{view: *, uuid: *, points: []}}
 */
export function createAnnotation(view, type, parent_region_uuid = null) {
    let annotation = {
        uuid: uuidv4(),
        points: [],
        view: view
    };

    if (type === 'regions') {
        annotation.order = 0;
        annotation.is_deleted = false;
    } else if (type === 'rows') {
        annotation.region_annotation_uuid = parent_region_uuid; // Parent region
        annotation.state = ''; // active/ignored/edited
        annotation.is_valid = false;
        annotation.text = '';
    }
    // console.log(annotation)

    // Emit event
    type = type === 'regions'? 'region': 'row';
    this.$emit(type+'-created-event', serializeAnnotation(annotation));

    return annotation;
}

/**
 * Create annotation GUI view
 * this: annotator_component
 * @param annotation
 * @param type
 * @returns {{path: paper.Path, text: null, group: paper.Group}}
 */
export function createAnnotationView(annotation, type) {
    //
    let path = new paper.Path();
    path.closed = true;

    // Color path
    path = setPathColor(path, type, annotation);

    // Add points to path
    for (let point of annotation.points)
        path.add(new paper.Point(point));

    path.onMouseDown = (e) => {
        e.preventDefault();

        // Find nearest segment on path
        let p_min = path.segments[0].point;
        this.last_segm = null;
        let dist = 50;
        let p = path.getNearestPoint(e.point);

        // Find nearest path segment
        for (const s of path.segments) {
            let d = Math.sqrt(Math.pow(s.point.x - p.x, 2) + Math.pow(s.point.y - p.y, 2));
            if (d < dist) {
                this.last_segm = s;
                dist = d;
                p_min = s.point;
            }
        }

        // Find annotation and make it active
        if (type === 'regions')
            this.last_active_annotation = this.active_region = this.annotations.regions.find((item) => item.view.path === e.target);
        else if (type === 'rows')
            this.last_active_annotation = this.active_row = this.annotations.rows.find((item) => item.view.path === e.target);

        if (e.event.which === 3)
            this.activateContextMenu();
    }

    // Create new group with bbox and text
    let group = new paper.Group([path]);

    let text = null;
    if (type === 'rows') {
        // Create text
        text = new paper.PointText(path.firstSegment.point.add(new paper.Point(20, -20))); // TODO
        text.content = annotation.text_content? annotation.text_content: '';
        text.opacity = 0;
        group.addChild(text);
    }

    return {group: group, path: path, text: text};
}

export function activeRegionChangedHandler(next, prev) {
    // Active row
    if (!(this.active_row && this.active_region && this.active_row.region_annotation_uuid === this.active_region.uuid))
        this.active_row = null;

    if (next) {
        next.view.path.selected = true;

        // Open region rows
        this.$nextTick(() => {
            let region_idx = this.annotations.regions.findIndex((item) => item === next);

            // Click on region in Annotation_list_component
            this.$refs.annotation_list_component.clickRegion(region_idx);
        });

        // Emit event
        this.$emit('region-selected-event', serializeAnnotation(next))
    }

    if (prev) {
        prev.view.path.selected = false;
    }
}

export function activeRowChangedHandler(next, prev) {
    if (next) {
        next.view.path.selected = true;

        // Notify join rows tool
        if (this.canvasIsToolActive(this.join_rows_tool))
            this.join_rows_tool.row_selected(next);

        this.$nextTick(() => {
            //
            let parent_region = this.annotations.regions.find((item) => item.uuid === next.region_annotation_uuid)
            this.active_region = parent_region? parent_region: null;

            this.$refs['input-transcription-text'].focus();
        });

        // Emit event
        this.$emit('row-selected-event', serializeAnnotation(next))
    }
    if (prev) {
        prev.view.path.selected = false;
        prev.view.path = setPathColor(prev.view.path, 'row', prev);
    }
}
