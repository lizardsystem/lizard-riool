import logging
import os

from django.conf import settings
from django.contrib.gis import geos
from django.contrib.gis.geos import fromstr
from staticfiles import finders
import mapnik

from lizard_map.models import ICON_ORIGINALS
from lizard_map.symbol_manager import SymbolManager
from lizard_map.workspace import WorkspaceItemAdapter

from lizard_riool.models import Manhole
from lizard_riool.models import Sewer
from lizard_riool.models import SewerMeasurement

logger = logging.getLogger(__name__)

# Colors from http://www.herethere.net/~samson/php/color_gradient/

CLASSES = (
    ('A', '0%-10%',   0.00, 0.10, '00ff00'),  # green
    ('B', '10%-25%',  0.10, 0.25, '3fbf00'),
    ('C', '25%-50%',  0.25, 0.50, '7f7f00'),
    ('D', '50%-75%',  0.50, 0.75, 'bf3f00'),
    ('E', '75%-100%', 0.75, 1.01, 'ff0000'),  # red
    ('?', 'Onbekend', 1.00, 0.00, '000000'),  # black
)


def get_class_boundaries(pct):
    "Return the class and its boundaries for a given fraction."
    for klasse, _, min_pct, max_pct, _ in CLASSES:
        if pct >= min_pct and pct < max_pct:
            return klasse, min_pct, max_pct


MEDIA_URL = settings.MEDIA_URL
STATIC_URL = settings.STATIC_URL
GENERATED_ICONS = os.path.join(settings.MEDIA_ROOT, 'generated_icons')
SYMBOL_MANAGER = SymbolManager(ICON_ORIGINALS, GENERATED_ICONS)
RIOOL_ICON = 'pixel2.png'
RIOOL_ICON_LARGE = 'pixel16.png'

DATABASE = settings.DATABASES['default']
PARAMS = {
    'host': DATABASE['HOST'],
    'port': DATABASE['PORT'],
    'user': DATABASE['USER'],
    'password': DATABASE['PASSWORD'],
    'dbname': DATABASE['NAME'],
}


def html_to_mapnik(color):
    r, g, b = color[0:2], color[2:4], color[4:6]
    rr, gg, bb = int(r, 16), int(g, 16), int(b, 16)

    return rr / 255.0, gg / 255.0, bb / 255.0, 1.0


def default_database_params():
    """Get default database params. Use a copy of the dictionary
    because it is mutated by the functions that use it."""
    return PARAMS.copy()


