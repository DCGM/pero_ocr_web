
class ImageChange
{
    constructor(text_lines_editor)
    {
        this.text_lines_editor = text_lines_editor;
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
        let back_btn = document.getElementById('back-btn')
        back_btn.addEventListener('click', this.previous_page.bind(this));
        let next_btn = document.getElementById('next-btn')
        next_btn.addEventListener('click', this.next_page.bind(this));
    }

    change(image)
    {
        let document_id = $(image).data('document');
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

        document.getElementById('btn-export-page-xml').setAttribute("href", Flask.url_for('document.get_page_xml_lines', {'image_id': image_id}));
        document.getElementById('btn-export-alto-xml').setAttribute("href", Flask.url_for('document.get_alto_xml', {'image_id': image_id}));
        document.getElementById('btn-export-text').setAttribute("href", Flask.url_for('document.get_text', {'image_id': image_id}));
        document.getElementById('btn-export-img').setAttribute("href", Flask.url_for('document.get_image', {'image_id': image_id}));
        if (typeof this.text_lines_editor.lines !== 'undefined')
        {
            let unsaved_lines = false;
            for (let l of this.text_lines_editor.lines)
            {
                if (l.edited)
                {
                    unsaved_lines = true;
                }
            }
            if (unsaved_lines)
            {
                if (confirm("Save changes?"))
                {
                    this.text_lines_editor.save_annotations();
                }
            }
        }
        this.text_lines_editor.get_image(document_id, image_id)
    }

    previous_page()
    {
        if (this.image_index > 0)
        {
            this.image_index -= 1;
            $('.scrolling-wrapper .figure[data-index=' + this.image_index + ']').click();
        }
    }

    next_page()
    {
        if ((this.image_index + 1) < this.number_of_images)
        {
            this.image_index += 1;
            $('.scrolling-wrapper .figure[data-index=' + this.image_index + ']').click();
        }
    }
}
