

class TextLine
{
    constructor(id, document_id, text, confidences)
    {
        this.id = id;
        this.document_id = document_id;
        this.text = text;
        this.confidences = confidences;
        this.edited = false;
        this.saved = false;

        this.container = document.createElement("div");
        this.container.setAttribute("class", "text-line");
        this.container.setAttribute("contentEditable", "true");
        this.container.style.lineHeight = "220%";

        this.container.addEventListener('keypress', this.press.bind(this));
        this.container.addEventListener('keydown', this.keydown.bind(this));
        this.container.addEventListener('paste', this.paste.bind(this));

        this.set_line_confidences_to_text_line_element();

        this.observer = new MutationObserver(this.mutate.bind(this));
        let config = { attributes: false, childList: true, characterData: true };
        this.observer.observe(this.container, config);
    }

    set_line_confidences_to_text_line_element()
    {
        let chars = this.text.split("");
        for (let i in this.confidences)
        {
            let char_span = document.createElement('span');
            char_span.setAttribute("style", "font-size: 150%; background: " + rgbToHex(255, Math.floor(this.confidences[i] * 255),
                                                                                            Math.floor(this.confidences[i] * 255)));
            char_span.innerHTML = chars[i];
            this.container.appendChild(char_span);
        }
    }

    set_background_to_annotated()
    {
        this.container.style.backgroundColor = "#d0ffcf";
    }

    set_background_to_save()
    {
        this.set_background_to_annotated();
        let descendants = this.container.getElementsByTagName('*');
        for (let child of descendants)
        {
            child.style.backgroundColor = "#ffffff";
        }
    }

    press(e)
    {
        e.preventDefault();

        if (e.keyCode == 13)
        {
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
            this.insert_new_char_to_current_position(String.fromCharCode(e.keyCode));
        }
    }

    keydown(e)
    {
        let empty_text_line_element = !($(this.container).has('span').length);

        // LEFT ARROW
        if (e.keyCode == 37 && !e.ctrlKey && !e.shiftKey && !empty_text_line_element)
        {
            e.preventDefault();
            this.skip_all_empty_spans_to_the_left()
        }

        // RIGHT ARROW
        if (e.keyCode == 39 && !e.ctrlKey && !e.shiftKey && !empty_text_line_element)
        {
            e.preventDefault();
            this.skip_all_empty_spans_to_the_right();
        }

        // BACKSPACE
        if (e.keyCode == 8 && !empty_text_line_element)
        {
            let selection = document.getSelection();
            let range = selection.getRangeAt(0);
            let text_selected = range.cloneContents().children.length;
            if (text_selected)
            {
                insert_new_char_to_current_position("&#8203;")
                e.preventDefault();
            }
            else
            {
                if (!this.set_caret_before_actual_char())
                {
                    e.preventDefault();
                }
            }
        }
    }

    paste(e)
    {
        e.preventDefault();
        let text = (e.originalEvent || e).clipboardData.getData('text/plain');
        for (let i = 0; i < text.length; i++)
        {
            this.insert_new_char_to_current_position(text.charAt(i));
        }
    }

    mutate()
    {
        this.edited = true;
        this.saved = false;
        this.container.style.backgroundColor = "#ffcc54";
    }

