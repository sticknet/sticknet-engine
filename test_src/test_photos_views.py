from knox.models import AuthToken
from users.models import User, Preferences
from photos.models import Image, Album, Blob, Note
from groups.models import Group
from rest_framework.test import APITestCase
from stick_protocol.models import EncryptionSenderKey, IdentityKey, Party

# Important Note: "photos" models is deprecated
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


def set_up_images(self):
    # case 1: user owned images (image should be included in `fetch-images`)
    image_1 = Image.objects.create(id=1, user=self.user)
    group_1 = Group.objects.create(id='abc123')
    self.user.groups.add(group_1)

    # case 2: Group image (image should be included in `fetch-images`)
    image_2 = Image.objects.create(id=2)
    image_2.groups.set([group_1])

    # case 3: Profile images (image should be included in `fetch-images`)
    user_1 = User.objects.create(phone='+555', username='bob123', finished_registration=True)
    self.user.connections.add(user_1)
    user_1.connections.add(self.user)
    party_1 = Party.objects.create(user=user_1)
    image_3 = Image.objects.create(id=3, party_id=party_1.id)

    # case 4: Connection images (image should be included in `fetch-images`)
    user_2 = User.objects.create(phone='+666', username='charles123', finished_registration=True)
    Party.objects.create(user=user_2)
    self.user.connections.add(user_2)
    user_2.connections.add(self.user)
    image_4 = Image.objects.create(id=4)
    image_4.connections.set([self.user])

    # case 5: deactivated account (image should be excluded)
    user_3 = User.objects.create(phone='+777', username='mike123', finished_registration=True, is_active=False)
    self.user.connections.add(user_3)
    user_3.connections.add(self.user)
    image_5 = Image.objects.create(user=user_3, id=5)
    image_5.connections.set([self.user])

    # case 6: blocked user (image should be excluded)
    user_4 = User.objects.create(phone='+888', username='will123', finished_registration=True)
    image_6 = Image.objects.create(user=user_4, id=6)
    image_6.groups.set([group_1])
    self.user.blocked.add(user_4)

    # case 7: blocked by another user (image should be excluded)
    user_5 = User.objects.create(phone='+999', username='sena123', finished_registration=True)
    image_7 = Image.objects.create(user=user_5, id=7)
    image_7.groups.set([group_1])
    user_5.blocked.add(self.user)

    # case 8: hidden image (image should be excluded)
    user_6 = User.objects.create(phone='+000', username='bill123', finished_registration=True)
    image_8 = Image.objects.create(user=user_6, id=8)
    image_8.groups.set([group_1])
    self.user.hidden_images = ['8']
    self.user.save()


CIPHER_BODY = {'stick_id': '5a71cdda-77d0-40ab-b232-2898880625620', 'chain_step': 50, 'text': 'text', 'uri': 'uri',
               'file_size': 100, 'text_length': 100}


