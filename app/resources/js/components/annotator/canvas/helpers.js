/**
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
**/

import {createScaleMoveViewTool} from "./scale_move_tool_canvas_events";
import {createBboxTool} from "./bbox_tool";
import {createPolygonTool} from "./polygon_tool";
import {createBaselineTool} from "./baseline_tool";
import {createJoinRowsTool} from "./join_rows_tool";

/**
 * Remove all annotations from canvas
 * this: annotator_component
 */
export function canvasClean(start=1) {
    this.scope.project.activeLayer.removeChildren(start);
    this.annotations = {regions: [], rows: []};
}

/**
 * Prepare PaperJs, create tools, activate default tools, register events
 * this: annotator_component
 */
export function canvasInit() {
    this.scope = new paper.PaperScope();
    this.scope.setup("canvas");

    // Create a new layer:
    let first_layer = new paper.Layer();

    // Zero point text
    let text = new paper.PointText(new paper.Point(0, -5));
    text.fillColor = 'rgb(0, 0, 0)';
    // text.fontSize = 20;
    text.content = "[0,0]";

    new paper.Layer();
    first_layer.bringToFront();

    /** Create tools **/
    this.scale_move_tool = createScaleMoveViewTool(this);
    this.bbox_tool = createBboxTool(this);
    this.polygon_tool = createPolygonTool(this);
    this.baseline_tool = createBaselineTool(this);
    this.join_rows_tool = createJoinRowsTool(this);

    /** Activate default tool and select other **/
    this.scale_move_tool.activate();
    this.selected_tool = this.bbox_tool;

    /** Register events **/
    $(document).keydown((event) => {
        if (event.code === "ControlLeft") {
            this.left_control_active = true;

            // View points of selected row
            if (this.active_row && this.canvasIsToolActive(this.scale_move_tool)) {
                this.active_row.view.baseline.baseline_path.selected = true;
                this.active_row.view.baseline.baseline_left_path.selected = true;
                this.active_row.view.baseline.baseline_right_path.selected = true;
            }
            event.preventDefault();
        }
        else if (event.code === "AltLeft") {
           this.left_alt_active = true;

            // View points of selected region
            if (this.active_region && this.canvasIsToolActive(this.scale_move_tool)) {
                this.active_region.view.path.selected = true;
            }
            event.preventDefault();
        }
        else if(event.code === "Enter" || event.code === "NumpadEnter") {
            if (this.active_row && this.active_row.text.length) {
                this.active_row.is_valid = true;
                this.emitAnnotationEditedEvent(this.active_row);
            }
        }
        else if (event.code === "Backspace") {
            // Remove last
            // this.active_row.text = this.active_row.text.slice(0, -1);
        }
        else if (event.code === "Escape") {
            // Remove annotation text
            // this.active_row.is_valid = false;
            // this.active_row.text = "";
            // this.emitAnnotationEditedEvent(this.active_row);
        }
        else if (event.code === "Delete") {
            if (this.left_control_active) {
                // Remove last
                this.canvasSelectTool(this.scale_move_tool);
                this.removeAnnotation(this.last_active_annotation.uuid);
            }
        }
        else if (event.code === "ArrowUp") {
            if (this.active_row) {
                let active_annotation_idx = this.annotations.rows.findIndex(item => item.uuid === this.active_row.uuid);
                this.last_active_annotation = this.active_row = this.annotations.rows[Math.max(0, active_annotation_idx - 1)];
            }
        }
        else if (event.code === "ArrowDown") {
            if (this.active_row) {
                let active_annotation_idx = this.annotations.rows.findIndex(item => item.uuid === this.active_row.uuid);
                this.last_active_annotation = this.active_row = this.annotations.rows[Math.min(this.annotations.rows.length, active_annotation_idx + 1)];
            }
        }

    });
    $(document).keyup((event) => {
        if (event.code === "ControlLeft") {
            this.left_control_active = false;
            // Hide points of selected row
            if (this.active_row && this.canvasIsToolActive(this.scale_move_tool)) {
                this.active_row.view.baseline.baseline_path.selected = false;
                this.active_row.view.baseline.baseline_left_path.selected = false;
                this.active_row.view.baseline.baseline_right_path.selected = false;
            }
            event.preventDefault();
        }
        else if (event.code === "AltLeft") {
            this.left_alt_active = false;
            // Hide points of selected region
            if (this.active_region && this.canvasIsToolActive(this.scale_move_tool)) {
                this.active_region.view.path.selected = false;
            }
            event.preventDefault();
        }
        else if (event.code === "Space") {
        }
    });

    this.$on('imageSelectedEv', (id) => {
        this.canvasSelectImage(id);
    });

    this.$on('annotationListEv_activeRegionChanged', region => {
        this.active_region = region;
    });

    this.$on('annotationListEv_activeRowChanged', row => {
        this.active_row = row;
    });

    this.$on('annotationListEv_activeRowTextChanged', row => {
        // Delegate to AnnotatorWrapperComponent
        this.$emit('row-edited-event', this.serializeAnnotation(row));
    });

    /** Animation handling **/
    this.scope.view.zoom_animation = {on: false,
                                      start_zoom: 0,
                                      end_zoom: 0,
                                      center: this.scope.view.center,
                                      total_time: 0,
                                      p: 1,
                                      time_passed: 0};
    this.scope.view.zoom_animation.reset = function(event)
    {
        self.scope.view.zoom_animation.on = false;
        self.scope.view.zoom_animation.start_zoom = 0;
        self.scope.view.zoom_animation.end_zoom = 0;
        self.scope.view.zoom_animation.center = self.scope.view.center;
        self.scope.view.zoom_animation.total_time = 0;
        self.scope.view.zoom_animation.p = 1;
        self.scope.view.zoom_animation.time_passed = 0;
    }

    this.scope.view.translate_animation = {on: false,
                                           start_point: new paper.Point(0, 0),
                                           end_point: new paper.Point(0, 0),
                                           total_time: 0,
                                           p: 1,
                                           time_passed: 0};
    this.scope.view.translate_animation.reset = function(event)
    {
        self.scope.view.translate_animation.on = false;
        self.scope.view.translate_animation.start_point = new paper.Point(0, 0);
        self.scope.view.translate_animation.end_point = new paper.Point(0, 0);
        self.scope.view.translate_animation.total_time = 0;
        self.scope.view.translate_animation.p = 1;
        self.scope.view.translate_animation.time_passed = 0;
    }

    let self = this;
    this.scope.view.onFrame = function(event)
    {
        if (self.scope.view.zoom_animation.on)
        {
            let start_zoom = self.scope.view.zoom_animation.start_zoom;
            let end_zoom = self.scope.view.zoom_animation.end_zoom;
            let center = self.scope.view.zoom_animation.center;
            let total_time = self.scope.view.zoom_animation.total_time;
            let p = self.scope.view.zoom_animation.p;
            let time_passed = self.scope.view.zoom_animation.time_passed;
            let previous_zoom = self.scope.view.zoom

            if (time_passed < total_time)
            {
                let new_zoom = start_zoom + (end_zoom - start_zoom) * reverse_polynomial_trajectory(time_passed, total_time, p);
                if ((new_zoom >= previous_zoom && new_zoom < end_zoom) ||
                    (new_zoom <= previous_zoom && new_zoom > end_zoom))
                {
                    let scale_factor = new_zoom / previous_zoom;
                    self.scope.view.scale(scale_factor, center);
                }
                else
                {
                    let scale_factor = end_zoom / previous_zoom;
                    self.scope.view.scale(scale_factor, center);
                }
            }
            else
            {
                self.scope.view.zoom = end_zoom;
                self.$emit('zoom-end-event');
                self.scope.view.zoom_animation.reset();
            }
            self.scope.view.zoom_animation.time_passed += event.delta;
        }

        if (self.scope.view.translate_animation.on)
        {
            let start_point = self.scope.view.translate_animation.start_point;
            let end_point = self.scope.view.translate_animation.end_point;
            let total_time = self.scope.view.translate_animation.total_time;
            let p = self.scope.view.translate_animation.p;
            let time_passed = self.scope.view.translate_animation.time_passed;

            if (time_passed < total_time)
            {
                let actual_point = start_point.add(end_point.subtract(start_point).multiply(reverse_polynomial_trajectory(time_passed, total_time, p)));
                self.scope.view.center = actual_point;
            }
            else
            {
                self.scope.view.center = end_point;
                self.scope.view.translate_animation.reset();
            }
            self.scope.view.translate_animation.time_passed += event.delta;
        }
    }

    this.scope.view.onResize = function(event) {
            console.log(event);
        };
}

