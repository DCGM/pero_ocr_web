

class TextLine
{
    constructor(id, annotated, text, confidences, ligatures_mapping, arabic)
    {
        this.id = id;
        this.text = text;
        this.confidences = confidences;
        this.ligatures_mapping = ligatures_mapping;
        this.arabic = arabic;
        this.edited = false;
        this.annotated = annotated;

        this.container = document.createElement("div");
        this.container.setAttribute("class", "text-line");
        this.container.setAttribute("contentEditable", "true");
        this.container.style.lineHeight = "220%";

        if (this.arabic)
        {
            this.container.style.direction = "rtl";
            this.arabic_resharper = new ArabicReshaper();
            this.text = this.arabic_resharper.reshape(this.text);
        }

        this.container.addEventListener('keypress', this.press.bind(this));
        this.container.addEventListener('keydown', this.keydown.bind(this));
        this.container.addEventListener('paste', this.paste.bind(this));

        this.set_line_confidences_to_text_line_element();

        this.observer = new MutationObserver(this.mutate.bind(this));
        let config = { attributes: false, childList: true, characterData: true , subtree: true};
        this.observer.observe(this.container, config);
        this.mutate();
    }

    set_line_confidences_to_text_line_element()
    {
        let chars = this.text.split("");
        if (this.confidences.length)
        {
            this.confidences.forEach((confidence, index) =>
            {
                let char_span = document.createElement('span');
                char_span.setAttribute("style", "font-size: 150%; background: " + rgbToHex(255, Math.floor(confidence * 255),
                                                                                                Math.floor(confidence * 255)));
                for (let char_index of this.ligatures_mapping[index])
                {
                    char_span.innerHTML += chars[char_index];
                }
                this.container.appendChild(char_span);
            });
        }
    }

    clear_confidence_colors()
    {
        let descendants = this.container.getElementsByTagName('*');
        for (let child of descendants)
        {
            child.style.backgroundColor = "#ffffff";
        }
    }

    press(e)
    {
        if (e.keyCode == 13)
        {
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
            this.remove_selection_and_prepare_line_for_insertion()
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
            range.setEnd(last_span, last_span.innerHTML.length);
            selection.removeAllRanges();
            selection.addRange(range);
        }
    }

    paste(e)
    {
        e.preventDefault();
        var text = (e.originalEvent || e).clipboardData.getData('text/plain');
        this.remove_selection_and_prepare_line_for_insertion();
        document.execCommand("insertText", false, text);
    }

    mutate()
    {
        this.edited = this.text != this.get_text_content();
        if(this.edited){
            this.container.style.backgroundColor = "#ffcc54";
        } else if(this.annotated){
            this.container.style.backgroundColor = "#d0ffcf";
        } else {
            this.container.style.backgroundColor = "#ffffff";
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
        let empty_text_line_element = this.empty_text_line_element();
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
        let range = this.get_range();
        let selected_spans_length = range.cloneContents().children.length;
        let current_span = range.startContainer.parentNode;
        let first_span = current_span;
        let first_span_text = current_span.innerHTML;
        current_span.innerHTML = first_span_text.slice(0, range.startOffset);
        if (range.startContainer != range.endContainer)
        {
            current_span = current_span.nextSibling;
            for (let i = 1; i < selected_spans_length - 1; i++)
            {
                let previous_span = current_span;
                current_span = current_span.nextSibling;
                previous_span.remove();
            }
            let last_span = current_span;
            let last_span_text = last_span.innerHTML;
            last_span_text = last_span_text.slice(range.endOffset, last_span_text.length);
            if (last_span_text == "")
            {
                last_span.remove();
            }
            else
            {
                last_span.innerHTML = last_span_text;
            }
        }
        range.selectNodeContents(first_span);
        range.collapse(false);
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
        let previous_span = this.skip_invalid_previous_spans(caret_span);
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
        if (caret_span != next_span)
        {
            let span_to_move = this.get_span_to_move(next_span.previousSibling);
            selection.collapse(span_to_move, span_to_move.length);
            return true;
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
        //Firefox bug, doesn't delete span after pressing backspace
        if (caret_span.tagName != "SPAN")
        {
            caret_span = caret_span.parentNode;
        }
        // Anchor offset should be always 1 apart from caret on first position
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

    get_range()
    {
        return document.getSelection().getRangeAt(0);
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
        let self = this
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
      return filtered_text;
    }


}