class TestImageViewSetGet(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_images(self)

    def test_get_queryset(self):
        response = self.client.get('/api/images/')
        self.assertEqual(len(response.data['results']), 4)
        self.assertEqual(response.data['results'][0]['id'], '4')
        self.assertEqual(response.data['results'][1]['id'], '3')
        self.assertEqual(response.data['results'][2]['id'], '2')
        self.assertEqual(response.data['results'][3]['id'], '1')


class TestImageViewSetDelete(APITestCase):
    def setUp(self):
        set_up_user(self)
        Preferences.objects.create(user=self.user)

        # case 1: deleting another user's image (should return 404)
        user_1 = User.objects.create(phone='+555', username='bob123', finished_registration=True)
        image_1 = Image.objects.create(id=1, user=user_1)

        # case 2: deleting owned image
        image_2 = Image.objects.create(id=2, user=self.user)

        # case 3: delete image that is album cover
        self.album_1 = Album.objects.create(id=1, user=self.user)
        image_3 = Image.objects.create(id=3, user=self.user, album=self.album_1, album_cover=self.album_1)
        blob_1 = Blob.objects.create(id=1, image=image_3, uri='uri_1', album_cover=self.album_1, file_size=[1])
        image_4 = Image.objects.create(id=4, user=self.user, album=self.album_1)
        blob_2 = Blob.objects.create(id=2, image=image_4, uri='uri_2', file_size=[1])

        # case 4: delete image that is the only one in album
        self.album_2 = Album.objects.create(id=2, user=self.user)
        image_5 = Image.objects.create(id=5, user=self.user, album=self.album_2, album_cover=self.album_2)
        blob_3 = Blob.objects.create(id=3, image=image_5, uri='uri_3', album_cover=self.album_2, file_size=[1])

    def test_delete_image(self):
        response = self.client.delete('/api/images/1/')
        self.assertEqual(response.status_code, 404)

        response = self.client.delete('/api/images/2/')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Image.objects.filter(id=2).exists(), False)

        response = self.client.delete('/api/images/3/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Image.objects.filter(id=3).exists(), False)
        self.assertEqual(Blob.objects.filter(id=1).exists(), False)
        self.assertEqual(response.data['cover_updated'], True)
        self.assertEqual(response.data['cover']['id'], 2)

        response = self.client.delete('/api/images/5/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Image.objects.filter(id=3).exists(), False)
        self.assertEqual(Blob.objects.filter(id=1).exists(), False)
        self.assertEqual(Album.objects.filter(id=2).exists(), False)
        self.assertEqual(response.data['album_deleted'], True)


class TestFetchImageUri(APITestCase):
    def setUp(self):
        set_up_user(self)
        image_1 = Image.objects.create(id=1, user=self.user, audio_uri='audio_uri_1')

    def test_fetch_image_uri(self):
        response = self.client.get('/api/fetch-image-audio-uri/?id=1')
        self.assertEqual(response.data['results'][0]['audio_uri'], 'http://testserver/media/audio_uri_1')


class TestFetchBlobUri(APITestCase):
    def setUp(self):
        set_up_user(self)
        image_1 = Image.objects.create(id=1, user=self.user)
        Blob.objects.create(id=1, image=image_1, uri='uri_1')

    def test_fetch_blob_uri(self):
        response = self.client.get('/api/fetch-blob-uri/?id=1')
        self.assertEqual(response.data['results'][0]['uri'], 'http://testserver/media/uri_1')


class TestDeleteBlob(APITestCase):
    def setUp(self):
        set_up_user(self)
        Preferences.objects.create(user=self.user)

        # case 1: deleting another user's blob (should return 401)
        user_1 = User.objects.create(phone='+555', username='bob123', finished_registration=True)
        image_1 = Image.objects.create(id=1, user=user_1)
        Blob.objects.create(id=1, image=image_1, uri='uri_1')

        # case 2: deleting owned blob
        image_2 = Image.objects.create(id=2, user=self.user)
        Blob.objects.create(id=2, image=image_2, uri='uri_2')

    def test_delete_blob(self):
        response = self.client.post('/api/delete-blob/', {'blob_id': '1'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Blob.objects.filter(id=1).exists(), True)

        response = self.client.post('/api/delete-blob/', {'blob_id': '2'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Blob.objects.filter(id=2).exists(), False)


class TestChangeAlbumCover(APITestCase):
    def setUp(self):
        set_up_user(self)
        album = Album.objects.create(id=1, user=self.user)
        image_1 = Image.objects.create(id=1, user=self.user, album=album)
        Blob.objects.create(id=1, image=image_1)
        image_2 = Image.objects.create(id=2, user=self.user, album=album, album_cover=album)
        Blob.objects.create(id=2, image=image_2, album_cover=album)

    def test_change_album_cover(self):
        response = self.client.post('/api/change-album-cover/', {'blob_id': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(Image.objects.get(id=1).album_cover)
        self.assertIsNotNone(Blob.objects.get(id=1).album_cover)
        self.assertIsNone(Image.objects.get(id=2).album_cover)
        self.assertIsNone(Blob.objects.get(id=2).album_cover)


class TestToggleFavorite(APITestCase):

    def setUp(self):
        set_up_user(self)
        Preferences.objects.create(user=self.user)
        image_1 = Image.objects.create(id=1, user=self.user)
        Blob.objects.create(id=1, image=image_1)
        Blob.objects.create(id=2, image=image_1)

    def test_toggle_favorite(self):
        # Favorite
        response = self.client.post('/api/toggle-favorite/', {'image_id': '1', 'blob_id': '1'})
        self.assertEqual(response.data['faved'], True)
        updated_user = User.objects.get(id=self.user.id)
        self.assertIn('1-1', updated_user.preferences.favorites_ids)

        # Remove favorite
        response = self.client.post('/api/toggle-favorite/', {'image_id': '1', 'blob_id': '1'})
        self.assertEqual(response.data['faved'], False)
        updated_user = User.objects.get(id=self.user.id)
        self.assertNotIn('1-1', updated_user.preferences.favorites_ids)

        # Favorite all blobs of an image
        response = self.client.post('/api/toggle-favorite/', {'image_id': '1', 'is_fav': False})
        self.assertEqual(response.data['faved'], True)
        updated_user = User.objects.get(id=self.user.id)
        self.assertIn('1-1', updated_user.preferences.favorites_ids)
        self.assertIn('1-2', updated_user.preferences.favorites_ids)


class TestSelectedBlobsView(APITestCase):
    def setUp(self):
        set_up_user(self)
        image_1 = Image.objects.create(id=1, user=self.user)
        Blob.objects.create(id=1, image=image_1)
        image_2 = Image.objects.create(id=2, user=self.user)
        Blob.objects.create(id=2, image=image_2)

    def test_selected_blobs_view(self):
        response = self.client.get('/api/selected-blobs/?ids=1,2')
        self.assertEqual(response.data['results'][0]['id'], '2')
        self.assertEqual(response.data['results'][1]['id'], '1')


class TestSelectedBlobsImageView(APITestCase):
    def setUp(self):
        set_up_user(self)
        image_1 = Image.objects.create(id=1, user=self.user)
        Blob.objects.create(id=1, image=image_1)
        image_2 = Image.objects.create(id=2, user=self.user)
        Blob.objects.create(id=2, image=image_2)

    def test_selected_blobs_image_view(self):
        response = self.client.get('/api/selected-blobs-image/?ids=1,2')
        self.assertEqual(response.data['results'][0]['id'], '1')
        self.assertEqual(response.data['results'][1]['id'], '2')


class TestFavoriteImages(APITestCase):

    def setUp(self):
        set_up_user(self)
        image_1 = Image.objects.create(id=5, user=self.user)
        Blob.objects.create(id=1, image=image_1)
        image_1 = Image.objects.create(id=10, user=self.user)
        Blob.objects.create(id=2, image=image_1)
        Preferences.objects.create(user=self.user, favorites_ids=['5-1'])

    def test_favorite_images(self):
        response = self.client.get('/api/favorite-images/')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], '5')


class TestHiddenImages(APITestCase):

    def setUp(self):
        set_up_user(self)
        user_1 = User.objects.create(phone='+555', username='bob123', finished_registration=True)
        party_1 = Party.objects.create(user=user_1)
        self.user.connections.add(user_1)
        user_1.connections.add(self.user)
        image_1 = Image.objects.create(id=1, user=user_1, party_id=party_1.id)
        Blob.objects.create(id=1, image=image_1)
        self.user.hidden_images = ['1']
        self.user.save()

    def test_hidden_images(self):
        response = self.client.get('/api/fetch-hidden-images/')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], '1')


class TestYoutubeShare(APITestCase):
    def setUp(self):
        set_up_user(self)
        Group.objects.create(id='abc')

    def test_youtube_share(self):
        body = {'youtube': 'encrypted_url', 'youtube_thumbnail': 'encrypted_url_2', 'caption': 'caption',
                'stick_id': 'stick_id', 'party_id': 'party_id', 'groups_id': ['abc']}
        response = self.client.post('/api/youtube-share/', body)
        self.assertIn('id', response.data)


class TestYoutubeRestick(APITestCase):
    def setUp(self):
        set_up_user(self)
        Group.objects.create(id='abc')

    def test_youtube_restick(self):
        body = {'youtube': 'encrypted_url', 'youtube_thumbnail': 'encrypted_url_2', 'caption': 'caption',
                'stick_id': 'stick_id', 'party_id': 'party_id', 'groups_id': ['abc']}
        response = self.client.post('/api/youtube-restick/', body)
        self.assertIn('id', response.data[0])


class TestLatestShared(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_images(self)

        # This image should not be returned as it is an album image
        album = Album.objects.create(id=10, user=self.user)
        Image.objects.create(id=20, user=self.user, album=album)

    def test_latest_shared(self):
        response = self.client.get('/api/latest-shared/')
        self.assertEqual(len(response.data['results']), 4)
        self.assertEqual(response.data['results'][0]['id'], '4')
        self.assertEqual(response.data['results'][1]['id'], '3')
        self.assertEqual(response.data['results'][2]['id'], '2')
        self.assertEqual(response.data['results'][3]['id'], '1')


class TestHighlightedImages(APITestCase):
    def setUp(self):
        set_up_user(self)
        image_1 = Image.objects.create(id=11, user=self.user)
        Blob.objects.create(id=22, image=image_1)
        image_2 = Image.objects.create(id=33, user=self.user)
        Blob.objects.create(id=44, image=image_2)
        self.user.highlights_ids = ['11-22']
        self.user.save()

    def test_highlighted_images(self):
        response = self.client.get('/api/highlighted-images/')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], '11')


class TestIsProfileImages(APITestCase):
    def setUp(self):
        set_up_user(self)
        Image.objects.create(id=11, user=self.user)
        Image.objects.create(id=22, user=self.user, is_profile=True)

    def test_is_profile_images(self):
        response = self.client.get('/api/is-profile-images/')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], '22')


