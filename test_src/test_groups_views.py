from knox.models import AuthToken
from users.models import User, Preferences
from groups.models import Group, GroupCover, Cipher, GroupRequest, TempDisplayName
from notifications.models import Invitation
from rest_framework.test import APITestCase
from stick_protocol.models import EncryptionSenderKey, IdentityKey, Party
from django.contrib.auth.hashers import make_password, check_password


def set_up_user(self):
    self.user = User.objects.create(username='alice123', phone='1', phone_hash='AX(*$', finished_registration=True)
    self.auth_token = AuthToken.objects.create(self.user)
    self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.auth_token[1])


def set_up_esk(self):
    ik = IdentityKey.objects.create(key_id=123, public='public', cipher='cipher', user=self.user, salt='salt',
                                    timestamp='timestamp')
    self.esk = EncryptionSenderKey.objects.create(user=self.user, key_id=789,
                                                  party_id='5a71cdda-77d0-40ab-b232-289888062562', chain_id='0',
                                                  identity_key=ik, key='key')


class TestFetchGroups(APITestCase):
    def setUp(self):
        set_up_user(self)
        group_1 = Group.objects.create(id='abc')
        self.user.groups.add(group_1)
        Group.objects.create(id='def')

    def test_fetch_groups(self):
        response = self.client.get('/api/groups/')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], 'abc')


class TestCreateGroup(APITestCase):
    def setUp(self):
        set_up_user(self)
        User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
        User.objects.create(id='2', phone='+666', username='charles123', finished_registration=True)

    def test_create_group(self):
        body = {'added_users': ['1'], 'invited_users': ['2'], 'id': 'abc', 'display_name': {'text': 'My Group'}}
        response = self.client.post('/api/groups/', body)
        self.assertEqual(response.data['id'], 'abc')
        self.assertEqual(Group.objects.filter(id='abc').exists(), True)
        self.assertEqual(User.objects.get(id='1').groups.filter(id='abc').exists(), True)
        self.assertEqual(User.objects.get(id='2').invited_groups.filter(id='abc').exists(), True)


class TestUpdateGroup(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_esk(self)
        display_name = Cipher.objects.create(text='text')
        cover_1 = GroupCover.objects.create(id=76, uri='group_cover_1', stick_id='stick_id', cipher='cipher')
        group_1 = Group.objects.create(id='abc', cover=cover_1, display_name=display_name)
        cover_2 = GroupCover.objects.create(id=77, uri='group_cover_2', stick_id='stick_id', cipher='cipher',
                                            user=self.user)
        self.user.groups.add(group_1)

    def test_update_group(self):
        body = {'stick_id': '5a71cdda-77d0-40ab-b232-2898880625620', 'chain_step': 50,
                'display_name': {'text': 'My Group'},
                'status': {'text': 'some status'}, 'cover_id': 77, 'resize_mode': 'H'}
        response = self.client.patch('/api/groups/abc/', body)
        self.assertEqual(response.data['id'], 'abc')
        self.assertEqual(response.data['display_name']['text'], 'My Group')
        self.assertEqual(response.data['status']['text'], 'some status')
        self.assertEqual(response.data['cover']['id'], 77)
        self.assertEqual(response.data['cover']['resize_mode'], 'H')


class TestDeleteGroup(APITestCase):
    def setUp(self):
        set_up_user(self)
        user_1 = User.objects.create(phone='+555', username='bob123', finished_registration=True)
        group_1 = Group.objects.create(id='abc', owner=user_1)
        group_1 = Group.objects.create(id='def', owner=self.user)

    def test_delete_group(self):
        response = self.client.post('/api/delete-group/', {'id': 'abc'})
        self.assertEqual(response.status_code, 401)

        response = self.client.post('/api/delete-group/', {'id': 'def'})
        self.assertEqual(response.status_code, 200)


class TestGroupMembers(APITestCase):
    def setUp(self):
        set_up_user(self)
        user_1 = User.objects.create(phone='+555', username='bob123', finished_registration=True)
        group_1 = Group.objects.create(id='abc')
        self.user.groups.add(group_1)
        user_1.groups.add(group_1)

    def test_group_members(self):
        response = self.client.get('/api/group-members/?q=abc')
        self.assertEqual(len(response.data), 2)


class TestFetchConnections(APITestCase):
    def setUp(self):
        set_up_user(self)
        user_1 = User.objects.create(phone='+555', username='bob123', finished_registration=True)
        self.user.connections.add(user_1)

    def test_fetch_connections(self):
        response = self.client.get('/api/connections/')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'bob123')


class TestFetchMemberRequests(APITestCase):
    def setUp(self):
        set_up_user(self)
        user_1 = User.objects.create(phone='+555', username='bob123', finished_registration=True)
        group_1 = Group.objects.create(id='abc')
        group_1.admins.add(self.user)
        GroupRequest.objects.create(group=group_1, user=user_1)

    def test_fetch_member_requests(self):
        response = self.client.get('/api/fetch-member-requests/?id=abc')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'bob123')


