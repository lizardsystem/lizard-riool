# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from __future__ import division
from django.contrib.gis.geos import Point
from django.core.cache import get_cache
from django.core.files import File
from django.db import transaction
from django.http import HttpResponse
from django.utils import simplejson as json
from django.views.generic import TemplateView, View
from lizard_map.matplotlib_settings import SCREEN_DPI
from lizard_map.models import WorkspaceEdit
from lizard_map.views import AppView
from lizard_riool import parsers
from math import sqrt
from matplotlib import figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from models import Riool, Upload
from parsers import parse
from pprint import pprint
import logging
import networkx as nx
import os.path
import tempfile
import urllib

logger = logging.getLogger(__name__)
cache = get_cache('file_based_cache')


def _get_riool_from_pool(pool, suf_id):
    for obj in pool[suf_id]:
        if obj.suf_id == suf_id:
            return obj


class ScreenFigure(figure.Figure):
    """A convenience class for creating matplotlib figures.

    Dimensions are in pixels. Float division is required,
    not integer division!

    """
    def __init__(self, width, height):
        super(ScreenFigure, self).__init__(dpi=SCREEN_DPI)
        self.set_size_pixels(width, height)
        self.set_facecolor('white')

    def set_size_pixels(self, width, height):
        dpi = self.get_dpi()
        self.set_size_inches(width / dpi, height / dpi)


class FileView(AppView):
    "View file uploads."
    template_name = 'lizard_riool/beheer.html'
    javascript_click_handler = ''

    def files(self):
        return Upload.objects.all()


class SideProfileView(AppView):
    "View side profiles."
    template_name = 'lizard_riool/side_profile.html'
    javascript_click_handler = 'put_click_handler'

    def files(self):
        return Upload.objects.filter(the_file__iendswith='.rmb')


class SideProfilePopup(TemplateView):
    ""

    template_name = 'lizard_riool/side_profile_popup.html'

    def post(self, request, *args, **kwargs):

        upload_id = request.POST.get('upload_id')
        putten = request.POST.getlist('putten[]')
        strengen = request.POST.getlist('strengen[]')
        width = request.POST.get('width', 900)
        height = request.POST.get('height', 300)

        # If the length of the query string appears to be a problem,
        # the above data could be cached or saved as session data.

        context = {
            'query_string': urllib.urlencode({
                'upload_id': upload_id,
                'putten': json.dumps(putten),
                'strengen': json.dumps(strengen),
                'width': width,
                'height': height,
            }),
            'width': width,
            'height': height,
        }

        return self.render_to_response(context)


