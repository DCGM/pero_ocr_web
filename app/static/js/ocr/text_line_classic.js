

class TextLine
{
    constructor(id, annotated, text, confidences, ligatures_mapping, arabic, for_training, debug_line_container,
                debug_line_container_2)
    {
        this.id = id;
        this.text = text;
        this.confidences = confidences;
        this.line_confidence = 0;
        this.ligatures_mapping = ligatures_mapping;
        this.arabic = arabic;
        this.debug_line_container = debug_line_container;
        this.debug_line_container_2 = debug_line_container_2;
        this.edited = false;
        this.annotated = annotated;
        this.valid = true;
        this.for_training = for_training;
        this.for_training_checkbox = null;

        this.container = document.createElement("span");
        this.container.setAttribute("class", "text-line");
        this.container.setAttribute("contentEditable", "true");
        this.container.setAttribute("data-uuid", id);
        this.container.style.display = "block";
        this.container.style.lineHeight = "220%";

        if(confidences.length > 0){
            var power_const = 5;
            for(var c of this.confidences){
                this.line_confidence += (1 - c) ** power_const;
            }
            this.line_confidence = 1 - (this.line_confidence / this.confidences.length) ** (1.0/power_const)
        } else {
            this.line_confidence = 1;
        }

        let text_to_show = "";
        let confidences_to_show = [];
        if (this.arabic)
        {
            this.container.style.direction = "rtl";
            this.arabic_reshaper = new ArabicReshaper();
            let values = this.arabic_reshaper.reverse(this.text, this.confidences);
            text_to_show = values[0];
            confidences_to_show = values[1];
            text_to_show = this.arabic_reshaper.label_to_visual_form(text_to_show);
            this.current_text = "";
        }
        else
        {
            text_to_show = this.text;
            confidences_to_show = this.confidences;
        }

        this.container.addEventListener('focus', this.focus.bind(this));
        this.container.addEventListener('keypress', this.press.bind(this));
        this.container.addEventListener('keydown', this.keydown.bind(this));
        this.container.addEventListener('paste', this.paste.bind(this));

        this.set_line_confidences_to_text_line_element(text_to_show, confidences_to_show);

        this.text = this.get_text_content();
        this.set_training_checkbox();

        this.observer = new MutationObserver(this.mutate.bind(this));
        let config = { attributes: false, childList: true, characterData: true , subtree: true};
        this.observer.observe(this.container, config);
        this.mutate();
    }

    set_training_checkbox(){
        this.checkbox_span = document.createElement("span");
        this.for_training_checkbox = document.createElement("input");

        this.checkbox_span.setAttribute("style", "float: right;");
        this.checkbox_span.setAttribute("data-uuid", this.id);

        this.for_training_checkbox.setAttribute("type", "checkbox");
        this.for_training_checkbox.setAttribute("tabindex", "-1");
        this.for_training_checkbox.setAttribute("title", "training line");
        this.for_training_checkbox.setAttribute("style", "margin-right: 10px; vertical-align: -webkit-baseline-middle; filter: hue-rotate(-30deg)");
        this.for_training_checkbox.setAttribute("contenteditable", "false");
        this.for_training_checkbox.checked = this.for_training;

        this.checkbox_span.appendChild(this.for_training_checkbox);
        this.checkbox_span.setAttribute("tabindex", "-1");
    }

    set_line_confidences_to_text_line_element(text_to_show, confidences_to_show)
    {
        let chars = text_to_show.split("");
        this.ligatures_mapping.forEach((ligature_mapping, index) =>
        {
            let char_span = document.createElement('span');
            char_span.style.fontSize = "150%";
            let ligature_confidences = [];
            for (let char_index of ligature_mapping)
            {
                if (confidences_to_show.length)
                {
                    ligature_confidences.push(confidences_to_show[index])
                }
                char_span.innerHTML += chars[char_index];
            }
            if (ligature_confidences.length)
            {
                let span_confidence = Math.min(ligature_confidences);
                char_span.style.backgroundColor = rgbToHex(255, Math.floor(span_confidence * 255),
                                                                Math.floor(span_confidence * 255));
            }
            else
            {
                char_span.style.backgroundColor = "#ffffff";
            }
            /*
            if (ligature_mapping.length > 1)
            {
                char_span.style.backgroundColor = "#d9f5ff";
            }
            */
            this.container.appendChild(char_span);
        });
    }

