/**
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
**/


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
            if (bbox.path.area > 50)
                annotator_component.confirmAnnotation(bbox);

            // Remove tmp path
            bbox.path.remove();
        }

        bbox.start = null;
        bbox.path = null;
    }

    return tool;
}
