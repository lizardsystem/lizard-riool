# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.conf.urls.defaults import patterns
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from lizard_riool.views import FileView, UploadView
from lizard_ui.urls import debugmode_urlpatterns

admin.autodiscover()

urlpatterns = patterns('',
    (r'^beheer/$', login_required(FileView.as_view())),
    (r'^beheer/files/$', login_required(FileView.as_view(template_name="lizard_riool/files.html"))),
    (r'^upload/$', login_required(UploadView.as_view())),
)

urlpatterns += debugmode_urlpatterns()
