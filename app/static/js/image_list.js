
class ImageList
{
    constructor(objects_to_change)
    {
        this.objects_to_change = objects_to_change;

        this.image_index = 0;
        this.images = $('.scrolling-wrapper .figure');
        for (let i of this.images)
        {
            i.addEventListener('click', this.change.bind(this, i));
        }
        this.number_of_images = this.images.length;
        if (this.number_of_images)
        {
            let first_image = this.images[0];
            $(first_image).click();
        }
        let back_btn = document.getElementById('back-btn');
        back_btn.addEventListener('click', this.previous_image.bind(this));
        let next_btn = document.getElementById('next-btn');
        next_btn.addEventListener('click', this.next_image.bind(this));
        document.addEventListener('keydown', this.keydown.bind(this));
    }

    change(image)
    {
        let image_id = $(image).data('image');
        this.image_index = $(image).data('index');

        let previous_active_figure = $('.scrolling-wrapper .figure.active');
        if (previous_active_figure.length)
        {
            previous_active_figure.removeClass('active');
            $(previous_active_figure.children()[0]).css('background-color', 'white');
        }
        $(image).addClass('active');
        $($(image).children()[0]).css('background-color', '#ff00f2');
        document.getElementsByClassName('figure m-1 active')[0].scrollIntoView();
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
}
