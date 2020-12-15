class Focuser {
    constructor(image_list, text_lines_editor) {
         this.image_list = image_list;
         this.images = $('.scrolling-wrapper .figure');
         for (let i = 0; i < this.images.length; i++){
             let image_id = window.location.href.split('/').reverse()[1];
             let line_id = window.location.href.split('/').reverse()[0].split('?')[0];
             if (image_id == this.images[i].getAttribute('data-image')){
                 let page = $("[data-image=" + this.images[i].getAttribute('data-image') +"]")[0];
                 text_lines_editor.focus_to = line_id;
                 this.image_list.change(page);
             }
        }
    }
}