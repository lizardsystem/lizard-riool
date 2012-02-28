// (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

// jslint configuration
/*global $ */

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

function put_click_handler (x, y, map) {

    $("#map").css("cursor", "progress");
    var extent, radius, url, user_workspace_id;
    extent = map.getExtent();
    radius = Math.abs(extent.top - extent.bottom) / 30;
    url = '/riolering/foo/';
    user_workspace_id = $(".workspace").attr("data-workspace-id");
    if (url !== undefined) {
        $.getJSON(
            url,
            { x: x, y: y, radius: radius, srs: map.getProjection(),
              user_workspace_id: user_workspace_id }, draw_put
        );
    }

}

function do_nothing_click_handler () {
    // do nothing
}

function draw_put (data) {

    if (data) {
    
    	layers = map.getLayersByName('profileLayer');
    	
    	if (layers.length > 0) {
    		layer = layers[0];
    	} else {
    		layer = new OpenLayers.Layer.Vector('profileLayer');
    		map.addLayer(layer);
			//var select_feature_control = new OpenLayers.Control.SelectFeature(layer);
			//map.addControl(select_feature_control);
			//select_feature_control.activate();
    	}
    	
		if (!layer.getFeatureById(data.label)) {
			var put = new OpenLayers.Feature.Vector(new OpenLayers.Geometry.Point(data.x, data.y));
			put.id = data.label;
			layer.addFeatures([put]);
		}
		
    }

    $("#map").css("cursor", "default");

}
