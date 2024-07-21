from knox.models import AuthToken
from users.models import User, Preferences
from vault.models import File, VaultAlbum, VaultNote
from rest_framework.test import APITestCase

def set_up_user(self):
    self.user = User.objects.create(username='alice123', phone='1', phone_hash='AX(*$', finished_registration=True)
    self.auth_token = AuthToken.objects.create(self.user)
    self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.auth_token[1])

def set_up_files(self):
    folder = File.objects.create(user=self.user, folder_type='home', name='Home', is_folder=True)
    self.file_1 = File.objects.create(user=self.user, name='file1.txt', folder=folder, uri_key='uri_key1')
    self.file_2 = File.objects.create(user=self.user, name='file2.txt', folder=folder, uri_key='uri_key2')
    self.file_3 = File.objects.create(user=self.user, name='file3.txt', folder=folder, is_photo=True, uri_key='uri_key3')
    self.file_4 = File.objects.create(user=self.user, name='file4.txt', folder=folder, is_photo=True, uri_key='uri_key4')
    self.file_5 = File.objects.create(user=self.user, name='file5', folder=folder, is_folder=True)

def set_up_vault_notes(self):
    self.note_1 = VaultNote.objects.create(user=self.user, cipher='cipher_1')
    self.note_2 = VaultNote.objects.create(user=self.user, cipher='cipher_2')


class TestUploadFiles(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_files(self)

    def test_upload_files(self):
        files = [
            {'uri_key': 'key1', 'cipher': 'cipher1', 'file_size': 100, 'name': 'file1', 'type': 'text', 'duration': 0, 'is_photo': False, 'created_at': 1234},
            {'uri_key': 'key2', 'cipher': 'cipher2', 'file_size': 200, 'name': 'file2', 'type': 'text', 'duration': 0, 'is_photo': False, 'created_at': 1235}
        ]
        response = self.client.post('/api/upload-files/', {'files': files, 'folder_id': 'home'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

class TestGetUploadUrls(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_files(self)

    def test_get_upload_urls(self):
        uri_keys = [{'uri_key': 'key1', 'preview_uri_key': 'preview_key1'}, {'uri_key': 'key2', 'preview_uri_key': 'preview_key2'}]
        response = self.client.post('/api/get-upload-urls/', {'uri_keys': uri_keys})
        self.assertEqual(response.status_code, 200)
        self.assertIn('key1', response.data)
        self.assertIn('key2', response.data)

class TestCreateFolder(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_files(self)

    def test_create_folder(self):
        response = self.client.post('/api/create-folder/', {'parent_folder_id': 'home', 'name': 'New Folder'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.data)

class TestRenameFile(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_files(self)

    def test_rename_file(self):
        response = self.client.post('/api/rename-file/', {'id': self.file_1.id, 'name': 'renamed_file.txt'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(File.objects.get(id=self.file_1.id).name, 'renamed_file.txt')

class TestCreateVaultAlbum(APITestCase):
    def setUp(self):
        set_up_user(self)

    def test_create_vault_album(self):
        response = self.client.post('/api/create-vault-album/', {'name': 'New Album'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.data)

class TestFetchFiles(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_files(self)

    def test_fetch_files(self):
        response = self.client.get('/api/fetch-files/?folder_id=home')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 5)

class TestFetchPhotos(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_files(self)

    def test_fetch_photos(self):
        response = self.client.get('/api/fetch-photos/?album_id=recents')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

class TestFetchVaultAlbums(APITestCase):
    def setUp(self):
        set_up_user(self)
        self.album = VaultAlbum.objects.create(name='Album 1', user=self.user)

    def test_fetch_vault_albums(self):
        response = self.client.get('/api/fetch-vault-albums/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

class TestFetchVaultNotes(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_vault_notes(self)

    def test_fetch_vault_notes(self):
        response = self.client.get('/api/fetch-vault-notes/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

class TestCreateVaultNote(APITestCase):
    def setUp(self):
        set_up_user(self)

    def test_create_vault_note(self):
        response = self.client.post('/api/create-vault-note/', {'cipher': 'new_cipher'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.data)

class TestUpdateVaultNote(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_vault_notes(self)

    def test_update_vault_note(self):
        response = self.client.post('/api/update-vault-note/', {'id': self.note_1.id, 'cipher': 'updated_cipher'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(VaultNote.objects.get(id=self.note_1.id).cipher, 'updated_cipher')

class TestDeleteFiles(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_files(self)

    def test_delete_files(self):
        response = self.client.post('/api/delete-files/', {'ids': [self.file_1.id, self.file_2.id]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(File.objects.filter(id__in=[self.file_1.id, self.file_2.id]).count(), 0)

class TestFetchHomeItems(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_files(self)
        set_up_vault_notes(self)

    def test_fetch_home_items(self):
        response = self.client.get('/api/fetch-home-items/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('files', response.data)
        self.assertIn('photos', response.data)
        self.assertIn('notes', response.data)

class TestFetchLatestFiles(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_files(self)

    def test_fetch_latest_files(self):
        response = self.client.get('/api/fetch-latest-files/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['files']), 4)

class TestSearchFiles(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_files(self)

    def test_search_files(self):
        response = self.client.get('/api/search-files/?q=file')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 5)

class TestMoveFile(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_files(self)

    def test_move_file(self):
        response = self.client.post('/api/move-file/', {'file_id': self.file_1.id, 'folder_id': self.file_5.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(File.objects.get(id=self.file_1.id).folder.id, self.file_5.id)

class TestFetchAllVaultCipher(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_files(self)
        set_up_vault_notes(self)

    def test_fetch_all_vault_cipher(self):
        response = self.client.get('/api/fetch-all-vault-cipher/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('files_cipher', response.data)
        self.assertIn('notes_cipher', response.data)
