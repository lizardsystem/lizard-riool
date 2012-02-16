from django.contrib import admin
from models import Put, Upload


class UploadAdmin(admin.ModelAdmin):
    readonly_fields = ['the_file', 'the_time', ]

admin.site.register(Put)
admin.site.register(Upload, UploadAdmin)
