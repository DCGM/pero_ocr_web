/**
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
**/

import {makePolygonFromBaseline} from './baseline_tool';
import {getPathPoints} from "./annotations";

/**
 * Create tool for scaling and moving over canvas
 * @param annotator_component
 * @returns {paper.Tool}
 */
export function createScaleMoveViewTool(annotator_component) {
    let tool = new paper.Tool();

    tool.onMouseDrag = (event) => {
        if (!annotator_component.left_control_active) {  // Move camera
            let offset = event.point.subtract(event.downPoint);
            annotator_component.scope.view.center = annotator_component.scope.view.center.subtract(offset);
        }
        else {  // Move baseline point
            if (annotator_component.last_segm) {
                annotator_component.mouse_drag = true;

                if (annotator_component.last_segm_type === 'left_path' || annotator_component.last_segm_type === 'right_path') { // Baseline left/right path
                    let path = annotator_component.last_segm_type === 'left_path'? annotator_component.last_baseline.baseline_left_path: annotator_component.last_baseline.baseline_right_path;  // Currently moving
                    let oposite_path = annotator_component.last_segm_type === 'left_path'? annotator_component.last_baseline.baseline_right_path: annotator_component.last_baseline.baseline_left_path;
                    let second_segm = annotator_component.last_segm === path.segments[0] ? path.segments[1] : path.segments[0];

                    if (Math.abs(event.delta.x) > Math.abs(event.delta.y)) { // Move both points
                        // Move baseline left/right path
                        annotator_component.last_segm.point = annotator_component.last_segm.point.add(event.delta);
                        second_segm.point = second_segm.point.add(event.delta);

                        // Move baseline left/right point
                        let idx = annotator_component.last_segm_type === 'left_path'? 0: annotator_component.last_baseline.baseline_path.segments.length - 1;
                        annotator_component.last_baseline.baseline_path.segments[idx].point = annotator_component.last_baseline.baseline_path.segments[idx].point.add(event.delta)
                    }
                    else { // Move one point vertically
                        let is_up_segm = annotator_component.last_segm.point.y > second_segm.point.y;
                        let oposite_segm = (oposite_path.segments[0].point.y > oposite_path.segments[1].point.y) === is_up_segm? oposite_path.segments[0]: oposite_path.segments[1];

                        oposite_segm.point = oposite_segm.point.add({x: 0, y: event.delta.y});
                        annotator_component.last_segm.point = annotator_component.last_segm.point.add({x: 0, y: event.delta.y});
                    }
                }
                else { // Baseline/region path
                    // Move baseline/region point
                    annotator_component.last_segm.point = annotator_component.last_segm.point.add(event.delta);

                    // Move baseline left/right path (if moving first or last baseline point)
                    if (annotator_component.last_segm_type === 'baseline_path') {
                        let p = null;
                        if (annotator_component.last_segm === annotator_component.last_baseline.baseline_path.firstSegment)
                            p = annotator_component.last_baseline.baseline_left_path;
                        else if (annotator_component.last_segm === annotator_component.last_baseline.baseline_path.lastSegment)
                            p = annotator_component.last_baseline.baseline_right_path;

                        if (p) {
                            p.firstSegment.point = p.firstSegment.point.add(event.delta);
                            p.lastSegment.point = p.lastSegment.point.add(event.delta);
                        }
                    }
                }

                if (annotator_component.last_segm_type !== 'region_path') {
                    // Make polygon
                    let left_baseline_point = _.pick(annotator_component.last_baseline.baseline_path.firstSegment.point, ['x', 'y']);
                    let up_point = _.pick(annotator_component.last_baseline.baseline_left_path.lastSegment.point, ['x', 'y']);
                    let down_point = _.pick(annotator_component.last_baseline.baseline_left_path.firstSegment.point, ['x', 'y']);

                    let up_height = pointDistance(left_baseline_point, up_point);
                    let down_height = pointDistance(left_baseline_point, down_point);
                    let polygon = makePolygonFromBaseline(getPathPoints(annotator_component.last_baseline.baseline_path), up_height, down_height);
                    annotator_component.active_row.view.path.clear();
                    annotator_component.active_row.view.path.segments = polygon.segments;
                    polygon.remove();
                }
            }
        }
    };

    return tool;
}

