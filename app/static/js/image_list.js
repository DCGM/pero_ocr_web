
class ImageList
{
    constructor(objects_to_change)
    {
        this.objects_to_change = objects_to_change;

        this.images = $('.scrolling-wrapper .figure');

        //set image index to last opened page otherwise to 1
        this.image_index = 1;
        this.last_opened_page_handle(true);

         //if there is more specific href, set image index to it
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
             }

             if (image_id == this.images[i].getAttribute('data-image')){
                 this.image_index = i+1;
             }
        }

        for (let i of this.images)
        {
            i.addEventListener('click', this.change.bind(this, i));
        }
        this.number_of_images = this.images.length;
        this.image_index = Math.max(1, this.image_index);
        this.image_index = Math.min(this.number_of_images, this.image_index);
        if (this.number_of_images)
        {
            let first_image = this.images[this.image_index - 1];
            $(first_image).click();
        }
        let back_btn = document.getElementById('back-btn');
        back_btn.addEventListener('click', this.previous_image.bind(this));
        let next_btn = document.getElementById('next-btn');
        next_btn.addEventListener('click', this.next_image.bind(this));
        document.addEventListener('keydown', this.keydown.bind(this));
    }

    change(image, initialization=false)
    {
        let image_id = $(image).data('image');
        this.image_index = $(image).data('index');
        this.last_opened_page_handle();

        let previous_active_figure = $('.scrolling-wrapper .figure.active');
        if (previous_active_figure.length)
        {
            previous_active_figure.removeClass('active');
            $(previous_active_figure.children()[0]).css('background-color', 'white');
        }
        $(image).addClass('active');
        $($(image).children()[0]).css('background-color', '#ff00f2');

        const pageYOffset = window.pageYOffset;
        document.getElementsByClassName('figure m-1 active')[0].scrollIntoView({block: "nearest"});
        window.scrollTo(0, pageYOffset);

        this.change_url(initialization);

        for (let o of this.objects_to_change)
        {
            o.change_image(image_id)
        }
    }

    previous_image()
    {
        if ((this.image_index - 1) > 0)
        {
            this.image_index -= 1;
            $('.scrolling-wrapper .figure[data-index=' + this.image_index + ']').click();
            this.last_opened_page_handle();
            this.change_url();
        }
    }

    next_image()
    {
        if ((this.image_index + 1) <= this.number_of_images)
        {
            this.image_index += 1;
            $('.scrolling-wrapper .figure[data-index=' + this.image_index + ']').click();
            this.last_opened_page_handle();
            this.change_url();
        }
    }

    change_url(initialization=false){
        let image_id = $('.scrolling-wrapper .figure[data-index=' + this.image_index + ']')[0].getAttribute('data-image');
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

        if (counter == 1){
            let document_id = window.location.href.split('/').reverse()[0];
            window.history.replaceState({}, '','/ocr/show_results/'+document_id+'/'+image_id);
        }
        if (counter == 2){
            let document_id = window.location.href.split('/').reverse()[1];
            window.history.replaceState({}, '','/ocr/show_results/'+document_id+'/'+image_id);
        }
        if (counter == 3){
            let line_id = window.location.href.split('/').reverse()[0];
            let document_id = window.location.href.split('/').reverse()[2];
            if (initialization.isTrusted || initialization === false){
                window.history.replaceState({}, '','/ocr/show_results/'+document_id+'/'+image_id);
            }
            else{

                window.history.replaceState({}, '','/ocr/show_results/'+document_id+'/'+image_id+'/'+line_id);
            }
        }
    }

    keydown(e)
    {
        // LEFT ARROW
        if (e.keyCode == 37 && !e.ctrlKey && !e.shiftKey && e.altKey)
        {
            e.preventDefault();
            this.previous_image();
        }

        // RIGHT ARROW
        if (e.keyCode == 39 && !e.ctrlKey && !e.shiftKey && e.altKey)
        {
            e.preventDefault();
            this.next_image();
        }
    }

    last_opened_page_handle(initialization=false){
        var last_opened_page = window.localStorage.getItem('last_opened_page');

        let parsed_url = window.location.href.split('/').reverse();
        let counter = 0;
        for (let part of parsed_url) {
            if (part == 'show_results') {
                break;
            } else {
                counter += 1;
            }
        }

        var document_id;
        if (counter == 2){
            document_id = window.location.href.split("/").slice(-1)[1];
        }
        if (counter == 3){
            document_id = window.location.href.split("/").slice(-1)[2];
        }

        if (last_opened_page != null && last_opened_page != ''){
            var json_dict = JSON.parse(last_opened_page);
        }
        else {
            var json_dict = {};
        }

        if (initialization){
            if (json_dict.hasOwnProperty(document_id)){
                this.image_index = json_dict[document_id];
            }
            else {
                json_dict[document_id] = this.image_index;
            }
        }
        else {
            json_dict[document_id] = this.image_index;
        }

        window.localStorage.setItem('last_opened_page', JSON.stringify(json_dict));
    }
}
