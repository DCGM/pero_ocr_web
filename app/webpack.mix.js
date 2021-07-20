// webpack.mix.js
let mix = require('laravel-mix');

mix.setPublicPath('static');

mix.js('resources/js/app.js', '')
   .sass('resources/sass/app.scss', '');
