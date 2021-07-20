/**
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
**/

/**
 * Create tool for scaling and moving over canvas
 * @param annotator_component
 * @returns {paper.Tool}
 */
export function createScaleMoveViewTool(annotator_component) {
    let tool = new paper.Tool();

    tool.onMouseDrag = (event) => {
        if (!annotator_component.left_control_active) {
            let offset = event.point.subtract(event.downPoint);
            annotator_component.scope.view.center = annotator_component.scope.view.center.subtract(offset);
        }
        else {
            if (annotator_component.last_segm) {
                annotator_component.last_segm.point = annotator_component.last_segm.point.add(event.delta);
                annotator_component.mouse_drag = true;
            }
        }
    };

    return tool;
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
    // Print coordinates
    let canvasMousePosition = new paper.Point(event.offsetX, event.offsetY);
    let viewPosition = this.scope.view.viewToProject(canvasMousePosition);

    this.mouse_coordinates.x = Math.round(viewPosition.x);
    this.mouse_coordinates.y = Math.round(viewPosition.y);
}

/**
 * Event: Mouse down on canvas
 * this: annotator_component
 * @param event
 */
export function canvasMouseDownEv(event) {
}

/**
 * Event: Mouse up on canvas
 * this: annotator_component
 * @param event
 */
export function canvasMouseUpEv(event) {
    // Finish editing polygon
    if (this.mouse_drag) {
        this.mouse_drag = false;
        this.last_segm = null;
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
