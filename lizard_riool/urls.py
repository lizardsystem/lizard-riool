# (c) Nelen & Schuurmans. GPL licensed, see LICENSE.txt.

from django.conf.urls.defaults import include, patterns
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from lizard_riool import views
from lizard_ui.urls import debugmode_urlpatterns

admin.autodiscover()

urlpatterns = patterns('',
    (r'^beheer/$', login_required(views.FileView.as_view())),
    (r'^beheer/files/$', login_required(views.FileView.as_view(template_name="lizard_riool/files.html"))),
    (r'^beheer/files/upload/$', login_required(views.UploadView.as_view())),
    (r'^beheer/files/delete/(?P<id>\d+)/$', login_required(views.DeleteFileView.as_view())),
    (r'^langsprofielen/$', login_required(views.SideProfileView.as_view())),
    (r'^langsprofielen/graph/$', login_required(views.SideProfileGraph.as_view())),
    (r'^langsprofielen/popup/$', login_required(views.SideProfilePopup.as_view())),
    (r'^putten/$', login_required(views.PutList.as_view())),
    (r'^put/$', login_required(views.PutFinder.as_view())),
    (r'^bar/$', login_required(views.Bar.as_view())),
)

if settings.DEBUG:
    urlpatterns += patterns('', ('^djcelery/', include('djcelery.urls')))

urlpatterns += debugmode_urlpatterns()

