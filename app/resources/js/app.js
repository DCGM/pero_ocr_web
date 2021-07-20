/**
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
**/

/** Vue.js **/
// import Vue from 'vue'
// import Vue from 'vue/dist/vue.js';
window.Vue = require('vue');

/** Lodash **/
import _ from 'lodash';
window._ = _;

/** Paper.js **/
import * as paper from 'paper';
window.paper = paper;

/** Axios **/
window.axios = require('axios').default;

/** Register Vue components **/
const files = require.context('./', true, /\.vue$/i)
files.keys().map(key => Vue.component(key.split('/').pop().split('.')[0], files(key).default))

/** Setup Vue application **/
window.vue_app = new Vue({
    el: '#app_app',
});
