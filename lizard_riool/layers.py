from django.conf import settings
from lizard_map.coordinates import RD
from lizard_map.workspace import WorkspaceItemAdapter
from lizard_riool.models import Put, Upload
import mapnik


class RibAdapter(WorkspaceItemAdapter):
    "WorkspaceItemAdapter for SUFRIB files."

    def __init__(self, *args, **kwargs):
        super(RibAdapter, self).__init__(*args, **kwargs)
        self.id = self.layer_arguments["id"]

    def layer(self, layer_ids=None, request=None):
        "Return Mapnik layers and styles."
        layers = []
        styles = {}

        upload = Upload.objects.get(pk=self.id)

        style = mapnik.Style()
        rule = mapnik.Rule()
#        symbol = mapnik.PointSymbolizer()
        symbol = mapnik.LineSymbolizer(mapnik.Color('brown'), 2)
        rule.symbols.append(symbol)
        style.rules.append(rule)

#        query = '(select cab as "CAB" from lizard_riool_put where upload_id=%d) data' % upload.pk
        query = '(select the_geom as "AAE" from lizard_riool_riool where upload_id=%d) data' % upload.pk

        default_database = settings.DATABASES['default']
        datasource = mapnik.PostGIS(
            host=default_database['HOST'],
            port=default_database['PORT'],
            user=default_database['USER'],
            password=default_database['PASSWORD'],
            dbname=default_database['NAME'],
            table=query
        )

        layer = mapnik.Layer(str(upload), RD)
        layer.datasource = datasource
        layer.styles.append("put")

        layers.append(layer)
        styles["put"] = style

        return layers, styles

    def extent(self, identifiers=None):
        ""
        return {'north': None, 'south': None, 'east': None, 'west': None}


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
