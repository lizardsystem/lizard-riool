# (c) Nelen & Schuurmans. GPL licensed, see LICENSE.txt.

from __future__ import division

import logging
import os.path
import tempfile
import urllib

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse
from django.utils import simplejson as json
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView, View
from django.views.static import serve

from matplotlib import figure, transforms
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import networkx as nx

from lizard_map.coordinates import RD
from lizard_map.matplotlib_settings import SCREEN_DPI
from lizard_map.models import WorkspaceEditItem
from lizard_map.views import AppView
from lizard_ui.views import ViewContextMixin

from sufriblib.parsers import enumerate_file

from lizard_riool import tasks
from lizard_riool import models
from lizard_riool.layers import SewerageAdapter
from lizard_riool.models import Upload
from lizard_riool.models import Sewer
from lizard_riool.models import Sewerage
from lizard_riool.models import UploadedFileError
from lizard_riool.waar import WAAR

logger = logging.getLogger(__name__)


def transform(the_geom, srid):
    """Perform an in-place geometry transformation.

    the_geom: a GEOSGeometry
    srid: an integer SRID

    GEOS transform() is not accurate for 28992.
    The infamous towgs84 parameter is missing?

    """

    if srid == 28992:
        the_geom.transform(RD)
    else:
        the_geom.transform(srid)


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


class DeleteFileView(View):
    "Delete a previously uploaded file."

    def post(self, request, *args, **kwargs):
        upload = Upload.objects.get(pk=kwargs['id'])
        upload.the_file.delete()  # from filesystem
        upload.delete()  # from database
        return HttpResponse()


class SideProfileView(AppView):
    "View side profiles."
    template_name = 'lizard_riool/side_profile.html'
    javascript_click_handler = 'put_click_handler'

    def files(self):
        files = [{
                "upload": upload,
                "available": upload.has_computed_percentages
                }
                 for upload in
                 Upload.objects.filter(the_file__iendswith='.rmb')]

        self.some_missing = any(not f['available'] for f in files)
        if self.some_missing:
            # Then create them
            tasks.compute_lost_capacity_async()

        return files


class SewerageView(AppView):
    """Docstring.

    """
    template_name = 'lizard_riool/sewerage.html'
    javascript_click_handler = 'put_click_handler'

    def sewerages(self):
        return Sewerage.objects.filter(active=True).order_by('name')


class SideProfilePopup(TemplateView):
    ""

    template_name = 'lizard_riool/side_profile_popup.html'

    def post(self, request, *args, **kwargs):

        upload_id = request.POST.get('upload_id')
        putten = request.POST.getlist('putten[]')
        strengen = request.POST.getlist('strengen[]')

        # Unlike Chrome, Firefox sends dimensions as float.

        width = int(float(request.POST.get('width', 900)))
        height = int(float(request.POST.get('height', 300)))

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


class SideProfileGraph2(View):

    def get(self, request, *args, **kwargs):

        # Initialize variables with request parameters.

        sewerage_pk = int(request.GET['upload_id'])
        manholes = json.loads(request.GET['putten'])
        width = int(request.GET['width'])
        height = int(request.GET['height'])

        # Create an empty graph.

        G = nx.Graph()

        # Create nodes (manholes) and edges (sewers).

        sewers = (
            Sewer.objects.filter(sewerage__pk=sewerage_pk).
            select_related('manhole1', 'manhole2')
        )

        for sewer in sewers:
            G.add_edge(sewer.manhole1, sewer.manhole2, sewer=sewer)

        # Create a convience dict, mapping a manhole to its code.

        d = {manhole.code: manhole for manhole in G.nodes()}

        # Create matplotlib figure.

        fig = ScreenFigure(width, height)
        ax1 = fig.add_subplot(111)

        # Place the manholes being traversed on a straight line.

        xs = [0]

        for i in range(len(manholes) - 1):
            sewer = G[d[manholes[i]]][d[manholes[i + 1]]]['sewer']
            xs.append(xs[-1] + sewer.the_geom_length)

        # Visualize ground level.

        ground_levels = []

        for manhole in manholes:
            ground_levels.append(d[manhole].ground_level)

        ax1.plot(xs, ground_levels, color='green')

        # Visualize measurements.

        for i in range(len(manholes) - 1):

            bobx, boby, obby, water = [], [], [], []
            sewer = G[d[manholes[i]]][d[manholes[i + 1]]]['sewer']

            for measurement in sewer.measurements.order_by('dist'):
                bobx.append(measurement.dist)
                boby.append(measurement.bob)
                obby.append(measurement.obb)
                # Sewers that are not connected to a sink,
                # either directly or indirectly, have a
                # water_level of `None`.
                if measurement.water_level is not None:
                    water_level = measurement.water_level
                else:
                    water_level = measurement.bob
                water.append(water_level)

            if sewer.manhole1.code == manholes[i]:
                # Direction manhole1 => manhole2
                bobx = [x + xs[i] for x in bobx]
            else:
                # Direction manhole2 => manhole1
                bobx = [xs[i + 1] - x for x in bobx]

            ax1.plot(bobx, boby, color='brown')
            ax1.plot(bobx, obby, color='brown')
            ax1.fill_between(bobx, boby, water, interpolate=False, alpha=0.5)

        # Visualize manholes as labeled, vertical lines.

        transform = transforms.blended_transform_factory(
            ax1.transData, ax1.transAxes
        )

        for x, label in zip(xs, manholes):
            ax1.axvline(x, color='red')
            ax1.text(x, 1.01, label, rotation='vertical', transform=transform,
                fontsize=9, ha='center', va='bottom',
            )

        # Finalize matplotlib figure.

        fig.subplots_adjust(top=0.84)  # Space for labels
        ax1.set_xlim(0)
        ax1.set_xlabel('Afstand (m)')
        ax1.set_ylabel('Diepte t.o.v. NAP (m)')
        ax1.grid(True)

        # Return image as png.

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
            upload = Upload()
            upload.move_file(fullpath)
            tasks.process_uploaded_file.delay(upload)

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


