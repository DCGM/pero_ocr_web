<!--
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
-->

<template>
        <!-- Annotations list -->
        <div class="overflow-auto p-2" id="annotations-container">
            <!-- Image info -->
            <div class="text-white p-2 text-center">
                <h5>Anotované řádky a regiony</h5>
                <hr class="mb-0">
            </div>

            <!-- Header -->
            <div class="text-center text-muted">Regiony ({{ annotations.regions.length }}), Řádky ({{ annotations.rows.length }}):</div>

            <div class="list-group scroll">
                <div v-for="(region,index) in region_annotations_with_empty" :key="index"
                     class="list-group-item p-0"
                >
                    <div class="d-flex justify-content-between">
                        <span class="mr-2" ref="regions" @click="emitActiveRegionChanged(isNotEmptyRegion(region)? region: null)">
                            <i class="fas fa-angle-down pl-2"></i> <span v-if="isNotEmptyRegion(region)" :class="{'active': isRegionActive(region)}">{{ index }} Region</span><span v-else>0 Řádky nepatřící do regionu</span>
                        </span>
                        <span>
                            <span class="badge bg-primary rounded-pill text-muted">{{ getRegionRows(region.uuid).length }}</span>
                            <i v-if="isNotEmptyRegion(region)" class="fas fa-trash-alt text-muted pl-2" @click="$parent.removeAnnotation(region.uuid)"></i>
                        </span>
                    </div>

                    <div :id="'region_'+index+'_rows'" class="pl-1 p-0" :class="{'collapse': !isRegionActive(region)}">
                        <div v-for="(row, row_index) in getRegionRows(region.uuid)" class="d-flex justify-content-end align-middle pl-3">
                            <span class="text-muted pr-1" :class="{'active': isRowActive(row)}">{{ row_index }}</span>
<!--                            <i class="far fa-square white pt-1 pr-1"></i>-->
                            <input
                                ref="rows"
                                placeholder="Přepis řádku..." type="text"
                                v-model="row.view.text.content"
                                @change="row.is_valid = true; emitActiveRowEdited(row);"
                                @click="emitActiveRowChanged(row);"
                                @focus="emitActiveRowChanged(row);"
                            >
                            {{ row.view.text.content.length }}
                            <i class="fas fa-trash-alt text-muted pt-1 pl-2" @click="$parent.removeAnnotation(row.uuid)"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
</template>

<script>

export default {
    props: ['annotations', 'active_region', 'active_row'],
    methods: {
        getRegionRows(region_uuid) {
            return this.annotations.rows.filter((item) => item.region_annotation_uuid === region_uuid);
        },
        clickRegion(region_idx) {
            // +1 because 'No parent region' is zero
            this.$refs.regions[region_idx+1].click();
        },
        emitActiveRowChanged(row) {
            this.$parent.$emit('annotationListEv_activeRowChanged', row);
        },
        emitActiveRegionChanged(region) {
            this.$parent.$emit('annotationListEv_activeRegionChanged', region);
        },
        emitActiveRowEdited(row) {
            this.$parent.$emit('annotationListEv_activeRowTextChanged',  row);
        },
        isNotEmptyRegion(region) {
            return region.hasOwnProperty('points');
        },
        isRegionActive(region) {
            return (this.active_region === null && !this.isNotEmptyRegion(region)) || (this.active_region && region.uuid === this.active_region.uuid);
        },
        isRowActive(row) {
            return this.active_row && row.uuid === this.active_row.uuid;
        },
    },
    computed: {
        region_annotations_with_empty() {
            let empty_region = {
                'uuid': null
            };
            return [empty_region].concat(this.annotations.regions);
        }
    },
    watch: {
        active_row(next, prev) {
            this.$nextTick(() => {
                // prev.blur();
                let row_idx = this.annotations.rows.findIndex((item) => item === next);
                this.$nextTick(() =>
                {
                    let row = this.$refs.rows[row_idx];
                    if (row) {
                        // row.focus();
                        // row.scrollIntoView(row.offsetTop);
                    }
                });
            });
        }
    }
}
</script>

<style scoped>
</style>
