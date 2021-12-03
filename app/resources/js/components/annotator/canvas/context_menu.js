/**
Tento soubor byl převzat z diplomové práce "Active Learning pro zpracování archivních pramenů"

Autor práce: David Hříbek
Rok: 2021
**/

/**
 * Show context menu
 */
export function activateContextMenu() {
    $('#canvas-contextmenu').css('top', event.clientY + 'px');
    $('#canvas-contextmenu').css('left', event.clientX + 'px');
    $('#canvas-contextmenu').addClass('active');
}

/**
 * Hide canvas context menu
 */
export function deactivateContextMenu() {
    $('#canvas-contextmenu').removeClass('active');
}

/**
 * Right click on canvas event
 * @param event
 */
export function canvasContextMenuEv(event) {
    event.preventDefault();
    // this.activeContextMenu();
}
