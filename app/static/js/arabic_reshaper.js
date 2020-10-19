
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

        this.letters = {};
        this.letters['ء'] = ['ﺀ', '', '', ''];
        this.letters['آ'] = ['ﺁ', '', '', 'ﺂ'];
        this.letters['أ'] = ['ﺃ', '', '', 'ﺄ'];
        this.letters['ؤ'] = ['ﺅ', '', '', 'ﺆ'];
        this.letters['إ'] = ['ﺇ', '', '', 'ﺈ'];
        this.letters['ئ'] = ['ﺉ', 'ﺋ', 'ﺌ', 'ﺊ'];
        this.letters['ا'] = ['ﺍ', '', '', 'ﺎ'];
        this.letters['ب'] = ['ﺏ', 'ﺑ', 'ﺒ', 'ﺐ'];
        this.letters['ة'] = ['ﺓ', '', '', 'ﺔ'];
        this.letters['ت'] = ['ﺕ', 'ﺗ', 'ﺘ', 'ﺖ'];
        this.letters['ث'] = ['ﺙ', 'ﺛ', 'ﺜ', 'ﺚ'];
        this.letters['ج'] = ['ﺝ', 'ﺟ', 'ﺠ', 'ﺞ'];
        this.letters['ح'] = ['ﺡ', 'ﺣ', 'ﺤ', 'ﺢ'];
        this.letters['خ'] = ['ﺥ', 'ﺧ', 'ﺨ', 'ﺦ'];
        this.letters['د'] = ['ﺩ', '', '', 'ﺪ'];
        this.letters['ذ'] = ['ﺫ', '', '', 'ﺬ'];
        this.letters['ر'] = ['ﺭ', '', '', 'ﺮ'];
        this.letters['ز'] = ['ﺯ', '', '', 'ﺰ'];
        this.letters['س'] = ['ﺱ', 'ﺳ', 'ﺴ', 'ﺲ'];
        this.letters['ش'] = ['ﺵ', 'ﺷ', 'ﺸ', 'ﺶ'];
        this.letters['ص'] = ['ﺹ', 'ﺻ', 'ﺼ', 'ﺺ'];
        this.letters['ض'] = ['ﺽ', 'ﺿ', 'ﻀ', 'ﺾ'];
        this.letters['ط'] = ['ﻁ', 'ﻃ', 'ﻄ', 'ﻂ'];
        this.letters['ظ'] = ['ﻅ', 'ﻇ', 'ﻈ', 'ﻆ'];
        this.letters['ع'] = ['ﻉ', 'ﻋ', 'ﻌ', 'ﻊ'];
        this.letters['غ'] = ['ﻍ', 'ﻏ', 'ﻐ', 'ﻎ'];
        this.letters['ـ'] = ['ـ', 'ـ', 'ـ', 'ـ'];
        this.letters['ف'] = ['ﻑ', 'ﻓ', 'ﻔ', 'ﻒ'];
        this.letters['ق'] = ['ﻕ', 'ﻗ', 'ﻘ', 'ﻖ'];
        this.letters['ك'] = ['ﻙ', 'ﻛ', 'ﻜ', 'ﻚ'];
        this.letters['ل'] = ['ﻝ', 'ﻟ', 'ﻠ', 'ﻞ'];
        this.letters['م'] = ['ﻡ', 'ﻣ', 'ﻤ', 'ﻢ'];
        this.letters['ن'] = ['ﻥ', 'ﻧ', 'ﻨ', 'ﻦ'];
        this.letters['ه'] = ['ﻩ', 'ﻫ', 'ﻬ', 'ﻪ'];
        this.letters['و'] = ['ﻭ', '', '', 'ﻮ'];
        this.letters['ى'] = ['ﻯ', 'ﯨ', 'ﯩ', 'ﻰ'];
        this.letters['ي'] = ['ﻱ', 'ﻳ', 'ﻴ', 'ﻲ'];
        this.letters['ٱ'] = ['ﭐ', '', '', 'ﭑ'];
        this.letters['ٷ'] = ['ﯝ', '', '', ''];
        this.letters['ٹ'] = ['ﭦ', 'ﭨ', 'ﭩ', 'ﭧ'];
        this.letters['ٺ'] = ['ﭞ', 'ﭠ', 'ﭡ', 'ﭟ'];
        this.letters['ٻ'] = ['ﭒ', 'ﭔ', 'ﭕ', 'ﭓ'];
        this.letters['پ'] = ['ﭖ', 'ﭘ', 'ﭙ', 'ﭗ'];
        this.letters['ٿ'] = ['ﭢ', 'ﭤ', 'ﭥ', 'ﭣ'];
        this.letters['ڀ'] = ['ﭚ', 'ﭜ', 'ﭝ', 'ﭛ'];
        this.letters['ڃ'] = ['ﭶ', 'ﭸ', 'ﭹ', 'ﭷ'];
        this.letters['ڄ'] = ['ﭲ', 'ﭴ', 'ﭵ', 'ﭳ'];
        this.letters['چ'] = ['ﭺ', 'ﭼ', 'ﭽ', 'ﭻ'];
        this.letters['ڇ'] = ['ﭾ', 'ﮀ', 'ﮁ', 'ﭿ'];
        this.letters['ڈ'] = ['ﮈ', '', '', 'ﮉ'];
        this.letters['ڌ'] = ['ﮄ', '', '', 'ﮅ'];
        this.letters['ڍ'] = ['ﮂ', '', '', 'ﮃ'];
        this.letters['ڎ'] = ['ﮆ', '', '', 'ﮇ'];
        this.letters['ڑ'] = ['ﮌ', '', '', 'ﮍ'];
        this.letters['ژ'] = ['ﮊ', '', '', 'ﮋ'];
        this.letters['ڤ'] = ['ﭪ', 'ﭬ', 'ﭭ', 'ﭫ'];
        this.letters['ڦ'] = ['ﭮ', 'ﭰ', 'ﭱ', 'ﭯ'];
        this.letters['ک'] = ['ﮎ', 'ﮐ', 'ﮑ', 'ﮏ'];
        this.letters['ڭ'] = ['ﯓ', 'ﯕ', 'ﯖ', 'ﯔ'];
        this.letters['گ'] = ['ﮒ', 'ﮔ', 'ﮕ', 'ﮓ'];
        this.letters['ڱ'] = ['ﮚ', 'ﮜ', 'ﮝ', 'ﮛ'];
        this.letters['ڳ'] = ['ﮖ', 'ﮘ', 'ﮙ', 'ﮗ'];
        this.letters['ں'] = ['ﮞ', '', '', 'ﮟ'];
        this.letters['ڻ'] = ['ﮠ', 'ﮢ', 'ﮣ', 'ﮡ'];
        this.letters['ھ'] = ['ﮪ', 'ﮬ', 'ﮭ', 'ﮫ'];
        this.letters['ۀ'] = ['ﮤ', '', '', 'ﮥ'];
        this.letters['ہ'] = ['ﮦ', 'ﮨ', 'ﮩ', 'ﮧ'];
        this.letters['ۅ'] = ['ﯠ', '', '', 'ﯡ'];
        this.letters['ۆ'] = ['ﯙ', '', '', 'ﯚ'];
        this.letters['ۇ'] = ['ﯗ', '', '', 'ﯘ'];
        this.letters['ۈ'] = ['ﯛ', '', '', 'ﯜ'];
        this.letters['ۉ'] = ['ﯢ', '', '', 'ﯣ'];
        this.letters['ۋ'] = ['ﯞ', '', '', 'ﯟ'];
        this.letters['ی'] = ['ﯼ', 'ﯾ', 'ﯿ', 'ﯽ'];
        this.letters['ې'] = ['ﯤ', 'ﯦ', 'ﯧ', 'ﯥ'];
        this.letters['ے'] = ['ﮮ', '', '', 'ﮯ'];
        this.letters['ۓ'] = ['ﮰ', '', '', 'ﮱ'];
        this.letters['‍'] = ['‍', '‍', '‍', '‍'];
    }

    reshape(text)
    {
        if (!text)
        {
            return '';
        }

        let output = [];

        for (let letter of text)
        {
            if (this.letters[letter] === undefined)
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
                         (!this.connects_with_letters_before_and_after(previous_letter[this.LETTER])))
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
                    result += this.letters[o[this.LETTER]][o[this.FORM]];
                }
            }
        }
        return result;
    }

    connects_with_letter_before(letter)
    {
        if (this.letters[letter] !== undefined)
        {
            let forms = this.letters[letter];
            return (forms[this.FINAL] || forms[this.MEDIAL]);
        }
        return false;
    }

    connects_with_letter_after(letter)
    {
        if (this.letters[letter] !== undefined)
        {
            let forms = this.letters[letter];
            return (forms[this.INITIAL] || forms[this.MEDIAL]);
        }
        return false;
    }

    connects_with_letters_before_and_after(letter)
    {
        if (this.letters[letter] !== undefined)
        {
            let forms = this.letters[letter];
            return forms[this.MEDIAL];
        }
        return false;
    }
}


