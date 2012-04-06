// (c) Nelen & Schuurmans. GPL licensed, see LICENSE.txt.

// jslint configuration
/*global $, map, OpenLayers */

"use strict";

$(function () {

    $('button#capacity').click(function () {

        var url, workspace_id;

        $("#map").css("cursor", "progress");

        url = '/riolering/berging/result/';
        workspace_id = $(".workspace").attr("data-workspace-id");
        $.getJSON(url, {workspace_id: workspace_id});

        $("#map").css("cursor", "default");

    });

});

