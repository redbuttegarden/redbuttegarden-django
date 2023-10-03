const dialog = $("#dialog");
const originalClass = dialog.attr("class");

dialog.dialog({
    create: function (event, ui) {
        $(event.target).parent().css('position', 'fixed');
    },
    buttons: [
        {
            text: "Ok",
            click: function () {
                $(this).dialog("close");
            }
        }
    ],
    minWidth: 350,
    show: {effect: "fold", duration: 700},
    hide: {effect: "fold", duration: 1000},
    modal: originalClass === 'full',
    position: {
        my: originalClass === 'full' ? "center" : "left top",
        at: originalClass === 'full' ? "center" : "left bottom",
        of: window
    }
});