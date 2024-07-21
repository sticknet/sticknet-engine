from django.contrib import admin
from .models import Group, GroupCover, TempDisplayName, GroupRequest, Cipher
from sticknet.admin_site import admin_site
from django.db import transaction
class GroupAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for obj in queryset:
                obj.delete()


class GroupCoverAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for obj in queryset:
                obj.delete()

admin_site.register(Group, GroupAdmin)
admin_site.register(GroupCover, GroupCoverAdmin)
admin_site.register(TempDisplayName)
admin_site.register(GroupRequest)
admin_site.register(Cipher)

