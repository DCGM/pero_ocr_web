<!--
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
-->

<template>
    <div class="d-flex">
        <!-- Left section (Toolbar) -->
        <aside id="tool-bar" class="d-flex flex-column">
            <div class="p-2 text-center" :class="{'active': canvasIsToolActive(scale_move_tool)}"
                 data-toggle="tooltip" data-placement="top" title="Scale/move image"
                 @click="canvasSelectTool(scale_move_tool)"><i class="fas fa-arrows-alt"></i>
            </div>

            <div class="text-small pt-3">Region</div>
            <div class="p-2 text-center"
                 :class="{'active': canvasIsToolActive(bbox_tool) && creating_annotation_type === 'regions'}"
                 data-toggle="tooltip" data-placement="top" title="Create new region (bbox)"
                 @click="canvasSelectTool(bbox_tool); creating_annotation_type='regions';"><i
                class="far fa-square"></i>
            </div>
            <div class="p-2 text-center"
                 :class="{'active': canvasIsToolActive(polygon_tool) && creating_annotation_type === 'regions'}"
                 data-toggle="tooltip" data-placement="top" title="Create new region (polygon)"
                 @click="canvasSelectTool(polygon_tool); creating_annotation_type='regions';"><i class="fas fa-draw-polygon"></i>
            </div>

            <div class="text-small pt-5">Row</div>
            <div class="p-2 text-center"
                 :class="{'active': canvasIsToolActive(baseline_tool) && creating_annotation_type === 'rows'}"
                 data-toggle="tooltip" data-placement="top" title="Create new row (baseline)"
                 @click="canvasSelectTool(baseline_tool); creating_annotation_type='rows';"
            >
                <i class="fas fa-grip-lines"></i>
            </div>
            <div class="p-2 text-center"
                 :class="{'active': canvasIsToolActive(join_rows_tool)}"
                 data-toggle="tooltip" data-placement="top" title="Join two rows into one"
                 @click="canvasSelectTool(join_rows_tool)"
            >
              <i class="fab fa-confluence"></i>
            </div>

            <div class="text-small pt-5">Other</div>

            <!-- Zoom to image -->
            <div class="p-2 text-center"
                 @click="canvasZoomImage"
                 data-toggle="tooltip" data-placement="top" title="Default zoom"
            >
              <i class="fas fa-compress-arrows-alt"></i>
            </div>

        </aside>

        <!-- Middle section (Canvas) -->
        <div id="canvas-wrapper" @contextmenu="canvasContextMenuEv">
            <canvas
                @mouseup="canvasMouseUpEv"
                @wheel="canvasMouseWheelEv"
                @mousedown="canvasMouseDownEv"
                @dblclick="canvasMouseDblClickEv"
                @mousemove="canvasMouseMoveEv"
                id="canvas"
                class="float-left"
                resize/>
            <div id="tutorial">
                <div>
<!--                    <span class="pr-3"><span class="badge badge-primary" style="background: #6cb2eb;">Přepsaný řádek</span> - Přepsané řádky jsou barevně zvýrazněny</span>-->
<!--                    <span class="pr-3"><span class="badge badge-primary">Levý Alt</span> - Podržením vyberete nástroj pro posuv</span>-->
                </div>
                <span v-if="active_row">
<!--                    <span class="pr-3"><span class="badge badge-success">Enter</span> - Potvrzení správnosti přepisu</span>-->
<!--                    <span class="pr-3"><span class="badge badge-danger">Levý Ctrl + Del</span> - Smazání anotace</span>-->
                    <span class="pr-3"><span class="badge badge-primary">Left Ctrl</span> - Edit active row</span>
                    <span class="pr-3"><span class="badge badge-primary">Left Alt</span> - Edit active region</span>
<!--                    <span class="pr-3"><span class="badge badge-primary">Esc</span> - Zrušení přepisu</span>-->
                    <span class="pr-3"><span class="badge badge-primary">Arrow Up</span> - Previous row</span>
                    <span class="pr-3"><span class="badge badge-primary">Arrow Down</span> - Next row</span>
                </span>
            </div>


            <!-- Row text -->
<!--            <div id="canvas-row-text" class="text-primary">-->
<!--                <span v-if="active_row"><input ref="input-transcription-text" type="text" class="input-transcription-text" v-model="active_row.text"/><span class="text-muted">({{ active_row.text.length }})</span></span>-->
<!--            </div>-->

            <!-- Mouse coordinates -->
