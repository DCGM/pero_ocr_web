
function show_description()
{
    var selectedIndex = $(this)[0].selectedIndex;
    var option_attributes = $(this)[0].options[selectedIndex].attributes;
    var model_type_description = option_attributes["model-type-description"].value;
    var description = option_attributes["data-description"].value;
    $("#" + model_type_description).html(description);
}

$('select').each(show_description);
$('select').change(show_description);

