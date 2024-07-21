from django.conf.urls import url, include
from rest_framework import routers
from .views import FileViewSet, UploadFiles, DeleteFiles, FetchFiles, CreateFolder, GetUploadUrls, FetchPhotos, \
    FetchVaultAlbums, CreateVaultAlbum, CreateVaultNote, FetchVaultNotes, FetchHomeItems, VaultNoteViewSet, UpdateVaultNote, SearchFiles, RenameFile, MoveFile, FetchAllVaultCipher, FetchLatestFiles

app_name = "vault"
router = routers.SimpleRouter()
router.register('files', FileViewSet, basename='files')
router.register('vault-notes', VaultNoteViewSet, basename='vault_notes')

urlpatterns = [
    url("^", include(router.urls)),
    url(r'^upload-files/$', UploadFiles.as_view(), name='upload_files'),
    url(r'^create-folder/$', CreateFolder.as_view(), name='create_folder'),
    url(r'^delete-files/$', DeleteFiles.as_view(), name='delete_files'),
    url(r'^fetch-files/$', FetchFiles.as_view(), name='fetch_files'),
    url(r'^fetch-photos/$', FetchPhotos.as_view(), name='fetch_photos'),
    url(r'^get-upload-urls/$', GetUploadUrls.as_view(), name='get_upload_urls'),
    url(r'^fetch-vault-albums/$', FetchVaultAlbums.as_view(), name='fetch_vault_albums'),
    url(r'^create-vault-album/$', CreateVaultAlbum.as_view(), name='create_vault_album'),
    url(r'^create-vault-note/$', CreateVaultNote.as_view(), name='create_vault_note'),
    url(r'^update-vault-note/$', UpdateVaultNote.as_view(), name='update_vault_note'),
    url(r'^fetch-vault-notes/$', FetchVaultNotes.as_view(), name='fetch_vault_notes'),
    url(r'^fetch-home-items/$', FetchHomeItems.as_view(), name='fetch_home_items'),
    url(r'^search-files/$', SearchFiles.as_view(), name='search_files'),
    url(r'^rename-file/$', RenameFile.as_view(), name='rename_file'),
    url(r'^move-file/$', MoveFile.as_view(), name='move_file'),
    url(r'^fetch-all-vault-cipher/$', FetchAllVaultCipher.as_view(), name='fetch_all_vault_cipher'),
    url(r'^fetch-latest-files/$', FetchLatestFiles.as_view(), name='fetch_latest_files'),
]