class SewerageAdapter(WorkspaceItemAdapter):

    def __init__(self, *args, **kwargs):
        super(SewerageAdapter, self).__init__(*args, **kwargs)
        self.id = int(self.layer_arguments['id'])
        logger.debug("Sewerage.pk=%d", self.id)

    def extent(self, identifiers=None):
        "Return the sewerage extent in Google projection."

        qs = Manhole.objects.filter(sewerage__pk=self.id)

        if qs.count() < 1:
            return super(SewerageAdapter, self).extent(identifiers)
        else:
            box = fromstr('MULTIPOINT (%s %s, %s %s)' % qs.extent())
            box.set_srid(qs[0].the_geom.srid)
            box.transform(3857)  # aka 900913
            return {
                'west': box[0].x, 'south': box[0].y,  # xmin, ymin
                'east': box[1].x, 'north': box[1].y,  # xmax, ymax
            }

    def search(self, x, y, radius=None):
        """Find the nearest SewerMeasurement.

        We only use this for the mouse hover function; return
        the minimal amount of information necessary to show
        the so-called `lost capacity`.

        """
        pnt = geos.Point(x, y, srid=3857)  # aka 900913

        qs = (
            SewerMeasurement.objects.
            filter(sewer__sewerage__pk=self.id).
            filter(the_geom__distance_lte=(pnt, radius)).
            distance(pnt).order_by('distance')
        )

        try:
            m = qs[0]  # SELECT ... LIMIT 1;
        except:
            return []

        return [{
            'name': '{:.0%} verloren berging'.format(m.flooded_pct),
            'distance': m.distance.m,
            'stored_graph_id': m.pk,
        }]

    def legend(self, updates=None):
        """Return a legend describing the different classes of lost capacity.

        A `legend` is simply a list of dictionaries.

        """
        legend = []

        # Lost capacity classes

        for name, description, _, _, color in CLASSES:
            r, g, b, a = html_to_mapnik(color)
            icon = SYMBOL_MANAGER.get_symbol_transformed(
                RIOOL_ICON_LARGE, color=(r, g, b, a)
            )
            legend.append({
                'img_url': os.path.join(MEDIA_URL, 'generated_icons', icon),
                'description': "klasse {0} ({1})".format(name, description),
            })

        # Insufficient measurements

        legend.append({
            'img_url': os.path.join(
                STATIC_URL, 'lizard_riool/sewer-label-red.png'
             ),
            'description': 'Onvoldoende metingen'
        })

        # Sufficient measurements

        legend.append({
            'img_url': os.path.join(
                STATIC_URL, 'lizard_riool/sewer-label-green.png'
             ),
            'description': 'Voldoende metingen'
        })

        # No measurements

        legend.append({
            'img_url': os.path.join(
                STATIC_URL, 'lizard_riool/sewer-label-blue.png'
             ),
            'description': 'Geen metingen'
        })

        return legend

    def layer(self, layer_ids=None, request=None):
        "Return Mapnik layers and styles."
        layers, styles = [], {}
        self.__add_sewers(layers, styles)
        self.__add_manholes(layers, styles)
        self.__add_measurements(layers, styles)
        return layers, styles

    def __add_measurements(self, layers, styles):
        "Docstring."

        measurements = SewerMeasurement.objects.filter(
            sewer__sewerage__pk=self.id
        )

        style = mapnik.Style()

        for _, _, min_pct, max_pct, color in CLASSES:

            r, g, b, a = html_to_mapnik(color)

            icon = SYMBOL_MANAGER.get_symbol_transformed(
                RIOOL_ICON, color=(r, g, b, a)
            )

            rule = mapnik.Rule()
            rule.filter = mapnik.Filter(
                str("[flooded_pct] >= %s and [flooded_pct] < %s"
                % (min_pct, max_pct))
            )
            symbol = mapnik.PointSymbolizer(
                os.path.join(GENERATED_ICONS, icon), "png", 16, 16
            )
            symbol.allow_overlap = True
            rule.symbols.append(symbol)
            style.rules.append(rule)

        # Style else rule.

        r, g, b, a = html_to_mapnik('00000')

        icon = SYMBOL_MANAGER.get_symbol_transformed(
            RIOOL_ICON, color=(r, g, b, a)
        )

        rule = mapnik.Rule()
        rule.set_else(True)
        symbol = mapnik.PointSymbolizer(
            os.path.join(GENERATED_ICONS, icon), "png", 16, 16
        )
        symbol.allow_overlap = True
        rule.symbols.append(symbol)
        style.rules.append(rule)

        # Setup datasource.

        params = default_database_params()
        params['table'] = "({}) data".format(measurements.query)
        datasource = mapnik.PostGIS(**params)
        params = default_database_params()

        # Define layer.

        layer = mapnik.Layer('measurementLayer')
        layer.datasource = datasource
        layer.maxzoom = 35000
        layer.styles.append('measurementStyle')

        layers.append(layer)
        styles['measurementStyle'] = style

    def __add_sewers(self, layers, styles):
        "Add sewer layer and styles."

        # Get all sewer pipes that constitute to this sewerage.

        sewers = Sewer.objects.filter(sewerage__pk=self.id)

        # Define a style.

        style = mapnik.Style()

        # QUALITY_UNKNOWN

        rule = mapnik.Rule()
        rule.filter = mapnik.Filter(
            "[quality] = {}".format(Sewer.QUALITY_UNKNOWN)
        )
        rule.max_scale = 1700
        symbol = mapnik.TextSymbolizer(
            'code', 'DejaVu Sans Book', 10, mapnik.Color('blue')
        )
        symbol.allow_overlap = True