<!--            <div id="canvas-coordinates" class="text-primary">-->
<!--                <span v-if="scope">ZOOM: {{ Math.round(scope.view.zoom*100, 2)/100 }} </span>-->
<!--                <span class="p-2">X: {{ mouse_coordinates.x }}, Y: {{ mouse_coordinates.y }}</span>-->
<!--            </div>-->

            <!-- Context menu -->
            <div id="canvas-contextmenu" class="d-flex flex-column">
                <div class="p-2 text-primary" @click="removeAnnotation(last_active_annotation.uuid, true); deactivateContextMenu();">
                    <i class="fas fa-trash-alt text-muted pr-2"></i>
                    <span v-if="last_active_annotation === active_region">Delete region</span><span v-else>Delete row</span>
                </div>
<!--                <div class="p-2 text-primary"-->
<!--                     v-if="last_active_annotation && last_active_annotation.is_valid"-->
<!--                     @click="last_active_annotation.is_valid = false; emitAnnotationEditedEvent(last_active_annotation); deactivateContextMenu();"-->
<!--                >-->
<!--                    <i class="fas fa-times text-muted pr-2"></i> Zrušit potvrzení správnosti přepisu-->
<!--                </div>-->
<!--                <div class="p-2 text-primary"-->
<!--                     v-if="last_active_annotation && !last_active_annotation.is_valid"-->
<!--                     @click="last_active_annotation.is_valid = true; emitAnnotationEditedEvent(last_active_annotation); deactivateContextMenu();"-->
<!--                >-->
<!--                    <i class="fas fa-check text-muted pr-2"></i> Potvrdit správnost přepisu-->
<!--                </div>-->
<!--                <div v-if="last_segm" class="p-2 text-primary" @click="removeAnnotationSegm(); deactivateContextMenu();">-->
<!--                    <i class="fas fa-edit text-muted pr-2"></i> Odstranit bod-->
<!--                </div>-->
<!--                <div class="p-2 text-primary" @click="canvasZoomAnnotation(last_active_annotation); deactivateContextMenu();">-->
<!--                    <i class="fas fa-edit text-muted pr-2"></i> Přiblížit-->
<!--                </div>-->
            </div>
        </div>
    </div>
</template>

<script>
import {canvasZoomAnnotation, getFocusLinePoints, canvasSelectRowAnnotation, canvasSelectImage, canvasSelectDataset, canvasClean, canvasInit, canvasZoomImage, canvasIsToolActive, canvasSelectTool} from './helpers';
import {activateContextMenu, deactivateContextMenu, canvasContextMenuEv} from './context_menu';
import {setPathColor, emitAnnotationEditedEvent, serializeAnnotation, getAnnotations, loadAnnotations, removeAnnotation, removeAnnotationSegm, createAnnotation, createAnnotationView, activeRegionChangedHandler, activeRowChangedHandler, confirmAnnotation, validateRowAnnotation} from './annotations';
import {canvasMouseWheelEv, canvasMouseMoveEv, canvasMouseDownEv, canvasMouseUpEv, canvasMouseDblClickEv} from './scale_move_tool_canvas_events';

export default {
    props: [],
    data() {
        return {
            scope: null, // PaperJs scope
            image: {raster: null, path: null},
            left_control_active: false,
            left_alt_active: false,

            // Edit annotation
            last_segm: null,
            last_baseline: null,
            last_segm_type: null,

            // Annotations
            annotations: {regions: [], rows: []},
            active_region: null,
            active_row: null,
            last_active_annotation: null,
            worst_confidence: null,

            // Tools
            selected_tool: null, //
            scale_move_tool: null, // Default
            bbox_tool: null,
            polygon_tool: null,
            baseline_tool: null,
            join_rows_tool: null,

            creating_annotation_type: 'regions',
            camera_move: false,
            point_move: false,

            // COMPONENT:
            dataset: null
        }
    },
    methods: {
        /** Public **/
        // Binding imports
        canvasMouseWheelEv, canvasMouseDownEv, canvasMouseUpEv, canvasMouseDblClickEv, canvasMouseMoveEv,
        canvasZoomImage,
        canvasIsToolActive, canvasSelectTool,

        canvasZoomAnnotation, getFocusLinePoints, canvasSelectDataset, canvasSelectImage, canvasSelectRowAnnotation, canvasClean, canvasInit,
        setPathColor, emitAnnotationEditedEvent, serializeAnnotation, getAnnotations, loadAnnotations, removeAnnotation, removeAnnotationSegm, createAnnotation, createAnnotationView, confirmAnnotation, validateRowAnnotation,
        activateContextMenu, deactivateContextMenu, canvasContextMenuEv,
        activeRegionChangedHandler, activeRowChangedHandler,
    },
    watch: {
        active_region: {
            handler(next, prev) {
                this.activeRegionChangedHandler(next, prev);
            },
            // deep: true
        },
        active_row: {
            handler(next, prev) {
                this.activeRowChangedHandler(next, prev);
            }
        }
    },
    mounted() {
        this.canvasInit();
    }
}
</script>

<style scoped>
</style>