export function reverse_polynomial_trajectory(t, t_max, p)
{
  return Math.max(0, 1 - (Math.pow((1 - (Math.min(1, t / t_max))) * 8.0, p) / Math.pow(8.0, p)));
}

/**
 * Clean canvas and load image
 * @param path - image path
 * this: annotator_component
 */
export function canvasSelectImage(path) {
    this.canvasClean(0);

    this.image.raster = new paper.Raster(path);
    this.image.path = path;

    // Fit to active layer after load
    this.image.raster.onLoad = this.canvasZoomImage;
}

/**
 * Load dataset
 * @param dataset - dataset object
 * this: annotator_component
 */
export function canvasSelectDataset(dataset) {
    this.dataset = dataset;
}

/**
 * Select row annotation by uuid
 * @param row_uuid
 * this: annotator_component
 */
export function canvasSelectRowAnnotation(row_uuid) {
    this.last_active_annotation = this.active_row = this.annotations.rows.find(item => item.uuid === row_uuid);
}

/**
 * Zoom to image
 * this: annotator_component
 */
export function canvasZoomImage() {
    this.scope.view.zoom_animation.reset();

    // move image left top corner to 0,0
    this.image.raster.position = this.image.raster.bounds.size.multiply(1/2);
    // set view to the center of image
    this.scope.view.center = this.image.raster.position;
    // derive zoom, so the image fits into the view
    let page_width_ratio = this.image.raster.width / this.image.raster.height;
    let view_width_ratio = this.scope.view.bounds.width / this.scope.view.bounds.height;
    let end_zoom;
    if (view_width_ratio > page_width_ratio)
    {
      end_zoom = (this.scope.view.bounds.height / this.image.raster.height) * this.scope.view.zoom;
    }
    else
    {
      end_zoom = (this.scope.view.bounds.width / this.image.raster.width) * this.scope.view.zoom;
    }
    let page_fraction_in_view = 0.75
    this.scope.view.zoom = end_zoom * page_fraction_in_view;

    this.scope.view.zoom_animation.start_zoom = this.scope.view.zoom;
    this.scope.view.zoom_animation.end_zoom = end_zoom;
    this.scope.view.zoom_animation.p = 3;
    this.scope.view.zoom_animation.total_time = 0.5;
    this.scope.view.zoom_animation.on = true;
}


