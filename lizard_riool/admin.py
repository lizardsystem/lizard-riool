from django.contrib import admin
from models import Put, Riool, Upload


class UploadAdmin(admin.ModelAdmin):
    readonly_fields = ['the_file', 'the_time', ]

admin.site.register(Put)
admin.site.register(Riool)
admin.site.register(Upload, UploadAdmin)
