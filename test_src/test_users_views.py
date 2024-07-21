from firebase_admin import auth
from unittest.mock import MagicMock
from knox.crypto import create_token_string, hash_token, create_salt_string
from knox.models import AuthToken
from users.models import User, AppSettings, LimitedAccessToken, Preferences, Device, EmailVerification
from photos.models import Image
from groups.models import Cipher
from rest_framework.test import APITestCase
from stick_protocol.models import EncryptionSenderKey, IdentityKey


def set_up_user(self):
    self.user = User.objects.create(username='alice123', phone='1', phone_hash='AX(*$', email='test@test.com', finished_registration=True)
    self.auth_token = AuthToken.objects.create(self.user)
    self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.auth_token[1])

def set_up_esk(self):
    ik = IdentityKey.objects.create(key_id=123, public='public', cipher='cipher', user=self.user, salt='salt',
                                    timestamp='timestamp')
    self.esk = EncryptionSenderKey.objects.create(user=self.user, key_id=789,
                                                  party_id='5a71cdda-77d0-40ab-b232-289888062562', chain_id='0',
                                                  identity_key=ik, key='key')

CIPHER_BODY = {'stick_id': '5a71cdda-77d0-40ab-b232-2898880625620', 'chain_step': 50, 'text': 'text', 'uri': 'uri',
                'file_size': 100, 'text_length': 100}

class TestGetAppSettings(APITestCase):
    def setUp(self):
        AppSettings.objects.create(minViableIOSVersion='3.2.0', minViableAndroidVersion='3.0.0')

    def test_get_app_settings(self):
        response = self.client.get('/api/get-app-settings/')
        self.assertEqual(response.data['minViableIOSVersion'], '3.2.0')
        self.assertEqual(response.data['minViableAndroidVersion'], '3.0.0')

class TestPhoneVerified(APITestCase):
    def setUp(self):
        self.url = '/api/phone-verified/'
        auth.verify_id_token = MagicMock(return_value=True)
        User.objects.create(phone='+971559999990', phone_hash='AX(*$', username='alice123', finished_registration=True,
                            password_salt='password_salt', password_key='password_key')

    def test_phone_verified_0(self):
        body = {'id_token': 'id_token_x', 'phone': '+971551111110'}
        response = self.client.post(self.url, body)
        self.assertEqual(response.data['exists'], False)
        self.assertEqual(len(response.data['limited_access_token']), 64)

    def test_phone_verified_1(self):
        body = {'id_token': 'id_token', 'phone': '+971559999990'}
        response = self.client.post(self.url, body)
        data = response.data
        self.assertEqual(data['exists'], True)
        self.assertEqual(len(data['limited_access_token']), 64)
        self.assertEqual(data['username'], 'alice123')
        self.assertEqual(data['password_salt'], 'password_salt')
        self.assertEqual(data['password_key'], 'password_key')
        self.assertEqual(data['username'], 'alice123')
        self.assertIn('user_id', data)

class TestCheckUsername(APITestCase):
    def setUp(self):
        self.url = '/api/check-username/'
        User.objects.create(username='alice123')

    def test_check_username_0(self):
        body = {'username': 'alice123'}
        response = self.client.post(self.url, body)
        self.assertEqual(response.data['valid'], False)

    def test_check_username_1(self):
        body = {'username': 'alice1234'}
        response = self.client.post(self.url, body)
        self.assertEqual(response.data['valid'], True)

class TestRegister(APITestCase):
    def setUp(self):
        self.url = '/api/register/'
        User.objects.create(username='alice123')

    def test_register_0(self):
        token = create_token_string()
        salt = create_salt_string()
        hash = hash_token(token, salt)
        LimitedAccessToken.objects.create(hash=hash, salt=salt, auth_id='test@test.com')
        body = {'username': 'alice123', 'email': 'test@test.com', 'name': 'alice', 'platform': 'ios'}
        self.client.credentials(HTTP_AUTHORIZATION=token)
        response = self.client.post(self.url, body)
        self.assertEqual(response.data['success'], False)

    def test_register_1(self):
        token = create_token_string()
        salt = create_salt_string()
        hash = hash_token(token, salt)
        LimitedAccessToken.objects.create(hash=hash, salt=salt, auth_id='test@test.com')
        body =  {'username': 'bob123', 'email': 'test@test.com', 'name': 'Bob', 'platform': 'ios'}
        self.client.credentials(HTTP_AUTHORIZATION=token)
        response = self.client.post(self.url, body)
        self.assertEqual(response.data['success'], True)
        self.assertIn('user', response.data)


