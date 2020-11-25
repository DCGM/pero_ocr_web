
class ArabicReshaper
{
    constructor()
    {
        this.LETTER = 0;
        this.FORM = 1;
        this.NOT_SUPPORTED = -1;
        this.ISOLATED = 0;
        this.INITIAL = 1;
        this.MEDIAL = 2;
        this.FINAL = 3;

        this.forward_mapping = {};
        this.forward_mapping['ء'] = ['ﺀ', '', '', ''];
        this.forward_mapping['آ'] = ['ﺁ', '', '', 'ﺂ'];
        this.forward_mapping['أ'] = ['ﺃ', '', '', 'ﺄ'];
        this.forward_mapping['ؤ'] = ['ﺅ', '', '', 'ﺆ'];
        this.forward_mapping['إ'] = ['ﺇ', '', '', 'ﺈ'];
        this.forward_mapping['ئ'] = ['ﺉ', 'ﺋ', 'ﺌ', 'ﺊ'];
        this.forward_mapping['ا'] = ['ﺍ', '', '', 'ﺎ'];
        this.forward_mapping['ب'] = ['ﺏ', 'ﺑ', 'ﺒ', 'ﺐ'];
        this.forward_mapping['ة'] = ['ﺓ', '', '', 'ﺔ'];
        this.forward_mapping['ت'] = ['ﺕ', 'ﺗ', 'ﺘ', 'ﺖ'];
        this.forward_mapping['ث'] = ['ﺙ', 'ﺛ', 'ﺜ', 'ﺚ'];
        this.forward_mapping['ج'] = ['ﺝ', 'ﺟ', 'ﺠ', 'ﺞ'];
        this.forward_mapping['ح'] = ['ﺡ', 'ﺣ', 'ﺤ', 'ﺢ'];
        this.forward_mapping['خ'] = ['ﺥ', 'ﺧ', 'ﺨ', 'ﺦ'];
        this.forward_mapping['د'] = ['ﺩ', '', '', 'ﺪ'];
        this.forward_mapping['ذ'] = ['ﺫ', '', '', 'ﺬ'];
        this.forward_mapping['ر'] = ['ﺭ', '', '', 'ﺮ'];
        this.forward_mapping['ز'] = ['ﺯ', '', '', 'ﺰ'];
        this.forward_mapping['س'] = ['ﺱ', 'ﺳ', 'ﺴ', 'ﺲ'];
        this.forward_mapping['ش'] = ['ﺵ', 'ﺷ', 'ﺸ', 'ﺶ'];
        this.forward_mapping['ص'] = ['ﺹ', 'ﺻ', 'ﺼ', 'ﺺ'];
        this.forward_mapping['ض'] = ['ﺽ', 'ﺿ', 'ﻀ', 'ﺾ'];
        this.forward_mapping['ط'] = ['ﻁ', 'ﻃ', 'ﻄ', 'ﻂ'];
        this.forward_mapping['ظ'] = ['ﻅ', 'ﻇ', 'ﻈ', 'ﻆ'];
        this.forward_mapping['ع'] = ['ﻉ', 'ﻋ', 'ﻌ', 'ﻊ'];
        this.forward_mapping['غ'] = ['ﻍ', 'ﻏ', 'ﻐ', 'ﻎ'];
        this.forward_mapping['ـ'] = ['ـ', 'ـ', 'ـ', 'ـ'];
        this.forward_mapping['ف'] = ['ﻑ', 'ﻓ', 'ﻔ', 'ﻒ'];
        this.forward_mapping['ق'] = ['ﻕ', 'ﻗ', 'ﻘ', 'ﻖ'];
        this.forward_mapping['ك'] = ['ﻙ', 'ﻛ', 'ﻜ', 'ﻚ'];
        this.forward_mapping['ل'] = ['ﻝ', 'ﻟ', 'ﻠ', 'ﻞ'];
        this.forward_mapping['م'] = ['ﻡ', 'ﻣ', 'ﻤ', 'ﻢ'];
        this.forward_mapping['ن'] = ['ﻥ', 'ﻧ', 'ﻨ', 'ﻦ'];
        this.forward_mapping['ه'] = ['ﻩ', 'ﻫ', 'ﻬ', 'ﻪ'];
        this.forward_mapping['و'] = ['ﻭ', '', '', 'ﻮ'];
        this.forward_mapping['ى'] = ['ﻯ', 'ﯨ', 'ﯩ', 'ﻰ'];
        this.forward_mapping['ي'] = ['ﻱ', 'ﻳ', 'ﻴ', 'ﻲ'];
        this.forward_mapping['ٱ'] = ['ﭐ', '', '', 'ﭑ'];
        this.forward_mapping['ٷ'] = ['ﯝ', '', '', ''];
        this.forward_mapping['ٹ'] = ['ﭦ', 'ﭨ', 'ﭩ', 'ﭧ'];
        this.forward_mapping['ٺ'] = ['ﭞ', 'ﭠ', 'ﭡ', 'ﭟ'];
        this.forward_mapping['ٻ'] = ['ﭒ', 'ﭔ', 'ﭕ', 'ﭓ'];
        this.forward_mapping['پ'] = ['ﭖ', 'ﭘ', 'ﭙ', 'ﭗ'];
        this.forward_mapping['ٿ'] = ['ﭢ', 'ﭤ', 'ﭥ', 'ﭣ'];
        this.forward_mapping['ڀ'] = ['ﭚ', 'ﭜ', 'ﭝ', 'ﭛ'];
        this.forward_mapping['ڃ'] = ['ﭶ', 'ﭸ', 'ﭹ', 'ﭷ'];
        this.forward_mapping['ڄ'] = ['ﭲ', 'ﭴ', 'ﭵ', 'ﭳ'];
        this.forward_mapping['چ'] = ['ﭺ', 'ﭼ', 'ﭽ', 'ﭻ'];
        this.forward_mapping['ڇ'] = ['ﭾ', 'ﮀ', 'ﮁ', 'ﭿ'];
        this.forward_mapping['ڈ'] = ['ﮈ', '', '', 'ﮉ'];
        this.forward_mapping['ڌ'] = ['ﮄ', '', '', 'ﮅ'];
        this.forward_mapping['ڍ'] = ['ﮂ', '', '', 'ﮃ'];
        this.forward_mapping['ڎ'] = ['ﮆ', '', '', 'ﮇ'];
        this.forward_mapping['ڑ'] = ['ﮌ', '', '', 'ﮍ'];
        this.forward_mapping['ژ'] = ['ﮊ', '', '', 'ﮋ'];
        this.forward_mapping['ڤ'] = ['ﭪ', 'ﭬ', 'ﭭ', 'ﭫ'];
        this.forward_mapping['ڦ'] = ['ﭮ', 'ﭰ', 'ﭱ', 'ﭯ'];
        this.forward_mapping['ک'] = ['ﮎ', 'ﮐ', 'ﮑ', 'ﮏ'];
        this.forward_mapping['ڭ'] = ['ﯓ', 'ﯕ', 'ﯖ', 'ﯔ'];
        this.forward_mapping['گ'] = ['ﮒ', 'ﮔ', 'ﮕ', 'ﮓ'];
        this.forward_mapping['ڱ'] = ['ﮚ', 'ﮜ', 'ﮝ', 'ﮛ'];
        this.forward_mapping['ڳ'] = ['ﮖ', 'ﮘ', 'ﮙ', 'ﮗ'];
        this.forward_mapping['ں'] = ['ﮞ', '', '', 'ﮟ'];
        this.forward_mapping['ڻ'] = ['ﮠ', 'ﮢ', 'ﮣ', 'ﮡ'];
        this.forward_mapping['ھ'] = ['ﮪ', 'ﮬ', 'ﮭ', 'ﮫ'];
        this.forward_mapping['ۀ'] = ['ﮤ', '', '', 'ﮥ'];
        this.forward_mapping['ہ'] = ['ﮦ', 'ﮨ', 'ﮩ', 'ﮧ'];
        this.forward_mapping['ۅ'] = ['ﯠ', '', '', 'ﯡ'];
        this.forward_mapping['ۆ'] = ['ﯙ', '', '', 'ﯚ'];
        this.forward_mapping['ۇ'] = ['ﯗ', '', '', 'ﯘ'];
        this.forward_mapping['ۈ'] = ['ﯛ', '', '', 'ﯜ'];
        this.forward_mapping['ۉ'] = ['ﯢ', '', '', 'ﯣ'];
        this.forward_mapping['ۋ'] = ['ﯞ', '', '', 'ﯟ'];
        this.forward_mapping['ی'] = ['ﯼ', 'ﯾ', 'ﯿ', 'ﯽ'];
        this.forward_mapping['ې'] = ['ﯤ', 'ﯦ', 'ﯧ', 'ﯥ'];
        this.forward_mapping['ے'] = ['ﮮ', '', '', 'ﮯ'];
        this.forward_mapping['ۓ'] = ['ﮰ', '', '', 'ﮱ'];
        this.forward_mapping['‍'] = ['‍', '‍', '‍', '‍'];

        this.backward_mapping = {}
        for (let letter in this.forward_mapping)
        {
            for (let letter_option of this.forward_mapping[letter])
            {
                if (letter_option.length > 0)
                {
                    this.backward_mapping[letter_option] = letter;
                }
            }
        }

        this.ligatures = ['لا', 'الله', 'لأ', 'لإ'];

        this.arabic_delimiters = ['،', 'ً', 'ّ', '»'];
        this.delimiters = [' ', ',', '-', '.', '"', ':'];
    }

