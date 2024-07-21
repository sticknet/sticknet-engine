from knox.models import AuthToken
from users.models import User, LimitedAccessToken, Device, Preferences
from rest_framework.test import APITestCase
from stick_protocol.models import EncryptionSenderKey, IdentityKey, SignedPreKey, PreKey, DecryptionSenderKey, Party, \
    PendingKey
from groups.models import Group, Cipher
from knox.crypto import create_token_string, hash_token, create_salt_string
from photos.models import Image


def set_up_user(self):
    self.user = User.objects.create(username='alice123', phone='+16501119999', phone_hash='AX(*$',
                                    finished_registration=True, one_time_id='zzzzz')
    self.auth_token = AuthToken.objects.create(self.user)
    self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.auth_token[1])


def set_up_user_1_keys():
    user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
    IdentityKey.objects.create(key_id=1, public='ik_public', cipher='ik_cipher', user=user_1, salt='ik_salt',
                               active=False, timestamp=998)
    IdentityKey.objects.create(key_id=2, public='ik2_public', cipher='ik2_cipher', user=user_1, salt='ik2_salt',
                               active=True, timestamp=999)
    SignedPreKey.objects.create(key_id=3, public='spk_public', signature='signature', cipher='spk_cipher',
                                user=user_1, salt='spk_salt', active=False, timestamp=998)
    SignedPreKey.objects.create(key_id=4, public='spk2_public', signature='signature2', cipher='spk2_cipher',
                                user=user_1, salt='spk_salt', active=True, timestamp=999)
    PreKey.objects.create(key_id=54, public='pk_public', cipher='pk_cipher', user=user_1, used=True, salt='pk_salt')
    PreKey.objects.create(key_id=55, public='pk2_public', cipher='pk2_cipher', user=user_1, used=False, salt='pk2_salt')
    return user_1


def set_up_user_2_keys():
    user_2 = User.objects.create(id='2', phone='+666', username='mike123', finished_registration=True)
    IdentityKey.objects.create(key_id=1, public='ik_public', cipher='ik_cipher', user=user_2, salt='ik_salt',
                               active=False, timestamp=998)
    IdentityKey.objects.create(key_id=2, public='ik2_public', cipher='ik2_cipher', user=user_2, salt='ik2_salt',
                               active=True, timestamp=999)
    SignedPreKey.objects.create(key_id=3, public='spk_public', signature='signature', cipher='spk_cipher',
                                user=user_2, salt='spk_salt', active=False, timestamp=998)
    SignedPreKey.objects.create(key_id=4, public='spk2_public', signature='signature2', cipher='spk2_cipher',
                                user=user_2, salt='spk_salt', active=True, timestamp=999)
    PreKey.objects.create(key_id=54, public='pk_public', cipher='pk_cipher', user=user_2, used=True, salt='pk_salt')
    PreKey.objects.create(key_id=55, public='pk2_public', cipher='pk2_cipher', user=user_2, used=False, salt='pk2_salt')
    return user_2


