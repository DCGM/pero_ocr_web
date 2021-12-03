<!--
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
-->

<template>
    <div id="annotator">
        <annotator-component
            ref="annotator_component"
        ></annotator-component>
    </div>
</template>

<!--v-on:row-selected-event="(event) => myEventHandler('row', event)"-->
<!--v-on:region-selected-event="(event) => myEventHandler('region', event)"-->

<!--v-on:row-created-event="(annotation) => annotationCreatedEditedEventHandler(annotation, 'row', this.image_id)"-->
<!--v-on:region-created-event="(annotation) => annotationCreatedEditedEventHandler(annotation, 'region', this.image_id)"-->

<!--v-on:row-edited-event="(annotation) => annotationCreatedEditedEventHandler(annotation, 'row')"-->
<!--v-on:region-edited-event="(annotation) => annotationCreatedEditedEventHandler(annotation, 'region')"-->

<!--v-on:row-deleted-event="(annotation) => annotationDeletedEventHandler('row', annotation.uuid)"-->
<!--v-on:region-deleted-event="(annotation) => annotationDeletedEventHandler('region', annotation.uuid)"-->

<script>
export default {
    data() {
        return {
            // Example data format
            region_annotation_example: {
                uuid: 'region_uuid_1',
                points: [{x: 0, y: 0}, {x: 0, y: 200}, {x: 500, y: 200}, {x: 500, y: 0}],
                is_deleted: false,
            },
            row_annotation_example: {
                uuid: 'row_uuid_1',
                points: [{x: 0, y: 0}, {x: 0, y: 100}, {x: 50, y: 100}, {x: 50, y: 0}],
                region_annotation_uuid: 'region_uuid_1',
                state: '', // active/ignored/edited
                order: 0,
                text: 'some text'
            },

            // Dataset info component example data format
            dataset_example: {
                id: 1,
                name: 'Dataset1',
                images: [
                    {
                        'id': 1,
                        'name': 'ImageName1',
                        'path': '/path.png'
                    }
                ]
            },

            image_id: null, // Annotated image id
            dataset_id: null, // Annotated dataset id
        }
    },
    methods: {
        /** PUBLIC API **/
        load_image(path) {
            this.$refs.annotator_component.canvasSelectImage(path);
        },
        load_annotations(annotations) {
            this.$refs.annotator_component.loadAnnotations(annotations);
        },
        select_row(row_uuid) {
            this.$refs.annotator_component.canvasSelectRowAnnotation(row_uuid);
        },
        zoom_row(uuid) {
          this.$refs.annotator_component.canvasZoomAnnotation(uuid);
        },
        validate_row_annotation(uuid) {
          this.$refs.annotator_component.validateRowAnnotation(uuid);
        },
    },
}
</script>

<style scoped>
</style>
