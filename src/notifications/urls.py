from django.urls import include, re_path
from rest_framework import routers

from .views import NotificationViewSet, InvitationViewSet, InvitedMembers, ConnectionRequestViewSet, CancelConnectionRequest, ConnReqRes, NotificationRead, FetchGroupRequests, SentConnectionRequests, SendConnectionRequest
from .push_notifications import PushNotification, PushNotificationMulticast, SetPushToken, CustomPushNotification

app_name = "notifications"

router = routers.SimpleRouter()
router.register('notifications', NotificationViewSet, basename='notifications')
router.register('invitations', InvitationViewSet, basename='invitations')
router.register('connection-requests', ConnectionRequestViewSet, basename='connection_requests')


urlpatterns = [
    re_path("^", include(router.urls)),
    re_path(r'^notification-read/$', NotificationRead.as_view(), name='notification-read'),
    re_path(r'^set-push-token/$', SetPushToken.as_view()),
    re_path(r'^push-notification/$', PushNotification.as_view(), name='push-notification'),
    re_path(r'^push-notification-multicast/$', PushNotificationMulticast.as_view(), name='push-notification-multicast'),
    re_path(r'^invited-members/$', InvitedMembers.as_view(), name='invited_members'),
    re_path(r'^cancel-connection-request/$', CancelConnectionRequest.as_view(), name='cancel_connection_request'),
    re_path(r'^conn-req-res/$', ConnReqRes.as_view(), name='conn_req_res'),
    re_path(r'^fetch-group-requests/$', FetchGroupRequests.as_view(), name='fetch_group_requests'),
    re_path(r'^sent-connection-requests/$', SentConnectionRequests.as_view(), name='sent_connection_requests'),
    re_path(r'^send-connection-request/$', SendConnectionRequest.as_view(), name='send_connection_request'),
    re_path(r'^custom-pn/$', CustomPushNotification.as_view(), name='custom_pn'),
]