/**
 * Zoom annotation (row)
 * * this: annotator_component
 * @param uuid
 */
export function canvasZoomAnnotation(uuid, show_line_height, show_bottom_pad, normalized_caret_position = 0) {
    this.scope.view.zoom_animation.reset();
    this.scope.view.translate_animation.reset();

    let row = this.annotations.rows.find(item => item.uuid === uuid);
    if (!row) return;

    let focus_line_points = getFocusLinePoints(row,
                                               show_line_height,
                                               show_bottom_pad,
                                               25,
                                               this.scope.view.viewSize.width,
                                               this.scope.view.viewSize.height,
                                               this.scope.view.bounds.x,
                                               this.scope.view.bounds.x + this.scope.view.bounds.width,
                                               normalized_caret_position);
    let line_x0 = focus_line_points[0];
    let line_x1 = focus_line_points[1];
    let y = focus_line_points[2];


    this.scope.view.zoom_animation.reset();
    this.scope.view.zoom_animation.start_zoom = this.scope.view.zoom;
    this.scope.view.zoom_animation.end_zoom = this.scope.view.zoom * (this.scope.view.bounds.width / (line_x1 - line_x0));
    this.scope.view.zoom_animation.p = 3;
    this.scope.view.zoom_animation.total_time = 0.5;
    this.scope.view.zoom_animation.on = true;

    this.scope.view.translate_animation.reset();
    this.scope.view.translate_animation.start_point = this.scope.view.center;
    this.scope.view.translate_animation.end_point = new paper.Point((line_x0 + line_x1) / 2, y);
    this.scope.view.translate_animation.p = 3;
    this.scope.view.translate_animation.total_time = 0.5;
    this.scope.view.translate_animation.on = true;

}

/*
image - coordinates, sizes, etc. relatively to original image
view - coordinates, sizes, etc. relatively to browser view
target - coordinates, sizes, etc. after focusing

Variables without target specify coordinates, sizes, etc. before focusing (current)
*/

