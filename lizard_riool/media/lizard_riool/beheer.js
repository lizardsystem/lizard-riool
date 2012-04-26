// (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

// jslint configuration
/*global $ */

"use strict";

$(function () {

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

$(function () {

    // Show hidden action icons.
    $('#uploaded-files .no-workspace-acceptable').mouseover(function () {
        $(this).children('.ss_sprite').css('display', 'block');
    });

    // Hide action icons.
    $('#uploaded-files .no-workspace-acceptable').mouseleave(function () {
        $(this).children('.ss_sprite').css('display', 'none');
    });

    // Handle click on delete icon.
    $('#uploaded-files .delete').click(function () {
        var $file;
        $file = $(this).parent().attr('data-name');
        $('<div title="Bestand verwijderen?"/>')
            .html('Bestand ' + $file + ' verwijderen?')
            .dialog({
                buttons: {
                    Ja: function () {
                        $(this).dialog("close");
                    },
                    Nee: function () {
                        $(this).dialog("close");
                    }
                },
                modal: true,
                resizable: false
            });
        return false;
    });

    // Handle click on download icon.
    $('#uploaded-files .download').click(function () {
        return false;
    });

});