class JSONResponseMixin(object):

    def render_to_response(self, context={}):
        return HttpResponse(json.dumps(context), mimetype="application/json")


class ManholeFinder(View, JSONResponseMixin):
    "Find the nearest manhole within a certain radius around a point."

    def get(self, request, *args, **kwargs):

        # Initialize variables with request parameters.

        x = float(request.GET.get('x'))
        y = float(request.GET.get('y'))
        radius = float(request.GET.get('radius'))
        srs = request.GET.get('srs')  # e.g. EPSG:28992
        workspace_id = int(request.GET.get('workspace_id'))

        # Which sewerages are we looking at?

        sewerage_pks = []

        workspace_items = (
            WorkspaceEditItem.objects.
            filter(workspace__pk=workspace_id).
            filter(visible=True)
        )

        for workspace_item in workspace_items:
            if isinstance(workspace_item.adapter, SewerageAdapter):
                sewerage_pks.append(workspace_item.adapter.id)

        if not sewerage_pks:
            return self.render_to_response()

        # What is the nearest manhole?

        srid = int(srs.split(':')[1])  # e.g. 28992
        pnt = Point(x, y, srid=srid)

        manholes = (
            models.Manhole.objects.
            filter(sewerage__pk__in=sewerage_pks).
            filter(the_geom__distance_lte=(pnt, radius)).
            distance(pnt).order_by('distance')
        )

        try:
            manhole = manholes[0]  # SELECT ... LIMIT 1;
        except:
            return self.render_to_response()

        transform(manhole.the_geom, srid)

        context = {
            'x': manhole.the_geom.x,
            'y': manhole.the_geom.y,
            'put': manhole.code,
            'upload_id': manhole.sewerage.pk,
        }

        return self.render_to_response(context)


class PathFinder(View, JSONResponseMixin):
    "Find the shortest path between two manholes."

    def get(self, request, *args, **kwargs):

        # Initialize variables with request parameters.

        sewerage_pk = int(request.GET.get('upload_id'))
        source = request.GET.get('source')
        target = request.GET.get('target')
        srs = request.GET.get('srs')  # e.g. EPSG:28992

        srid = int(srs.split(':')[1])  # e.g. 28992

        # Create an empty graph.

        G = nx.Graph()

        # Create nodes (manholes) and edges (sewers).

        sewers = (
            Sewer.objects.filter(sewerage__pk=sewerage_pk).
            select_related('manhole1', 'manhole2')
        )

        for sewer in sewers:
            manhole1, manhole2 = sewer.manhole1, sewer.manhole2
            G.add_edge(manhole1.code, manhole2.code, streng=sewer.code)
            G.node[manhole1.code]['location'] = manhole1.the_geom
            G.node[manhole2.code]['location'] = manhole2.the_geom

        try:
            path = nx.shortest_path(G, source, target)
        except Exception, e:
            logger.error(e)
            context = {'strengen': [], 'putten': []}
            return self.render_to_response(context)

        strengen = []

        for i in range(len(path) - 1):
            streng = G.edge[path[i]][path[i + 1]]['streng']
            strengen.append(streng)

        putten = []

        for put in path:
            location = G.node[put]['location']
            transform(location, srid)
            put = {'put': put, 'x': location.x, 'y': location.y}
            putten.append(put)

        context = {'strengen': strengen, 'putten': putten}

        return self.render_to_response(context)


class UploadsView(AppView):
    template_name = 'lizard_riool/uploads.html'
    javascript_click_handler = ''


def uploaded_file_list(request):
    return HttpResponse(json.dumps([
                {
                    "id": "uploaded-file-{0}".format(upload.pk),
                    "name": upload.filename,
                    "status": upload.status_string(),
                    "error_description": upload.error_description(),
                    "error_url": reverse(
                        "lizard_riool_uploaded_file_error_view",
                        kwargs={"upload_id": upload.id}),
                    "delete_url": reverse(
                        "lizard_riool_delete_uploaded_file",
                        kwargs={"upload_id": upload.id})
                    }
                for upload in Upload.objects.all()
                ]), mimetype="application/json")