    clear_confidence_colors()
    {
        let descendants = this.container.getElementsByTagName('*');
        for (let child of descendants)
        {
            if (child.nodeName != 'DIV'){
                child.style.backgroundColor = "#ffffff";
            }
        }
    }

    convert_to_visual_form()
    {
        let text = this.get_text_content();
        if (text == this.current_text)
        {
            return;
        }
        else
        {
            this.current_text = JSON.parse(JSON.stringify(text));
        }
        if ((!text || 0 === text.length))
        {
            return;
        }

        let letter_indexes_to_spans_mapping = this.get_letter_indexes_to_spans_mapping();

        let label_text = this.arabic_reshaper.reverse(text, []);
        label_text = label_text[0];
        let letter_indexes_to_ligatures_mapping = this.arabic_reshaper.get_letter_indexes_to_ligatures_mapping(label_text);
        letter_indexes_to_spans_mapping = this.get_merged_letter_indexes_to_spans_and_ligatures_mapping(letter_indexes_to_spans_mapping, letter_indexes_to_ligatures_mapping);

        let visual_text = this.arabic_reshaper.label_to_visual_form(label_text);

        this.container.innerHTML = "";

        for (let span_letter_indexes of letter_indexes_to_spans_mapping)
        {
            let span = document.createElement('span');
            span.style.fontSize = "150%";
            if ('user_input' in span_letter_indexes)
            {
                span.setAttribute("class", "user-input");
                span.style.backgroundColor = "#ffffff";
                span.style.color = "#028700";
            }
            else
            {
                span.style.backgroundColor = rgbToHex(255, span_letter_indexes['color'], span_letter_indexes['color']);
                /*
                if (span_letter_indexes['indexes'].length > 1)
                {
                    span.style.backgroundColor = "#d9f5ff";
                }
                */
            }
            let span_text = ""
            for (let letter_index of span_letter_indexes['indexes'])
            {
                let char = visual_text.charAt(letter_index);
                if (char == ' ')
                {
                    char = '&nbsp;';
                }
                span_text += char;
            }
            span.innerHTML = span_text;
            this.container.appendChild(span);
            if ('caret_offset' in span_letter_indexes)
            {
                let selection = document.getSelection();
                selection.collapse(span.childNodes[0], span_letter_indexes['caret_offset']);
            }
        }
    }

    get_letter_indexes_to_spans_mapping()
    {
        let caret_span = this.get_caret_span();
        let letter_indexes_to_spans_mapping = [];
        let letter_index = 0;
        for (let i = 0; i < this.container.children.length; ++i)
        {
            let span = this.container.children[i];
            let span_text_length = span.textContent.length;
            if (span_text_length > 0)
            {
                let rgb = span.style.backgroundColor;
                let color = 255;
                if (rgb != "")
                {
                    rgb = rgb.substring(4, rgb.length-1).replace(/ /g, '').split(',');
                    color = parseInt(rgb[1]);
                }
                let span_letter_indexes = {'indexes':[], 'color': color}
                if ($(span).hasClass('user-input'))
                {
                    span_letter_indexes['user_input'] = true;
                }
                if (span == caret_span)
                {
                    span_letter_indexes['caret_offset'] = this.get_range().startOffset;
                }
                for (let j = 0; j < span_text_length; ++j)
                {
                    span_letter_indexes['indexes'].push(letter_index);
                    letter_index += 1;
                }
                letter_indexes_to_spans_mapping.push(span_letter_indexes);
            }
        }
        return letter_indexes_to_spans_mapping;
    }

