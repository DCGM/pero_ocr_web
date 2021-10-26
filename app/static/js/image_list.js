
class ImageList
{
    constructor(objects_to_change)
    {
        this.objects_to_change = objects_to_change;
        this.images = $('.scrolling-wrapper .figure');

        this.document_id = null;
        this.image_id = null;
        this.line_id = null;
        this.parse_url();

        this.image_index = 1;
        if (this.image_id != null){
            try {
                this.image_index = $("[data-image="+this.image_id+"]")[0].getAttribute('data-index');
            }
            catch(err) {

            }
            window.localStorage.setItem('last_opened_page_'+this.document_id, this.image_index);
        }
        else{
            let last_opened_page_idx = window.localStorage.getItem('last_opened_page_'+this.document_id);
            if (last_opened_page_idx != null){
                this.image_index = last_opened_page_idx;
            }
        }
        this.image_id = this.images[this.image_index - 1].getAttribute("data-image");

        for (let i of this.images)
        {
            i.addEventListener('click', this.change.bind(this, i));
        }
        this.number_of_images = this.images.length;
        this.image_index = Math.max(1, this.image_index);
        this.image_index = Math.min(this.number_of_images, this.image_index);
        if (this.number_of_images)
        {
            this.change(this.images[this.image_index-1], true);
        }
        let back_btn = document.getElementById('back-btn');
        back_btn.addEventListener('click', this.previous_image.bind(this));
        let next_btn = document.getElementById('next-btn');
        next_btn.addEventListener('click', this.next_image.bind(this));
        document.addEventListener('keydown', this.keydown.bind(this));
    }

    change(image, initialization=false)
    {
        this.image_id = $(image).data('image');
        this.image_index = $(image).data('index');
        if (initialization != true){
            this.line_id = null;
        }

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

        this.change_url();

        for (let o of this.objects_to_change)
        {
            o.change_image(this.image_id, this.change_url.bind(this), this.line_id)
        }
        window.localStorage.setItem('last_opened_page_'+this.document_id, this.image_index);
    }

    previous_image()
    {
        if ((this.image_index - 1) > 0)
        {
            this.image_index -= 1;
            $('.scrolling-wrapper .figure[data-index=' + this.image_index + ']').click();
        }
    }

    next_image()
    {
        if ((this.image_index + 1) <= this.number_of_images)
        {
            this.image_index += 1;
            $('.scrolling-wrapper .figure[data-index=' + this.image_index + ']').click();
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

    change_url(line_id=null){
        if (line_id != null){
            this.line_id = line_id;
        }

        let results_type;
        if (window.location.href.includes("ocr")){
            results_type = 'ocr';
        }
        else{
            results_type = 'layout_analysis';
        }
        let classic = false;
        if (window.location.href.includes("classic")){
            classic = true;
        }

        let show_results_url = classic? 'show_results_classic': 'show_results';

        if (this.line_id == null){
            window.history.replaceState({}, '','/'+results_type+'/'+ show_results_url +'/'+this.document_id+'/'+this.image_id);
        }
        else{
            window.history.replaceState({}, '','/'+results_type+'/'+ show_results_url +'/'+this.document_id+'/'+this.image_id+'/'+this.line_id);
        }
    }

    parse_url(){
         let parsed_url = window.location.href.split('/').reverse();
         let counter = 0;
         for (let part of parsed_url) {
            if (part == 'show_results' || part == 'show_results_classic'){
                break;
            }
            else{
                counter += 1;
            }
         }
         if (counter == 1){
             this.document_id = window.location.href.split('/').reverse()[0];
         }
         if (counter == 2){
             this.image_id = window.location.href.split('/').reverse()[0];
             this.document_id = window.location.href.split('/').reverse()[1];
         }
         if (counter == 3){
             this.line_id = window.location.href.split('/').reverse()[0];
             this.image_id = window.location.href.split('/').reverse()[1];
             this.document_id = window.location.href.split('/').reverse()[2];
         }
    }
}
