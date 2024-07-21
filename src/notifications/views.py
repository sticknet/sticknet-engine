from rest_framework import permissions, viewsets, generics, mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView


from .serializers import NotificationSerializer, InvitationSerializer, InvitedMembersSerializer, ConnectionRequestSerializer
from photos.pagination import DynamicPagination
from .models import Invitation, ConnectionRequest
from .push_notifications import PushNotification
from groups.models import GroupRequest
from users.serializers import UserBaseConnectionSerializer
from sticknet.dynamic_fields import get_serializer_context
from users.models import User
class NotificationRead(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = request.user.notifications.all()
        for notification in notifications:
            notification.read = True
            notification.save()
        return Response(status=status.HTTP_200_OK)


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = DynamicPagination

    def get_queryset(self):
        qs = self.request.user.notifications.exclude(from_user__in=self.request.user.blocked.all()).order_by("-timestamp")
        notifications = NotificationSerializer.setup_eager_loading(qs)
        return notifications


class InvitationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InvitationSerializer

    def get_queryset(self):
        qs = self.request.user.invitations.order_by('-timestamp')
        invitations = InvitationSerializer.setup_eager_loading(qs)
        return invitations

class ConnectionRequestViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConnectionRequestSerializer

    def get_queryset(self):
        qs = self.request.user.connection_requests.order_by("-timestamp")
        requests = ConnectionRequestSerializer.setup_eager_loading(qs)
        return requests

class FetchGroupRequests(APIView):
    permission_classes = [permissions.IsAuthenticated]


    def get(self, request):
        groups = request.user.group_admin.all()
        query_set = GroupRequest.objects.filter(group__in=groups)
        group_requests = []
        for group_request in query_set:
            group_requests.append({'id': group_request.group.id, 'user': UserBaseConnectionSerializer(group_request.user, context=get_serializer_context(self)).data})
        return Response({'group_requests': group_requests})


class SentConnectionRequests(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        connection_requests = request.user.requests_sent.order_by('-timestamp')
        response = []
        for item in connection_requests:
            response.append(UserBaseConnectionSerializer(item.to_user, context=get_serializer_context(self)).data)
        return Response({'connection_requests': response})

class CancelConnectionRequest(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        connection_request = ConnectionRequest.objects.filter(from_user=request.user, to_user_id=request.data['id']).first()
        if connection_request:
            connection_request.delete()
        return Response(status=status.HTTP_200_OK)


class ConnReqRes(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cr = ConnectionRequest.objects.get(id=request.data['id'])
        if not cr.to_user_id == request.user.id:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if request.data['accepted'] == True:
            cr.to_user.connections.add(cr.from_user)
            cr.from_user.connections.add(cr.to_user)
            PushNotification.post(self, request)
        cr.delete()
        return Response(status=status.HTTP_200_OK)



class InvitedMembers(generics.ListAPIView):
    serializer_class = InvitedMembersSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group = self.request.GET.get("q")
        qs = Invitation.objects.filter(group=group)
        invited_members = InvitedMembersSerializer.setup_eager_loading(qs)
        return invited_members

class SendConnectionRequest(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = User.objects.filter(username__exact=request.data['username']).first()
        if not user or request.user in user.blocked.all():
            return Response({'user_exists': False})
        if not ConnectionRequest.objects.filter(from_user=request.user, to_user=user).exists():
            ConnectionRequest.objects.create(from_user=request.user, to_user=user)
        return Response({'user_exists': True, 'user': UserBaseConnectionSerializer(user, context=get_serializer_context(self)).data})