    get_merged_letter_indexes_to_spans_and_ligatures_mapping(letter_indexes_to_spans_mapping, letter_indexes_to_ligatures_mapping)
    {
        let current_letter_indexes_to_spans_mapping = JSON.parse(JSON.stringify(letter_indexes_to_spans_mapping));
        let new_letter_indexes_to_spans_mapping = [];
        for (let ligature_indexes of letter_indexes_to_ligatures_mapping)
        {
            new_letter_indexes_to_spans_mapping = [];
            let start_ligature_index = ligature_indexes[0];
            let end_ligature_index = ligature_indexes[1];
            let inside_ligature = false;
            let caret_in_span = false;
            let caret_offset = 0;
            let new_span_letter_indexes = {'indexes':[], 'color': 255}
            for (let span_letter_indexes of current_letter_indexes_to_spans_mapping)
            {
                if ('user_input' in span_letter_indexes)
                {
                    new_span_letter_indexes['user_input'] = true;
                    new_span_letter_indexes['color'] = 255;
                }
                if ('caret_offset' in span_letter_indexes)
                {
                    caret_in_span = true;
                    caret_offset += span_letter_indexes['caret_offset'];
                }
                if (!new_span_letter_indexes['user_input'])
                {
                    if (new_span_letter_indexes['color'] > span_letter_indexes['color'])
                    {
                        new_span_letter_indexes['color'] = span_letter_indexes['color'];
                    }
                }
                for (let letter_index of span_letter_indexes['indexes'])
                {
                    if (letter_index == start_ligature_index)
                    {
                        inside_ligature = true;
                    }
                    if (letter_index == end_ligature_index)
                    {
                        inside_ligature = false;
                    }
                    new_span_letter_indexes['indexes'].push(letter_index);
                    if (!caret_in_span)
                    {
                        caret_offset += 1;
                    }
                }
                if (!inside_ligature)
                {
                    if (caret_in_span)
                    {
                        new_span_letter_indexes['caret_offset'] = caret_offset;
                        caret_in_span = false;
                    }
                    new_letter_indexes_to_spans_mapping.push(new_span_letter_indexes);
                    new_span_letter_indexes = {'indexes':[], 'color': 255};
                    caret_offset = 0;
                }
            }
            current_letter_indexes_to_spans_mapping = JSON.parse(JSON.stringify(new_letter_indexes_to_spans_mapping));
        }
        return current_letter_indexes_to_spans_mapping;
    }

    focus(e)
    {
        this.show_line_in_debug_line_container();
    }

    press(e)
    {
        if (e.keyCode === 13) {  // Enter
            e.preventDefault();
            this.save();
        }

        // Skip
        // TAB (9)
        // ENTER (13)
        // CTRL+S (19)
        // CTRL+Y (25)
        // CTRL+Z (26)
        if (e.keyCode != 9 &&
            e.keyCode != 13 &&
            e.keyCode != 19 &&
            e.keyCode != 25 &&
            e.keyCode != 26)
        {
            this.remove_selection_and_prepare_line_for_insertion();
            // Chrome has a BUG. It inserts ' ' as a nested <font> tag.
            if (e.keyCode == 32){
                e.preventDefault();
                document.execCommand("insertHTML", false, '&nbsp;');
            }
        }
    }

    keydown(e)
    {
        let empty_text_line_element = this.empty_text_line_element();
        let isFirefox = typeof InstallTrigger !== 'undefined';

        // LEFT ARROW
        if (e.keyCode == 37 && !e.ctrlKey && !e.shiftKey && !empty_text_line_element)
        {
            e.preventDefault();
            if (!this.arabic)
            {
                this.move_caret_to_the_left();
            }
            else
            {
                this.move_caret_to_the_right();
            }
        }

        // RIGHT ARROW
        if (e.keyCode == 39 && !e.ctrlKey && !e.shiftKey && !empty_text_line_element)
        {
            e.preventDefault();
            if (!this.arabic)
            {
                this.move_caret_to_the_right();
            }
            else
            {
                this.move_caret_to_the_left();
            }
        }

        // BACKSPACE
        if (e.keyCode == 8 && !empty_text_line_element)
        {
            if (this.text_selected())
            {
                e.preventDefault();
                this.remove_selection_and_set_caret();
            }
            else
            {
                if (!this.set_caret_before_actual_char_for_backspace())
                {
                    e.preventDefault();
                }
            }
        }

        // DELETE
        if (e.keyCode == 46 && !empty_text_line_element)
        {
            if (this.text_selected())
            {
                e.preventDefault();
                this.remove_selection_and_set_caret();
            }
            else
            {
                if (!isFirefox)
                {
                    if (!this.set_caret_before_actual_char_for_delete())
                    {
                        e.preventDefault();
                    }
                }
            }
        }

        // CTRL + A
        if (e.ctrlKey && e.keyCode == 65 && !empty_text_line_element)
        {
            e.preventDefault();
            let selection = document.getSelection();
            let range = selection.getRangeAt(0);
            let first_span = this.container.childNodes[0];
            range.setStart(first_span, 0);
            let last_span = this.container.childNodes[this.container.childNodes.length - 1];
            range.setEnd(last_span, 1);
            selection.removeAllRanges();
            selection.addRange(range);
        }
    }

