from django.conf.urls import url, include
from rest_framework import routers
from .views import GroupViewSet, GroupCoverViewSet, GroupMembers, RemoveMember, AddMembers, InviteMembers, \
    StickIn, ConnectionsAPIView, DeleteTempDisplayName, ToggleAdmin, DeleteGroup, UpdateGroupLink, VerifyGroupLink, \
    GroupLinkJoin, RequestToJoin, FetchMemberRequests, RemoveMemberRequest, ToggleGroupLink, ToggleGroupLinkApproval,  RemoveConnection, FetchTargetConnectionIds, FetchTargetGroupIds

app_name = "groups"

router = routers.SimpleRouter()
router.register('groups', GroupViewSet, basename='groups')
router.register('groups-cover', GroupCoverViewSet, basename='groups_cover')

urlpatterns = [
    url("^", include(router.urls)),
    url(r'^group-members/$', GroupMembers.as_view(), name='group_members'),
    url(r'^connections/$', ConnectionsAPIView.as_view(), name='connections'),
    url(r'^remove-member/$', RemoveMember.as_view(), name='remove_member'),
    url(r'^stick-in/$', StickIn.as_view(), name='stick_in'),
    url(r'^add-members/$', AddMembers.as_view(), name='add_members'),
    url(r'^invite-members/$', InviteMembers.as_view(), name='invite_members'),
    url(r'^delete-tdn/$', DeleteTempDisplayName.as_view(), name='delete_tdn'),
    url(r'^toggle-admin/$', ToggleAdmin.as_view(), name='toggle_admin'),
    url(r'^delete-group/$', DeleteGroup.as_view(), name='delete_group'),
    url(r'^update-group-link/$', UpdateGroupLink.as_view(), name='update_group_link'),
    url(r'^toggle-group-link/$', ToggleGroupLink.as_view(), name='toggle_group_link'),
    url(r'^verify-group-link/$', VerifyGroupLink.as_view(), name='verify_group_link'),
    url(r'^group-link-join/$', GroupLinkJoin.as_view(), name='group_link_join'),
    url(r'^request-to-join/$', RequestToJoin.as_view(), name='request_to_join'),
    url(r'^fetch-member-requests/$', FetchMemberRequests.as_view(), name='fetch_member_requests'),
    url(r'^remove-member-request/$', RemoveMemberRequest.as_view(), name='remove_member_request'),
    url(r'^toggle-group-link-approval/$', ToggleGroupLinkApproval.as_view(), name='toggle_group_link_approval'),
    url(r'^remove-connection/$', RemoveConnection.as_view(), name='remove_connection'),
    url(r'^fetch-target-connection-ids/$', FetchTargetConnectionIds.as_view(), name='fetch_target_connection_ids'),
    url(r'^fetch-target-group-ids/$', FetchTargetGroupIds.as_view(), name='fetch_target_group_ids'),
]
