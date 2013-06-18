# (c) Nelen & Schuurmans. GPL licensed, see LICENSE.txt.

from __future__ import division

from math import sqrt
import logging
import os.path
import tempfile
import urllib

from django.contrib.gis.geos import Point
from django.core.cache import get_cache
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils import simplejson as json
from django.views.generic import TemplateView, View
from matplotlib import figure, transforms
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import networkx as nx

from lizard_map.coordinates import RD
from lizard_map.matplotlib_settings import SCREEN_DPI
from lizard_map.models import WorkspaceEditItem
from lizard_map.views import AppView
from lizard_ui.views import ViewContextMixin

from lizard_riool import parsers
from lizard_riool import tasks
from lizard_riool.datamodel import RMB
from lizard_riool.layers import SewerageAdapter
from lizard_riool.layers import get_class_boundaries
from lizard_riool.models import Manhole
from lizard_riool.models import Riool, Rioolmeting, Upload
from lizard_riool.models import Sewer
from lizard_riool.models import Sewerage
from lizard_riool.models import UploadedFileError
from lizard_riool.waar import WAAR

logger = logging.getLogger(__name__)

cache = get_cache('file_based_cache')


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

        # Init RMB object
        rmb = RMB(upload_id)
        rmb.compute_lost_water_depth(putten[0])

        mrios = parsers.string_of_riool_to_string_of_rioolmeting(
            rmb.pool, strengen)

        data = {}

        for suf_id in strengen:
            data[suf_id] = []

        for mrio in mrios:
            data[mrio.suf_fk_edge].append(mrio)

        # Store the index and label of each manhole,
        # so a vertical line can be drawn.

        verticals = []

        # bobs: "Bovenkant Onderkant Buizen"
        # obbs: "Onderkant Bovenkant Buizen"

        bobs, obbs, water, coordinates = [], [], [], []
        for idx, suf_id in enumerate(strengen):
            # The RIOO record.
            riool = rmb.get_riool(suf_id)

            # Append PUT to start from.
            put_source = putten[idx]
            obj = parsers.get_obj_from_graph(rmb.graph, put_source)
            if obj:
                put_source_xy = riool.get_knooppuntcoordinaten(put_source)
                coordinates.append(put_source_xy)
                verticals.append((len(coordinates) - 1, put_source))
                bobs.append(obj.z)
                if obj.is_put and hasattr(obj, 'maxz'):
                    # Instead of obj.z, use the maximum z value of the
                    # strengs connected to this put
                    obbs.append(obj.maxz + riool.height)
                else:
                    obbs.append(obj.z + riool.height)
                water.append(obj.z + obj.flooded)

            # Append MRIO measurements.

            for mrio in data[suf_id]:
                # Skip objects not having a "flooded" attribute.
                # https://office.lizard.net/trac/ticket/3547.
                # TODO: this has to be solved properly.
                if hasattr(mrio, 'flooded'):
                    coordinates.append(Point(mrio.point[0], mrio.point[1]))
                    bobs.append(mrio.point[2])
                    obbs.append(mrio.point[2] + riool.height)  # Too simple!
                    water.append(mrio.point[2] + mrio.flooded)

            # Append PUT to end with.

            put_target = putten[idx + 1]
            obj = parsers.get_obj_from_graph(rmb.graph, put_target)
            if obj:
                put_target_xy = riool.get_knooppuntcoordinaten(put_target)
                coordinates.append(put_target_xy)

                bobs.append(obj.z)
                # Top of the line

                # For a put, the top isn't necessarily above this
                # particular bottom, but above the bottom of the
                # highest streng leading up to it, saved in obj.height
                # if it's a put. Then riool.height may be the wrong
                # height, but it will have to do for now.
                if obj.is_put and hasattr(obj, 'maxz'):
                    # Instead of obj.z, use the maximum z value of the
                    # strengs connected to this put
                    obbs.append(obj.maxz + riool.height)
                else:
                    obbs.append(obj.z + riool.height)
                water.append(obj.z + obj.flooded)