class TestUploadPreKeyBundle(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='alice123', phone='+16501119999', phone_hash='AX(*$',
                                        finished_registration=False)
        token = create_token_string()
        salt = create_salt_string()
        hash = hash_token(token, salt)
        LimitedAccessToken.objects.create(hash=hash, salt=salt, auth_id='+16501119999')
        self.client.credentials(HTTP_AUTHORIZATION=token)

    def test_upload_pre_key_bundle(self):
        response = self.client.post('/api/upload-pkb/', upload_pkb_body)
        updated_user = User.objects.get(username='alice123')
        self.assertEqual(len(response.data['party_id']), 36)
        self.assertEqual(len(response.data['self_party_id']), 36)
        self.assertEqual(len(response.data['token']), 64)
        self.assertEqual(
            IdentityKey.objects.filter(user=self.user, key_id=upload_pkb_body['identity_key']['id']).exists(), True)
        self.assertEqual(
            SignedPreKey.objects.filter(user=self.user, key_id=upload_pkb_body['signed_pre_key']['id']).exists(), True)
        self.assertEqual(PreKey.objects.filter(user=self.user).count(), 10)
        self.assertEqual(updated_user.password_salt, 'd9Vmgv7VlM3QbtHH3yAaLure2CrGUoPu9PUcScyyN6E=')
        self.assertEqual(updated_user.check_password('uxPYx2/8Jlm9QDRMS+tP3aH+WSLA27/n0NlHILE3I/M='), True)
        self.assertEqual(updated_user.one_time_id, 'b85fa317-0daa-4409-a1f1-5d56b384b22c')
        self.assertEqual(updated_user.local_id, 14892)
        self.assertEqual(updated_user.next_pre_key_id, 10)
        self.assertEqual(updated_user.finished_registration, True)
        self.assertEqual(Device.objects.filter(device_id='ac7e940c-7d3a-4377-a9ca-adbb4b7ff1af').exists(), True)
        self.assertEqual(Party.objects.filter(user=self.user, individual=False).exists(), True)
        self.assertEqual(Party.objects.filter(user=self.user, individual=True).exists(), True)
        self.assertEqual(LimitedAccessToken.objects.filter(auth_id='+16501119999').exists(), False)


class TestUploadPreKeys(APITestCase):
    def setUp(self):
        set_up_user(self)

    def test_upload_pre_keys(self):
        response = self.client.post('/api/upload-pre-keys/', upload_pre_keys)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PreKey.objects.filter(user=self.user).count(), 10)