    paste(e)
    {
        e.preventDefault();
        var text = (e.originalEvent || e).clipboardData.getData('text/plain');
        let nbsp_text = "";
        for (let c of text)
        {
            if (c == ' ')
            {
                nbsp_text += '&nbsp;';
            }
            else
            {
                nbsp_text += c
            }
        }
        this.remove_selection_and_prepare_line_for_insertion();
        document.execCommand("insertHTML", false, nbsp_text);
    }

    mutate()
    {
        if (this.arabic)
        {
            this.convert_to_visual_form();
        }
        this.edited = this.text != this.get_text_content();
        if (this.edited)
        {
            this.container.style.backgroundColor = "#ffcc54";
            this.show_line_in_debug_line_container();
        }
        else if (this.annotated)
        {
            this.container.style.backgroundColor = "#d0ffcf";
        }
        else
        {
            this.container.style.backgroundColor = "#ffffff";
        }
        if (this.valid == false){
            this.container.style.backgroundColor = "#dc7f88";
        }
    }

    remove_selection_and_prepare_line_for_insertion()
    {
        if (this.text_selected())
        {
            this.remove_selection_and_set_caret();
        }
        this.prepare_line_for_insertion();
    }

    // Creates new user-input span if needed
    prepare_line_for_insertion()
    {
        // We can detele line if it has no text - suprisingly, CTRL-Z still works.
        let empty_text_line_element = this.container.textContent === "";
        let caret_span;
        if (empty_text_line_element)
        {
            $(this.container).html('');
            caret_span = this.container;
        }
        else
        {
            caret_span = this.get_caret_span();
        }
        if (caret_span.getAttribute("class") != "user-input")
        {
            console.log("huhuhuh");
            // Create new span for new char
            // Set it's content to &#8203; special empty char so caret can be set inside
            let new_span = document.createElement('span');
            new_span.setAttribute("class", "user-input");
            new_span.setAttribute("style", "font-size: 150%; background: #ffffff; color: #028700");
            new_span.innerHTML = "&#8203;";
            if (empty_text_line_element)
            {
                caret_span.appendChild(new_span);
            }
            else
            {
                if (this.check_caret_is_at_the_beginning_of_the_first_span(caret_span))
                {
                    caret_span.parentNode.insertBefore(new_span, caret_span);
                }
                else
                {
                    console.log("new span");
                    caret_span.parentNode.insertBefore(new_span, caret_span.nextSibling);
                }
            }
            let selection = document.getSelection();
            let range = selection.getRangeAt(0);
            range.selectNodeContents(new_span.childNodes[0]);
            selection.removeAllRanges();
            selection.addRange(range);
        }
    }

    remove_selection_and_set_caret()
    {
        document.execCommand('delete', false, null);
    }

    move_caret_to_the_left()
    {
        let selection = document.getSelection();
        // moving caret to the left but caret is not on the first char in span (just move the caret normally)
        if (selection.anchorOffset > 1)
        {
            selection.collapse(selection.anchorNode, selection.anchorOffset - 1);
            return;
        }
        let caret_span = this.get_caret_span();
        let previous_span = this.get_previous_valid_span();
        if (previous_span)
        {
            let span_to_move;
            if (previous_span.childNodes.length)
            {
                span_to_move = previous_span.childNodes[0];
            }
            else
            {
                span_to_move = previous_span;
            }
            selection.collapse(span_to_move, span_to_move.length);
        }
        else
        {
            selection.collapse(this.get_span_to_move(caret_span), 0);
        }
        return;
    }

