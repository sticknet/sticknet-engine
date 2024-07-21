from rest_framework import permissions, viewsets, generics, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response

from users.serializers import UserSerializer, GroupMemberSerializer, \
    UserBaseConnectionSerializer
from .serializers import GroupSerializer, GroupCoverSerializer
from .models import GroupCover, Group, TempDisplayName, Cipher, GroupRequest
from notifications.models import Invitation
from users.models import User
from notifications.push_notifications import PushNotification
from stick_protocol.models import DecryptionSenderKey, EncryptionSenderKey
from notifications.models import Notification
from django.db.models import Q
from django.contrib.auth.hashers import make_password, check_password


class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GroupSerializer

    def get_queryset(self):
        qs = self.request.user.get_groups()
        groups = GroupSerializer.setup_eager_loading(qs)
        return groups


class DeleteGroup(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group = Group.objects.get(id=request.data['id'])
        if group.owner.id != request.user.id:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        for image in group.shared_images.all():
            if len(image.groups.all()) < 2:
                image.delete()
        EncryptionSenderKey.objects.filter(party_id=group.id).all().delete()
        DecryptionSenderKey.objects.filter(party_id=group.id).all().delete()
        group.delete()
        return Response(status=status.HTTP_200_OK)


class GroupCoverViewSet(viewsets.GenericViewSet, mixins.DestroyModelMixin, mixins.CreateModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GroupCoverSerializer

    def get_queryset(self):
        return GroupCover.objects.filter(group__in=self.request.user.groups.all())


class GroupMembers(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GroupMemberSerializer
    pagination_class = None

    def get_queryset(self, *args, **kwargs):
        group_id = self.request.GET.get("q")
        group = Group.objects.get(id=group_id)
        if group not in self.request.user.get_groups() and group not in self.request.user.invited_groups.all():
            return User.objects.none()
        qs = group.get_members()
        group_members = UserSerializer.setup_eager_loading(qs)
        return group_members


class ConnectionsAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserBaseConnectionSerializer
    pagination_class = None

    def get_queryset(self, *args, **kwargs):
        return self.request.user.get_all_connections()


class FetchMemberRequests(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserBaseConnectionSerializer
    pagination_class = None

    def get_queryset(self, *args, **kwargs):
        group_id = self.request.GET.get("id")
        group = Group.objects.get(id=group_id)
        if not self.request.user in group.admins.all():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        group_requests = GroupRequest.objects.filter(group=group)
        users = []
        for request in group_requests:
            users.append(request.user)
        return users


class StickIn(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        accepted = False
        user = request.user
        invitation_id = request.data['invitation_id']
        invitation = Invitation.objects.filter(id=invitation_id).first()
        if invitation and invitation.to_user.id == request.user.id:
            invitation.delete()
            if (request.data['accepted']):
                user.invited_groups.remove(invitation.group.id)
                user.groups.add(invitation.group.id)
                accepted = True
                members = invitation.group.user_set.all()
                user.connections.add(*members)
                for member in members:
                    member.connections.add(user)
        if not accepted:
            DecryptionSenderKey.objects.filter(Q(stick_id=invitation.group.id) & (
                        Q(for_user=user) | Q(for_one_time_id=user.one_time_id))).all().delete()
        return Response({'accepted': accepted})


class RemoveMember(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_id = request.data['user_id']
        group_id = request.data['group_id']
        user = User.objects.get(id=user_id)
        group = Group.objects.get(id=group_id)
        if user_id != request.user.id and not request.user in group.admins.all():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user.groups.remove(group_id)
        if group_id in user.invited_groups.all():
            user.invited_groups.remove(group_id)
        Invitation.objects.filter(to_user=user_id, group=group_id).all().delete()
        if user in group.admins.all():
            group.admins.remove(user)
        count = group.get_members_count()
        if count == 0:
            group.delete()
        elif count > 0 and group.owner.id == user.id: # TODO: if possible make the owner one of the admins
            group.owner = User.objects.get(id=group.get_members_ids()[0])
            group.save()

        # Delete ESKs
        EncryptionSenderKey.objects.filter(party_id=group_id, user=user).all().delete()

        # DELETE NOTIFICATIONS
        Notification.objects.filter(to_user=user, group=group).all().delete()
        return Response({'count': count})

class AddMembers(APIView): # TODO: should chain_step be updated here?
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group_id = request.data['data']['group_id']
        group = Group.objects.get(id=group_id)
        if not request.user in group.admins.all():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        display_name = request.data['display_name']
        createTDN = False
        if (group.display_name.user.id != request.user.id):
            createTDN = True
        for id in request.data['to_user']:
            member = User.objects.get(id=id)
            member.groups.add(group_id)
            if createTDN:
                TempDisplayName.objects.create(group=group, from_user=request.user, to_user=member, cipher=display_name,
                                               stick_id=request.data['data']['stick_id'])
        PushNotification.post(self, request)
        return Response(status=status.HTTP_200_OK)

class InviteMembers(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group_id = request.data['data']['group_id']
        group = Group.objects.get(id=group_id)
        if not request.user in group.admins.all():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        stick_id = request.data['data']['stick_id']
        party_id = stick_id[:36]
        chain_id = stick_id[36:]
        key = EncryptionSenderKey.objects.get(party_id=party_id, chain_id=chain_id, user=request.user)
        key.step = request.data['chain_step']
        key.save()
        for id in request.data['to_user']:
            member = User.objects.get(id=id)
            member.invited_groups.add(group_id)
        PushNotification.post(self, request)
        return Response(status=status.HTTP_200_OK)

class ToggleAdmin(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group_id = request.data['group_id']
        group = Group.objects.get(id=group_id)
        if not request.user in group.admins.all():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        admin_id = request.data['to_user'][0]
        user = User.objects.get(id=admin_id)
        if user in group.admins.all():
            group.admins.remove(user)
        else:
            group.admins.add(user)
            PushNotification.post(self, request)
        return Response(status=status.HTTP_200_OK)


class UpdateGroupLink(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group = Group.objects.get(id=request.data['group_id'])
        if request.user in group.admins.all():
            group.verification_id = make_password(request.data['verification_id'])
            group.link = Cipher.objects.create(text=request.data['text'], user=request.user,
                                               stick_id=request.data['stick_id'])
            group.link_approval = request.data['link_approval']
            group.link_enabled = True
            group.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_401_UNAUTHORIZED)


class ToggleGroupLink(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group = Group.objects.get(id=request.data['id'])
        if request.user in group.admins.all():
            group.link_enabled = not group.link_enabled
            group.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_401_UNAUTHORIZED)


class ToggleGroupLinkApproval(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group = Group.objects.get(id=request.data['id'])
        if request.user in group.admins.all():
            group.link_approval = not group.link_approval
            group.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_401_UNAUTHORIZED)


class VerifyGroupLink(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group = Group.objects.get(id=request.data['group_id'])
        if group.link_enabled and check_password(request.data['verification_id'], group.verification_id):
            return Response({'verified': True, 'link_approval': group.link_approval})
        else:
            return Response({'verified': False})


class GroupLinkJoin(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group = Group.objects.get(id=request.data['group_id'])
        user = request.user
        if group.link_enabled and not group.link_approval and check_password(request.data['verification_id'],
                                                                             group.verification_id):
            user.groups.add(group.id)
            # members = group.user_set.all()
            # user.connections.add(*members)
            # for member in members:
            #     member.connections.add(user)
            return Response({'success': True, 'group': GroupSerializer(group).data})
        return Response({'success': False})


class RequestToJoin(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group = Group.objects.get(id=request.data['group_id'])
        user = request.user
        if group.link_enabled and check_password(request.data['verification_id'], group.verification_id):
            display_name = Cipher.objects.create(text=request.data['text'], user=request.user,
                                                 stick_id=request.data['stick_id'])
            if not GroupRequest.objects.filter(group=group, user=user).exists():
                GroupRequest.objects.create(group=group, user=user, display_name=display_name)
                PushNotification.post(self, request)
            return Response({'success': True})
        return Response({'success': False})


class RemoveMemberRequest(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group = Group.objects.get(id=request.data['group_id'])
        if request.user in group.admins.all() or request.data['user_id'] == request.user.id:
            GroupRequest.objects.get(group=group, user__id=request.data['user_id']).delete()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_401_UNAUTHORIZED)


class DeleteTempDisplayName(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        TempDisplayName.objects.filter(group__id=request.data['group_id'], to_user=request.user).all().delete()
        return Response(status=status.HTTP_200_OK)

class RemoveConnection(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = User.objects.get(id=request.data['user_id'])
        request.user.connections.remove(user)
        user.connections.remove(request.user)
        return Response(status=status.HTTP_200_OK)


class FetchTargetConnectionIds(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user_id = request.GET.get("user_id")
        user = User.objects.get(id=user_id)
        target_connection_ids = user.connections.values_list('id', flat=True)
        return Response({'target_connection_ids': target_connection_ids})


class FetchTargetGroupIds(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user_id = request.GET.get("user_id")
        user = User.objects.get(id=user_id)
        target_group_ids = user.groups.values_list('id', flat=True)
        return Response({'target_group_ids': target_group_ids})