class SideProfileGraph(View):
    """Create and return a side profile ("langsprofiel") as png.
    """

    def get(self, request, *args, **kwargs):

        # Get request parameters.

        upload_id = int(request.GET['upload_id'])
        putten = json.loads(request.GET['putten'])
        strengen = json.loads(request.GET['strengen'])
        width = int(request.GET['width'])
        height = int(request.GET['height'])

        # Get or create pool.
        # Indefinite caching is not possible?

        key = "pool_%d" % upload_id
        pool = cache.get(key, {})

        if not pool:

            upload = Upload.objects.get(pk=upload_id)
            parsers.parse(upload.full_path, pool)
            parsers.convert_to_graph(pool, nx.Graph())
            cache.set(key, pool)

        mrios = parsers.string_of_riool_to_string_of_rioolmeting(
            pool, strengen)

        #

        data = {}

        for streng in strengen:
            data[streng] = []

        for mrio in mrios:
            data[mrio.ZYE].append(mrio)

        for streng in strengen:
            if data[streng][0].reference == 2:
                data[streng].reverse()

        # bobs: "Bovenkant Onderkant Buizen"
        # obbs: "Onderkant Bovenkant Buizen"

        bobs, obbs, coordinates = [], [], []
        for idx, val in enumerate(strengen):

            # The RIOO record.

            riool = _get_riool_from_pool(pool, val)

            # Append PUT to start from.

            put_source = putten[idx]
            put_source_xy = riool.get_knooppuntcoordinaten(put_source)
            put_source_bob = riool.get_knooppuntbob(put_source)
            coordinates.append(put_source_xy)
            bobs.append(put_source_bob)
            obbs.append(put_source_bob + riool.height)

            # Append MRIO measurements.

            for mrio in data[val]:
                    coordinates.append(Point(mrio.point[0], mrio.point[1]))
                    bobs.append(mrio.point[2])
                    obbs.append(mrio.point[2] + riool.height)

            # Append PUT to end with.

            put_target = putten[idx + 1]
            put_target_xy = riool.get_knooppuntcoordinaten(put_target)
            put_target_bob = riool.get_knooppuntbob(put_target)
            coordinates.append(put_target_xy)
            bobs.append(put_target_bob)
            obbs.append(put_target_bob + riool.height)

        #

        distances = [0.0]
        for i in range(len(coordinates) - 1):
            distance = distances[i] + sqrt(
                (coordinates[i].x - coordinates[i + 1].x) ** 2 + \
                (coordinates[i].y - coordinates[i + 1].y) ** 2
            )
            distances.append(distance)

        # Create matplotlib figure.

        fig = ScreenFigure(width, height)
        ax1 = fig.add_subplot(111)
        ax1.plot(distances, bobs, color='brown')
        ax1.plot(distances, obbs, color='brown')
        ax1.set_xlim(0)
        ax1.set_xlabel('Afstand (m)')
        ax1.set_ylabel('Diepte t.o.v. NAP (m)')
        ax1.grid(True, color='r', linestyle='dotted')
        ax1.spines['right'].set_linestyle('dotted')
        ax1.spines['left'].set_linestyle('dotted')
        ax1.spines['bottom'].set_linestyle('dotted')
        ax1.spines['top'].set_linestyle('dotted')
        ax1.spines['top'].set_color('r')
        ax1.spines['top'].set_alpha(0.1)
        for t in ax1.xaxis.get_ticklines(): t.set_visible(False)
        for t in ax1.yaxis.get_ticklines(): t.set_visible(False)
        response = HttpResponse(content_type='image/png')
        canvas = FigureCanvas(fig)
        canvas.print_png(response)

        return response


class UploadView(TemplateView):
    "Process file uploads."
    template_name = "lizard_riool/plupload.html"
    dtemp = tempfile.mkdtemp()

    @classmethod
    def process(cls, request):

        # Create a temporary directory for file uploads.

        if not os.path.exists(cls.dtemp):
            cls.dtemp = tempfile.mkdtemp()

        # request.POST['filename'] = the client-side filename.
        # request.FILES['file'] = the name of a part.
        # These will be equal for small files only.

        filename = request.POST['filename']
        fullpath = os.path.join(cls.dtemp, filename)
        chunks = int(request.POST.get('chunks', 1))
        chunk = int(request.POST.get('chunk', 0))

        # Start a new file or append the next chunk.
        # NB: Django manages its own chunking.

        with open(fullpath, 'wb' if chunk == 0 else 'ab') as f:
            for b in request.FILES['file'].chunks():
                f.write(b)

        # On successful parsing, store the uploaded file in its permanent
        # location. Some information will be stored into the database as
        # well for convenience and performance. Roll back on any error.

        if chunk == chunks - 1:
            with transaction.commit_on_success():
                objects = []
                parse(fullpath, objects)
                f = open(fullpath)
                upload = Upload()
                upload.the_file.save(filename, File(f))
                f.close()
                for o in objects:
                    o.upload = upload
                    o.save()

    @classmethod
    def post(cls, request, *args, **kwargs):
        """Handle file upload.

        HTTP 200 (OK) is returned, even if processing fails. Not very RESTful,
        but the only way to show custom error messages when using Plupload.
        """
        try:
            cls.process(request)
        except Exception, e:
            logger.error(e)
            result = {'error': {'details': str(e)}}
        else:
            result = {}

        return HttpResponse(json.dumps(result), mimetype="application/json")


