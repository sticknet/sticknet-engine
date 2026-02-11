from django.urls import include, re_path
from rest_framework import routers
from .views import FileViewSet, UploadFiles, DeleteFiles, FetchFiles, CreateFolder, GetUploadUrls, FetchPhotos, \
    FetchVaultAlbums, CreateVaultAlbum, CreateVaultNote, FetchVaultNotes, FetchHomeItems, VaultNoteViewSet, UpdateVaultNote, SearchFiles, RenameFile, MoveFile, FetchAllVaultCipher, FetchLatestFiles

app_name = "vault"
router = routers.SimpleRouter()
router.register('files', FileViewSet, basename='files')
router.register('vault-notes', VaultNoteViewSet, basename='vault_notes')

urlpatterns = [
    re_path("^", include(router.urls)),
    re_path(r'^upload-files/$', UploadFiles.as_view(), name='upload_files'),
    re_path(r'^create-folder/$', CreateFolder.as_view(), name='create_folder'),
    re_path(r'^delete-files/$', DeleteFiles.as_view(), name='delete_files'),
    re_path(r'^fetch-files/$', FetchFiles.as_view(), name='fetch_files'),
    re_path(r'^fetch-photos/$', FetchPhotos.as_view(), name='fetch_photos'),
    re_path(r'^get-upload-urls/$', GetUploadUrls.as_view(), name='get_upload_urls'),
    re_path(r'^fetch-vault-albums/$', FetchVaultAlbums.as_view(), name='fetch_vault_albums'),
    re_path(r'^create-vault-album/$', CreateVaultAlbum.as_view(), name='create_vault_album'),
    re_path(r'^create-vault-note/$', CreateVaultNote.as_view(), name='create_vault_note'),
    re_path(r'^update-vault-note/$', UpdateVaultNote.as_view(), name='update_vault_note'),
    re_path(r'^fetch-vault-notes/$', FetchVaultNotes.as_view(), name='fetch_vault_notes'),
    re_path(r'^fetch-home-items/$', FetchHomeItems.as_view(), name='fetch_home_items'),
    re_path(r'^search-files/$', SearchFiles.as_view(), name='search_files'),
    re_path(r'^rename-file/$', RenameFile.as_view(), name='rename_file'),
    re_path(r'^move-file/$', MoveFile.as_view(), name='move_file'),
    re_path(r'^fetch-all-vault-cipher/$', FetchAllVaultCipher.as_view(), name='fetch_all_vault_cipher'),
    re_path(r'^fetch-latest-files/$', FetchLatestFiles.as_view(), name='fetch_latest_files'),
]
