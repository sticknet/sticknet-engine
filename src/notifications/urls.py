from django.conf.urls import url, include
from rest_framework import routers

from .views import NotificationViewSet, InvitationViewSet, InvitedMembers, ConnectionRequestViewSet, CancelConnectionRequest, ConnReqRes, NotificationRead, FetchGroupRequests, SentConnectionRequests, SendConnectionRequest
from .push_notifications import PushNotification, PushNotificationMulticast, SetPushToken, CustomPushNotification

app_name = "notifications"

router = routers.SimpleRouter()
router.register('notifications', NotificationViewSet, basename='notifications')
router.register('invitations', InvitationViewSet, basename='invitations')
router.register('connection-requests', ConnectionRequestViewSet, basename='connection_requests')


urlpatterns = [
    url("^", include(router.urls)),
    url(r'^notification-read/$', NotificationRead.as_view(), name='notification-read'),
    url(r'^set-push-token/$', SetPushToken.as_view()),
    url(r'^push-notification/$', PushNotification.as_view(), name='push-notification'),
    url(r'^push-notification-multicast/$', PushNotificationMulticast.as_view(), name='push-notification-multicast'),
    url(r'^invited-members/$', InvitedMembers.as_view(), name='invited_members'),
    url(r'^cancel-connection-request/$', CancelConnectionRequest.as_view(), name='cancel_connection_request'),
    url(r'^conn-req-res/$', ConnReqRes.as_view(), name='conn_req_res'),
    url(r'^fetch-group-requests/$', FetchGroupRequests.as_view(), name='fetch_group_requests'),
    url(r'^sent-connection-requests/$', SentConnectionRequests.as_view(), name='sent_connection_requests'),
    url(r'^send-connection-request/$', SendConnectionRequest.as_view(), name='send_connection_request'),
    url(r'^custom-pn/$', CustomPushNotification.as_view(), name='custom_pn'),
]
