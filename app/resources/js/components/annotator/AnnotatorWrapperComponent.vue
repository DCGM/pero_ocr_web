<!--
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
-->

<template>
    <div id="annotator">
        <annotator-component
            ref="annotator_component"

            v-on:row-deleted-event="(annotation) => annotationDeletedEventHandler('row', annotation.uuid)"
            v-on:region-deleted-event="(annotation) => annotationDeletedEventHandler('region', annotation.uuid)"

            v-on:row-edited-event="(annotation) => annotationCreatedEditedEventHandler(annotation, 'row')"
            v-on:region-edited-event="(annotation) => annotationCreatedEditedEventHandler(annotation, 'region')"
        ></annotator-component>
    </div>
</template>

<!--v-on:row-selected-event="(event) => myEventHandler('row', event)"-->
<!--v-on:region-selected-event="(event) => myEventHandler('region', event)"-->

<!--v-on:row-created-event="(annotation) => annotationCreatedEditedEventHandler(annotation, 'row', this.image_id)"-->
<!--v-on:region-created-event="(annotation) => annotationCreatedEditedEventHandler(annotation, 'region', this.image_id)"-->


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
            this.$refs.annotator_component.canvasZoomAnnotation(uuid)
        },



        // Custom event handler
        myEventHandler: (type, event) => {
        //     console.log('selected event ' + type, event);
        },

        annotationDeletedEventHandler(type, uuid) {
            axios.delete('/api/annotations/' + type + '/' + uuid);
        },

        imageSelectedEventHandler(image_id) {
            return new Promise((resolve, reject) => {
                this.fetchImageWithAnnotationsPromise(image_id, this.dataset_id)
                    .then((dataset_image) => {
                        // Select image
                        this.load_image(dataset_image.image.path);

                        // // Load region annotations
                        // this.load_annotations(dataset_image.region_annotations);
                        // // Load row annotations
                        // this.$refs.annotator_component.loadAnnotations(dataset_image.row_annotations);
                        resolve();
                    });
            });
        },
        fetchDatasetWithImagesPromise(dataset_id) {
            return new Promise(function (resolve, reject) {
                axios
                    .get('/api/datasets/showWithImages/' + dataset_id)
                    .then((response) => resolve(response.data))
                    .catch((errors) => reject(errors));
            });
        },
        fetchImageWithAnnotationsPromise(image_id, dataset_id) {
            return new Promise(function (resolve, reject) {
                axios
                    .get('/api/datasetImageWithAnnotations/' + dataset_id + '/image/' + image_id)
                    .then((response) => resolve(response.data))
                    .catch((errors) => reject(errors));
            });
        },

        annotationCreatedEditedEventHandler(annotation, annotation_type, image_id=null) {
            axios
                .post('/api/annotations', {
                    annotation: annotation,
                    annotation_type: annotation_type,
                    image_id: image_id,
                    dataset_id: this.dataset_id
                })
                .catch((errors) => console.log(errors));
        }
    },
    mounted() {
      // this.image_id = 1;
        // Get image and dataset id from url
        // let url_params = window.location.pathname.split('/');
        // this.dataset_id = url_params[3];
        // this.image_id = url_params.length >= 5? url_params[4]: null;
        // let row_uuid = url_params.length >= 6? url_params[5]: null;
        // console.log(url_params);
        // console.log(this.document_id)

        // this.fetchDatasetWithImagesPromise(this.dataset_id)
        //     .then((dataset) => {
                // Load dataset to annotator
                // this.$refs.annotator_component.canvasSelectDataset(dataset);  // Optional

                // Load image with annotations to annotator
                // let selected_image = dataset.images.find((item) => item.id === this.image_id);
                // this.image_id = selected_image? selected_image.id: dataset.images[0].id;  // Find or first

                // this.imageSelectedEventHandler(this.image_id)
                //     .then(() => {
                //         // Select row annotation
                //         if (row_uuid)
                //             this.$refs.annotator_component.canvasSelectRowAnnotation(row_uuid);
                //     });
            // });

        // this.$on('imageSelectEv_imageSelected', (image_id) => {
        //     this.image_id = image_id;
        //     this.imageSelectedEventHandler(image_id);
        // });
    }
}
</script>

<style scoped>
</style>
