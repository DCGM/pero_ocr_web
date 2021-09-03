/**
 * Autor práce: David Hříbek
 * Rok: 2021
**/


import {getPathPoints} from "./annotations";

/**
 * Create polygon based on baseline
 * @returns {paper.Path}
 * @param baseline_points {[{x:int, y:int}]}
 * @param up_height {float}
 * @param down_height {float}
 */
export function makePolygonFromBaseline(baseline_points, up_height, down_height) {
    let polygon = new paper.Path();
    polygon.closed = true;

    polygon.strokeWidth = 2;
    polygon.strokeColor = 'rgba(34,43,68,0.8)';

    let up_seg, down_seg;
    for (let i=0; i < baseline_points.length; i++) {
        up_seg = new paper.Point(baseline_points[i].x, baseline_points[i].y - up_height);
        down_seg = new paper.Point(baseline_points[i].x, baseline_points[i].y + down_height);

        polygon.insert(i, up_seg);
        polygon.insert(i+1, down_seg);
    }

    return polygon;
}

export function createBaselineTool(annotator_component) {
    let tool = new paper.Tool();

    // Create tmp variables
    let baseline = null;
    let up = null;
    let down = null;
    let polygon = null;

    tool.onKeyDown = (event) => {
        if (event.key === "escape") {
            // Remove currently created annotation
            for (let item of [baseline, up, down, polygon]) {
                if (item)
                    item.remove();
            }
            baseline = up = down = polygon = null;
        }
    }

    tool.onMouseDown = (event) => {
        event.preventDefault();

        if (event.event.which !== 1) { // Right click
            if (baseline.segments.length >= 2) {
                if (!up) { // Baseline -> Up
                    baseline.selected = false;
                    up = new paper.Path([baseline.lastSegment, baseline.lastSegment]);
                    up.selected = true;
                }
            }
        }
        else { // Left click
            if (!baseline) { // Baseline create
                baseline = new paper.Path();
                baseline.strokeColor = 'rgb(34 43 68)';
                baseline.strokeWidth = 2;
                baseline.selected = true;
            }

            if (!up && !down) { // Baseline add point
                let canvasMousePosition = new paper.Point(event.event.offsetX, event.event.offsetY);
                let viewPosition = annotator_component.scope.view.viewToProject(canvasMousePosition);
                baseline.add(new paper.Point(viewPosition));
            }

            if (up && !down) { // Up -> Down
                up.selected = false;
                down = new paper.Path([baseline.lastSegment, baseline.lastSegment]);
                down.selected = true;
            }
            else if (down) { // Down -> Finish
                down.selected = false;
                //
                annotator_component.confirmAnnotation(null, {baseline: baseline, up: up, down: down});

                // Remove tmps
                up.remove();
                down.remove();
                baseline.remove();
                polygon.remove();
                up = down = baseline = polygon = false;
            }
        }
    }

    tool.onMouseMove = (event) => {
        let direction = down? down: up;

        if (direction) {
            // Move last point
            let pp = annotator_component.scope.view.projectToView(baseline.lastSegment.point);
            let canvasMousePosition = new paper.Point(pp.x, event.event.offsetY);
            let viewPosition = annotator_component.scope.view.viewToProject(canvasMousePosition);
            let point = new paper.Point(viewPosition);

            // Check up above baseline or down below baseline
            if ((direction === up && point.y < baseline.lastSegment.point.y) || (direction === down && point.y > baseline.lastSegment.point.y)) {
                direction.lastSegment.remove();
                direction.add(point);
            }

            // Make tmp polygon
            if (polygon)
                polygon.remove();
            polygon = makePolygonFromBaseline(
                getPathPoints(baseline),
                up? up.length: 0,
                down? down.length: 0
            );
        }
    }

    return tool;
}