#                bobs.append(put_target_bob)
#                obbs.append(put_target_bob + riool.height)
#                water.append(put_target_bob + obj.flooded)

        if obj:
            verticals.append((len(coordinates) - 1, put_target))

        #
        distances = [0.0]
        for i in range(len(coordinates) - 1):
            distance = distances[i] + sqrt(
                (coordinates[i].x - coordinates[i + 1].x) ** 2 +
                (coordinates[i].y - coordinates[i + 1].y) ** 2
            )
            distances.append(distance)

        # Create matplotlib figure.

        fig = ScreenFigure(width, height)
        fig.subplots_adjust(top=0.85)  # Space for labels
        ax1 = fig.add_subplot(111)
        ax1.plot(distances, bobs, color='brown')
        ax1.plot(distances, obbs, color='brown')
        ax1.fill_between(distances, bobs, water, interpolate=False, alpha=0.5)
        ax1.set_xlim(0)
        ax1.set_xlabel('Afstand (m)')
        ax1.set_ylabel('Diepte t.o.v. NAP (m)')
        ax1.grid(True)

        # Plot PUT labels.

        transform = transforms.blended_transform_factory(
            ax1.transData, ax1.transAxes)

        for vertical in verticals:
            x = distances[vertical[0]]
            ax1.axvline(x=x, color='green')
            ax1.text(x, 1.01, vertical[1], rotation='vertical',
                transform=transform, va='bottom', fontsize=9)

        # Return image as png.

        response = HttpResponse(content_type='image/png')
        canvas = FigureCanvas(fig)
        canvas.print_png(response)

        return response


class SideProfileGraph2(View):

    def get(self, request, *args, **kwargs):

        # Initialize variables with request parameters.

        sewerage_pk = int(request.GET['upload_id'])
        manholes = json.loads(request.GET['putten'])
#       sewers = json.loads(request.GET['strengen'])
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

        d = {manhole.code: manhole for manhole in G.nodes()}

        # Create matplotlib figure.

        fig = ScreenFigure(width, height)
        fig.subplots_adjust(top=0.84)  # Space for labels
        ax1 = fig.add_subplot(111)
        ax1.set_xlabel('Afstand (m)')
        ax1.set_ylabel('Diepte t.o.v. NAP (m)')
        ax1.grid(True)

        # Visualize manholes as vertical lines with labels.

        xs = [0]

        for i in range(len(manholes) - 1):
            sewer = G[d[manholes[i]]][d[manholes[i + 1]]]['sewer']
            xs.append(xs[-1] + sewer.the_geom_length)

#       transform = transforms.blended_transform_factory(
#           ax1.transData, ax1.transAxes
#       )

#       for x, label in zip(xs, manholes):
#           ax1.axvline(x, color='red')
#           ax1.text(x, 1.01, label, rotation='vertical',
#               transform=transform, va='bottom', fontsize=9
#           )

        # Visualize ground level.

        ground_levels = []

        for manhole in manholes:
            ground_levels.append(d[manhole].ground_level)

#       ax1.plot(xs, ground_levels, color='green')

        # Visualize measurements.

        for i in range(len(manholes) - 1):

            bobx, boby, obby, water = [], [], [], []
            sewer = G[d[manholes[i]]][d[manholes[i + 1]]]['sewer']

            bobx.append(0)
            boby.append(sewer.bob1)
            obby.append(sewer.bob1 + sewer.diameter)
            ##water.append(?)

            for measurement in sewer.measurements.order_by('dist'):
                bobx.append(measurement.dist)
                boby.append(measurement.bob)
                obby.append(measurement.obb)
                water.append(measurement.water_level)

            bobx.append(sewer.the_geom_length)
            boby.append(sewer.bob2)
            obby.append(sewer.bob2 + sewer.diameter)
            ##water.append(?)

            if sewer.manhole1.code == manholes[i]:
                # Direction manhole1 => manhole2
                bobx = [x + xs[i] for x in bobx]
            else:
                # Direction manhole2 => manhole1
                bobx.reverse()
                bobx = [sewer.the_geom_length - x for x in bobx]
                bobx = [x + xs[i] for x in bobx]
                boby.reverse()
                obby.reverse()
                water.reverse()

            ax1.plot(bobx, boby, color='brown')
            ax1.plot(bobx, obby, color='brown')
            bobx.pop(0), bobx.pop()
            boby.pop(0), boby.pop()
            ax1.fill_between(bobx, boby, water, interpolate=False, alpha=0.5)

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

        if not (filename.lower().endswith('.rib') or
                filename.lower().endswith('.rmb')):
            raise Exception("Upload een .RIB of .RMB file.")

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


