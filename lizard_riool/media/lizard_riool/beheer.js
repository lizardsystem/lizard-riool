// (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

// jslint configuration
/*global $ */

"use strict";

/* Upload stuff. */
$(function () {

    var $dialog;

    $dialog = $('<div class="upload-dialog"/>').load('files/upload/').dialog({
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

/* Action icon stuff. */
$(function () {

    // Show hidden action icons.
    $('#uploaded-files .workspace-acceptable-look-alike').live('mouseover', function () {
        $(this).children('.ss_sprite').css('display', 'block');
    });

    // Hide action icons.
    $('#uploaded-files .workspace-acceptable-look-alike').live('mouseleave', function () {
        $(this).children('.ss_sprite').css('display', 'none');
    });

    // Handle click on delete icon.
    $('#uploaded-files .delete').live('click', function () {
        var file_id, file_name;
        file_id = $.parseJSON($(this).parent().attr('data-adapter-layer-json')).id;
        file_name = $(this).parent().attr('data-name');
        $('<div title="Bestand verwijderen?"/>')
            .html('Bestand ' + file_name + ' verwijderen?')
            .dialog({
                buttons: {
                    Ja: function () {
                        // Server-side delete.
                        $.post('files/delete/' + file_id + '/', function () {
                            // Refresh file list.
                            $('#uploaded-files').load('files/');
                        });
                        // Close dialog.
                        $(this).dialog("close");
                    },
                    Nee: function () {
                        // Close dialog.
                        $(this).dialog("close");
                    }
                },
                modal: true,
                resizable: false
            });
        // prevent the default action, e.g., following a link
        return false;
    });

/*
    // Handle click on download icon.
    $('#uploaded-files .download').live('click', function () {
        var file_id;
        file_id = $.parseJSON($(this).parent().attr('data-adapter-layer-json')).id;
        $.get('files/download/' + file_id + '/');
        // prevent the default action, e.g., following a link
        return false;
    });
*/

});