    move_caret_to_the_right()
    {
        let selection = document.getSelection();
        // moving caret to the right but caret is not on the last char in span (just move the caret normally)
        if (selection.anchorNode.length - selection.anchorOffset > 0)
        {
            selection.collapse(selection.anchorNode, selection.anchorOffset + 1);
            return;
        }
        let caret_span = this.get_caret_span();
        let caret_at_the_beginning_of_the_first_span = this.check_caret_is_at_the_beginning_of_the_first_span(caret_span);
        let valid_current_span = false;
        if (caret_at_the_beginning_of_the_first_span)
        {
            valid_current_span = ((caret_span.innerHTML.charCodeAt(0) != 8203) && (caret_span.innerHTML != ""));
        }
        let next_span = this.get_next_valid_span();
        if (next_span && !(valid_current_span && caret_at_the_beginning_of_the_first_span))
        {
            selection.collapse(this.get_span_to_move(next_span), 1);
            return;
        }
        return;
    }

    set_caret_before_actual_char_for_backspace()
    {
        let selection = document.getSelection();
        let caret_span = this.get_caret_span();
        if (this.check_caret_is_at_the_beginning_of_the_first_span(caret_span))
        {
            return false;
        }
        let previous_span = this.skip_previous_invalid_spans(caret_span);
        if (previous_span == caret_span)
        {
            return true;
        }
        if (previous_span)
        {
            let span_to_move = this.get_span_to_move(previous_span);
            selection.collapse(span_to_move, span_to_move.length);
            return true;
        }
        return false;
    }

    set_caret_before_actual_char_for_delete()
    {
        let selection = document.getSelection();
        if (selection.anchorNode.length - selection.anchorOffset > 0)
        {
            return true;
        }
        let caret_span = this.get_caret_span();
        let next_span = this.skip_next_invalid_spans(caret_span.nextSibling);
        if (next_span != null) {
            if (caret_span != next_span)
            {
                let span_to_move = this.get_span_to_move(next_span.previousSibling);
                selection.collapse(span_to_move, span_to_move.length);
                return true;
            }
        }
        return false;
    }

    get_previous_valid_span()
    {
        let caret_span = this.get_caret_span();
        let previous_span = caret_span.previousSibling;
        return this.skip_previous_invalid_spans(previous_span);
    }

    skip_previous_invalid_spans(previous_span)
    {
        while (previous_span)
        {
            let skip_span = ((previous_span.innerHTML.charCodeAt(0) == 8203) || (previous_span.innerHTML == ""));
            if (skip_span)
            {
                previous_span = previous_span.previousSibling;
            }
            else
            {
                break;
            }
        }
        return previous_span;
    }

    get_next_valid_span()
    {
        let caret_span = this.get_caret_span();
        let next_span = caret_span.nextSibling;
        return this.skip_next_invalid_spans(next_span);
    }

    skip_next_invalid_spans(next_span)
    {
        while (next_span)
        {
            let skip_span = ((next_span.innerHTML.charCodeAt(0) == 8203) || (next_span.innerHTML == ""));
            if (skip_span)
            {
                next_span = next_span.nextSibling;
            }
            else
            {
                break;
            }
        }
        return next_span;
    }

    get_span_to_move(caret_span)
    {
        let span_to_move;
        if (caret_span.childNodes.length)
        {
            span_to_move = caret_span.childNodes[0];
        }
        else
        {
            span_to_move = caret_span;
        }
        return span_to_move;
    }

    get_caret_span()
    {
        //let selection = document.getSelection();
        //let range = selection.getRangeAt(0);
        //let caret_span = range.endContainer;
        let selection = document.getSelection();
        let caret_span = selection.anchorNode;
        if (!caret_span)
        {
            return false;
        }
        //Firefox bug, doesn't delete span after pressing backspace
        if (caret_span.tagName != "SPAN")
        {
            caret_span = caret_span.parentNode;
        }
        // Anchor offset should be always higher than one apart from caret on the first position
        if (selection.anchorOffset == 0 && selection.anchorNode.length > 0)
        {
            // Firefox bug, anchor offset is 0 but caret element is not the first element
            if (caret_span.previousSibling)
            {
                caret_span = caret_span.previousSibling;
            }
        }
        return caret_span;
    }

    check_caret_is_at_the_beginning_of_the_first_span(caret_span)
    {
        let selection = document.getSelection();
        if (selection.anchorOffset == 0)
        {
            if (!caret_span.previousSibling)
            {
                return true;
            }
        }
        return false;
    }

