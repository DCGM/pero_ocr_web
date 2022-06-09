/**
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
**/

function confirm (polygon, annotator_component) {
    polygon.path.lastSegment.remove();
    annotator_component.confirmAnnotation(polygon);

    // Remove tmp path
    polygon.path.remove();
    polygon.path = null;

    // Select default tool
    annotator_component.canvasSelectTool(annotator_component.scale_move_tool);
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
                confirm(polygon, annotator_component);
            }
        }
    }

    tool.onMouseDown = (event) => {
        event.preventDefault();
        // Check if right click
        if (event.event.which !== 1) {
            if (polygon.path.segments.length >= 4) {
                confirm(polygon, annotator_component);
            }
        }
        else {
            //
            if (polygon.path == null) {
                polygon.path = new paper.Path();
                polygon.path.closed = true;
                polygon.path.strokeColor = 'rgb(34 43 68)';
                polygon.path.fillColor = 'rgba(75,202,172, 0.1)';
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
