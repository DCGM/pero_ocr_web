/**
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
**/

import {confirmAnnotation} from "./annotations";


export function createBboxTool(annotator_component) {
    let tool = new paper.Tool();

    // Create bbox tmp variables
    let bbox = {start: null, path: null};

    // this.tool.minDistance = 5;

    tool.onKeyDown = (event) => {
        if (event.key === "escape") {
            // Remove currently created rectangle
            if (bbox.path) {
                bbox.path.remove();
                bbox.path = bbox.start = null;
            }
        }
    }

    tool.onMouseDown = (event) => {
        // Check if right click
        if (event.event.which !== 1)
            return;

        let canvasMousePosition = new paper.Point(event.event.offsetX, event.event.offsetY);
        let viewPosition = annotator_component.scope.view.viewToProject(canvasMousePosition);
        if (bbox.start == null) {
            bbox.start = viewPosition;

            bbox.path = new paper.Path.Rectangle(new paper.Rectangle(bbox.start, bbox.start)); // Initial bbox
            bbox.path.closed = true;
        }
    }

    tool.onMouseMove = (event) => {
        if (bbox.start == null)
            return;

        let canvasMousePosition = new paper.Point(event.event.offsetX, event.event.offsetY);
        let viewPosition = annotator_component.scope.view.viewToProject(canvasMousePosition);

        bbox.path.remove();
        bbox.path = new paper.Path.Rectangle(new paper.Rectangle(bbox.start, viewPosition));
        // bbox.path.fillColor = 'rgba(34 43 68,0.4)';
        bbox.path.strokeColor = 'rgb(34 43 68)';
        bbox.path.strokeWidth = 1;
        bbox.path.selected = false;
    }

    tool.onMouseUp = (event) => {
        if (bbox.path) {
            // Check if area is too small (probably miss click)
            if (bbox.path.area > 50) {
                confirmAnnotation(bbox, annotator_component);
                // let annotation_view = annotator_component.createAnnotationView(getPathPoints(bbox.path), annotator_component.creating_annotation_type, false, false);
                // let active_region_uuid = annotator_component.active_region ? annotator_component.active_region.uuid : null;
                // let annotation = annotator_component.createAnnotation(annotation_view, annotator_component.creating_annotation_type, active_region_uuid);
                //
                // // Push region to annotations
                // annotator_component.annotations[annotator_component.creating_annotation_type].push(annotation);
                //
                // // Set this annotation to active
                // if (annotator_component.creating_annotation_type === 'regions')
                //     annotator_component.active_region = annotation;
                // else
                //     annotator_component.active_row = annotation;
            }

            // Remove tmp path
            bbox.path.remove();
        }

        bbox.start = null;
        bbox.path = null;
    }

    return tool;
}