    label_to_visual_form(text)
    {
        if (!text)
        {
            return '';
        }

        let output = [];

        for (let letter of text)
        {
            if (this.forward_mapping[letter] === undefined)
            {
                output.push([letter, this.NOT_SUPPORTED])
            }
            else if (output.length == 0)
            {
                output.push([letter, this.ISOLATED])
            }
            else
            {
                let previous_letter = output[output.length - 1];
                if (previous_letter[this.FORM] == this.NOT_SUPPORTED)
                {
                    output.push([letter, this.ISOLATED]);
                }
                else if (!this.connects_with_letter_before(letter))
                {
                    output.push([letter, this.ISOLATED]);
                }
                else if (!this.connects_with_letter_after(previous_letter[this.LETTER]))
                {
                    output.push([letter, this.ISOLATED]);
                }
                else if (previous_letter[this.FORM] == this.FINAL &&
                         (!this.connects_with_forward_mapping_before_and_after(previous_letter[this.LETTER])))
                {
                    output.push([letter, this.ISOLATED]);
                }
                else if (previous_letter[this.FORM] == this.ISOLATED)
                {
                    output[output.length - 1] = [previous_letter[this.LETTER], this.INITIAL];
                    output.push([letter, this.FINAL]);
                }
                else
                {
                    output[output.length - 1] = [previous_letter[this.LETTER], this.MEDIAL];
                    output.push([letter, this.FINAL]);
                }
            }
        }

        let result = '';
        for (let o of output)
        {
            if (o[this.LETTER])
            {
                if (o[this.FORM] == this.NOT_SUPPORTED)
                {
                    result += o[this.LETTER];
                }
                else
                {
                    result += this.forward_mapping[o[this.LETTER]][o[this.FORM]];
                }
            }
        }
        return result;
    }

