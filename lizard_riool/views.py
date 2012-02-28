# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.core.files import File
from django.db import transaction
from django.http import HttpResponse
from django.utils import simplejson as json
from django.views.generic import TemplateView, View
from lizard_map import coordinates
from lizard_map.models import WorkspaceEdit
from lizard_map.views import AppView, search
from models import Upload
from parsers import parse
import logging
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


class Foo(View):
    ""

    def get(self, request, *args, **kwargs):
        x = float(request.GET.get('x'))
        y = float(request.GET.get('y'))
        radius = float(request.GET.get('radius'))
        srs = request.GET.get('srs')
        user_workspace_id = request.GET.get('user_workspace_id')
        workspace = WorkspaceEdit.objects.get(pk=user_workspace_id)

        upload_ids = []
        for workspace_item in workspace.workspace_items.filter(visible=True):
            upload_ids.append(workspace_item.adapter.id)

        from django.contrib.gis.geos import *
        from django.contrib.gis.measure import D
        from django.contrib.gis.geos import Point
        from models import Riool
        from math import sqrt

        # Cannot reliably use the QuerySet's distance method, because it will
        # always use the first geometry field for its distance calculations?

        print "@@@@@@@@@@@@"
        pnt = Point(x, y)

        riolen = []

        for riool in Riool.objects.filter(upload__pk__in=upload_ids).filter(_AAE__distance_lte=(pnt, radius)):
            riool._put_distance = sqrt((riool.AAE.x - pnt.x)**2 + (riool.AAE.y - pnt.y)**2)
            riool._put_label = riool.AAD
            riool._put_xy = riool.AAE
            riolen.append(riool)

        for riool in Riool.objects.filter(upload__pk__in=upload_ids).filter(_AAG__distance_lte=(pnt, radius)):
            riool._put_distance = sqrt((riool.AAG.x - pnt.x)**2 + (riool.AAG.y - pnt.y)**2)
            riool._put_label = riool.AAF
            riool._put_xy = riool.AAG
            riolen.append(riool)

        riolen = sorted(riolen, key=lambda riool: riool._put_distance)
        for riool in riolen:
            print riool._put_label, riool._put_distance, riool

        if len(riolen) > 0:
            riool = riolen[0]
            context = {
                'x': riool._put_xy.x,
                'y': riool._put_xy.y,
                'label': riool._put_label,
                'upload_id': riool.upload.pk,
                }
        else:
            context = None

        return self.render_to_response(context)

    def render_to_response(self, context):
        return HttpResponse(json.dumps(context), mimetype="application/json")
