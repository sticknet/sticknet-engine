from knox.models import AuthToken
from users.models import User
from groups.models import Group, GroupRequest
from notifications.models import Invitation
from rest_framework.test import APITestCase
from notifications.models import Notification, ConnectionRequest


def set_up_user(self):
    self.user = User.objects.create(username='alice123', phone='1', phone_hash='AX(*$', finished_registration=True)
    self.auth_token = AuthToken.objects.create(self.user)
    self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.auth_token[1])

class TestNotificationRead(APITestCase):
    def setUp(self):
        set_up_user(self)
        Notification.objects.create(id=1, to_user=self.user, body='body', channel='channel')

    def test_notification_read(self):
        response = self.client.get('/api/notification-read/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.get(id=1).read, True)


class TestNotificationViewSet(APITestCase):
    def setUp(self):
        set_up_user(self)
        Notification.objects.create(id=1, to_user=self.user, body='body', channel='channel')
        user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
        Notification.objects.create(id=2, to_user=user_1, body='body', channel='channel')

    def test_notification_view_set(self):
        response = self.client.get('/api/notifications/')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], 1)


class TestInvitationViewSet(APITestCase):
    def setUp(self):
        set_up_user(self)
        group = Group.objects.create(id='edf')
        user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
        user_2 = User.objects.create(id='2', phone='+666', username='mike444', finished_registration=True)
        Invitation.objects.create(id=1, from_user=user_1, to_user=self.user, group=group)
        Invitation.objects.create(id=2, from_user=user_1, to_user=user_2, group=group)

    def test_notification_view_set(self):
        response = self.client.get('/api/invitations/')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], 1)


class TestConnectionRequestViewSet(APITestCase):
    def setUp(self):
        set_up_user(self)
        user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
        user_2 = User.objects.create(id='2', phone='+666', username='mike444', finished_registration=True)
        ConnectionRequest.objects.create(id=1, from_user=user_1, to_user=self.user)
        ConnectionRequest.objects.create(id=2, from_user=user_1, to_user=user_2)

    def test_connection_request_view_set(self):
        response = self.client.get('/api/connection-requests/')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], 1)


class TestFetchGroupRequests(APITestCase):
    def setUp(self):
        set_up_user(self)
        user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
        group_1 = Group.objects.create(id='abc')
        group_2 = Group.objects.create(id='xyz')
        group_1.admins.add(self.user)
        GroupRequest.objects.create(user=user_1, group=group_1)
        GroupRequest.objects.create(user=user_1, group=group_2)

    def test_fetch_group_requests(self):
        response = self.client.get('/api/fetch-group-requests/')
        self.assertEqual(len(response.data['group_requests']), 1)
        self.assertEqual(response.data['group_requests'][0]['id'], 'abc')


class TestCancelConnectionRequest(APITestCase):
    def setUp(self):
        set_up_user(self)
        user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
        ConnectionRequest.objects.create(id=44, from_user=self.user, to_user=user_1)

    def test_cancel_connection_request(self):
        response = self.client.post('/api/cancel-connection-request/', {'id': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ConnectionRequest.objects.filter(id=44).exists(), False)


class TestConnReqRes(APITestCase):
    def setUp(self):
        set_up_user(self)
        user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
        user_2 = User.objects.create(id='2', phone='+666', username='mike444', finished_registration=True)
        ConnectionRequest.objects.create(id=44, from_user=user_1, to_user=self.user)
        ConnectionRequest.objects.create(id=45, from_user=user_1, to_user=user_2)

    def test_conn_req_res(self):
        response = self.client.post('/api/conn-req-res/', {'id': 45, 'accepted': True, 'data': {'title': 'title', 'body': 'body', 'channel_id': 'request_channel'}})
        self.assertEqual(response.status_code, 401)

        response = self.client.post('/api/conn-req-res/', {'id': 44, 'accepted': True,'data': {'title': 'title', 'body': 'body',  'channel_id': 'request_channel'},
                                                           'is_conn_req': False, 'to_user': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.connections.filter(id='1').exists(), True)
        self.assertEqual(ConnectionRequest.objects.filter(id=44).exists(), False)