    visual_to_label_form(text)
    {
        if (!text)
        {
            return '';
        }

        let result = '';
        for (let letter of text)
        {
            if (letter in this.backward_mapping)
            {
                result += this.backward_mapping[letter];
            }
            else
            {
                result += letter;
            }
        }
        return result
    }

    reverse(text, confidences)
    {
        let tmp_chars = text.split('');
        let chars = [];
        tmp_chars.forEach((c, index) =>
        {
            if (confidences.length)
            {
                chars.push({'char': c, 'confidence': confidences[index]});
            }
            else
            {
                chars.push({'char': c});
            }
        });

        let sequences = [];
        let seq = {'chars': [], 'arabic': true};
        for (let c of chars)
        {
            if (c['char'] in this.forward_mapping || this.arabic_delimiters.includes(c['char']))
            {
                if (!seq['arabic'])
                {
                    if (seq['chars'].length > 0)
                    {
                        let arabic_seq = []
                        let number_of_ending_spaces = 0;
                        for (let i of seq['chars'].slice().reverse())
                        {
                            if (this.delimiters.includes(i['char']))
                            {
                                arabic_seq.unshift(i);
                                number_of_ending_spaces += 1;
                            }
                            else
                            {
                                break;
                            }
                        }
                        seq['chars'].splice(-number_of_ending_spaces, number_of_ending_spaces);
                        sequences.push(JSON.parse(JSON.stringify(seq)));
                        seq = {'chars': arabic_seq, 'arabic': true};
                    }
                    seq['arabic'] = true;
                }
            }

            else if (!this.delimiters.includes(c['char']))
            {
                if (seq['arabic'])
                {
                    if (seq['chars'].length > 0)
                    {
                        sequences.push(JSON.parse(JSON.stringify(seq)));
                        seq = {'chars': [], 'arabic': false};
                    }
                    seq['arabic'] = false;
                }
            }

            seq['chars'].push(c);
        }

        if (seq['chars'].length > 0)
        {
            let arabic_seq = []
            let number_of_ending_spaces = 0;
            for (let i of seq['chars'].slice().reverse())
            {
                if (this.delimiters.includes(i['char']))
                {
                    arabic_seq.unshift(i);
                    number_of_ending_spaces += 1;
                }
                else
                {
                    break;
                }
            }
            seq['chars'].splice(-number_of_ending_spaces, number_of_ending_spaces);
            sequences.push(JSON.parse(JSON.stringify(seq)));
            if (arabic_seq.length)
            {
                seq = {'chars': arabic_seq, 'arabic': true};
                sequences.push(JSON.parse(JSON.stringify(seq)));
            }
        }

        //console.log(JSON.parse(JSON.stringify(sequences)));

        for (let seq of sequences)
        {
            if (seq['arabic'])
            {
                seq['chars'].reverse();
            }
        }

        sequences.reverse();

        let reversed_text = "";
        let reversed_confidences = [];
        for (let seq of sequences)
        {
            for (let c of seq['chars'])
            {
                reversed_text += c['char'];
                if ('confidence' in c)
                {
                    reversed_confidences.push(c['confidence']);
                }
            }
        }

        return [reversed_text, reversed_confidences];
    }

