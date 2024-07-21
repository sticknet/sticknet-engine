from django.contrib import admin
from .models import Notification, PNToken, Invitation, ConnectionRequest
from sticknet.admin_site import admin_site

admin_site.register(PNToken)
admin_site.register(Notification)
admin_site.register(Invitation)
admin_site.register(ConnectionRequest)
