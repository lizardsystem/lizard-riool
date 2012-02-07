// (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

// jslint configuration
/*global $ */

$().ready(function () {

    var $dialog;

    $dialog = $('<div class="upload-dialog"/>').load('/riolering/upload/').dialog({
        autoOpen: false,
        title: 'Uploaden',
        width: 500
    });

    $('.upload').click(function () {
        $dialog.dialog('open');
        // prevent the default action, e.g., following a link
        return false;
    });

});

