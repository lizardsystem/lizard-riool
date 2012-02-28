from django.conf import settings
from django.db import connection
from lizard_map.coordinates import RD
from lizard_map.workspace import WorkspaceItemAdapter
from lizard_riool.models import Riool, SRID
import mapnik
import re

database = settings.DATABASES['default']

params = {
    'host': database['HOST'],
    'port': database['PORT'],
    'user': database['USER'],
    'password': database['PASSWORD'],
    'dbname': database['NAME'],
    'srid': SRID,
}


class Adapter(WorkspaceItemAdapter):
    """Superclass for SUFRIB and SUBRMB WorkspaceItemAdapters.

    Both SUFRIB and SUBRMB files may have *RIOO and/or *PUT
    records, so visualization of these can be shared in a
    superclass.
    """

    def __init__(self, *args, **kwargs):
        super(Adapter, self).__init__(*args, **kwargs)
        self.id = int(self.layer_arguments['id'])  # upload_id

    def layer(self, layer_ids=None, request=None):
        "Return Mapnik layers and styles."
        layers, styles = [], {}

        # Visualization of "putten"

        style = mapnik.Style()
        rule = mapnik.Rule()
        symbol = mapnik.PointSymbolizer()
        rule.symbols.append(symbol)
        style.rules.append(rule)
        styles['putStyle'] = style

        style = mapnik.Style()
        rule = mapnik.Rule()
        rule.max_scale = 1700
        symbol = mapnik.TextSymbolizer('put_id', 'DejaVu Sans Book', 10,
            mapnik.Color('black'))
        symbol.allow_overlap = True
        symbol.label_placement = mapnik.label_placement.POINT_PLACEMENT
        symbol.vertical_alignment = mapnik.vertical_alignment.TOP
        symbol.displacement(0, -3)  # slightly above
        rule.symbols.append(symbol)
        style.rules.append(rule)
        styles['putLabelStyle'] = style

        query = """(select * from lizard_riool_putten
            where upload_id=%d) data""" % self.id
        params['table'] = query
        params['geometry_field'] = 'the_geom'
        datasource = mapnik.PostGIS(**params)

        layer = mapnik.Layer('putLayer', RD)
        layer.datasource = datasource
        layer.maxzoom = 35000
        layer.styles.append('putStyle')
        layer.styles.append('putLabelStyle')
        layers.append(layer)

        # Visualization of "riolen"

        style = mapnik.Style()
        rule = mapnik.Rule()
        symbol = mapnik.LineSymbolizer(mapnik.Color('brown'), 1.5)
        rule.symbols.append(symbol)
        style.rules.append(rule)
        styles['rioolStyle'] = style

        style = mapnik.Style()
        rule = mapnik.Rule()
        rule.max_scale = 1700
        symbol = mapnik.TextSymbolizer('aaa', 'DejaVu Sans Book', 10,
            mapnik.Color('brown'))
        symbol.allow_overlap = True
        symbol.label_placement = mapnik.label_placement.LINE_PLACEMENT
        symbol.displacement(0, 6)
        rule.symbols.append(symbol)
        style.rules.append(rule)
        styles['rioolLabelStyle'] = style

        query = """(select aaa, the_geom from lizard_riool_riool
            where upload_id=%d) data""" % self.id
        params['table'] = query
        params['geometry_field'] = 'the_geom'
        datasource = mapnik.PostGIS(**params)

        layer = mapnik.Layer("rioolLayer", RD)
        layer.datasource = datasource
        layer.maxzoom = 35000
        layer.styles.append("rioolStyle")
        layer.styles.append("rioolLabelStyle")
        layers.append(layer)

        return layers, styles

    def extent(self, identifiers=None):
        "Return the extent in Google projection"
        cursor = connection.cursor()
        cursor.execute("""
            select ST_Extent(ST_Transform(the_geom, 900913))
            from lizard_riool_putten where upload_id=%s
            """, [self.id])
        row = cursor.fetchone()
        box = re.compile('[(|\s|,|)]').split(row[0])[1:-1]
        return {
            'west': box[0], 'south': box[1],
            'east': box[2], 'north': box[3],
        }

    def search(self, x, y, radius=None):
        """Search by coordinates. Return list of dicts for matching
        items.

        {'distance': <float>,
        'name': <name>,
        'shortname': <short name>,
        'workspace_item': <...>,
        'identifier': {...},
        'google_coords': (x, y) coordinate in google,
        'object': <object>,
       ['grouping_hint': ... ] (optional)
        } of closest fews point that matches x, y, radius.

        Required: distance, name, workspace_item, google_coords
        Highly recommended (else some functions will not work):
        identifier (for popups)

        If 'grouping_hint' is given, that is used to group items,
        otherwise the workspace_item.id. This way a single workspace
        item can have things show up in different tabs. Please don't
        use grouping_hints that can possible come from other workspace
        items (use the workspace item id in the hint).


        """
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++"
        from django.contrib.gis.geos import *
        from django.contrib.gis.measure import D
        from django.contrib.gis.geos import Point
        pnt = Point(x, y, srid=900913)
        riolen = Riool.objects.filter(upload__pk=self.id).filter(_AAE__distance_lte=(pnt, radius))
        for riool in riolen:
            print riool.AAD
        #return [{'distance': 0.0, 'name': str(self.id), 'workspace_item': self.workspace_item, 'identifier': 'foo'}]
        return []


class RibAdapter(Adapter):
    "WorkspaceItemAdapter for SUFRIB files."


class RmbAdapter(Adapter):
    "WorkspaceItemAdapter for SUFRMB files."
