// webpack.mix.js
let mix = require('laravel-mix');

mix.setPublicPath('static');

mix.js('resources/js/app.js', 'annotator_component.js')
   .sass('resources/sass/app.scss', 'annotator_component.css');