class UploadedFileErrorsView(ViewContextMixin, TemplateView):
    template_name = 'lizard_riool/uploaded_file_error_page.html'

    def get(self, request, upload_id):
        self.uploaded_file = Upload.objects.get(pk=upload_id)
        self.user = request.user

        self.errors = self._errors()
        self.general_errors = self._general_errors()
        self.lines_and_errors = self._lines_and_errors()

        return super(UploadedFileErrorsView, self).get(request)

    def _errors(self):
        return UploadedFileError.objects.filter(
            uploaded_file=self.uploaded_file).order_by('line')

    def _general_errors(self):
        """Return the errors that have line number 0."""
        return [error.error_message
                for error in self.errors if error.line == 0]

    def _lines_and_errors(self):
        """Return a line-for-line of the file, with errors.

        Each line is a dictionary:
        - 'line_number' (1, ...)
        - 'has_error' (boolean)
        - 'file_line' (string)
        - 'errors' (list of strings)
        """

        errordict = dict()
        for error in self.errors:
            if error.line > 0:
                errordict.setdefault(error.line, []).append(
                    error.error_message)

        lines = []
        path = self.uploaded_file.the_file
        if errordict and os.path.exists(path):
            for line_minus_one, line in enumerate(open(path)):
                line_number = line_minus_one + 1
                lines.append({
                        'line_number': line_number,
                        'has_error': line_number in errordict,
                        'file_line': line.strip("\r\n"),
                        'file_line_short': line.strip("\r\n")[:300],
                        'errors': errordict.get(line_number)})

        return lines


def delete_uploaded_file(request, upload_id):
    if request.method != "DELETE":
        return

    try:
        upload = Upload.objects.get(pk=upload_id)
    except Upload.DoesNotExist:
        # Well, that's no problem here
        return HttpResponse()

    if upload.status != Upload.BEING_PROCESSED:
        # Only delete if not processing
        upload.delete()

    return HttpResponse()


class ArchivePage(AppView):
    template_name = "lizard_riool/archive_page.html"

    def get(self, request, page_number=1):
        try:
            self.page_number = int(page_number)
        except ValueError:
            self.page_number = 1

        self.paginator = Paginator(
            models.Sewerage.objects.all().order_by("name"), 15)

        return super(ArchivePage, self).get(request)

    def page(self):
        return self.paginator.page(self.page_number)

    def page_range(self):
        return self.paginator.page_range

    def previous_page_url(self):
        return reverse('lizard_riool_archive_page_numbered',
                       kwargs={'page_number': str(self.page_number - 1)})

    def next_page_url(self):
        return reverse('lizard_riool_archive_page_numbered',
                       kwargs={'page_number': str(self.page_number + 1)})


@require_http_methods(["POST", "DELETE"])
def activate_sewerage_view(request, sewerage_id):
    """The archive page POSTs to this. Posting "active=1" to a sewerage id
    activates it, "active=0" deactivates it. All errors are ignored and
    nothing is returned.

    The delete button on the archive page sends a DELETE request to this
    view. It deletes the sewerage and its files without further ado."""
    if request.method == "POST":
        if 'active' in request.POST:
            active = (request.POST['active'] == u'1')
            try:
                sewerage = Sewerage.objects.get(pk=sewerage_id)
                sewerage.active = active
                sewerage.save()
            except Sewerage.DoesNotExist:
                pass

    if request.method == "DELETE":
        try:
            sewerage = Sewerage.objects.get(pk=sewerage_id)
            sewerage.delete()
        except Sewerage.DoesNotExist:
            pass

    return HttpResponse()


def download_original_view(request, sewerage_id, filename):
    try:
        sewerage = Sewerage.objects.get(pk=sewerage_id)
    except Sewerage.DoesNotExist:
        raise Http404

    if filename == sewerage.rib_filename:
        path = sewerage.rib
    elif filename == sewerage.rmb_filename:
        path = sewerage.rmb
    elif filename == sewerage.generated_rib_filename:
        path = sewerage.generated_rib
    else:
        raise Http404

    if settings.DEBUG or '+' in path:
        # Nginx fails to serve files with a '+' in their name. Encoding
        # the '+' doesn't work, because there is an Nginx issue that says
        # it doesn't decode X-Accel-Redirect paths.
        # In short, we just do these ourselves...
        # XXX
        return serve(request, path, '/')

    response = HttpResponse()
    response['X-Accel-Redirect'] = (
        '/riolering/stelsels/nginx_download/{sewerage_id}/{filename}'
        .format(sewerage_id=sewerage.id, filename=filename))
    response['Content-Disposition'] = (
            'attachment; filename="{filename}"'.format(filename=filename))
    # content-type is set in nginx.
    response['Content-Type'] = ''
    return response
