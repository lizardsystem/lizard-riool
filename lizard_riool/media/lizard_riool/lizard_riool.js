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

$(function () {
	vector_layer = new OpenLayers.Layer.Vector('Basic Vector Layer');
	var feature_point = new OpenLayers.Feature.Vector(
		new OpenLayers.Geometry.Point(145908.86, 485672.35), {'location': 'The Sea', 'description': 'Here be dragons'}, {'label': 'foo'}
	);
	vector_layer.addFeatures([feature_point]);
	map.addLayer(vector_layer);
	var select_feature_control = new OpenLayers.Control.SelectFeature(vector_layer);
	map.addControl(select_feature_control);
	select_feature_control.activate();
});

function my_popup_click_handler() {
	alert('foobar');
}