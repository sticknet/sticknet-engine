from .models import User, ProfilePicture, ProfileCover, Device, LimitedAccessToken, Preferences, AppSettings, EmailVerification
from sticknet.admin_site import admin_site
from knox.models import AuthToken
from sticknet.settings import DEBUG
from django.contrib import admin
from django.db import transaction

class UserAdmin(admin.ModelAdmin):
    search_fields = ['username', 'email']

    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for obj in queryset:
                obj.delete()

class ProfilePictureAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for obj in queryset:
                obj.delete()

class ProfileCoverAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for obj in queryset:
                obj.delete()


admin_site.register(User, UserAdmin)
admin_site.register(Device)
admin_site.register(LimitedAccessToken)
admin_site.register(ProfilePicture, ProfilePictureAdmin)
admin_site.register(ProfileCover, ProfileCoverAdmin)
admin_site.register(Preferences)
admin_site.register(AppSettings)
admin_site.register(EmailVerification)
if not DEBUG:
    admin_site.register(AuthToken)