class TestGroupSharedImages(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_images(self)

    def test_group_shared_images(self):
        response = self.client.get('/api/group-shared-images/?id=abc123')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], '2')


class TestSharedImages(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_images(self)

    def test_shared_images(self):
        response = self.client.get('/api/shared-images/')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], '1')


class TestSharedByOthers(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_images(self)

    def test_shared_images(self):
        response = self.client.get('/api/shared-by-others/')
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['results'][0]['id'], '4')
        self.assertEqual(response.data['results'][1]['id'], '3')
        self.assertEqual(response.data['results'][2]['id'], '2')


class TestAlbumViewSet(APITestCase):
    def setUp(self):
        set_up_user(self)
        group_1 = Group.objects.create(id='abc')
        group_2 = Group.objects.create(id='efg')
        album_1 = Album.objects.create(id=1, group=group_1, user=self.user)
        album_2 = Album.objects.create(id=2, group=group_1, user=self.user)
        album_3 = Album.objects.create(id=3, group=group_2, user=self.user)
        self.user.groups.add(group_1)
        self.user.groups.add(group_2)

    def test_album_view_set(self):
        response = self.client.get('/api/albums/?q=abc')
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['id'], 2)
        self.assertEqual(response.data['results'][1]['id'], 1)


class TestDeleteAlbum(APITestCase):
    def setUp(self):
        set_up_user(self)
        user_2 = User.objects.create(phone='+555', username='bob123', finished_registration=True)
        self.group = Group.objects.create(id='abc', owner=user_2)
        self.user.groups.add(self.group)
        user_2.groups.add(self.group)
        Album.objects.create(id=1, user=user_2, group=self.group)
        Album.objects.create(id=2, user=self.user, group=self.group)

    def test_delete_album(self):
        # Case 1: can delete own album
        response = self.client.post('/api/delete-album/', {'id': '2'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Album.objects.filter(id=2).exists(), False)

        # Case 2: can't delete others albums
        response = self.client.post('/api/delete-album/', {'id': '1'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Album.objects.filter(id=1).exists(), True)

        # Case 3: can delete any album in group if group owner
        self.group.owner = self.user
        self.group.save()
        response = self.client.post('/api/delete-album/', {'id': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Album.objects.filter(id=1).exists(), False)


class TestFetchSingleAlbum(APITestCase):
    def setUp(self):
        set_up_user(self)
        group = Group.objects.create(id='abc')
        self.user.groups.add(group)
        album = Album.objects.create(id=1, user=self.user, group=group)

    def test_fetch_single_album(self):
        response = self.client.get('/api/single-album/?id=1')
        self.assertIn('album', response.data)


class TestAlbumImagesUris(APITestCase):
    def setUp(self):
        set_up_user(self)
        group = Group.objects.create(id='abc')
        self.user.groups.add(group)
        album = Album.objects.create(id=1, user=self.user, group=group)
        image_1 = Image.objects.create(id=100, album=album, user=self.user)
        image_2 = Image.objects.create(id=101, album=album, user=self.user)
        image_3 = Image.objects.create(id=102, user=self.user)

    def test_album_images_uris(self):
        response = self.client.get('/api/album-images-uris/?q=1')
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['id'], '100')
        self.assertEqual(response.data['results'][1]['id'], '101')


class TestAlbumDetail(APITestCase):
    def setUp(self):
        set_up_user(self)
        group = Group.objects.create(id='abc')
        self.user.groups.add(group)
        album_1 = Album.objects.create(id=1, user=self.user, group=group)
        album_2 = Album.objects.create(id=2, user=self.user, group=group)
        image_1 = Image.objects.create(id=44, user=self.user, album=album_1)
        image_2 = Image.objects.create(id=55, user=self.user, album=album_2)

    def test_album_detail(self):
        response = self.client.get('/api/album-detail/?q=1&timestamp=-timestamp')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], '44')


