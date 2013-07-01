# (c) Nelen & Schuurmans. GPL licensed, see LICENSE.txt.

from django.conf.urls.defaults import include, patterns, url
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from lizard_riool import views
from lizard_ui.urls import debugmode_urlpatterns

admin.autodiscover()

urlpatterns = patterns(
    '',
    # Upload pages
    (r'^beheer/uploads/$', login_required(views.UploadsView.as_view())),
    (r'^beheer/uploads/files/$', views.uploaded_file_list),
    # The next line expects DELE requests
    url('^beheer/uploads/files/uploaded-file-(?P<upload_id>\d+)/$',
        login_required(views.delete_uploaded_file),
        name='lizard_riool_delete_uploaded_file'),
    url('^beheer/uploads/files/uploaded-file-(?P<upload_id>\d+)/errors/$',
        login_required(views.UploadedFileErrorsView.as_view()),
        name='lizard_riool_uploaded_file_error_view'),

    # Stelsels, profielen
    (r'^stelsels/$', login_required(views.SewerageView.as_view())),
    (r'^langsprofielen/graph/$', login_required(
            views.SideProfileGraph2.as_view())),
    (r'^langsprofielen/popup/$', login_required(
            views.SideProfilePopup.as_view())),

    # Archiefpagina
    url(r'^archief/$',
        login_required(views.ArchivePage.as_view()),
        name='lizard_riool_archive_page'),
    url(r'^archief/(?P<page_number>\d+)/$',
        login_required(views.ArchivePage.as_view()),
        name='lizard_riool_archive_page_numbered'),

    # Activate / deactivate and also deletion. One uses POST the other DELETE
    url(r'^stelsels/(?P<sewerage_id>\d+)/$',
        login_required(views.activate_sewerage_view),
        name='lizard_riool_activate_sewerage'),
    # Download originals
    url(r'^stelsels/(?P<sewerage_id>\d+)/(?P<filename>.+)$',
        login_required(views.download_original_view),
        name='lizard_riool_download_original'),

    (r'^beheer/files/$', login_required(
            views.FileView.as_view(template_name="lizard_riool/files.html"))),
    url(r'^beheer/files/upload/$', login_required(views.UploadView.as_view()),
        name="upload_dialog_url"),
    (r'^beheer/files/delete/(?P<id>\d+)/$', login_required(
            views.DeleteFileView.as_view())),
    (r'^langsprofielen/$', login_required(views.SideProfileView.as_view())),
    (r'^beheer/$', login_required(views.FileView.as_view())),
    (r'^put/$', login_required(views.ManholeFinder.as_view())),
    (r'^bar/$', login_required(views.PathFinder.as_view())),
)

if settings.DEBUG:
    urlpatterns += patterns('', ('^djcelery/', include('djcelery.urls')))

urlpatterns += debugmode_urlpatterns()
