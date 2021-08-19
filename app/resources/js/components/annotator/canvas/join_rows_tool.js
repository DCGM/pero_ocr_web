import {getPathPoints, serializeAnnotation} from "./annotations";

/**
 * Autor práce: David Hříbek
 * Rok: 2021
 **/


export function createJoinRowsTool(annotator_component) {
    let tool = new paper.Tool();
    let base_row = null;

    tool.row_selected = (to_join_row) => {
        if (base_row && base_row !== to_join_row) {
            // Join points
            let points = getPathPoints(base_row.view.path).concat(getPathPoints(to_join_row.view.path));

            // Calc. convex envelope and join paths
            points = points.map((item) => [item.x, item.y]);
            points = hull(points, 200);
            base_row.view.path.clear();
            for (let point of points)
                base_row.view.path.add(new paper.Point(point));

            // annotator_component.last_active_annotation = annotator_component.active_row = base_row;
            // Join texts
            base_row.text += to_join_row.text;
            base_row.view.text.content = base_row.text;

            // Delete second row
            annotator_component.removeAnnotation(to_join_row.uuid);

            // Init
            base_row = null;
            // annotator_component.canvasSelectTool(annotator_component.scale_move_tool);
        }
        else
            base_row = to_join_row;
    }


    tool.onKeyDown = (event) => {
        if (event.key === "escape") {
            base_row = null;
            annotator_component.canvasSelectTool(annotator_component.scale_move_tool);
        }
    }

    return tool;
}
