from .models import ChatFile, ChatAlbum, ChatAudio
from sticknet.admin_site import admin_site
from django.db import transaction
from django.contrib import admin


class ChatFileAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for obj in queryset:
                obj.delete()

    readonly_fields = ['timestamp']

class ChatAlbumAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for obj in queryset:
                obj.delete()

class ChatAudioAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for obj in queryset:
                obj.delete()


admin_site.register(ChatFile, ChatFileAdmin)
admin_site.register(ChatAlbum, ChatAlbumAdmin)
admin_site.register(ChatAudio, ChatAudioAdmin)
