/**
 Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

 Autor práce: David Hříbek
 Rok: 2021
 **/

import {v4 as uuidv4} from 'uuid';
import {makePolygonFromBaseline} from "./baseline_tool";


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
    let annotations = {regions: [], rows: []};
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
        // annotation.state = ''; // active/ignored/edited
        annotation.is_valid = true;
        annotation.annotated = false;
        annotation.edited = false;
        annotation.text = '';
    }

    // Emit event
    type = type === 'regions'? 'region': 'row';
    this.$emit(type+'-created-event', serializeAnnotation(annotation));

    return annotation;
}

/**
 * Get nearest path segment from point
 * @param path
 * @param point
 * @returns {null}
 */
function getNearestPathSegment(path, point) {
    // Find nearest segment on path
    let p_min = path.segments[0].point;
    let last_segm = null;
    let dist = 100;
    let p = path.getNearestPoint(point);

    // Find nearest path segment
    for (const s of path.segments) {
        let d = Math.sqrt(Math.pow(s.point.x - p.x, 2) + Math.pow(s.point.y - p.y, 2));
        if (d < dist) {
            last_segm = s;
            dist = d;
            p_min = s.point;
        }
    }
    return last_segm;
}

/**
 * Create annotation GUI view
 * this: annotator_component
 * @param annotation
 * @param type
 * @returns {{path: paper.Path, text: null, group: paper.Group}}
 */
export function createAnnotationView(annotation, type) {
    // Create new group with bbox and text
    let polygon = new paper.Path();
    let group = new paper.Group([polygon]);

    let text = null;
    let baseline = {};

    if (type === 'rows') { // Rows
        // Create baseline
        let baseline_left = annotation.baseline[0];
        let baseline_right = annotation.baseline[annotation.baseline.length - 1];
        let heights = annotation.heights;

        // Baseline path
        baseline.baseline_path = new paper.Path(annotation.baseline);
        baseline.baseline_path.strokeWidth = 2;
        baseline.baseline_path.strokeColor = 'rgba(34,43,68,0.1)';
        baseline.baseline_path.onMouseDown = (event) => {
            event.preventDefault();
            this.last_segm = getNearestPathSegment(baseline.baseline_path, event.point);
            this.last_baseline = baseline;
            this.last_segm_type = 'baseline_path';
        };

        // Left path
        baseline.baseline_left_path = new paper.Path([
            [baseline_left.x, baseline_left.y + heights.down],
            [baseline_left.x, baseline_left.y - heights.up]
        ]);
        baseline.baseline_left_path.strokeWidth = 2;
        baseline.baseline_left_path.strokeColor = 'rgba(34,43,68,0.1)';
        baseline.baseline_left_path.onMouseDown = (event) => {
            event.preventDefault();
            this.last_segm = getNearestPathSegment(baseline.baseline_left_path, event.point);
            this.last_baseline = baseline;
            this.last_segm_type = 'left_path';
        };

        // Right path
        baseline.baseline_right_path = new paper.Path([
            [baseline_right.x, baseline_right.y + heights.down],
            [baseline_right.x, baseline_right.y - heights.up]
        ]);
        baseline.baseline_right_path.strokeWidth = 2;
        baseline.baseline_right_path.strokeColor = 'rgba(34,43,68,0.1)';
        baseline.baseline_right_path.onMouseDown = (event) => {
            event.preventDefault();
            this.last_segm = getNearestPathSegment(baseline.baseline_right_path, event.point);
            this.last_baseline = baseline;
            this.last_segm_type = 'right_path';
        }

        group.addChild(baseline.baseline_path);
        group.addChild(baseline.baseline_left_path);
        group.addChild(baseline.baseline_right_path);

        // Make polygon
        polygon = makePolygonFromBaseline(
            baseline.baseline_path,
            new paper.Path([baseline.baseline_path.segments[0], baseline.baseline_left_path.segments[1]]),
            new paper.Path([baseline.baseline_path.segments[0], baseline.baseline_left_path.segments[0]])
        );
        baseline.baseline_path.insertAbove(polygon);
        baseline.baseline_left_path.insertAbove(polygon);
        baseline.baseline_right_path.insertAbove(polygon);

        // Create text
        text = new paper.PointText(polygon.firstSegment.point.add(new paper.Point(20, -20))); // TODO
        text.content = annotation.text ? annotation.text : '';
        text.opacity = 0;
        group.addChild(text);
    }
    else { // Regions
        // Create polygon
        polygon.closed = true;

        // Add points to path
        for (let point of annotation.points)
            polygon.add(new paper.Point(point));
    }

    // Color polygon
    polygon = setPathColor(polygon, type, annotation);

    polygon.onMouseDown = (e) => {
        e.preventDefault();

        // Find annotation and make it active
        if (type === 'regions')
            this.last_active_annotation = this.active_region = this.annotations.regions.find((item) => item.view.path === e.target);
        else if (type === 'rows')
            this.last_active_annotation = this.active_row = this.annotations.rows.find((item) => item.view.path === e.target);

        if (e.event.which === 3)
            this.activateContextMenu();
    }

    return {group: group, path: polygon, text: text, baseline: baseline};
}

/**
 * TODO
 * this: annotator_component
 * @param tmp_view
 * @param annotator_component
 */
export function confirmAnnotation(tmp_view, annotator_component) {
    let tmp_ann = {
        points: getPathPoints(tmp_view.path),
        is_valid: false,
        baseline: tmp_view.baseline? getPathPoints(tmp_view.baseline.baseline): [],
        heights: tmp_view.baseline? {down: tmp_view.baseline.down.length, up: tmp_view.baseline.up.length}: {}
    };

    let annotation_view = annotator_component.createAnnotationView(tmp_ann, annotator_component.creating_annotation_type);
    let active_region_uuid = annotator_component.active_region ? annotator_component.active_region.uuid : null;
    let annotation = annotator_component.createAnnotation(annotation_view, annotator_component.creating_annotation_type, active_region_uuid);

    // Push region to annotations
    annotator_component.annotations[annotator_component.creating_annotation_type].push(annotation);

    // Set this annotation to active
    if (annotator_component.creating_annotation_type === 'regions')
        annotator_component.active_region = annotation;
    else {
        annotator_component.active_row = annotation;
        annotator_component.active_row.is_valid = false;
    }

    // Remove tmp path
    if (tmp_view.path)
        tmp_view.path.remove();
    tmp_view.path = null;
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
            if (this.$refs.annotation_list_component)
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
        // Select row
        next.view.baseline.baseline_path.selected = true;
        next.view.baseline.baseline_left_path.selected = true;
        next.view.baseline.baseline_right_path.selected = true;

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
        prev.view.path = setPathColor(prev.view.path, 'row', prev);
        prev.view.baseline.baseline_path.selected = false;
        prev.view.baseline.baseline_left_path.selected = false;
        prev.view.baseline.baseline_right_path.selected = false;
    }
}
