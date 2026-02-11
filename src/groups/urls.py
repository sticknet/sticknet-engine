from django.urls import include, re_path
from rest_framework import routers
from .views import GroupViewSet, GroupCoverViewSet, GroupMembers, RemoveMember, AddMembers, InviteMembers, \
    StickIn, ConnectionsAPIView, DeleteTempDisplayName, ToggleAdmin, DeleteGroup, UpdateGroupLink, VerifyGroupLink, \
    GroupLinkJoin, RequestToJoin, FetchMemberRequests, RemoveMemberRequest, ToggleGroupLink, ToggleGroupLinkApproval,  RemoveConnection, FetchTargetConnectionIds, FetchTargetGroupIds

app_name = "groups"

router = routers.SimpleRouter()
router.register('groups', GroupViewSet, basename='groups')
router.register('groups-cover', GroupCoverViewSet, basename='groups_cover')

urlpatterns = [
    re_path("^", include(router.urls)),
    re_path(r'^group-members/$', GroupMembers.as_view(), name='group_members'),
    re_path(r'^connections/$', ConnectionsAPIView.as_view(), name='connections'),
    re_path(r'^remove-member/$', RemoveMember.as_view(), name='remove_member'),
    re_path(r'^stick-in/$', StickIn.as_view(), name='stick_in'),
    re_path(r'^add-members/$', AddMembers.as_view(), name='add_members'),
    re_path(r'^invite-members/$', InviteMembers.as_view(), name='invite_members'),
    re_path(r'^delete-tdn/$', DeleteTempDisplayName.as_view(), name='delete_tdn'),
    re_path(r'^toggle-admin/$', ToggleAdmin.as_view(), name='toggle_admin'),
    re_path(r'^delete-group/$', DeleteGroup.as_view(), name='delete_group'),
    re_path(r'^update-group-link/$', UpdateGroupLink.as_view(), name='update_group_link'),
    re_path(r'^toggle-group-link/$', ToggleGroupLink.as_view(), name='toggle_group_link'),
    re_path(r'^verify-group-link/$', VerifyGroupLink.as_view(), name='verify_group_link'),
    re_path(r'^group-link-join/$', GroupLinkJoin.as_view(), name='group_link_join'),
    re_path(r'^request-to-join/$', RequestToJoin.as_view(), name='request_to_join'),
    re_path(r'^fetch-member-requests/$', FetchMemberRequests.as_view(), name='fetch_member_requests'),
    re_path(r'^remove-member-request/$', RemoveMemberRequest.as_view(), name='remove_member_request'),
    re_path(r'^toggle-group-link-approval/$', ToggleGroupLinkApproval.as_view(), name='toggle_group_link_approval'),
    re_path(r'^remove-connection/$', RemoveConnection.as_view(), name='remove_connection'),
    re_path(r'^fetch-target-connection-ids/$', FetchTargetConnectionIds.as_view(), name='fetch_target_connection_ids'),
    re_path(r'^fetch-target-group-ids/$', FetchTargetGroupIds.as_view(), name='fetch_target_group_ids'),
]
