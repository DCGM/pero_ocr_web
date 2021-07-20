<!--
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
-->

<template>
    <div id="images-select-bar" class="d-flex flex-column" v-if="dataset">
        <!-- Image info -->
        <div class="text-white p-2 text-center">
            <h5>{{ dataset.name }}</h5>
            <div class="text-center text-muted mb-2">Obrázek: {{ current_image_idx + 1 }} / {{ dataset.images.length }}</div>
            <button class="btn btn-primary btn-primary-outline btn-sm" @click="nextImage(-1)">Předchozí obrázek</button>
            <button class="btn btn-primary btn-primary-outline btn-sm" @click="nextImage(1)">Následující obrázek</button>

            <hr class="mb-0">
        </div>

        <!-- Annotations list -->
        <div class="overflow-auto p-2" id="annotations-container">
            <!-- Header -->
            <div class="text-center text-muted">Obrázky ({{ dataset.images.length }}):</div>

            <div class="list-group scroll" ref="imageScroll">
                <div v-for="(image,index) in dataset.images" :key="index" class="list-group-item p-0">
                    <div class="d-flex justify-content-between">
                        <span class="mr-2" ref="images" :class="current_image_path !== image.path? 'text-muted': 'active'" @click="emitImgSelectedEv(image.id)" data-toggle="tooltip" data-placement="top" :title="image.name">
                            <i class="fas fa-image pl-2"></i> {{ index + 1 }} {{ printImageName(image.name) }}
                        </span>
                    </div>
                </div>
            </div>

        </div>
    </div>
</template>

<script>

export default {
    props: ['dataset', 'current_image_path'],
    watch: {
        current_image_path(next, prev) {
            let img_idx = this.dataset.images.findIndex(item => item.path === this.current_image_path);
            let img = this.$refs.images[img_idx];
            if (img) {
                // img.offsetTop;
                // console.log(this.$refs.imageScroll);
                // this.$refs.imageScroll.scrollTop = img.offsetTop;
                img.scrollIntoView(img.offsetTop);
            }
        }
    },
    methods: {
        emitImgSelectedEv(id) {
            // Emit event to AnnotatorWrapperComponent
            this.$parent.$parent.$emit('imageSelectEv_imageSelected', id);
        },
        nextImage(step=1) {
            let num_imgs = this.dataset.images.length;
            let next_idx = (((this.current_image_idx + step)%num_imgs)+num_imgs)%num_imgs;  // Modulo
            let next_image = this.dataset.images[next_idx];
            this.emitImgSelectedEv(next_image.id)
        },
        printImageName(name) {
            let len = 25;
            if (name.length > len)
                return name.substr(0, 15) + ' ... ' + name.substr(name.length-7, 7);
            return name;
        }
    },
    computed: {
        current_image_idx() {
            return this.dataset.images.findIndex(item => item.path === this.current_image_path)
        }
    }
}
</script>

<style scoped>
</style>