class PutList(View):
    ""

    def get(self, request, *args, **kwargs):
        context = {'location': 'The Sea', 'description': 'Here be dragons'}
        return self.render_to_response(context)

    def render_to_response(self, context):
        return HttpResponse(json.dumps(context), mimetype="application/json")


class PutFinder(View):
    """Find the nearest "put" within a certain radius around a point.
    """

    def get(self, request, *args, **kwargs):

        x = float(request.GET.get('x'))
        y = float(request.GET.get('y'))
        radius = float(request.GET.get('radius'))
        srs = request.GET.get('srs')
        workspace_id = int(request.GET.get('workspace_id'))

        # So far, only RD New has been tested.
        # Return [] for other projections.

        if srs != "EPSG:28992":
            logger.error("%s projection not yet supported" % srs)
            return self.render_to_response([])

        workspace = WorkspaceEdit.objects.get(pk=workspace_id)

        upload_ids = []
        for workspace_item in workspace.workspace_items.filter(visible=True):
            upload_ids.append(workspace_item.adapter.id)

        # TODO: SUFRMB Only?

        pnt = Point(x, y)
        riolen = []

        # Cannot reliably use the QuerySet's distance method, because it will
        # always use the first geometry field for its distance calculations?

        # We are only interested in "putten" that are connected, i.e. that
        # are part of a "streng", so only Riool not Put is queried.

        # Investigate AAD, i.e. "Knooppuntreferentie 1".

        for riool in Riool.objects.\
            filter(upload__pk__in=upload_ids).\
            filter(_AAE__distance_lte=(pnt, radius)):
            riool._put_distance = \
                sqrt((riool.AAE.x - pnt.x) ** 2 + (riool.AAE.y - pnt.y) ** 2)
            riool._put_label = riool.AAD
            riool._put_xy = riool.AAE
            riolen.append(riool)

        # Investigate AAF, i.e. "Knooppuntreferentie 2".

        for riool in Riool.objects.\
            filter(upload__pk__in=upload_ids).\
            filter(_AAG__distance_lte=(pnt, radius)):
            riool._put_distance = \
                sqrt((riool.AAG.x - pnt.x) ** 2 + (riool.AAG.y - pnt.y) ** 2)
            riool._put_label = riool.AAF
            riool._put_xy = riool.AAG
            riolen.append(riool)

        # Sort by distance.

        riolen = sorted(riolen, key=lambda riool: riool._put_distance)

        # Return the nearest "put".

        if len(riolen) > 0:
            riool = riolen[0]
            context = {
                'x': riool._put_xy.x,
                'y': riool._put_xy.y,
                'put': riool._put_label,
                'upload_id': riool.upload.pk,
            }
        else:
            context = {}

        return self.render_to_response(context)

    def render_to_response(self, context):
        return HttpResponse(json.dumps(context), mimetype="application/json")


class Bar(View):
    ""

    def get(self, request, *args, **kwargs):
        ""
        upload_id = int(request.GET.get('upload_id'))
        source = request.GET.get('source')
        target = request.GET.get('target')

        G = nx.Graph()
        for riool in Riool.objects.filter(upload__pk=upload_id):
            G.add_edge(riool.AAD, riool.AAF, streng=riool.AAA)
            G.node[riool.AAD]['location'] = riool.AAE
            G.node[riool.AAF]['location'] = riool.AAG

        try:
            path = nx.shortest_path(G, source, target)
        except nx.NetworkXNoPath:
            logger.warning("No path from %s to %s" % (source, target))
            path = []

        strengen = []
        for i in range(len(path) - 1):
            streng = G.edge[path[i]][path[i + 1]]['streng']
            strengen.append(streng)

        putten = []
        for put in path:
            location = G.node[put]['location']
            put = {'put': put, 'x': location.x, 'y': location.y}
            putten.append(put)

        context = {'strengen': strengen, 'putten': putten}

        return self.render_to_response(context)

    def render_to_response(self, context):
        return HttpResponse(json.dumps(context), mimetype="application/json")
