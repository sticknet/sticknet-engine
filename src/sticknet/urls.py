import os
from django.urls import path
from django.urls import include, re_path
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from .admin_site import admin_site
from django.views.decorators.cache import never_cache
from django.views.static import serve

from support.views import stick_protocol_paper

favicon_url = '/public/favicon.ico' if settings.DEBUG else 'https://d3vpnljghm98zc.cloudfront.net/public/favicon.ico'
favicon_view = RedirectView.as_view(url=favicon_url, permanent=True)

urlpatterns = []

if settings.DEBUG:
    # import debug_toolbar
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.PUBLIC_URL, document_root=settings.PUBLIC_ROOT)

    # urlpatterns += path('__debug__/', include(debug_toolbar.urls)),

urlpatterns += [
    path(os.environ['ADMIN_URL'], admin_site.urls),
    re_path(r'^api/auth/', include('knox.urls')),
    re_path(r'^api/', include('chat.urls', namespace='chat')),
    re_path(r'^api/', include('iap.urls', namespace='iap')),
    re_path(r'^api/', include('groups.urls', namespace='groups')),
    re_path(r'^api/', include('notifications.urls', namespace='notifications')),
    re_path(r'^api/', include('photos.urls', namespace='photos')),
    re_path(r'^api/', include('support.urls', namespace='support')),
    re_path(r'^api/', include('keys.urls', namespace='keys')),
    re_path(r'^api/', include('users.urls', namespace='users')),
    re_path(r'^api/', include('vault.urls', namespace='vault')),
    re_path(r'^api/', include('wallet.urls', namespace='wallet')),
    re_path(r'^stick-protocol.pdf$', stick_protocol_paper, name='stick_protocol_paper'),
    re_path(r'^service-worker.js$', never_cache(serve), {
        'document_root': settings.STATIC_ROOT,
        'path': 'service-worker.js'
    }),
    re_path(r'^', TemplateView.as_view(template_name='index.html'), name='index'),
    re_path(r'^favicon\.ico$', favicon_view),

]