class TestRefreshUser(APITestCase):
    def setUp(self):
        set_up_user(self)
        Preferences.objects.create(user=self.user)

    def test_refresh_user(self):
        response = self.client.get('/api/refresh-user/')
        self.assertIn('user', response.data)
        self.assertIn('pre_keys_count', response.data)
        self.assertIn('unread_count', response.data)


class TestUserSearch(APITestCase):
    def setUp(self):
        set_up_user(self)
        User.objects.create(username='bob123', phone='2', finished_registration=True)
        User.objects.create(name='John Doe', phone='3', finished_registration=True)

    def test_user_search(self):
        response = self.client.get('/api/search/?q=bob')
        self.assertEqual(response.data['results'][0]['username'], 'bob123')
        response = self.client.get('/api/search/?q=John')
        self.assertEqual(response.data['results'][0]['name'], 'John Doe')


class TestUploadCategories(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_esk(self)

    def test_upload_categories(self):
        response = self.client.post('/api/upload-categories/', CIPHER_BODY)
        updated_user = User.objects.get(id=self.user.id)
        updated_esk = EncryptionSenderKey.objects.get(id=self.esk.id)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(updated_user.categories)
        self.assertEqual(updated_esk.step, 50)


class TestBackupChats(APITestCase):

    def setUp(self):
        set_up_user(self)
        set_up_esk(self)

    def test_backup_chats(self):
        response = self.client.post('/api/backup-chats/', CIPHER_BODY)
        updated_user = User.objects.get(id=self.user.id)
        updated_esk = EncryptionSenderKey.objects.get(id=self.esk.id)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(updated_user.chat_backup)
        self.assertEqual(updated_esk.step, 50)

        response = self.client.post('/api/delete-chat-backup/')
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(updated_user.chat_backup)

class TestUpdateBackupFreq(APITestCase):

    def setUp(self):
        set_up_user(self)

    def test_update_chat_backup(self):
        response = self.client.post('/api/update-backup-freq/', {'freq': 'weekly'})
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(updated_user.backup_frequency, 'weekly')


class TestBlock(APITestCase):

    def setUp(self):
        set_up_user(self)

    def test_block(self):
        # test BlockUser
        connection = User.objects.create(username='bob123', phone='+2', finished_registration=True)
        self.user.connections.add(connection)
        response = self.client.post('/api/block/', {'id': connection.id})
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(updated_user.connections.all(), [])
        self.assertQuerysetEqual(updated_user.blocked.all(), map(repr, [connection]))

        # test FetchBlockedAccounts
        response = self.client.get('/api/fetch-blocked/', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(len(response.data), 1)
        # test UnblockUser
        response = self.client.post('/api/unblock/', {'id': connection.id})
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(updated_user.blocked.all(), [])


class TestFetchSingleUser(APITestCase):

    def setUp(self):
        set_up_user(self)
        User.objects.create(id='abc')

    def test_fetch_single_user(self):
        response = self.client.get('/api/fetch-single-user/?id=abc')
        self.assertEqual(response.data['is_connected'], False)
        self.assertEqual(response.data['requested'], False)
        self.assertIn('user', response.data)


class TestFetchDevices(APITestCase):

    def setUp(self):
        set_up_user(self)
        Device.objects.create(device_id='device_id', user=self.user, name='test')
        token = create_token_string()
        salt = create_salt_string()
        hash = hash_token(token, salt)
        LimitedAccessToken.objects.create(hash=hash, salt=salt, auth_id=self.user.phone)
        self.client.credentials(HTTP_AUTHORIZATION=token)

    def test_fetch_devices(self):
        response = self.client.post('/api/fetch-devices/', {'phone': self.user.phone,
                                                            'current_device_id': 'current_device_id'})
        self.assertEqual(response.data[0]['id'], 'device_id')
        self.assertEqual(response.data[0]['name'], 'test')


class TestFetchUserDevices(APITestCase):

    def setUp(self):
        set_up_user(self)
        Device.objects.create(device_id='device_id', user=self.user, name='test')

    def test_fetch_user_devices(self):
        response = self.client.get('/api/fetch-user-devices/')
        self.assertEqual(response.data[0]['id'], 'device_id')
        self.assertEqual(response.data[0]['name'], 'test')


class TestUploadPasswordKey(APITestCase):

    def setUp(self):
        set_up_user(self)

    def test_upload_password_key(self):
        response = self.client.post('/api/upload-pk/', {'password_key': 'password_key'})
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(updated_user.password_key, 'password_key')


class TestVerifyPassword(APITestCase):

    def setUp(self):
        set_up_user(self)
        self.user.set_password('initial_password_hash')
        self.user.save()

    def test_verify_password(self):
        response = self.client.post('/api/verify-password/', {'password': 'initial_password_hash'})
        self.assertEqual(response.data['verified'], True)

class TestFetchPreferences(APITestCase):

    def setUp(self):
        set_up_user(self)
        self.device = Device.objects.create(device_id='device_id', user=self.user, name='test')
        Preferences.objects.create(user=self.user, chat_device=self.device, favorites_ids=['abc-123'])
    def test_fetch_preferences(self):
        response = self.client.get('/api/fetch-preferences/')
        self.assertEqual(response.data['chat_device_id'], self.device.device_id)
        self.assertEqual(response.data['favorites_ids'], ['abc-123'])


class TestFetchUserCategories(APITestCase):

    def setUp(self):
        set_up_user(self)
        self.user.categories = Cipher.objects.create(user=self.user, id=123)
        self.user.save()

    def test_fetch_user_categories(self):
        response = self.client.get('/api/fetch-user-categories/')
        self.assertEqual(response.data['results'][0]['id'], 123)


class TestFetchUserChatBackup(APITestCase):

    def setUp(self):
        set_up_user(self)
        self.user.chat_backup = Cipher.objects.create(user=self.user, id=123)
        self.user.save()

    def test_fetch_user_chat_backup(self):
        response = self.client.get('/api/fetch-user-chat-backup/')
        self.assertEqual(response.data['results'][0]['id'], 123)


class TestUpdateChatDevice(APITestCase):

    def setUp(self):
        set_up_user(self)
        self.device = Device.objects.create(user=self.user, device_id='device_id', chat_id='chat_id')
        Preferences.objects.create(user=self.user)


    def test_update_chat_device(self):
        response = self.client.post('/api/update-chat-device/', {'device_id': 'device_id', 'latest': False})
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(updated_user.one_time_id, self.device.chat_id)
        self.assertEqual(updated_user.preferences.chat_device, self.device)

class TestDeactivateAccount(APITestCase):

    def setUp(self):
        set_up_user(self)

    def test_deactivate_account(self):
        response = self.client.post('/api/deactivate/')
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(updated_user.is_active, False)
        self.assertQuerysetEqual(updated_user.auth_token_set.all(), [])


class TestDeleteAccount(APITestCase):

    def setUp(self):
        set_up_user(self)
        auth.verify_id_token = MagicMock(return_value=True)
        Preferences.objects.create(user=self.user)
        EmailVerification.objects.create(email=self.user.email, code='123456')
        self.user.set_password('initial_password_hash')
        self.user.save()

    def test_delete_account(self):
        response = self.client.post('/api/code-confirmed-delete-account/', {'code': '123456'})
        self.assertIn('delete_account_token', response.data)
        response = self.client.post('/api/delete-account/', {'delete_account_token': response.data['delete_account_token'],
                                                             'password': 'initial_password_hash'})
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['correct_password'], True)
        self.assertEqual(response.data['correct_token'], True)
        self.assertEqual(User.objects.filter(id=self.user.id).exists(), False)


class TestRecreateUser(APITestCase):
    def setUp(self):
        set_up_user(self)
        Preferences.objects.create(user=self.user)
        token = create_token_string()
        salt = create_salt_string()
        hash = hash_token(token, salt)
        LimitedAccessToken.objects.create(hash=hash, salt=salt, auth_id=self.user.phone)
        self.client.credentials(HTTP_AUTHORIZATION=token)

    def test_recreate_user(self):
        response = self.client.post('/api/recreate-user/', {'user_id': self.user.id, 'phone': self.user.phone})
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['user']['username'], self.user.username)
        self.assertEqual(response.data['user']['phone'], self.user.phone)
        self.assertEqual(response.data['user']['name'], self.user.name)
        self.assertEqual(response.data['user']['dial_code'], self.user.dial_code)
        self.assertEqual(response.data['user']['country'], self.user.country)
        self.assertEqual(response.data['user']['color'], self.user.color)
        self.assertEqual(User.objects.filter(id=self.user.id).exists(), False)


class TestHighlightImage(APITestCase):

    def setUp(self):
        set_up_user(self)
        self.image = Image.objects.create(user=self.user)

    def test_highlight_image(self):
        response = self.client.post('/api/highlight-image/', {'image_id': self.image.id, 'blobs_ids': ['123']})
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(response.data['highlighted'], True)
        self.assertEqual(updated_user.highlights_ids, [str(self.image.id) + '-' + '123'])

class TestToggleHideImage(APITestCase):
    def setUp(self):
        set_up_user(self)

    def test_toggle_hide_image(self):
        response = self.client.post('/api/toggle-hide-image/', {'hide': True, 'image_id': '123'})
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(updated_user.hidden_images, ['123'])

        response = self.client.post('/api/toggle-hide-image/', {'hide': False, 'image_id': '123'})
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(updated_user.hidden_images, [])









