/**
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
**/

import {getPathPoints} from "./annotations";

export function confirmAnnotation(polygon, annotator_component) {
    let tmp_ann = {points: getPathPoints(polygon.path), is_valid: false};
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
    if (polygon.path)
        polygon.path.remove();
    polygon.path = null;
}

export function createPolygonTool(annotator_component) {
    let tool = new paper.Tool();

    // Create bbox tmp variables
    let polygon = {path: null};

    // this.tool.minDistance = 5;

    tool.onKeyDown = (event) => {
        if (event.key === "escape") {
            // Remove currently created rectangle
            if (polygon.path) {
                polygon.path.remove();
                polygon.path = null;
            }
        } else if (event.key === "enter") {
            // Remove currently created rectangle
            if (polygon.path && polygon.path.segments.length >= 4) {
                polygon.path.lastSegment.remove();
                confirmAnnotation(polygon, annotator_component);
            }
        }
    }

    tool.onMouseDown = (event) => {
        event.preventDefault();
        // Check if right click
        if (event.event.which !== 1) {
            if (polygon.path.segments.length >= 4) {
                polygon.path.lastSegment.remove();
                confirmAnnotation(polygon, annotator_component);
            }
        }
        else {
            //
            if (polygon.path == null) {
                polygon.path = new paper.Path();
                polygon.path.closed = true;
                polygon.path.strokeColor = 'rgb(34 43 68)';
                polygon.path.fillColor = 'rgba(75,202,172, 0.1)'
                polygon.path.strokeWidth = 1;
                polygon.path.selected = true;
                console.log('created');
            }

            let canvasMousePosition = new paper.Point(event.event.offsetX, event.event.offsetY);
            let viewPosition = annotator_component.scope.view.viewToProject(canvasMousePosition);
            polygon.path.add(new paper.Point(viewPosition));
        }
    }

    tool.onMouseMove = (event) => {
        if (polygon.path == null)
            return;

        let canvasMousePosition = new paper.Point(event.event.offsetX, event.event.offsetY);
        let viewPosition = annotator_component.scope.view.viewToProject(canvasMousePosition);

        if (polygon.path.segments.length > 1)
            polygon.path.lastSegment.remove();
        polygon.path.add(new paper.Point(viewPosition));
    }

    return tool;
}