    text_selected()
    {
        let range = this.get_range();
        //console.log(range.startContainer, range.endContainer, range.startOffset, range.endOffset);
        if (range != null){
            if (range.startContainer != range.endContainer)
            {
                return true;
            }
            else
            {
                if (range.startOffset != range.endOffset)
                {
                    return true;
                }
            }
        }
        return false;
    }

    empty_text_line_element()
    {
        if (this.get_text_content() == "")
        {
            return true;
        }
        return false;
    }

    get_range() {
        var sel = document.getSelection()
        if (sel && sel.rangeCount > 0) {
            return sel.getRangeAt(0);
        }
        return null;
    }

    save()
    {
        let annotations = [];
        let annotation_dict = {};
        let new_text = this.get_text_content();
        let this_text_line = this;
        annotation_dict["id"] = this.id;
        annotation_dict["text_original"] = this.text;
        annotation_dict["text_edited"] = new_text;
        annotations.push(annotation_dict);
        console.log(annotations);
        console.log(JSON.stringify(annotations));
        let route = Flask.url_for('ocr.save_annotations');
        let self = this;
        $.ajax({
            type: "POST",
            url: route,
            data: {annotations: JSON.stringify(annotations)},
            dataType: "json",
            success: function(data, textStatus) {
                if (data.status == 'redirect') {
                    // data.redirect contains the string URL to redirect to
                    window.location.href = data.href;
                } else {
                    this_text_line.text = new_text;
                    self.annotated = true;
                    self.clear_confidence_colors();
                    self.mutate();
                    // self.notify_line_validated();  // Notify text line editor -> line validated by user and saved successfully
                }
            },
            error: function(xhr, ajaxOptions, ThrownError){
                alert('Unable to save annotation. Check your remote connection. ');
            }
        });
    }

    skip()
    {
        let route = Flask.url_for('document.skip_line', {'line_id': this.id});
        $.get(route);
    }

    get_text_content()
    {
        let text = this.container.textContent;
        let filtered_text = "";
        for (let i = 0; i < text.length; i++)
        {
            let charCode = text.charCodeAt(i);
            if (charCode == 160)
            {
              filtered_text += " ";
            }
            if (charCode != 160 && charCode != 8203)
            {
              filtered_text += text.charAt(i);
            }
        }
        if (this.arabic)
        {
            filtered_text = this.arabic_reshaper.visual_to_label_form(filtered_text);
            filtered_text = this.arabic_reshaper.reverse(filtered_text, []);
            filtered_text = filtered_text[0];
        }
        return filtered_text;
    }

    show_line_in_debug_line_container()
    {
        if (!(this.debug_line_container && this.debug_line_container_2))
        {
            return;
        }
        let text = this.container.textContent;
        let filtered_text = "";
        for (let i = 0; i < text.length; i++)
        {
            let charCode = text.charCodeAt(i);
            if (charCode == 160)
            {
              filtered_text += " ";
            }
            if (charCode != 160 && charCode != 8203)
            {
              filtered_text += text.charAt(i);
            }
        }
        text = filtered_text;
        if ((!text || 0 === text.length))
        {
            return;
        }
        let this_debug_line_container = this.debug_line_container;
        let this_debug_line_container_2 = this.debug_line_container_2;

        if (this.arabic)
        {
            let route = Flask.url_for('ocr.get_arabic_label_form', {"text": encodeURIComponent(text)});
            $.ajax({
            type: "GET",
            url: route,
            success: function(data, textStatus) {
                this_debug_line_container.innerHTML = data;
            },
            error: function(xhr, ajaxOptions, ThrownError){
                alert('Error in callback for show_line_in_debug_line_container().');
                }
            });
            let values = this.get_text_content();
            this_debug_line_container_2.innerHTML = this.arabic_reshaper.visual_to_label_form(text);
            //let l = this.arabic_reshaper.reverse(this.arabic_reshaper.visual_to_label_form(this.text));
            //for (let c of l)
            //{
            //    let span = document.createElement('span');
            //    span.innerHTML = c;
            //    this_debug_line_container_2.appendChild(span);
            //}
        }
        return;
    }

    hexToRgb(hex) {
        var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
            } : null;
    }
}