class TestFetchPreKeyBundle(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_user_1_keys()

    def test_fetch_pre_key_bundle(self):
        response = self.client.get('/api/fetch-pkb/?id=1')
        self.assertEqual(response.data['identity_key_id'], 2)
        self.assertEqual(response.data['signed_pre_key_id'], 4)
        self.assertEqual(response.data['pre_key_id'], 55)


class TestFetchPreKeyBundles(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_user_1_keys()
        set_up_user_2_keys()

    def test_fetch_pre_key_bundles(self):
        response = self.client.post('/api/fetch-pkbs/', {'users_id': ['1', '2']})
        self.assertIn('1', response.data['bundles'])
        self.assertIn('2', response.data['bundles'])


class TestFetchSenderKey(APITestCase):
    def setUp(self):
        set_up_user(self)
        user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
        user_1_ik = IdentityKey.objects.create(key_id=1, public='ik_public', cipher='ik_cipher', user=user_1,
                                               salt='ik_salt', active=False, timestamp=998)
        Party.objects.create(user=self.user)
        Party.objects.create(user=self.user, individual=True)
        group_1 = Group.objects.create(id='abc')
        user_1.groups.add(group_1)
        group_2 = Group.objects.create(id='xyz')
        self.user.groups.add(group_2)
        party = Party.objects.create(id='33f54c2a-025b-4082-b296-e90dd2f0df78')
        party.groups.add(group_1)
        party.groups.add(group_2)
        DecryptionSenderKey.objects.create(stick_id='33f54c2a-025b-4082-b296-e90dd2f0df780',
                                           of_user=user_1,
                                           for_user=self.user,
                                           key='uqCoM6SIHVDPO2q2HXLtFW6S8RsnW5Y94j5NpM0UJbsl4+MMWuYDHYLdFBTWRmDbV2hbRk16fDndecS2i9/odQ==',
                                           identity_key=user_1_ik)

    def test_fetch_sender_key(self):
        response = self.client.post('/api/fetch-sk/',
                                    {'stick_id': '33f54c2a-025b-4082-b296-e90dd2f0df780', 'member_id': '1',
                                     'is_sticky': True})
        self.assertEqual(response.data['party_exists'], True)
        self.assertEqual(response.data['sender_key']['key'],
                         'uqCoM6SIHVDPO2q2HXLtFW6S8RsnW5Y94j5NpM0UJbsl4+MMWuYDHYLdFBTWRmDbV2hbRk16fDndecS2i9/odQ==')
        self.assertEqual(response.data['sender_key']['identity_key_id'], 1)
        response = self.client.post('/api/fetch-sk/', {'stick_id': 'random_id', 'member_id': '1', 'is_sticky': True})
        self.assertEqual(response.data['party_exists'], False)


class TestFetchStandardSenderKeys(APITestCase):
    def setUp(self):
        set_up_user(self)
        user_1 = User.objects.create(id='1', one_time_id='xxxxx', phone='+555', username='bob123',
                                     finished_registration=True)
        self.group_1 = Group.objects.create(id='abc')
        user_1.groups.add(self.group_1)
        DecryptionSenderKey.objects.create(stick_id='abc0', of_one_time_id='xxxxx', for_one_time_id='zzzzz',
                                           key='uqCoM6SIHVDPO2q2HXLtFW6S8RsnW5Y94j5NpM0UJbsl4+MMWuYDHYLdFBTWRmDbV2hbRk16fDndecS2i9/odQ==')

    def test_fetch_standard_sender_keys(self):
        response = self.client.post('/api/fetch-standard-sks/', {'group_id': 'abc', 'stick_id': 'abc0',
                                                                 'keys_to_fetch': ['xxxxx']})
        self.assertEqual(response.status_code, 401)

        self.user.groups.add(self.group_1)
        response = self.client.post('/api/fetch-standard-sks/', {'group_id': 'abc', 'stick_id': 'abc0',
                                                                 'keys_to_fetch': ['xxxxx']})
        self.assertEqual(response.data['sender_keys']['xxxxx'],
                         'uqCoM6SIHVDPO2q2HXLtFW6S8RsnW5Y94j5NpM0UJbsl4+MMWuYDHYLdFBTWRmDbV2hbRk16fDndecS2i9/odQ==')
        self.assertEqual(
            DecryptionSenderKey.objects.get(stick_id='abc0', of_one_time_id='xxxxx', for_one_time_id='zzzzz').key, '')


class TestFetchUploadedSenderKeys(APITestCase):
    def setUp(self):
        set_up_user(self)
        user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
        user_2 = User.objects.create(id='2', phone='+666', username='mike123', finished_registration=True)
        self.group_1 = Group.objects.create(id='abc')
        self.user.groups.add(self.group_1)
        user_1.groups.add(self.group_1)
        self.group_2 = Group.objects.create(id='edf')
        self.user.groups.add(self.group_2)
        user_2.groups.add(self.group_2)

    def test_fetch_uploaded_sender_keys(self):
        response = self.client.post('/api/fetch-uploaded-sks/',
                                    {'groups_ids': ['abc', 'edf'], 'connections_ids': [], 'is_sticky': True})
        self.assertEqual(len(response.data['bundles_to_fetch']), 3)


class TestGetActiveStickId(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.group_1 = Group.objects.create(id='abc')
        self.user.groups.add(self.group_1)
        ik = IdentityKey.objects.create(key_id=123, public='public', cipher='cipher', user=self.user, salt='salt',
                                        timestamp='timestamp')
        self.esk = EncryptionSenderKey.objects.create(user=self.user, key_id=789,
                                                      party_id='abc', chain_id='0',
                                                      identity_key=ik, key='key', step=50)

    def test_get_active_stick_id(self):
        response = self.client.post('/api/get-active-stick-id/', {'party_id': 'abc'})
        self.assertEqual(response.data['stick_id'], 'abc0')

        self.esk.step = 300
        self.esk.save()
        response = self.client.post('/api/get-active-stick-id/', {'party_id': 'abc'})
        self.assertEqual(response.data['stick_id'], 'abc1')


class TestUploadSenderKey(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.user_1 = User.objects.create(id='1', phone='+555', username='bob123', finished_registration=True)
        PreKey.objects.create(key_id=54, public='pk_public', cipher='pk_cipher', user=self.user_1, used=False,
                              salt='pk_salt')
        IdentityKey.objects.create(key_id=2, public='ik2_public', cipher='ik2_cipher', user=self.user_1,
                                   salt='ik2_salt',
                                   active=True, timestamp=999)

    def test_upload_sender_key(self):
        response = self.client.post('/api/upload-sk/',
                                    {'pre_key_id': 54, 'identity_key_id': 2, 'for_user': '1', 'key': 'key',
                                     'stick_id': 'stick_id'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            DecryptionSenderKey.objects.filter(for_user=self.user_1, of_user=self.user, stick_id='stick_id').exists(),
            True)


class TestUploadSenderKeys(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.user_1 = set_up_user_1_keys()
        self.user_2 = set_up_user_2_keys()

    def test_upload_sender_keys(self):
        response = self.client.post('/api/upload-sks/', {'users_id': ['1', '2'],
                                                         'keys':
                                                             {'1': {'pre_key_id': 54, 'identity_key_id': 2,
                                                                    'key': 'key', 'stick_id': 'stick_id',
                                                                    'for_user': '1'},
                                                              '2': {'pre_key_id': 54, 'identity_key_id': 2,
                                                                    'key': 'key', 'stick_id': 'stick_id',
                                                                    'for_user': '2'}}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            DecryptionSenderKey.objects.filter(of_user=self.user, for_user=self.user_1, stick_id='stick_id').exists(),
            True)
        self.assertEqual(
            DecryptionSenderKey.objects.filter(of_user=self.user, for_user=self.user_2, stick_id='stick_id').exists(),
            True)


class TestUploadStandardSenderKeys(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.user.one_time_id = 'xxxxx'
        self.user.save()

    def test_upload_standard_sender_keys(self):
        response = self.client.post('/api/upload-standard-sks/',
                                    {'stick_id': 'abc', 'keys_to_upload': {'one_time_id_1': 'key_1',
                                                                           'one_time_id_2': 'key_2'}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            DecryptionSenderKey.objects.filter(of_one_time_id=self.user.one_time_id, for_one_time_id='one_time_id_1',
                                               stick_id='abc').exists(), True)
        self.assertEqual(
            DecryptionSenderKey.objects.filter(of_one_time_id=self.user.one_time_id, for_one_time_id='one_time_id_2',
                                               stick_id='abc').exists(), True)


class TestUpdateActiveSPK(APITestCase):
    def setUp(self):
        set_up_user(self)
        SignedPreKey.objects.create(key_id=1, public='spk_public', signature='signature', cipher='spk_cipher',
                                    user=self.user, salt='spk_salt', active=True, timestamp=998)

    def test_update_active_spk(self):
        response = self.client.post('/api/update-active-spk/', {
            'signature': 'qlwi2G6VJDrtRCyv2u3NDbxOqSaSieJh7hXCwRZdTyKPS4tSEMKZzqvyykqEcotcFH7nArFujtcB6mK67zyGhA==',
            'public': 'BfN+T9WY12co0/RINuCz/m1ZgjouNa1yT0eiIRdmaIZ+',
            'cipher': '00Sn2ekqRTAgCY6LUNtExAiNBOryrb9bvkqZiUVZgotp71i/lxtUzB/BgJoTnAaxqDDytOIJjLkQWFgI9HYdxQ==',
            'id': 2,
            'timestamp': '1672460231481', 'salt': '5Q4aE2CD/llfS0Os0gUtNU+OffZsRJFTxt60nP9SbPc='})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SignedPreKey.objects.get(key_id=1, user=self.user).active, False)
        self.assertEqual(SignedPreKey.objects.get(key_id=2, user=self.user).active, True)


class TestUpdateActiveIK(APITestCase):
    def setUp(self):
        set_up_user(self)
        IdentityKey.objects.create(key_id=1, public='ik_public', cipher='ik_cipher', user=self.user, salt='ik_salt',
                                   active=True, timestamp=998)

    def test_update_active_ik(self):
        response = self.client.post('/api/update-active-ik/', {
            'cipher': 't3FqX6rzG3N4iDKpOmVP1T42NtaRAOd1DgpLam45MLgugbN1bxXSe8DqP6MAoeEWjpJLWSlRP4Ua6ZLlYwvdMQ==',
            'salt': 'uMXjIuWSa/xJgbsRc7m1BkpOvwO6wAC1mKdCQYsncFY=', 'timestamp': 1672460231000, 'id': 2,
            'public': 'BYqzx4D7PbzIM2ATmFXL3/NdpVb3pCgI60LgaQ+OFVxn'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(IdentityKey.objects.get(key_id=1, user=self.user).active, False)
        self.assertEqual(IdentityKey.objects.get(key_id=2, user=self.user).active, True)


class TestFetchOneTimeId(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.user_1 = User.objects.create(id='111', one_time_id='xxxxx', name='Bob',
                                          phone='+555', username='bob123', finished_registration=True)

    def test_fetch_one_time_id(self):
        response = self.client.get('/api/fetch-otid/?id=111')
        self.assertEqual(response.data['one_time_id'], 'xxxxx')
        self.assertEqual(response.data['is_blocked'], False)
        self.assertEqual(response.data['name'], 'Bob')


class TestFetchPendingKeys(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.user_1 = User.objects.create(id='111', one_time_id='xxxxx', name='Bob',
                                          phone='+555', username='bob123', finished_registration=True)
        PendingKey.objects.create(owner=self.user, user=self.user_1, stick_id='stick_id_0')

    def test_fetch_pending_keys(self):
        response = self.client.get('/api/fetch-pending-keys/')
        self.assertEqual(response.data['pending_keys'][0]['stick_id'], 'stick_id_0')
        self.assertEqual(response.data['pending_keys'][0]['receiver_id'], '111')
        self.assertEqual(PendingKey.objects.filter(owner=self.user, user=self.user_1, stick_id='stick_id_0').exists(),
                         False)


class TestLogin(APITestCase):
    def setUp(self):
        set_up_user(self)
        Preferences.objects.create(user=self.user)
        user_1 = User.objects.create(id='111', one_time_id='xxxxx', name='Bob',
                                     phone='+555', username='bob123', finished_registration=True)
        Party.objects.create(user=user_1)
        self.user.connections.add(user_1)
        user_1.connections.add(self.user)
        token = create_token_string()
        salt = create_salt_string()
        hash = hash_token(token, salt)
        LimitedAccessToken.objects.create(hash=hash, salt=salt, auth_id=self.user.phone)
        self.client.credentials(HTTP_AUTHORIZATION=token)
        self.user.set_password('uxPYx2/8Jlm9QDRMS+tP3aH+WSLA27/n0NlHILE3I/M=')
        self.user.password_salt = 'd9Vmgv7VlM3QbtHH3yAaLure2CrGUoPu9PUcScyyN6E='
        self.user.local_id = 14892
        self.user.save()
        ik = IdentityKey.objects.create(key_id=1, public='ik_public', cipher='ik_cipher', user=self.user,
                                        salt='ik_salt',
                                        active=False, timestamp=998)
        IdentityKey.objects.create(key_id=2, public='ik2_public', cipher='ik2_cipher', user=self.user, salt='ik2_salt',
                                   active=True, timestamp=999)
        SignedPreKey.objects.create(key_id=3, public='spk_public', signature='signature', cipher='spk_cipher',
                                    user=self.user, salt='spk_salt', active=False, timestamp=998)
        SignedPreKey.objects.create(key_id=4, public='spk2_public', signature='signature2', cipher='spk2_cipher',
                                    user=self.user, salt='spk_salt', active=True, timestamp=999)
        pk_1 = PreKey.objects.create(key_id=54, public='pk_public', cipher='pk_cipher', user=self.user, used=True,
                                     salt='pk_salt')
        pk_2 = PreKey.objects.create(key_id=55, public='pk2_public', cipher='pk2_cipher', user=self.user, used=True,
                                     salt='pk2_salt')
        EncryptionSenderKey.objects.create(user=self.user, key_id=789,
                                           party_id='5a71cdda-77d0-40ab-b232-289888062562', chain_id='0',
                                           identity_key=ik, key='key', pre_key=pk_1)
        display_name = Cipher.objects.create(text='text', user=self.user)
        group_1 = Group.objects.create(id='abc', display_name=display_name)
        self.user.groups.add(group_1)
        user_1.groups.add(group_1)

    def test_login(self):
        response = self.client.post('/api/login/', {'phone': self.user.phone,
                                                    'device_id': 'XYZ', 'device_name': 'iPhone 13',
                                                    'password_hash': 'uxPYx2/8Jlm9QDRMS+tP3aH+WSLA27/n0NlHILE3I/M='})
        self.assertIn('user', response.data)
        self.assertEqual(len(response.data['token']), 64)
        self.assertEqual(response.data['correct'], True)
        self.assertEqual(response.data['devices_count'], 1)
        self.assertEqual(response.data['chat_backup_timestamp'], 0)
        self.assertEqual(LimitedAccessToken.objects.filter(auth_id=self.user.phone).exists(), False)
        bundle = response.data['bundle']
        self.assertEqual(bundle['local_id'], 14892)
        self.assertEqual(len(bundle['identity_keys']), 2)
        self.assertEqual(len(bundle['signed_pre_keys']), 2)
        self.assertEqual(len(bundle['pre_keys']), 2)
        self.assertEqual(len(bundle['sender_keys']), 1)

class TestChangePassword(APITestCase):
    # TODO: important to update (vault cipher)
    def setUp(self):
        set_up_user(self)
        self.user.set_password('uxPYx2/8Jlm9QDRMS+tP3aH+WSLA27/n0NlHILE3I/M=')
        self.user.password_salt = 'd9Vmgv7VlM3QbtHH3yAaLure2CrGUoPu9PUcScyyN6E='
        self.user.save()
        IdentityKey.objects.create(key_id=1, public='ik_public', cipher='ik_cipher', user=self.user,
                                   salt='ik_salt', active=True, timestamp=998)
        SignedPreKey.objects.create(key_id=3, public='spk_public', signature='signature', cipher='spk_cipher',
                                    user=self.user, salt='spk_salt', active=True, timestamp=998)
        PreKey.objects.create(key_id=54, public='pk_public', cipher='pk_cipher', user=self.user, used=False,
                              salt='pk_salt')
        Device.objects.create(device_id='device_id', user=self.user, auth_token=self.auth_token[0])

    def test_change_password(self):
        body = {'keys': {'current_pass': 'uxPYx2/8Jlm9QDRMS+tP3aH+WSLA27/n0NlHILE3I/M=', 'new_pass': 'new_pass',
                         'new_salt': 'new_salt',
                         'pre_keys': [{'id': 54, 'cipher': 'new_pk_cipher', 'salt': 'new_pk_salt'}],
                         'signed_pre_keys': [{'id': 3, 'cipher': 'new_spk_cipher', 'salt': 'new_spk_salt'}],
                         'identity_keys': [{'id': 1, 'cipher': 'new_ik_cipher', 'salt': 'new_ik_salt'}]},
                'vault_cipher': {'files_cipher': [], 'notes_cipher': [], 'profile': {}},
                'device_id': 'device_id'}
        response = self.client.post('/api/change-password/', body)
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(updated_user.check_password('new_pass'), True)
        self.assertEqual(IdentityKey.objects.get(user=self.user, key_id=1).cipher, 'new_ik_cipher')
        self.assertEqual(IdentityKey.objects.get(user=self.user, key_id=1).salt, 'new_ik_salt')
        self.assertEqual(SignedPreKey.objects.get(user=self.user, key_id=3).cipher, 'new_spk_cipher')
        self.assertEqual(SignedPreKey.objects.get(user=self.user, key_id=3).salt, 'new_spk_salt')
        self.assertEqual(PreKey.objects.get(user=self.user, key_id=54).cipher, 'new_pk_cipher')
        self.assertEqual(PreKey.objects.get(user=self.user, key_id=54).salt, 'new_pk_salt')


pre_keys = [{'salt': 'mGhTzJnNI6OsVAs9hgb5cTw3wXjlt4y5vHo7KJytNfg=',
             'cipher': 'uqCoM6SIHVDPO2q2HXLtFW6S8RsnW5Y94j5NpM0UJbsl4+MMWuYDHYLdFBTWRmDbV2hbRk16fDndecS2i9/odQ==',
             'id': 512,
             'public': 'BcL/ciTDAH/yME+NOxdQkS+uLatqaVLWjioNm942GcE2'},
            {'id': 1, 'salt': 'qNkVPJOBRz5AdwYAGQWWPv+LgLP7ZYu6drf/NuMr3Fg=',
             'public': 'BSK+ct/txxNWyJ/HKVpv5ZYTfXXtBNrJkNXkmx2n8D0t',
             'cipher': 'uKFVpYRDQ2wT7YIXfYTMZnpAXU4xFpVxYn/gPs7KinsW//bM/YyNSRCoRM0eKs4FCutV1vB+nhROY6JmPNwFxA=='},
            {'public': 'BcIdFXFR5lrSBM+aRnQs+OVx0ZHwsjk0DB0hvhaIQa42',
             'salt': 'ULlmE/6k2ScU8kGk0hmmzRkyUdg7NCJ/3mIzPTlN/aA=',
             'cipher': 'gupohVRjYSpZOjehskgv6SPg1p+fBhs7meZpkl3cc7gRCN+xZhS7IbWmtHN6kO4iFYD+6ROjpMi+u/qoUARxBQ==',
             'id': 2},
            {'public': 'BQCLEFUhssK3rLVO5i+crZQ4Tj09qbn0ueEKSItLJh9J', 'id': 3,
             'salt': 'KPIF0v3bYjEMZEgCWaY7NtSKD1Tw+xxBeXL9dV7fU+c=',
             'cipher': 'kNsGOncUHYa7UgmxciQLDXRTMKcz7KpYCz1vO1ZpfquCritG3gmpnuL+o3OURVmLoa0O8exxF6CKoOb5qoh/Cw=='},
            {'id': 4, 'salt': 'zoU0AWXbELIvMwhqdk5zfeWD6Zsbi6Z7j9qzIAOla3Q=',
             'cipher': 'ATd8e2r6BQuBF4z4yfryAfE1YlGc8E/iabIVQIp5wBq/cF/eSKUievfMMpYMF8+T9clhTkP23RqytA3QpegVLg==',
             'public': 'BWVCV33gc+XWlxnWrhkgmCMD9H8CcqAWCvkSiSEwd2E/'},
            {'cipher': 'CwCEpAEe0E9cfxH1C55dYwiiZHDwaggQsJ/3a0suYOJ/uvmzSyyNQdeKrItp3mvo3MKQDjzb6qvB8rhwTr8rEw==',
             'salt': 'mjNfLe1ROY8L1UFGfRWBSIEoYrfzQ4fq+H9stXRJCbI=', 'id': 5,
             'public': 'BVUEbN5fRm35DXxMUlhirl+X6LnRTUfUAZeb6/7QasAi'},
            {'id': 6, 'public': 'BaYcpdmXhg5g+HG3nY0K4lUHKy6zWEjZC8DGPcaBmUkF',
             'salt': 'ZiXEb0++iaFbqm8GiD68Kxn4Jo20h1ad0mcuyZmTCD4=',
             'cipher': 'iYmriQ6VZfZ5Vec6YAmxr8RayNjRzGp+tzKR2hJKTQPSnaE36ELt+QPIN1BcjIUMk+tZ2Rb+7zEWdgLppwNFYw=='},
            {'cipher': 'HPGA46fAmcHHCKn8HnxkmvkX7LL0PGuxnVLg0I1sCfFBwblC9mt46tDarkTzqaqA6+7LCZ+yovs7c24xu77ioA==',
             'id': 7,
             'salt': 'EXuMpEXUzv20nELr2O1laYEeqAaGgZ3EQECrNicGm+A=',
             'public': 'BfFJGAqAFDbz1EsOTl/oEdZeoUb8h1L01A+yyZSEOU4A'},
            {'salt': 'EByYvx1IMil+GkNy9s/B1PlwKltZVIXT1QmFZHPMHMs=', 'id': 8,
             'cipher': 'PCyntDnu6rRsK+a9szKAc259H2KJ39AnaWpYfneXuS6Bc+ddLF8GI1HQ0XcHH1uit64DGxjmMAPxrwNbsyn+3g==',
             'public': 'BcyLZp8cWWetMMZS6npkOK476jGKd9COK4OAUaFI30B8'},
            {'cipher': 'IETQLyJ0vpf93LCkoIl0XklBvhh9jxVSmqP1ZmpGN0LeyzguccGaB0zTSbeIj86+CVWJjPCEA239J3Uz/kd38g==',
             'salt': 'YVvtCMIvvmUQmfkNDfQA1/qu9dJSMpn6cdlSD9aBoO0=',
             'public': 'BdnUUigOhty6bH9EwVZtTlhPvwJVPGzRjEmSYf2y+ZIB',
             'id': 9}]

upload_pkb_body = {'password_hash': 'uxPYx2/8Jlm9QDRMS+tP3aH+WSLA27/n0NlHILE3I/M=',
                   'identity_key': {
                       'cipher': 't3FqX6rzG3N4iDKpOmVP1T42NtaRAOd1DgpLam45MLgugbN1bxXSe8DqP6MAoeEWjpJLWSlRP4Ua6ZLlYwvdMQ==',
                       'salt': 'uMXjIuWSa/xJgbsRc7m1BkpOvwO6wAC1mKdCQYsncFY=', 'timestamp': 1672460231000, 'id': 23,
                       'public': 'BYqzx4D7PbzIM2ATmFXL3/NdpVb3pCgI60LgaQ+OFVxn'},
                   'local_id': 14892,
                   'pre_keys': pre_keys,
                   'password_salt': 'd9Vmgv7VlM3QbtHH3yAaLure2CrGUoPu9PUcScyyN6E=',
                   'one_time_id': 'b85fa317-0daa-4409-a1f1-5d56b384b22c',
                   'signed_pre_key': {
                       'signature': 'qlwi2G6VJDrtRCyv2u3NDbxOqSaSieJh7hXCwRZdTyKPS4tSEMKZzqvyykqEcotcFH7nArFujtcB6mK67zyGhA==',
                       'public': 'BfN+T9WY12co0/RINuCz/m1ZgjouNa1yT0eiIRdmaIZ+',
                       'cipher': '00Sn2ekqRTAgCY6LUNtExAiNBOryrb9bvkqZiUVZgotp71i/lxtUzB/BgJoTnAaxqDDytOIJjLkQWFgI9HYdxQ==',
                       'id': 0,
                       'timestamp': '1672460231481', 'salt': '5Q4aE2CD/llfS0Os0gUtNU+OffZsRJFTxt60nP9SbPc='},
                   'next_pre_key_id': 10,
                   'phone': '+16501119999',
                   'device_id': 'ac7e940c-7d3a-4377-a9ca-adbb4b7ff1af',
                   'device_name': 'iPhone 13 Pro'}

upload_pre_keys = {'pre_keys': pre_keys, 'next_pre_key_id': 10}
