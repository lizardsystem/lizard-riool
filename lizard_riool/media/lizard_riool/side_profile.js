// (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

// jslint configuration
/*global $, map, OpenLayers */

"use strict";

$.lizard_riool = {};

$.lizard_riool.init = function () {
    $.lizard_riool.profileLayer.destroyFeatures();
    $.lizard_riool.routeLayer.destroyFeatures();
    $.lizard_riool.upload_id = null;
    $.lizard_riool.putten = [];
    $.lizard_riool.strengen = [];
};

$(function () {

    $.lizard_riool.profileLayer = new OpenLayers.Layer.Vector('profileLayer');
    $.lizard_riool.profileLayer.displayInLayerSwitcher = false;
    map.addLayer($.lizard_riool.profileLayer);

    $.lizard_riool.routeLayer = new OpenLayers.Layer.Vector('routeLayer');
    $.lizard_riool.routeLayer.displayInLayerSwitcher = false;
    map.addLayer($.lizard_riool.routeLayer);

    $.lizard_riool.init();

});

$(function () {

    $('button#route').click(function () {
        $.lizard_riool.init();
    });

});

function draw_path(data) {

    var feature, i, layer, line, point, points, put, putten, strengen;

    layer = $.lizard_riool.routeLayer;

    putten = data.putten;

    if (putten.length > 1) {

        // Draw the path.

        points = [];
        for (i = 0; i < putten.length; i += 1) {
            put = putten[i];
            point = new OpenLayers.Geometry.Point(put.x, put.y);
            points.push(point);
        }
        line = new OpenLayers.Geometry.LineString(points);
        feature = new OpenLayers.Feature.Vector(line, null, {'strokeColor': '#0000ff', 'strokeWidth': 2});
        layer.addFeatures([feature]);

        // Mark the last "put" in the path.

        point = new OpenLayers.Feature.Vector(point, {label: put.put});
        $.lizard_riool.profileLayer.addFeatures([point]);

    }

    if ($.lizard_riool.putten.length > 1) {
        for (i = 1; i < putten.length; i += 1) {
            $.lizard_riool.putten.push(putten[i].put);
        }
    } else {
        for (i = 0; i < putten.length; i += 1) {
            $.lizard_riool.putten.push(putten[i].put);
        }
    }

    strengen = data.strengen;

    for (i = 0; i < strengen.length; i += 1) {
        $.lizard_riool.strengen.push(strengen[i]);
    }
}

$.lizard_riool.mark_put = function (put) {

    var layer, point, prev_put, url;

    if (!$.isEmptyObject(put)) {

        if (put.upload_id !== $.lizard_riool.upload_id) {
            $.lizard_riool.init();
        }

        layer = $.lizard_riool.profileLayer;

        if (layer.features.length === 0) {
            point = new OpenLayers.Feature.Vector(new OpenLayers.Geometry.Point(put.x, put.y), {label: put.put});
            layer.addFeatures([point]);
            $.lizard_riool.upload_id = put.upload_id;
        } else if (put.upload_id === $.lizard_riool.upload_id) {
            url = '/riolering/bar/';
            prev_put = layer.features[layer.features.length - 1];
            $.getJSON(url, {upload_id: put.upload_id, source: prev_put.attributes.label, target: put.put}, draw_path);
        }

    }

};

// Find the nearest "put" within a certain radius
// around a point clicked on the map and mark it.
function put_click_handler(x, y, map) {

    var extent, radius, url, workspace_id;

    $("#map").css("cursor", "progress");

    url = '/riolering/put/';
    extent = map.getExtent();
    radius = Math.abs(extent.top - extent.bottom) / 60;
    workspace_id = $(".workspace").attr("data-workspace-id");

    $.getJSON(
        url,
        {
            x: x,
            y: y,
            radius: radius,
            srs: map.getProjection(),
            workspace_id: workspace_id
        },
        $.lizard_riool.mark_put
    );

    $("#map").css("cursor", "default");

}

$(function () {

    $('button#profile').click(function () {

        // Display a side profile ("langsprofiel")
        // graph of the selected route.

        var putten, strengen, upload_id;

        upload_id = $.lizard_riool.upload_id;
        putten = $.lizard_riool.putten;
        strengen = $.lizard_riool.strengen;

        if (strengen.length === 0) {
            return;
        }

        // To properly center its dialog, jQuery
        // first needs the resulting html.

        var $dialog_content = $('<div/>');
        var $dialog = $dialog_content.dialog({
            modal: true,
            title: 'Langsprofiel',
            width: 700,
            height: 300,
            zIndex: 2000
        });
        function load_graph () {
            // show a spinner
            var $loading = $('<img src="/static_media/lizard_ui/ajax-loader.gif" class="popup-loading-animation" />');
            $dialog_content.empty().append($loading);
            // grab the html containing the <img>
            $.get(
                '/riolering/langsprofielen/popup/',
                {
                    upload_id: upload_id,
                    putten: putten,
                    strengen: strengen,
                    width: $dialog_content.width(),
                    height: $dialog_content.height()
                },
                function (data, textStatus, jqXHR) {
                    // append response to the dialog
                    $dialog_content.append(data);
                    // attach a load event to the image in the response
                    $dialog_content.find('img').load(function () {
                        // remove the spinner when loaded
                        $loading.remove();
                    });
                }
            );
        }
        load_graph();
        $dialog.bind('dialogresizestop', load_graph);
    });
});