class TestDeleteNote(APITestCase):
    def setUp(self):
        set_up_user(self)
        image_1 = Image.objects.create(id=1, user=self.user)
        note_1 = Note.objects.create(id=44, image=image_1, user=self.user)

    def test_delete_note(self):
        response = self.client.post('/api/delete-note/', {'id': 44})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Note.objects.filter(id=44).exists(), False)


class TestDeleteReactionNote(APITestCase):
    def setUp(self):
        set_up_user(self)
        image_1 = Image.objects.create(id=1, user=self.user)
        note_1 = Note.objects.create(id=44, image=image_1, user=self.user, reaction='A')
    def test_delete_note(self):
        response = self.client.post('/api/delete-reaction-note/', {'id': 44, 'image': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Note.objects.filter(id=44).exists(), False)


class TestEditNote(APITestCase):
    def setUp(self):
        set_up_user(self)
        set_up_esk(self)
        image_1 = Image.objects.create(id=1, user=self.user)
        note_1 = Note.objects.create(id=44, image=image_1, user=self.user, text='some comment', stick_id='5a71cdda-77d0-40ab-b232-2898880625620')

    def test_edit_note(self):
        response = self.client.post('/api/edit-note/', {'note_id': 44, 'cipher_text': 'edited comment', 'chain_step': 5})
        self.assertEqual(response.status_code, 200)


class TestFetchNotes(APITestCase):
    def setUp(self):
        set_up_user(self)
        image_1 = Image.objects.create(id=1, user=self.user)
        Note.objects.create(id=44, image=image_1, user=self.user)
        Note.objects.create(id=45, image=image_1, user=self.user)

    def test_fetch_notes(self):
        response = self.client.get('/api/fetch-notes/?q=1')
        self.assertEqual(len(response.data['results']), 2)


class TestFetchAlbumNotes(APITestCase):
    def setUp(self):
        set_up_user(self)
        group_1 = Group.objects.create(id='abc')
        self.user.groups.add(group_1)
        album_1 = Album.objects.create(id=1, user=self.user, group=group_1)
        Note.objects.create(id=44, album=album_1, user=self.user)
        Note.objects.create(id=45, album=album_1, user=self.user)

    def test_fetch_album_notes(self):
        response = self.client.get('/api/fetch-album-notes/?q=1')
        self.assertEqual(len(response.data['results']), 2)


class TestReactionsCount(APITestCase):
    def setUp(self):
        set_up_user(self)
        image_1 = Image.objects.create(id=1, user=self.user)
        image_1.likes.add(self.user)
        Note.objects.create(id=44, image=image_1, user=self.user, reaction='A')
        Note.objects.create(id=45, image=image_1, user=self.user)


    def test_reaction_count(self):
        response = self.client.get('/api/reactions-count/?q=1&type=image')
        self.assertEqual(response.data['notes_count'], 2)
        self.assertEqual(response.data['likes_count'], 1)
        self.assertEqual(len(response.data['liked_by']), 1)

# TODO: test all cases
class TestToggleLike(APITestCase):
    def setUp(self):
        set_up_user(self)
        image_1 = Image.objects.create(id=1, user=self.user)

    def test_toggle_like(self):
        response = self.client.post('/api/like/', {'type': 'image', 'id': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Image.objects.get(id=1).likes.all().count(), 1)
        self.client.post('/api/like/', {'type': 'image', 'id': '1'})
        self.assertEqual(Image.objects.get(id=1).likes.all().count(), 0)




# import io
# from PIL import Image as PILImage
#
# def generate_photo_file():
#     file = io.BytesIO()
#     image = PILImage.new('RGBA', size=(100, 100), color=(155, 0, 0))
#     image.save(file, 'png')
#     file.name = 'test.png'
#     file.seek(0)
#     return file


# class TestUploadImages(APITestCase):
#     def setUp(self):
#         set_up_user(self)
#         # self.group = Group.objects.create(id=1)
#         # self.user.groups.add(self.group)
#         # self.user_1 = User.objects.create(phone='+555', username='bob123', finished_registration=True)
#         # self.user.connections.add(self.user_1)
#         # self.user_1.connections.add(self.user)
#         # party_1 = Party.objects.create(user=user_1)
#
#     def test_upload_images(self):
#         body = {'type': 'share', 'is_profile': 'true', 'party_id': 'abcdef', 'stick_id': 'abcdef0',
#                 'share_ext': 'false',
#                 'cipher': 'cipher', 'size': 'C', 'width': 1000, 'height': 1000,
#                 'duration': 0, 'asset_size': 500, 'media_type': 'image', 'location': 'Dubai',
#                 'is_video': 'false', 'uri': generate_photo_file()}
#         response = self.client.post('/api/images/', body, format='multipart')
#         self.assertIn('id', response.data)
#         print('USERX', response.data['user'])