class DownloadView(View):
    "Return computed results in a SUFRIB-like format."

    def get(self, request, *args, **kwargs):

        # The SUFRMB file for which results have been computed.
        upload = Upload.objects.get(pk=kwargs['id'])

        # A list of SUFRIB records (i.e. strings).
        results = []

        # The computation has to be finished.
        if upload.has_computed_percentages:
            self.storedgraph_dict = dict((obj.suf_id, obj) for obj in upload.
                storedgraph_set.only('suf_id', 'flooded_percentage'))
            self.rmb = RMB(upload.pk)
            with upload.the_file.file as f:
                for line in f:
                    if line.startswith('*ALGE|'):
                        # Just copy it.
                        results.append(line.strip('\r\n'))
                    elif line.startswith('*RIOO|'):
                        # Just copy it.
                        results.append(line.strip('\r\n'))
                        # Add *WAAR.
                        riool = line[6:36].strip()
                        results.extend(self.__get_results(riool))

        response = HttpResponse('\n'.join(results), content_type='text/plain')
        filename = os.path.splitext(upload.filename)[0] + '_results.txt'
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        return response

    def __get_results(self, riool):
        """Construct and return *WAAR records.

        Each *MRIO can be classified according to its percentage flooded.
        The class boundaries are printed in the ZZI and ZZJ fields of
        the *WAAR record. Only *WAAR records that mark a change of
        class are returned.
        """
        results = []
        prev_klasse = None
        for obj in self.rmb.pool[riool]:
            if isinstance(obj, Rioolmeting):
                try:
                    node = self.storedgraph_dict[obj.suf_id]
                except KeyError:
                    msg = "Skipping %s (not in stored graph)." % obj.suf_id
                    logger.debug(msg)
                    continue
                pct = node.flooded_percentage
                klasse, min_pct, max_pct = get_class_boundaries(pct)
                if klasse != prev_klasse:
                    waar = WAAR()
                    waar.ZZA = obj.ZYA
                    waar.ZZB = obj.ZYB
                    waar.ZZE = riool
                    waar.ZZF = 'BDD'
                    waar.ZZI = min_pct
                    waar.ZZJ = max_pct
                    waar.ZZV = 'Door Lizard Riool Toolkit'
                    results.append(str(waar))
                    prev_klasse = klasse
        return results


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
            Manhole.objects.
            filter(sewerage__pk__in=sewerage_pks).
            filter(the_geom__distance_lte=(pnt, radius)).
            distance(pnt).order_by('distance')
        )

        try:
            manhole = manholes[0]  # SELECT ... LIMIT 1;
        except:
            return self.render_to_response()

        # GEOS transform() is not accurate for 28992.
        # The infamous towgs84 parameter is missing?

        if srid == 28992:
            manhole.the_geom.transform(RD)
        else:
            manhole.the_geom.transform(srid)

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
            location.transform(RD)  # TODO
            put = {'put': put, 'x': location.x, 'y': location.y}
            putten.append(put)

        context = {'strengen': strengen, 'putten': putten}

        return self.render_to_response(context)


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
                        'file_line': line.strip(),
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

    upload.delete()

    return HttpResponse()
