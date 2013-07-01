from django.contrib import admin
from models import Upload


class UploadAdmin(admin.ModelAdmin):
    readonly_fields = ['the_file', 'the_time']

admin.site.register(Upload, UploadAdmin)
