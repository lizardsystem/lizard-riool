from django.conf import settings
from django.db import connection
from lizard_map.coordinates import RD
from lizard_map.workspace import WorkspaceItemAdapter
from lizard_riool.models import SRID
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


class RibAdapter(WorkspaceItemAdapter):
    "WorkspaceItemAdapter for SUFRIB files."

    def __init__(self, *args, **kwargs):
        super(RibAdapter, self).__init__(*args, **kwargs)
        self.id = int(self.layer_arguments['id'])

    def layer(self, layer_ids=None, request=None):
        "Return Mapnik layers and styles."
        layers, styles = [], {}

#

        style = mapnik.Style()
        rule = mapnik.Rule()
        symbol = mapnik.PointSymbolizer()
        rule.symbols.append(symbol)
        style.rules.append(rule)

        query = '(select cab from lizard_riool_put ' + \
            'where upload_id=%d) data' % self.id
        params['table'] = query
        params['geometry_field'] = 'cab'
        datasource = mapnik.PostGIS(**params)

        layer = mapnik.Layer("put", RD)
        layer.datasource = datasource
        layer.maxzoom = 35000
        layer.styles.append("put")

        layers.append(layer)
        styles["put"] = style

        #

        style = mapnik.Style()
        rule = mapnik.Rule()
#        rule.max_scale = 50000
        symbol = mapnik.LineSymbolizer(mapnik.Color('brown'), 2)
        rule.symbols.append(symbol)
        style.rules.append(rule)

        rule = mapnik.Rule()
        symbol = mapnik.TextSymbolizer("aaa", "DejaVu Sans Book", 10,
                                       mapnik.Color("black"))
        symbol.label_placement = mapnik.label_placement.LINE_PLACEMENT
        symbol.displacement(0, 6)
        rule.symbols.append(symbol)
        style.rules.append(rule)

        query = '(select aaa, the_geom from lizard_riool_riool ' + \
            'where upload_id=%d) data' % self.id
        params['table'] = query
        params['geometry_field'] = 'the_geom'
        datasource = mapnik.PostGIS(**params)

        layer = mapnik.Layer("riool", RD)
        layer.datasource = datasource
        layer.maxzoom = 35000
        layer.styles.append("riool")

        layers.append(layer)
        styles["riool"] = style

        #

        return layers, styles

    def extent(self, identifiers=None):
        "Return the extent in Google projection"
        cursor = connection.cursor()
        cursor.execute("""
            select ST_Extent(ST_Transform(the_geom, 900913)) from (
            select the_geom from lizard_riool_riool where upload_id=%s union
            select cab the_geom from lizard_riool_put where upload_id=%s
            ) data""", [self.id, self.id])
        row = cursor.fetchone()
        box = re.compile('[(|\s|,|)]').split(row[0])[1:-1]
        return {
            'west': box[0], 'south': box[1],
            'east': box[2], 'north': box[3],
        }


class RmbAdapter(WorkspaceItemAdapter):
    "WorkspaceItemAdapter for SUFRMB files."

    def __init__(self, *args, **kwargs):
        super(RmbAdapter, self).__init__(*args, **kwargs)
        self.id = self.layer_arguments["id"]

    def layer(self, layer_ids=None, request=None):
        "Return Mapnik layers and styles."
        layers = []
        styles = {}

        return layers, styles

    def extent(self, identifiers=None):
        ""
        return {'north': None, 'south': None, 'east': None, 'west': None}
