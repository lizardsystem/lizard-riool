# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.contrib.gis.geos import Point
from django.core.files import File
from django.db import transaction
from django.http import HttpResponse
from django.utils import simplejson as json
from django.views.generic import TemplateView, View
from lizard_map.models import WorkspaceEdit
from lizard_map.views import AppView
from math import sqrt
from models import Riool, Upload
from parsers import parse
import logging
import networkx as nx
import os.path
import tempfile

logger = logging.getLogger(__name__)


class FileView(AppView):
    "View file uploads."
    template_name = 'lizard_riool/beheer.html'
    javascript_click_handler = ''  # do nothing: requires lizard_map >= 3.24
    javascript_click_handler = 'do_nothing_click_handler'

    def files(self):
        return Upload.objects.all()


class SideProfileView(AppView):
    "View side profiles."
    template_name = 'lizard_riool/side_profile.html'
    javascript_click_handler = 'put_click_handler'

    def files(self):
        return Upload.objects.filter(the_file__iendswith='.rmb')


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
            context = [{
                'x': riool._put_xy.x,
                'y': riool._put_xy.y,
                'put': riool._put_label,
                'upload_id': riool.upload.pk,
            }]
        else:
            context = []

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
            G.add_edge(riool.AAD, riool.AAF)
            G.node[riool.AAD]['location'] = riool.AAE
            G.node[riool.AAF]['location'] = riool.AAG

        try:
            path = nx.shortest_path(G, source, target)
        except nx.NetworkXNoPath:
            logger.warning("No path from %s to %s" % (source, target))
            path = []

        context = []
        for put in path:
            location = G.node[put]['location']
            context.append({
                'put': put,
                'x': location.x,
                'y': location.y,
            })

        return self.render_to_response(context)

    def render_to_response(self, context):
        return HttpResponse(json.dumps(context), mimetype="application/json")