    insert_new_char_to_current_position(char)
    {
        let empty_text_line_element = !($(this.container).has('span').length);
        if (empty_text_line_element)
        {
            $(this.container).html('');
        }

        // Insert nonbreaking space instead of normal space (more robust)
        if (char == " ")
        {
          char = "&nbsp;";
        }

        let selection = document.getSelection();
        let range = selection.getRangeAt(0);
        let text_selected = range.cloneContents().children.length;

        let start_span;
        let end_span;

        let caret_element;
        let caret_before_first_span = false;

        if (empty_text_line_element)
        {
            caret_element = this.container;
        }
        else
        {
            caret_element = this.get_caret_span();
            caret_before_first_span = this.check_caret_before_first_span(caret_element);

            // If text is selected remove it
            // Removal of selection keeps two empty spans, store them for deletion
            if (text_selected)
            {
                start_span = range.startContainer.parentNode;
                end_span = range.endContainer.parentNode;
                range.deleteContents();
            }
        }

        // Create new span for new char
        // Set it's content to &#8203; special empty char so caret can be set inside
        let new_span = document.createElement('span');
        new_span.setAttribute("style", "font-size: 150%; background: #ffffff; color: #028700");
        new_span.innerHTML = "&#8203;";

        if (empty_text_line_element)
        {
            caret_element.appendChild(new_span);
        }
        else
        {
            if (caret_before_first_span)
            {
                caret_element.parentNode.insertBefore(new_span, caret_element);
            }
            else
            {
                caret_element.parentNode.insertBefore(new_span, caret_element.nextSibling);
            }
        }


        // Set range (selection) on content of new span &#8203
        range.selectNodeContents(new_span.childNodes[0]);
        selection.removeAllRanges();
        selection.addRange(range);

        let isFirefox = typeof InstallTrigger !== 'undefined';
        if (isFirefox)
        {
            new_span = document.createElement('span');
            new_span.setAttribute("style", "font-size: 150%; background: #ffffff; color: #028700");
            new_span.innerHTML = char;

            // Replace current span with new span
            document.execCommand("insertHTML", false, new_span.outerHTML);
        }
        else
        {
            // Replace the content (&#8203) of current new span
            document.execCommand("insertHTML", false, char);
        }

        // Usage of &#8203 and execCommand ensures that CTRL+Z and CTRL+Y works
        // properly. After pressing CTRL+Z the char is replaced by &#8203 and after
        // pressing CTRL+Y the &#8203 is replaced with the char.

        // Remove empty spans
        if (text_selected)
        {
            start_span.remove();
            end_span.remove();
        }
    }

    skip_all_empty_spans_to_the_left()
    {
        let caret_span = this.get_caret_span();
        let previous_span = caret_span;
        while (previous_span)
        {
            let skip_span = ((previous_span.innerHTML.charCodeAt(0) == 8203) || (previous_span.innerHTML == ""));

            if (skip_span)
            {
                if (previous_span.previousSibling)
                {
                    previous_span = previous_span.previousSibling;
                }
                else
                {
                    break;
                }
            }
            else
            {
                break;
            }
        }
        let selection = document.getSelection();
        let range = selection.getRangeAt(0);
        if (previous_span.previousSibling)
        {
            if (previous_span.previousSibling.childNodes.length)
            {
                range.selectNodeContents(previous_span.previousSibling.childNodes[0]);
            }
            else
            {
                range.selectNodeContents(previous_span.previousSibling);
            }
            range.collapse(false);
        }
        else
        {
            if (previous_span.childNodes.length)
            {
                range.selectNodeContents(previous_span.childNodes[0]);
            }
            else
            {
                range.selectNodeContents(previous_span);
            }
            range.collapse(true);
        }
        selection.removeAllRanges();
        selection.addRange(range);
    }

    select_span_to_the_left()
    {
        let caret_span = this.get_caret_span();
        let previous_span = caret_span;
        while (previous_span)
        {
            let skip_span = ((previous_span.innerHTML.charCodeAt(0) == 8203) || (previous_span.innerHTML == ""));

            if (skip_span)
            {
                if (previous_span.previousSibling)
                {
                    previous_span = previous_span.previousSibling;
                }
                else
                {
                    break;
                }
            }
            else
            {
                break;
            }
        }
        let selection = document.getSelection();
        let range = selection.getRangeAt(0);
        console.log(selection);
        if (previous_span.previousSibling)
        {
            if (previous_span.previousSibling.childNodes.length)
            {
                range.setStartAfter(previous_span.previousSibling.childNodes[0]);
            }
            else
            {
                range.setStartAfter(previous_span.previousSibling);
            }
        }
        else
        {
            if (previous_span.childNodes.length)
            {
                range.setStartAfter(previous_span.childNodes[0]);
            }
            else
            {
                range.setStartAfter(previous_span);
            }
        }
        selection.removeAllRanges();
        selection.addRange(range);
    }

