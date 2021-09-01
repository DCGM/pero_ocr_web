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
    text.fillColor = 'rgb(255, 255, 255)';
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
        }
        else if (event.code === "AltLeft") {
            this.scale_move_tool.activate();
            this.$forceUpdate();
        }
        else if(event.code === "Enter" || event.code === "NumpadEnter") {
            if (this.active_row && this.active_row.view.text.content.length) {
                this.active_row.is_valid = true;
                this.emitAnnotationEditedEvent(this.active_row);
            }
        }
        else if (event.code === "Backspace") {
            // Remove last
            // this.active_row.view.text.content = this.active_row.view.text.content.slice(0, -1);
        }
        else if (event.code === "Escape") {
            // Remove annotation text
            this.active_row.is_valid = false;
            this.active_row.view.text.content = "";
            this.emitAnnotationEditedEvent(this.active_row);
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
        }
        else if (event.code === "AltLeft") {
            this.selected_tool.activate();
            this.bbox = {start: null, path: null}; // Reset bbox tool
            this.$forceUpdate();
        }
        else if (event.code === "Space") {
            event.preventDefault();
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
    this.active_row = this.annotations.rows.find(item => item.uuid === row_uuid);
}

/**
 * Zoom to image
 * this: annotator_component
 */
export function canvasZoomImage() {
    this.scope.view.zoom = 0.2;
    // this.image.raster.size = this.scope.view.viewSize.multiply(0.9);
    // this.image.raster.size.width = this.scope.view.viewSize.width

    // console.log(this.scope.view.bounds);
    // console.log(this.image.raster.bounds);
    // console.log(this.image.raster.size);

    // this.scope.view.position = this.image.raster.position.add(new paper.Point(100,100));
    // this.scope.project.activeLayer.fitBounds(this.image.raster.view.bounds);
    // this.image.raster.fitBounds(this.scope.view.bounds);
    // this.image.raster.position = this.scope.view.bounds.multiply(1/2);
    // this.scope.project.activeLayer.fitBounds(this.scope.view.bounds);
    // this.image.raster.position

    // console.log(this.image.raster.view.bounds.size.multiply(1/2));

    // this.scope.view.setCenter(this.image.raster.size.multiply(-1/4));
    // this.image.raster.position = new paper.Point(0,0).subtract(this.scope.view.viewSize.multiply(-1/2));
    // this.scope.view.center = this.image.raster.size.multiply(-1/2);

    this.image.raster.position = this.image.raster.bounds.size.multiply(1/2);//.add(new paper.Size(0, 30));
    this.scope.view.center = this.image.raster.bounds.size.multiply(1/2);//.subtract(new paper.Size(0, 30));
    // this.scope.view.fitBounds(this.image.raster.bounds);
    // this.scope.project.view.fitBounds(this.scope.view.bounds);

    // this.scope.project.activeLayer.fitBounds(this.image.raster.bounds);

    // console.log('zoom');
    // this.scope.project.activeLayer.fitBounds(this.scope.view.bounds);
    // this.scope.view.fitBounds(this.scope.project.activeLayer.bounds);
    // this.scope.project.activeLayer.fitBounds(this.scope.project.activeLayer.children()[0].bounds);
    // this.scope.project.activeLayer.fitBounds(this.image.raster.bounds);
}

/**
 * Zoom annotation (row)
 * * this: annotator_component
 * @param uuid
 */
export function canvasZoomAnnotation(uuid) {
    let row = this.annotations.rows.find(item => item.uuid === uuid);
    if (!row) return;

    // Inspired by: https://github.com/paperjs/paper.js/issues/1688
    let item_bounds = row.view.group.bounds;
    let view = this.scope.project.activeLayer.view;
    let view_bounds = view.bounds;

    // Zoom
    let scale_ratio = Math.min(view_bounds.width / item_bounds.width, view_bounds.height / item_bounds.height);
    view.scale(scale_ratio);

    // Translate
    let delta = view_bounds.center.subtract(item_bounds.center);
    view.translate(delta);
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
    this.active_row = this.active_region = this.last_active_annotation = null;
    this.$forceUpdate();
}
