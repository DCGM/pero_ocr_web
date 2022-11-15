/**
 Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

 Autor práce: David Hříbek
 Rok: 2021
 **/

import {v4 as uuidv4} from 'uuid';
import {makePolygonFromBaseline} from "./baseline_tool";


/**
 * Emit edit event
 * this: annotator_component
 * @param annotation_type
 * @param annotation
 */
export function emitAnnotationEditedEvent(annotation) {
    let annotation_type = annotation.hasOwnProperty('text')? 'row': 'region';
    annotation.view.path = this.setPathColor(annotation.view.path, annotation_type, annotation);
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
 * Validate row annotation (mark annotated, change polygon color)
 * this: annotator_component
 * @param uuid - row uuid
 */
export function validateRowAnnotation(uuid) {
    let row = this.annotations.rows.find((item) => item.uuid === uuid);
    if (row) {
        row.annotated = true;
        row.is_valid = true;
        console.log(row);
        row.view.path = this.setPathColor(row.view.path, 'row', row);
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
    // Serialize view
    copy.points = getPathPoints(copy.view.path);
    if (annotation.hasOwnProperty('text')) {  // Row annotation
        copy.baseline = getPathPoints(copy.view.baseline.baseline_path);
        copy.heights = [
            copy.view.baseline.baseline_left_path.segments[1].point.subtract(copy.view.baseline.baseline_path.segments[0].point).length,
            copy.view.baseline.baseline_left_path.segments[0].point.subtract(copy.view.baseline.baseline_path.segments[0].point).length
        ];
    }
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
 * @param prompt
 */
export function removeAnnotation(uuid, prompt=false) {
    // Delete region
    let region_idx = this.annotations.regions.findIndex((item) => item.uuid === uuid);
    if (region_idx !== -1) {
        // Confirm removing
        if (prompt) {
            let num_child_rows = this.annotations.rows.filter(item => item.region_annotation_uuid === uuid).length;
            if (!confirm('Opravdu smazat odstavec i s řádky ('+ num_child_rows +')'))
                return
        }

        // Emit event
        this.$emit('region-deleted-event', serializeAnnotation(this.annotations.regions[region_idx]));

        // Disable active region
        if (this.annotations.regions[region_idx] === this.active_region)
            this.active_region = null;

        this.annotations.regions[region_idx].view.path.remove();
        this.annotations.regions[region_idx].view.group.remove();

        // Unregister region
        this.annotations.regions.splice(region_idx, 1)

        // Delete region rows
        let row;
        while (row = this.annotations.rows.find((item) => item.region_annotation_uuid === uuid)) {
            this.removeAnnotation(row.uuid);
        }
        return;
    }

    // Delete row
    let row_idx = this.annotations.rows.findIndex((item) => item.uuid === uuid);
    if (row_idx !== -1) {
        // Confirm removing
        if (prompt) {
            if (!confirm('Opravdu smazat řádek?'))
                return
        }

        // Emit event
        this.$emit('row-deleted-event', serializeAnnotation(this.annotations.rows[row_idx]));

        // Disable active row
        if (this.annotations.rows[row_idx] === this.active_row)
            this.active_row = null;

        // Remove view items
        let ann_view = this.annotations.rows[row_idx].view;
        if (ann_view.baseline) {
            ann_view.baseline.baseline_path.remove();
            ann_view.baseline.baseline_left_path.remove();
            ann_view.baseline.baseline_right_path.remove();
        }
        ann_view.path.remove();
        ann_view.group.remove();

        // Check if parent region has no rows => delete entire region
        let parent_region_uuid = this.annotations.rows[row_idx].region_annotation_uuid;
        if (parent_region_uuid) {
            /** Delete parent region **/
            let rows = this.annotations.rows.filter(item => item.region_annotation_uuid === parent_region_uuid);
            if (rows.length === 0)
                this.removeAnnotation(parent_region_uuid);
        }

        // Unregister row
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
 * this: annotator_component
 * @param path
 * @param annotation_type
 * @param annotation
 */
export function setPathColor(path, annotation_type, annotation) {
    if (annotation_type === 'row' || annotation_type === 'rows') {

        let is_focused = (this.active_row && annotation.uuid === this.active_row.uuid);

        let conf = (annotation.confidence - this.worst_confidence) / (1 - this.worst_confidence);

        let fill_opacity = 0.1;
        let stroke_opacity = 0.5;
        let stroke_width = 2.5;
        if (is_focused) {
            fill_opacity = 0.15;
            stroke_opacity = 1;
            stroke_width = 3;
        }
        let fill_color = `rgba(${(1 - conf) * 255}, ${16}, ${conf * 255}, ${fill_opacity})`;
        let stroke_color = `rgba(${(1 - conf) * 255}, ${16}, ${conf * 255}, ${stroke_opacity})`;
        if (!annotation.is_valid) {
            fill_color = `rgba(16, 16, 16, ${fill_opacity})`;
            stroke_color = `rgba(16, 16, 16, ${stroke_opacity})`;
        } else if (annotation.edited) {
            fill_color = `rgba(255, 204, 84, ${fill_opacity})`;
            stroke_color = `rgba(255, 204, 84, ${stroke_opacity})`;
        } else if (annotation.annotated) {
            fill_color = `rgba(2, 135, 0, ${fill_opacity})`;
            stroke_color = `rgba(2, 135, 0, ${stroke_opacity})`;
        }

        path.strokeScaling = false;
        path.fillColor = fill_color;
        path.strokeColor = stroke_color;
        path.strokeWidth = stroke_width;

    }
    else { // Region
        path.strokeWidth = 2;
        path.fillColor = 'rgba(0,0,0,0.01)';

        // Stroke
        if (this.active_region && annotation.uuid === this.active_region.uuid) {  // Active
            path.strokeColor = 'rgba(231,160,8,0.8)';
        }
        else {  // In-active
            path.strokeColor = 'rgba(34,43,68,0.8)';
        }
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
    let dist = 50;
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
 * @returns {{path: paper.Path, baseline: {}, group: paper.Group}}
 */
export function createAnnotationView(annotation, type) {
    // Create new group
    let group = new paper.Group();
    let polygon = new paper.Path();

    let baseline = {};

    if (type === 'rows') { // Rows
        let heights = annotation.heights;

        /** Make polygon **/
        polygon = makePolygonFromBaseline(annotation.baseline, heights.up, heights.down);
        group.addChild(polygon);

        /** Make baseline **/
        let baseline_left = annotation.baseline[0];
        let baseline_right = annotation.baseline[annotation.baseline.length - 1];

        // Left path
        baseline.baseline_left_path = new paper.Path([
            [baseline_left.x, baseline_left.y + heights.down],
            [baseline_left.x, baseline_left.y - heights.up]
        ]);

        // Right path
        baseline.baseline_right_path = new paper.Path([
            [baseline_right.x, baseline_right.y + heights.down],
            [baseline_right.x, baseline_right.y - heights.up]
        ]);

        // Baseline path
        baseline.baseline_path = new paper.Path(annotation.baseline);

        group.addChild(baseline.baseline_path);
        group.addChild(baseline.baseline_left_path);
        group.addChild(baseline.baseline_right_path);
    }
    else { // Regions
        // Create polygon
        polygon.closed = true;

        // Add points to path
        for (let point of annotation.points)
            polygon.add(new paper.Point(point));

        group.addChild(baseline.baseline_path);
    }

    // Color polygon
    polygon = this.setPathColor(polygon, type, annotation);

    polygon.onMouseUp = (e) => {
        e.preventDefault();

        // Find annotation and make it active
        if (!this.camera_move && (this.canvasIsToolActive(this.scale_move_tool) || this.canvasIsToolActive(this.join_rows_tool)) && !this.left_control_active && !this.left_alt_active)
            activateAnnotation(type);
    }

    let self = this;
    function activateAnnotation(type) {
        if (type === 'regions')
            self.last_active_annotation = self.active_region = self.annotations.regions.find((item) => item.view.path === polygon);
        else if (type === 'rows')
            self.last_active_annotation = self.active_row = self.annotations.rows.find((item) => item.view.path === polygon);

    }

    return {group: group, path: polygon, baseline: baseline};
}

/**
 * Create and register new row/region
 * this: annotator_component
 * @param tmp_view
 * @param annotator_component
 */
export function confirmAnnotation(polygon=null, baseline=null) {
    let annotation_data = {
        points: polygon? getPathPoints(polygon.path): null,
        is_valid: false,
        baseline: baseline? getPathPoints(baseline.baseline): null,
        heights: baseline? {down: baseline.down.length, up: baseline.up.length}: null
    };

    let annotation_view = this.createAnnotationView(annotation_data, this.creating_annotation_type);
    let active_region_uuid = this.active_region ? this.active_region.uuid : null;
    let annotation = this.createAnnotation(annotation_view, this.creating_annotation_type, active_region_uuid);

    // Push region to annotations
    this.annotations[this.creating_annotation_type].push(annotation);

    // Set this annotation to active
    if (this.creating_annotation_type === 'regions')
        this.active_region = annotation;
    else {
        this.active_row = annotation;
        this.active_row.is_valid = false;
    }

    return annotation;
}

export function activeRegionChangedHandler(next, prev) {
    // Active row
    if (!(this.active_row && this.active_region && this.active_row.region_annotation_uuid === this.active_region.uuid))
        this.active_row = null;

    if (next) {
        // Open region rows
        this.$nextTick(() => {
            let region_idx = this.annotations.regions.findIndex((item) => item === next);

            // Click on region in Annotation_list_component
            if (this.$refs.annotation_list_component)
                this.$refs.annotation_list_component.clickRegion(region_idx);
        });

        next.view.path = this.setPathColor(next.view.path, 'region', next);

        // Emit event
        this.$emit('region-selected-event', serializeAnnotation(next))
    }

    if (prev) {
        prev.view.path = this.setPathColor(prev.view.path, 'region', prev);
    }
}

export function activeRowChangedHandler(next, prev) {
    if (next) {

        // Notify join rows tool
        if (this.canvasIsToolActive(this.join_rows_tool))
            this.join_rows_tool.row_selected(next);

        this.$nextTick(() => {
            //
            let parent_region = this.annotations.regions.find((item) => item.uuid === next.region_annotation_uuid)
            this.active_region = parent_region? parent_region: null;

            // this.$refs['input-transcription-text'].focus(); // Disabled (shadowing focus on scrol text)
        });

        next.view.path = this.setPathColor(next.view.path, 'row', next);

        // Emit event
        this.$emit('row-selected-event', serializeAnnotation(next))
    }
    if (prev) {
        prev.view.path = this.setPathColor(prev.view.path, 'row', prev);
    }
}
