from sticknet.admin_site import admin_site
from django.contrib import admin
from .models import File, VaultAlbum, VaultNote
from django.db import transaction

class FileAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for obj in queryset:
                obj.delete()

    readonly_fields = ['timestamp']


admin_site.register(File, FileAdmin)
admin_site.register(VaultAlbum)
admin_site.register(VaultNote)