export function getFocusLinePoints(line,
                                   view_target_line_height,
                                   view_target_bottom_pad,
                                   view_target_left_pad,
                                   view_port_width,
                                   view_port_height,
                                   image_port_x0,
                                   image_port_x1,
                                   normalized_caret_position) {

    let image_line_width_boundary = get_image_line_width_boundary(line);
    let image_line_height_boundary = get_image_line_height_boundary(line);
    let image_line_x0 = image_line_width_boundary[0];
    let image_line_x1 = image_line_width_boundary[1];
    let image_line_y0 = image_line_height_boundary[0];
    let image_line_y1 = image_line_height_boundary[1];
    let image_line_width = image_line_x1 - image_line_x0;
    let image_line_height = line.heights.down + line.heights.up;
    let image_port_width = image_port_x1 - image_port_x0;

    let view_to_image_target_scale = image_line_height /  view_target_line_height;
    let image_target_port_height = view_port_height * view_to_image_target_scale;
    let image_target_port_width = view_port_width * view_to_image_target_scale;
    let image_target_bottom_pad =  view_target_bottom_pad * view_to_image_target_scale;
    let image_target_left_pad = view_target_left_pad * view_to_image_target_scale;

    let image_target_port_x0;
    let image_target_port_x1;

    // line fits in the view
    if (image_target_port_width >= (image_line_width + 2 * image_target_left_pad)) {
        let center_pad = (image_target_port_width - image_line_width) / 2;
        image_target_port_x0 = image_line_x0 - center_pad;
        image_target_port_x1 = image_line_x1 + center_pad;
    }
    else {
        if (normalized_caret_position == 0) {
            image_target_port_x0 = image_line_x0 - image_target_left_pad;
            image_target_port_x1 = image_target_port_x0 + image_target_port_width;
        }
        // focus based on caret position
        else {
            let image_caret_position = image_line_x0 + image_line_width * normalized_caret_position;
            let image_half_port_width = image_port_width / 2;
            let image_offset = image_port_width / 8;
            let image_current_focus = image_port_x0 + image_half_port_width;
            // do not refocus each time caret position is changed
            if ((image_caret_position > image_current_focus + image_half_port_width - image_offset) ||
                (image_caret_position < image_current_focus - image_half_port_width + image_offset)) {
                image_current_focus = image_caret_position;
            }
            // clip focus
            if (image_current_focus + image_half_port_width > image_line_x1 + image_target_left_pad) {
                image_current_focus = image_line_x1 - image_half_port_width + image_target_left_pad;
            }
            if (image_current_focus - image_half_port_width < image_line_x0 - image_target_left_pad) {
                image_current_focus = image_line_x0 + image_half_port_width - image_target_left_pad;
            }
            image_target_port_x0 = image_current_focus - image_half_port_width;
            image_target_port_x1 = image_current_focus + image_half_port_width;
        }
    }

    let y = image_line_y1 + image_target_bottom_pad - image_target_port_height / 2;
    return [image_target_port_x0, image_target_port_x1, y];
}


export function to_image_coords(x, image_line_height) {
    return (image_line_height * view_left_pad) / view_target_line_height;
}

export function get_image_line_height_boundary(line) {
    let height_min = 100000000000000000000000;
    let height_max = 0;
    for (let coord of line.points) {
        if (coord.y < height_min) {
            height_min = coord.y;
        }
        if (coord.y > height_max) {
            height_max = coord.y;
        }
    }
    return [height_min, height_max];
}


export function get_image_line_width_boundary(line) {
    let width_min = 100000000000000000000000;
    let width_max = 0;
    for (let coord of line.points) {
        if (coord.x < width_min) {
            width_min = coord.x;
        }
        if (coord.x > width_max) {
            width_max = coord.x;
        }
    }
    return [width_min, width_max];
}


/**
 *
 * * this: annotator_component
 * @param tool
 * @returns {boolean}
 */
export function canvasIsToolActive(tool) {
    return this.scope && this.scope.tool === tool;
}

/**
 * Select PaperJs tool
 * this: annotator_component
 * @param tool
 */
export function canvasSelectTool(tool) {
    this.selected_tool = tool;
    this.selected_tool.activate();
    this.active_row = null;
    // Disable focus if not creating new row
    if (tool !== this.baseline_tool)
        this.active_row = this.active_region = this.last_active_annotation = null;
    this.$forceUpdate();
}