    connects_with_letter_before(letter)
    {
        if (this.forward_mapping[letter] !== undefined)
        {
            let forms = this.forward_mapping[letter];
            return (forms[this.FINAL] || forms[this.MEDIAL]);
        }
        return false;
    }

    connects_with_letter_after(letter)
    {
        if (this.forward_mapping[letter] !== undefined)
        {
            let forms = this.forward_mapping[letter];
            return (forms[this.INITIAL] || forms[this.MEDIAL]);
        }
        return false;
    }

    connects_with_forward_mapping_before_and_after(letter)
    {
        if (this.forward_mapping[letter] !== undefined)
        {
            let forms = this.forward_mapping[letter];
            return forms[this.MEDIAL];
        }
        return false;
    }

    get_letter_indexes_to_ligatures_mapping(text)
    {
        let letter_indexes_to_ligatures_mapping = [];
        let regexp = "";
        for (let i in this.ligatures)
        {
            regexp += this.ligatures[i];
            if (i == this.ligatures.length - 1)
            {
                break;
            }
            regexp += '|';
        }
        let matches = text.matchAll(regexp)
        for (let match of matches)
        {
            letter_indexes_to_ligatures_mapping.push([match['index'], match['index'] + match[0].length - 1]);
        }
        return letter_indexes_to_ligatures_mapping;
    }
}


