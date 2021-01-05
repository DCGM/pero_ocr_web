class Focuser {
    constructor(image_list, text_lines_editor) {
         this.image_list = image_list;
         this.images = $('.scrolling-wrapper .figure');

         let parsed_url = window.location.href.split('/').reverse();
         let counter = 0;
         for (let part of parsed_url) {
            if (part == 'show_results'){
                break;
            }
            else{
                counter += 1;
            }
         }

         for (let i = 0; i < this.images.length; i++){
             if (counter == 2){
                 var image_id = window.location.href.split('/').reverse()[0];
             }
             if (counter == 3){
                 var image_id = window.location.href.split('/').reverse()[1];
                 var line_id = window.location.href.split('/').reverse()[0];
             }

             if (image_id == this.images[i].getAttribute('data-image')){
                 let page = $("[data-image=" + this.images[i].getAttribute('data-image') +"]")[0];
                 if (counter == 3){
                    text_lines_editor.focus_to = line_id;
                 }
                 this.image_list.change(page, true);
             }
        }
    }
}