class TestStickIn(APITestCase):
    def setUp(self):
        set_up_user(self)
        group_1 = Group.objects.create(id='abc')
        self.user_x = User.objects.create(phone='+555', username='bob123', finished_registration=True)
        self.user_x.groups.add(group_1)
        Invitation.objects.create(id=55, group=group_1, from_user=self.user_x, to_user=self.user)
        self.user.invited_groups.add(group_1)

    def test_stick_in(self):
        response = self.client.post('/api/stick-in/', {'invitation_id': 55, 'accepted': True})
        self.assertEqual(response.data['accepted'], True)
        self.assertEqual(Invitation.objects.filter(id=55).exists(), False)
        self.assertEqual(self.user.invited_groups.filter(id='abc').exists(), False)
        self.assertEqual(self.user.groups.filter(id='abc').exists(), True)
        self.assertEqual(self.user_x.connections.filter(id=self.user.id).exists(), True)
        self.assertEqual(self.user.connections.filter(id=self.user_x.id).exists(), True)


class TestRemoveMember(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.group_1 = Group.objects.create(id='abc', owner=self.user)
        self.group_2 = Group.objects.create(id='edf')
        self.user_x = User.objects.create(phone='+555', username='bob123', finished_registration=True)
        self.user.groups.add(self.group_1)
        self.user.groups.add(self.group_2)
        self.group_1.admins.add(self.user)
        self.user_x.groups.add(self.group_1)
        self.user_x.groups.add(self.group_2)

    def test_remove_member(self):
        response = self.client.post('/api/remove-member/', {'user_id': self.user_x.id, 'group_id': self.group_1.id})
        self.assertEqual(response.data['count'], 1)  # count of remaining members
        self.assertEqual(self.user_x.groups.filter(id=self.group_1.id).exists(), False)

        response = self.client.post('/api/remove-member/', {'user_id': self.user_x.id, 'group_id': self.group_2.id})
        self.assertEqual(response.status_code, 401)


class TestAddMembers(APITestCase):
    def setUp(self):
        set_up_user(self)
        display_name = Cipher.objects.create(text='display_name', user=self.user)
        self.group_1 = Group.objects.create(id='abc', owner=self.user, display_name=display_name)
        self.user_x = User.objects.create(id='xyz', phone='+555', username='bob123', finished_registration=True)

    def test_add_members(self):
        body = {'data': {'group_id': self.group_1.id, 'stick_id': '5a71cdda-77d0-40ab-b232-2898880625620',
                         'title': 'title', 'body': 'body', 'channel_id': 'group_channel'},
                'display_name': 'display_name',
                'to_user': ['xyz']}
        response = self.client.post('/api/add-members/', body)
        self.assertEqual(response.status_code, 401)

        self.group_1.admins.add(self.user)
        response = self.client.post('/api/add-members/', body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user_x.groups.filter(id='abc').exists(), True)


class TestInviteMembers(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_esk(self)
        self.group_1 = Group.objects.create(id='abc', owner=self.user)
        self.user_x = User.objects.create(id='xyz', phone='+555', username='bob123', finished_registration=True)

    def test_invite_members(self):
        body = {'data': {'group_id': self.group_1.id, 'stick_id': '5a71cdda-77d0-40ab-b232-2898880625620',
                         'title': 'title', 'body': 'body', 'channel_id': 'group_channel'}, 'to_user': ['xyz'],
                'chain_step': 50}
        response = self.client.post('/api/invite-members/', body)
        self.assertEqual(response.status_code, 401)

        self.group_1.admins.add(self.user)
        response = self.client.post('/api/invite-members/', body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user_x.invited_groups.filter(id='abc').exists(), True)


class TestToggleAdmin(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.group_1 = Group.objects.create(id='abc', owner=self.user)
        self.user_x = User.objects.create(id='xyz', phone='+555', username='bob123', finished_registration=True)

    def test_toggle_admin(self):
        body = {'group_id': self.group_1.id, 'to_user': ['xyz'],
                'data': {'title': 'title', 'body': 'body',
                         'channel_id': 'group_channel', 'group_id': self.group_1.id}}
        response = self.client.post('/api/toggle-admin/', body)
        self.assertEqual(response.status_code, 401)

        self.group_1.admins.add(self.user)
        response = self.client.post('/api/toggle-admin/', body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.group_1.admins.filter(id='xyz').exists(), True)

        response = self.client.post('/api/toggle-admin/', body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.group_1.admins.filter(id='xyz').exists(), False)


class TestUpdateGroupLink(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.group_1 = Group.objects.create(id='abc', owner=self.user)

    def test_update_group_link(self):
        body = {'group_id': self.group_1.id, 'verification_id': 'verification_id', 'text': 'group_link',
                'stick_id': 'stick_id', 'link_approval': True}
        response = self.client.post('/api/update-group-link/', body)
        self.assertEqual(response.status_code, 401)

        self.group_1.admins.add(self.user)
        response = self.client.post('/api/update-group-link/', body)
        updated_group = Group.objects.get(id='abc')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(check_password('verification_id', updated_group.verification_id), True)
        self.assertEqual(updated_group.link.text, 'group_link')
        self.assertEqual(updated_group.link_approval, True)
        self.assertEqual(updated_group.link_enabled, True)


class TestToggleGroupLink(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.group_1 = Group.objects.create(id='abc', owner=self.user)

    def test_toggle_group_link(self):
        response = self.client.post('/api/toggle-group-link/', {'id': 'abc'})
        self.assertEqual(response.status_code, 401)

        self.group_1.admins.add(self.user)
        self.client.post('/api/toggle-group-link/', {'id': 'abc'})
        updated_group = Group.objects.get(id='abc')
        self.assertEqual(updated_group.link_enabled, True)

        self.client.post('/api/toggle-group-link/', {'id': 'abc'})
        updated_group = Group.objects.get(id='abc')
        self.assertEqual(updated_group.link_enabled, False)


class TestToggleGroupLinkApproval(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.group_1 = Group.objects.create(id='abc', owner=self.user)

    def test_toggle_group_link_approval(self):
        response = self.client.post('/api/toggle-group-link-approval/', {'id': 'abc'})
        self.assertEqual(response.status_code, 401)

        self.group_1.admins.add(self.user)
        self.client.post('/api/toggle-group-link-approval/', {'id': 'abc'})
        updated_group = Group.objects.get(id='abc')
        self.assertEqual(updated_group.link_approval, True)

        self.client.post('/api/toggle-group-link-approval/', {'id': 'abc'})
        updated_group = Group.objects.get(id='abc')
        self.assertEqual(updated_group.link_approval, False)


class TestVerifyGroupLink(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.group_1 = Group.objects.create(id='abc', link_enabled=True)
        self.group_1.verification_id = make_password('verification_id')
        self.group_1.save()

    def test_verify_group_link(self):
        response = self.client.post('/api/verify-group-link/',
                                    {'group_id': 'abc', 'verification_id': 'incorrect_id'})
        self.assertEqual(response.data['verified'], False)

        response = self.client.post('/api/verify-group-link/',
                                    {'group_id': 'abc', 'verification_id': 'verification_id'})
        self.assertEqual(response.data['verified'], True)


class TestGroupLinkJoin(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.group_1 = Group.objects.create(id='abc', link_enabled=True, link_approval=True)
        self.group_1.verification_id = make_password('verification_id')
        self.group_1.save()

    def test_group_link_join(self):
        response = self.client.post('/api/group-link-join/', {'group_id': 'abc', 'verification_id': 'verification_id'})
        self.assertEqual(response.data['success'], False)

        self.group_1.link_approval = False
        self.group_1.save()
        response = self.client.post('/api/group-link-join/', {'group_id': 'abc', 'verification_id': 'verification_id'})
        self.assertEqual(response.data['success'], True)
        self.assertEqual(self.user.groups.filter(id='abc').exists(), True)


class TestRequestToJoin(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.group_1 = Group.objects.create(id='abc', link_enabled=False, link_approval=True)
        self.group_1.verification_id = make_password('verification_id')
        self.group_1.save()

    def test_request_to_join(self):
        body = {'group_id': 'abc', 'verification_id': 'verification_id', 'text': 'cipher_text', 'stick_id': 'stick_id',
                'member_id': self.user.id,
                'data': {'channel_id': 'request_channel', 'group_id': 'abc', 'from_user_id': self.user.id,
                         'is_conn_req': False, 'title': 'title', 'body': 'body'}}

        response = self.client.post('/api/request-to-join/', body)
        self.assertEqual(response.data['success'], False)

        self.group_1.link_enabled = True
        self.group_1.save()
        response = self.client.post('/api/request-to-join/', body)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(GroupRequest.objects.filter(group=self.group_1, user=self.user).exists(), True)


class TestRemoveMemberRequest(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.group_1 = Group.objects.create(id='abc', link_enabled=False, link_approval=True)
        user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
        GroupRequest.objects.create(user=user_1, group=self.group_1)

    def test_remove_member_request(self):
        response = self.client.post('/api/remove-member-request/', {'group_id': 'abc', 'user_id': '1'})
        self.assertEqual(response.status_code, 401)

        self.group_1.admins.add(self.user)
        response = self.client.post('/api/remove-member-request/', {'group_id': 'abc', 'user_id': '1'})
        self.assertEqual(response.status_code, 200)


class TestDeleteTempDisplayName(APITestCase):
    def setUp(self):
        set_up_user(self)
        user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
        self.group_1 = Group.objects.create(id='abc', link_enabled=False, link_approval=True)
        TempDisplayName.objects.create(id=55, group=self.group_1, from_user=user_1, to_user=self.user, cipher='cipher',
                                       stick_id='stick_id')

    def test_delete_temp_display_name(self):
        response = self.client.post('/api/delete-tdn/', {'group_id': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TempDisplayName.objects.filter(id=55).exists(), False)

# class TestGroupCoverViewSet(APITestCase):
#     def setUp(self):
#         set_up_user(self)
#
#     def test_delete_group(self):
#         body = {'stick_id': 'stick_id', 'uri': 'uri', 'file_size': 1000, 'resize_mode': 'H',
#                 'cipher': 'cipher', 'width': 1000, 'height': 1000}
#         response = self.client.post('/api/groups-cover/', body)