    skip_all_empty_spans_to_the_right()
    {
        let caret_span = this.get_caret_span();
        let caret_before_first_span = this.check_caret_before_first_span(caret_span);
        let valid_current_span = false;
        if (caret_before_first_span)
        {
            valid_current_span = ((caret_span.innerHTML.charCodeAt(0) != 8203) && (caret_span.innerHTML != ""));
        }
        let next_span = caret_span;
        if (caret_span.nextSibling && !valid_current_span)
        {
            next_span = caret_span.nextSibling;
            while (next_span)
            {
                let skip_span = ((next_span.innerHTML.charCodeAt(0) == 8203) || (next_span.innerHTML == ""));
                if (skip_span)
                {
                    if (next_span.nextSibling)
                    {
                        next_span = next_span.nextSibling;
                    }
                    else
                    {
                        break;
                    }
                }
                else
                {
                    break;
                }
            }
        }
        let selection = document.getSelection();
        let range = selection.getRangeAt(0);
        if (next_span.childNodes.length)
        {
            range.selectNodeContents(next_span.childNodes[0]);
        }
        else
        {
            range.selectNodeContents(next_span);
        }
        range.collapse(false);
        selection.removeAllRanges();
        selection.addRange(range);
    }

    set_caret_before_actual_char()
    {
        let caret_span = this.get_caret_span();
        let caret_before_first_span = this.check_caret_before_first_span(caret_span);
        let previous_span = caret_span;
        let valid_span_char = false;
        while (previous_span)
        {
            let skip_span = ((previous_span.innerHTML.charCodeAt(0) == 8203) || (previous_span.innerHTML == ""));

            if (skip_span)
            {
                if (previous_span.previousSibling)
                {
                    previous_span = previous_span.previousSibling;
                }
                else
                {
                    break;
                }
            }
            else
            {
                valid_span_char = true;
                break;
            }
        }
        let selection = document.getSelection();
        let range = selection.getRangeAt(0);
        if (valid_span_char && !caret_before_first_span)
        {
            range.selectNodeContents(previous_span.childNodes[0]);
            range.collapse(false);
            selection.removeAllRanges();
            selection.addRange(range);
            return true;
        }
        else
        {
            return false;
        }
    }

    get_caret_span()
    {
        let selection = document.getSelection();
        let caret_span = selection.anchorNode;
        //Firefox bug, doesn't delete span after pressing backspace
        if (caret_span.tagName != "SPAN")
        {
            caret_span = caret_span.parentNode;
        }
        // Anchor offset should be always 1 apart from caret on first position
        if (selection.anchorOffset == 0)
        {
            // Firefox bug, anchor offset is 0 but caret element is not the first element
            if (caret_span.previousSibling)
            {
                caret_span = caret_span.previousSibling;
            }
        }
        return caret_span;
    }

    check_caret_before_first_span(caret_span)
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

    save()
    {
        let annotations = [];
        let annotation_dict = {};
        annotation_dict["id"] = this.id;
        annotation_dict["text_original"] = this.text;
        annotation_dict["text_edited"] = this.get_text_content();
        annotations.push(annotation_dict);
        console.log(annotations);
        console.log(JSON.stringify(annotations));
        let route = Flask.url_for('ocr.save_annotations', {'document_id': this.document_id});
        $.ajax({
            type: "POST",
            url: route,
            data: {annotations: JSON.stringify(annotations)},
            dataType: "json",
            success: function(data, textStatus) {
                if (data.status == 'redirect') {
                    // data.redirect contains the string URL to redirect to
                    window.location.href = data.href;
                }
            },
            error: function(xhr, ajaxOptions, ThrownError){
                alert('Unable to save annotation. Check your remote connection. ');
            }
        });
        this.edited = false;
        this.saved = true;
        this.set_background_to_save();
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