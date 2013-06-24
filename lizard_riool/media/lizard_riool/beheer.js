// (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

// jslint configuration
/*global $, window, setTimeout */

"use strict";

/* Upload stuff. */
$(function () {

    var $dialog;

    var upload_dialog_url = $("#upload-button").attr("data-upload-dialog-url");
    $dialog = $('<div class="upload-dialog"/>').load(upload_dialog_url).dialog({
        autoOpen: false,
        title: 'Uploaden',
        width: 500
    });

    $('.upload h2').click(function () {
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
});

/* Constantly rebuild the file list ajaxically */
var beheer_functions = beheer_functions || (function () {
    var refresh_url = $("#uploaded_file_lists").attr("data-refresh-url");

    /* The refresh url will give a bit of JSON data. This is an array
       of objects, of the form:
       {
           id: a unique id string
           name: filename
           status: One of "not_being_processed_yet", "being_processed", "with_errors", "successful"
           }
    */

    var id_present_in = function (status, id) {
        var result = false;
        $("#uploaded_files_" + status + " ul li").each(function (i, item) {
            item = $(item);
            if (item.attr("data-file-id") === id) {
                result = true;
            }
        });

        return result;
    };

    var remove_ids = function (status, ids_to_keep) {
        $("#uploaded_files_" + status + " ul li").each(function (i, item) {
            item = $(item);
            if (!(item.attr("data-file-id") in (ids_to_keep[status] || {}))) {
                item.remove();
            }
        });
    };

    var add_to_list = function (uploaded_file) {
        var status = uploaded_file.status;
        var id = uploaded_file.id;
        var name = uploaded_file.name;

        var li = $("<li>").attr("data-file-id", id).append(name);
        
        var sprite_remove;
        var sprite_errors;

        if (status === "not_being_processed_yet") {
            sprite_remove = ($("<span>")
                                 .attr("class", "remove ss_sprite ss_delete")
                                 .attr("rel", "tipsy-south")
                                 .attr("title", "Bestand verwijderen")
                                 .attr("data-delete-url", uploaded_file.delete_url));
            li = li.append(sprite_remove);
        }

        if (status === "with_errors") {
            sprite_remove = ($("<span>")
                             .attr("class", "remove ss_sprite ss_delete")
                             .attr("rel", "tipsy-south")
                             .attr("title", "Verwijderen")
                             .attr("data-delete-url", uploaded_file.delete_url)
                            );
            sprite_errors = ($("<span>")
                             .attr("class", "ss_sprite ss_help error_link")
                             .attr("rel", "tipsy-south")
                             .attr("title", uploaded_file.error_description)
                             .attr("data-error-url", uploaded_file.error_url));

            li = li.append(sprite_remove).append(sprite_errors);
        }

        if (status === "successful") {
            var sprite = ($("<span>")
                          .attr("class", "remove ss_sprite ss_accept")
                          .attr("rel", "tipsy-south")
                          .attr("title", "Melding verbergen")
                          .attr("data-delete-url", uploaded_file.delete_url));

            li = li.append(sprite);
        }

        $("#uploaded_files_" + status + " ul").append(li);
    };

    var record_id_to_keep = function (ids_to_keep, status, id) {
        ids_to_keep[status] = ids_to_keep[status] || {};
        ids_to_keep[status][id] = true;
    };

    var repeat_update_file_list = true;

    var reupdate_file_list = function () {
        // This function repeats infinitely every second
        // If repeat_update_file_list is true, it calls
        // update_file_list.
        if (repeat_update_file_list) {
            update_file_list();
            repeat_update_file_list = false;
        }

        setTimeout(reupdate_file_list, 1000);
    };
    $(reupdate_file_list);

    var schedule_update_file_list = function () {
        repeat_update_file_list = true;
    }

    var update_file_list = function () {
        $.getJSON(refresh_url, function(data) {
            var ids_to_keep = {};

            // Sync the lists to the file ids in the data
            // First go through all the data, add the files to the right
            // lists, adding all ids to ids_to_keep.
            // Then go through all the lists and remove the files we haven't
            // seen this way.
            $.each(data, function (i, uploaded_file) {
                var id = uploaded_file.id;
                var status = uploaded_file.status;

                record_id_to_keep(ids_to_keep, status, id);

                if (!id_present_in(status, id)) {
                    add_to_list(uploaded_file);
                }
            });

            remove_ids("not_being_processed_yet", ids_to_keep);
            remove_ids("being_processed", ids_to_keep);
            remove_ids("with_errors", ids_to_keep);
            remove_ids("successful", ids_to_keep);

            if (($("#uploaded_files_not_being_processed_yet ul li").length !== 0) ||
                ($("#uploaded_files_being_processed ul li").length !== 0)) {
                // Keep refreshing until these tables are empty
                repeat_update_file_list = true;
            }
        });
    };

    var open_error_page = function () {
        var url = $(this).attr("data-error-url");

        if (url !== undefined) {
            window.open(url, "_blank");
        }
    };

    var delete_uploaded_file = function () {
        var url = $(this).attr("data-delete-url");

        var that = $(this);

        if (url !== undefined) {
            $.ajax({
                url: url,
                type: 'DELETE',
                success: function () {
                    that.closest("li").remove();
                    schedule_update_file_list();
                }
            });
        }
    };

    return {
        schedule_update_file_list: schedule_update_file_list,
        open_error_page: open_error_page,
        delete_uploaded_file: delete_uploaded_file
    };
})();

$(".error_link").live('click', beheer_functions.open_error_page);
$(".remove").live('click', beheer_functions.delete_uploaded_file);
