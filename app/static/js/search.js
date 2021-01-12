class SearchObject {
    constructor() {
        this.lines = document.getElementsByClassName("line");
        this.lines_images = document.getElementsByClassName("line_image");

        for (let i = 0; i < this.lines.length; i++){
            this.lines_images[i].setAttribute("src", Flask.url_for('document.get_cropped_image', {'line_id': this.lines[i].innerHTML}));
        }
    }
}