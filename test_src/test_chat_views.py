from knox.models import AuthToken
from users.models import User
from chat.models import ChatFile, ChatAlbum, ChatAudio
from groups.models import Group, Cipher
from stick_protocol.models import Party
from rest_framework.test import APITestCase

def set_up_user(self):
    self.user = User.objects.create(username='alice123', phone='1', phone_hash='AX(*$', finished_registration=True)
    self.auth_token = AuthToken.objects.create(self.user)
    self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.auth_token[1])

def set_up_groups_and_parties(self):
    self.group = Group.objects.create(id='group1', chat_id='chat1', owner=self.user)
    self.group.admins.add(self.user)  # Ensure the user is an admin of the group
    self.party = Party.objects.create(id='party1', user=self.user)
    self.user.groups.add(self.group)

def set_up_chat_files(self):
    title_cipher = Cipher.objects.create(text='Test Title', user=self.user)
    self.album = ChatAlbum.objects.create(user=self.user, title=title_cipher, group=self.group)
    self.chat_file_1 = ChatFile.objects.create(user=self.user, name='file1.txt', uri_key='uri_key1', preview_uri_key='preview_uri_key1', album=self.album, group=self.group)
    self.chat_file_2 = ChatFile.objects.create(user=self.user, name='file2.txt', uri_key='uri_key2', preview_uri_key='preview_uri_key2', album=self.album, group=self.group)
    self.chat_audio_1 = ChatAudio.objects.create(user=self.user, uri_key='audio_key1', cipher='cipher1', file_size=100, duration=60, group=self.group)
    self.chat_audio_2 = ChatAudio.objects.create(user=self.user, uri_key='audio_key2', cipher='cipher2', file_size=200, duration=120)

class TestUploadChatFiles(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_groups_and_parties(self)

    def test_upload_chat_files(self):
        files = [
            {'uri_key': 'key1', 'preview_uri_key': 'preview_key1', 'cipher': 'cipher1', 'preview_cipher': 'preview_cipher1', 'file_size': 100, 'preview_file_size': 10, 'width': 100, 'height': 100, 'name': 'file1', 'type': 'text', 'duration': 0, 'created_at': 1234},
            {'uri_key': 'key2', 'preview_uri_key': 'preview_key2', 'cipher': 'cipher2', 'preview_cipher': 'preview_cipher2', 'file_size': 200, 'preview_file_size': 20, 'width': 100, 'height': 100, 'name': 'file2', 'type': 'text', 'duration': 0, 'created_at': 1235}
        ]
        response = self.client.post('/api/upload-chat-files/', {'files': files, 'stick_id': 'stick_id', 'message_id': 'message_id', 'is_media': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['files']), 2)

class TestUploadChatAudio(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_groups_and_parties(self)

    def test_upload_chat_audio(self):
        audio = {'uri_key': 'audio_key', 'cipher': 'audio_cipher', 'file_size': 100, 'duration': 60}
        response = self.client.post('/api/upload-chat-audio/', {'audio': audio, 'stick_id': 'stick_id'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('audio', response.data)

class TestFetchChatFiles(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_groups_and_parties(self)
        set_up_chat_files(self)

    def test_fetch_chat_files(self):
        response = self.client.get(f'/api/fetch-chat-files/?ids={self.chat_file_1.id},{self.chat_file_2.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
#
class TestFetchChatAudio(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_groups_and_parties(self)
        set_up_chat_files(self)

    def test_fetch_chat_audio(self):
        response = self.client.get(f'/api/fetch-chat-audio/?id={self.chat_audio_1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('audio', response.data)

class TestFetchChatAlbums(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_groups_and_parties(self)
        set_up_chat_files(self)

    def test_fetch_chat_albums(self):
        response = self.client.get(f'/api/fetch-chat-albums/?room_id={self.group.id}&is_group=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
#
class TestFetchSingleChatAlbum(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_groups_and_parties(self)
        set_up_chat_files(self)

    def test_fetch_single_chat_album(self):
        response = self.client.get(f'/api/fetch-single-chat-album/?id={self.album.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('album', response.data)

class TestFetchAlbumPhotos(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_groups_and_parties(self)
        set_up_chat_files(self)

    def test_fetch_album_photos(self):
        response = self.client.get(f'/api/fetch-album-photos/?q={self.album.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

class TestDeleteChatFiles(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_groups_and_parties(self)
        set_up_chat_files(self)

    def test_delete_chat_files(self):
        response = self.client.post('/api/delete-chat-files/', {'ids': [self.chat_file_1.id, self.chat_file_2.id]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChatFile.objects.filter(id__in=[self.chat_file_1.id, self.chat_file_2.id]).count(), 0)

class TestDeleteChatAudio(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_groups_and_parties(self)
        set_up_chat_files(self)

    def test_delete_chat_audio(self):
        response = self.client.post('/api/delete-chat-audio/', {'id': self.chat_audio_1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChatAudio.objects.filter(id=self.chat_audio_1.id).count(), 0)

class TestRenameAlbum(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_groups_and_parties(self)
        set_up_chat_files(self)

    def test_rename_album(self):
        response = self.client.post('/api/rename-album/', {'album_id': self.album.id, 'encrypted_album_title': 'New Title', 'stick_id': 'stick_id'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChatAlbum.objects.get(id=self.album.id).title.text, 'New Title')
#
class TestDeleteChatAlbum(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_groups_and_parties(self)
        set_up_chat_files(self)

    def test_delete_chat_album(self):
        response = self.client.post('/api/delete-chat-album/', {'album_id': self.album.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChatAlbum.objects.filter(id=self.album.id).count(), 0)
#
class TestFetchStorages(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_groups_and_parties(self)
        set_up_chat_files(self)

    def test_fetch_storages(self):
        response = self.client.get('/api/fetch-storages/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('group_storages', response.data)
        self.assertIn('party_storages', response.data)
#
class TestFetchRoomFiles(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_groups_and_parties(self)
        set_up_chat_files(self)

    def test_fetch_room_files(self):
        response = self.client.get(f'/api/fetch-room-files/?room_id={self.group.id}&is_group=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