/**
 * Compute point distance
 * @param p1 {{x: float, y:float}}
 * @param p2 {{x: float, y:float}}
 * @returns {number}
 */
function pointDistance(p1, p2) {
    let dx = p1.x - p2.x;
    let dy = p1.y - p2.y;
    return Math.sqrt(dx*dx + dy*dy);
}

/**
 * Event: Wheel mouse on canvas
 * this: annotator_component
 * @param event
 */
export function canvasMouseWheelEv(event) {
    // Cast kodu funkce byla inspirovana ukazkou: https://codepen.io/hichem147/pen/dExxNK
    event.preventDefault();

    // Scale_move tool need to be activated
    if (this.scope.tool !== this.scale_move_tool)
        return;

    if (!this.left_control_active) {
        // Zooming
        let speed = 0.05;
        let oldZoom = this.scope.view.zoom;
        let newZoom = this.scope.view.zoom * (1 + ((event.deltaY < 0) ? speed : -speed));
        this.scope.view.zoom = newZoom;

        // Move view center toward mouse position (zoom to mouse position)
        let canvasMousePosition = new paper.Point(event.offsetX, event.offsetY);
        //viewToProject: gives the coordinates in the Project space from the Screen Coordinates
        let viewPosition = this.scope.view.viewToProject(canvasMousePosition);
        let viewCenter = this.scope.view.center;
        let pc = viewPosition.subtract(viewCenter);
        let ratio = oldZoom / newZoom;
        let offset = viewPosition.subtract(pc.multiply(ratio)).subtract(viewCenter);

        this.scope.view.center = this.scope.view.center.add(offset);
    }
}

/**
 * Event: Move mouse over canvas
 * this: annotator_component
 * @param event
 */
export function canvasMouseMoveEv(event) {
}

/**
 * Event: Mouse down on canvas
 * this: annotator_component
 * @param event
 */
export function canvasMouseDownEv(event) {
    this.deactivateContextMenu();

    //
    if (!this.active_region && !this.active_row)
        return;

    //
    let canvasMousePosition = new paper.Point(event.offsetX, event.offsetY);
    let viewPosition = this.scope.view.viewToProject(canvasMousePosition);

    let checks = []
    if (this.active_region)
        checks.push({path: this.active_region.view.path, segm_type: 'region_path'});
    if (this.active_row) {
        checks.push({path: this.active_row.view.baseline.baseline_path, segm_type: 'baseline_path', baseline: this.active_row.view.baseline});
        checks.push({path: this.active_row.view.baseline.baseline_left_path, segm_type: 'left_path', baseline: this.active_row.view.baseline});
        checks.push({path: this.active_row.view.baseline.baseline_right_path, segm_type: 'right_path', baseline: this.active_row.view.baseline});
    }

    //
    let min_dist = 2000;
    for (let check of checks) {
        for (let segment of check.path.segments) {
            let dist = pointDistance(viewPosition, segment.point);
            if (dist < min_dist) {
                min_dist = dist;
                this.last_baseline = check.baseline;
                this.last_segm = segment;
                this.last_segm_type = check.segm_type;
            }
        }
    }
}

/**
 * Event: Mouse up on canvas
 * this: annotator_component
 * @param event
 */
export function canvasMouseUpEv(event) {
    // Finish editing annotation
    if (this.mouse_drag) {
        this.mouse_drag = false;
        this.last_segm = null;
        this.last_baseline = null;
        this.last_segm_type = null;
        this.emitAnnotationEditedEvent(this.last_active_annotation);
    }
}


/**
 * Event: Mouse double click on canvas
 * this: annotator_component
 * @param event
 */
export function canvasMouseDblClickEv(event) {
    this.deactivateContextMenu();

    if (this.active_row && this.event_mouse_drag === false) {
        this.emitAnnotationEditedEvent(this.active_row);
        this.active_row = null;
        this.active_region = null;
    }
}
