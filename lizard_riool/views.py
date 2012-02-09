# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.core.files import File
from django.db import transaction
from django.http import HttpResponse
from django.utils import simplejson as json
from django.views.generic import TemplateView
from lizard_map.views import AppView
from models import Upload
from parsers import parse
import logging
import os.path
import tempfile

logger = logging.getLogger(__name__)


class FileView(AppView):
    "View file uploads."
    template_name = 'lizard_riool/beheer.html'

    def files(self):
        return Upload.objects.all()


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
                    print "SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSs"
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