#       symbol.label_placement = mapnik.label_placement.LINE_PLACEMENT
        rule.symbols.append(symbol)
        style.rules.append(rule)

        # QUALITY_RELIABLE

        rule = mapnik.Rule()
        rule.filter = mapnik.Filter(
            "[quality] = {}".format(Sewer.QUALITY_RELIABLE)
        )
        rule.max_scale = 1700
        symbol = mapnik.TextSymbolizer(
            'code', 'DejaVu Sans Book', 10, mapnik.Color('green')
        )
        symbol.allow_overlap = True
#       symbol.label_placement = mapnik.label_placement.LINE_PLACEMENT
        symbol.allow_overlap = True
        symbol.opacity = 1.0
        rule.symbols.append(symbol)
        style.rules.append(rule)

        # QUALITY_UNRELIABLE

        rule = mapnik.Rule()
        rule.filter = mapnik.Filter(
            "[quality] = {}".format(Sewer.QUALITY_UNRELIABLE)
        )
        rule.max_scale = 1700
        symbol = mapnik.TextSymbolizer(
            'code', 'DejaVu Sans Book', 10, mapnik.Color('red')
        )
        symbol.allow_overlap = True
#       symbol.label_placement = mapnik.label_placement.LINE_PLACEMENT
#       symbol.displacement(16, 16)  # slightly above
        rule.symbols.append(symbol)
        style.rules.append(rule)

        # Setup datasource.

        params = default_database_params()
        params['table'] = "({}) data".format(sewers.query)
        datasource = mapnik.PostGIS(**params)

        # Define layer.

        layer = mapnik.Layer('sewerLayer')
        layer.datasource = datasource
        layer.maxzoom = 35000
        layer.styles.append('sewerStyle')

        layers.append(layer)
        styles['sewerStyle'] = style

    def __add_manholes(self, layers, styles):
        "Add manhole layer and styles."

        # Select the manholes that are part of this sewerage.

        manholes = Manhole.objects.filter(sewerage__pk=self.id)

        # Define a style.

        style = mapnik.Style()

        # Style the `normal` manholes.

        rule = mapnik.Rule()
        rule.filter = mapnik.Filter("[sink] != 1")
        symbol = mapnik.PointSymbolizer()
        symbol.allow_overlap = True
        rule.symbols.append(symbol)
        style.rules.append(rule)

        # Style the sink.

        rule = mapnik.Rule()
        rule.filter = mapnik.Filter("[sink] = 1")
        symbol = mapnik.PointSymbolizer(
            str(finders.find("lizard_riool/sink.png")), "png", 8, 8
        )
        symbol.allow_overlap = True
        rule.symbols.append(symbol)
        style.rules.append(rule)

        # Add labels.

        rule = mapnik.Rule()
        rule.max_scale = 1700
        symbol = mapnik.TextSymbolizer(
            'code', 'DejaVu Sans Book', 10, mapnik.Color('black')
        )
        symbol.allow_overlap = True
        symbol.label_placement = mapnik.label_placement.POINT_PLACEMENT
        symbol.vertical_alignment = mapnik.vertical_alignment.TOP
        symbol.displacement(0, -5)  # slightly above
        rule.symbols.append(symbol)
        style.rules.append(rule)

        # Setup datasource.

        params = default_database_params()
        params['table'] = "({}) data".format(manholes.query)
        datasource = mapnik.PostGIS(**params)

        # Define layer.

        layer = mapnik.Layer('manholeLayer')
        layer.datasource = datasource
        layer.maxzoom = 35000
        layer.styles.append('manholeStyle')

        layers.append(layer)
        styles['manholeStyle'] = style
