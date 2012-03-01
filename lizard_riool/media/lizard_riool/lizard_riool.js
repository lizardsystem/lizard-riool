// (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

// jslint configuration
/*global $, map, OpenLayers */

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

function draw_path(putten) {

    var feature, i, layer, layers, line, point, points, put;

    layers = map.getLayersByName('routeLayer');

    if (layers.length > 0) {
        layer = layers[0];
    } else {
        layer = new OpenLayers.Layer.Vector('routeLayer');
        map.addLayer(layer);
    }

    if (putten.length > 1) {
        points = [];
        for (i = 0; i < putten.length; i += 1) {
            put = putten[i];
            point = new OpenLayers.Geometry.Point(put.x, put.y);
            points.push(point);
        }
        line = new OpenLayers.Geometry.LineString(points);
        feature = new OpenLayers.Feature.Vector(line, null, {'strokeColor': '#0000ff', 'strokeWidth': 2});
        layer.addFeatures([feature]);
    }
}

//
//
function mark_put(data) {

    var i, layer, layers, prev_put, put, routeLayer, url;

    if (data.length > 0) {

        // A "put" was found. We need a layer to draw it.

        layers = map.getLayersByName('profileLayer');

        if (layers.length > 0) {
            layer = layers[0];
        } else {
            layer = new OpenLayers.Layer.Vector('profileLayer');
            map.addLayer(layer);
        }

        if (layer.features.length === 0) {
            put = new OpenLayers.Feature.Vector(new OpenLayers.Geometry.Point(data[0].x, data[0].y), {label: data[0].put});
            layer.addFeatures([put]);
        } else if (layer.features.length === 1) {
            url = '/riolering/bar/';
            prev_put = layer.features[layer.features.length - 1];
            $.getJSON(url, {upload_id: data[0].upload_id, source: prev_put.attributes.label, target: data[0].put}, draw_path);
            put = new OpenLayers.Feature.Vector(new OpenLayers.Geometry.Point(data[0].x, data[0].y), {label: data[0].put});
            layer.addFeatures([put]);
        } else {
            routeLayer = map.getLayersByName('routeLayer')[0];
            url = '/riolering/bar/';
            prev_put = layer.features[layer.features.length - 1];
            $.getJSON(url, {upload_id: data[0].upload_id, source: prev_put.attributes.label, target: data[0].put}, draw_path);
            put = new OpenLayers.Feature.Vector(new OpenLayers.Geometry.Point(data[0].x, data[0].y), {label: data[0].put});
            layer.addFeatures([put]);
        }

    }

}

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
        mark_put
    );

    $("#map").css("cursor", "default");

}

function do_nothing_click_handler() {
    // do nothing
}

$(function () {

    $('button#route').click(function () {

        var i, layers;

        layers = map.getLayersByName('routeLayer');
        for (i = 0; i < layers.length; i += 1) {
            layers[i].destroy();
        }

        layers = map.getLayersByName('profileLayer');
        for (i = 0; i < layers.length; i += 1) {
            layers[i].destroy();
        }

    });

});

$(function () {

    $('button#profile').click(function () {

        var $dialog;

        $dialog = $('<div class="profile-dialog"/>').dialog({
            autoOpen: true,
            height: 400,
            modal: true,
            title: 'Dwarsprofiel',
            width: 600
        });

    });

});

