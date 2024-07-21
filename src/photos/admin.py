from .models import Image, Album, Note, Blob
from sticknet.admin_site import admin_site
from django.db import transaction
from django.contrib import admin
class ImageAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for obj in queryset:
                obj.delete()

admin_site.register(Image, ImageAdmin)
admin_site.register(Blob)
admin_site.register(Album)
admin_site.register(Note)
