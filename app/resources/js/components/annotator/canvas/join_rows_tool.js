import {getPathPoints} from "./annotations";

/**
 * Autor práce: David Hříbek
 * Rok: 2021
 **/


export function createJoinRowsTool(annotator_component) {
    let tool = new paper.Tool();
    let base_row = null;

    tool.row_selected = (to_join_row) => {
        if (base_row && base_row !== to_join_row) {
            // Join baselines and create new row
            for (let segment of to_join_row.view.baseline.baseline_path.segments)
                base_row.view.baseline.baseline_path.add(segment);

            let up = new paper.Path([base_row.view.baseline.baseline_path.firstSegment.point, base_row.view.baseline.baseline_left_path.lastSegment.point]);
            let down = new paper.Path([base_row.view.baseline.baseline_path.firstSegment.point, base_row.view.baseline.baseline_left_path.firstSegment.point]);
            let baseline = {baseline: base_row.view.baseline.baseline_path, up: up, down: down};
            annotator_component.creating_annotation_type = 'rows';
            let new_row = annotator_component.confirmAnnotation(null, baseline);
            up.remove();
            down.remove();

            // Join texts
            new_row.text = base_row.text + to_join_row.text;

            // Delete both rows
            annotator_component.removeAnnotation(base_row.uuid);
            annotator_component.removeAnnotation(to_join_row.uuid);

            // Init
            base_row = null;
            annotator_component.canvasSelectTool(annotator_component.scale_move_tool);
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
