from django_otp.admin import OTPAdminSite
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
from .settings import DEBUG
from django.contrib import admin

class OTPAdmin(OTPAdminSite):
    pass


admin_site = OTPAdmin(name='OTPAdmin') if not DEBUG else admin.site
if not DEBUG:
    admin_site.register(TOTPDevice, TOTPDeviceAdmin)
admin_site.site_header = "Sticknet" if DEBUG else "Sticknet | PRODUCTION"
admin_site.index_title = "Debug API Admin" if DEBUG else "PRODUCTION API ADMIN"
admin_site.site_title = 'Sticknet'
