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

        # Visualization of *PUT records

        style = mapnik.Style()
        rule = mapnik.Rule()
        symbol = mapnik.PointSymbolizer()
        rule.symbols.append(symbol)
        style.rules.append(rule)
        styles['putStyle'] = style

        style = mapnik.Style()
        rule = mapnik.Rule()
        rule.max_scale = 1700
        symbol = mapnik.TextSymbolizer('caa', 'DejaVu Sans Book', 10,
            mapnik.Color('black'))
        symbol.allow_overlap = True
        rule.symbols.append(symbol)
        style.rules.append(rule)
        styles['putLabelStyle'] = style

        query = """(select caa, cab from lizard_riool_put
            where upload_id=%d) data""" % self.id
        params['table'] = query
        params['geometry_field'] = 'cab'
        datasource = mapnik.PostGIS(**params)

        layer = mapnik.Layer('putLayer', RD)
        layer.datasource = datasource
        layer.maxzoom = 35000
        layer.styles.append('putStyle')
        layer.styles.append('putLabelStyle')
        layers.append(layer)

        # Visualization of *RIOOL records

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


class RibAdapter(Adapter):
    "WorkspaceItemAdapter for SUFRIB files."


class RmbAdapter(Adapter):
    "WorkspaceItemAdapter for SUFRMB files."
