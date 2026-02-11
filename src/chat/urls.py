from django.urls import include, re_path
from rest_framework import routers
from .views import UploadChatFiles, FetchChatFiles, FetchChatAlbums, \
    FetchAlbumPhotos, FetchSingleChatAlbum, UploadChatAudio, FetchChatAudio, DeleteChatFiles, DeleteChatAudio, \
    RenameAlbum, DeleteChatAlbum, FetchStorages, FetchRoomFiles

app_name = "chat"
router = routers.SimpleRouter()

urlpatterns = [
    re_path("^", include(router.urls)),
    re_path(r'^upload-chat-files/$', UploadChatFiles.as_view(), name='upload_chat_files'),
    re_path(r'^fetch-chat-files/$', FetchChatFiles.as_view(), name='fetch_chat_files'),
    re_path(r'^fetch-chat-albums/$', FetchChatAlbums.as_view(), name='fetch_chat_albums'),
    re_path(r'^fetch-album-photos/$', FetchAlbumPhotos.as_view(), name='fetch_album_photos'),
    re_path(r'^fetch-single-chat-album/$', FetchSingleChatAlbum.as_view(), name='fetch_single_chat_album'),
    re_path(r'^upload-chat-audio/$', UploadChatAudio.as_view(), name='upload_chat_audio'),
    re_path(r'^fetch-chat-audio/$', FetchChatAudio.as_view(), name='fetch_chat_audio'),
    re_path(r'^delete-chat-files/$', DeleteChatFiles.as_view(), name='delete_chat_files'),
    re_path(r'^delete-chat-audio/$', DeleteChatAudio.as_view(), name='delete_chat_audio'),
    re_path(r'^rename-album/$', RenameAlbum.as_view(), name='rename_album'),
    re_path(r'^delete-chat-album/$', DeleteChatAlbum.as_view(), name='delete_chat_album'),
    re_path(r'^fetch-storages/$', FetchStorages.as_view(), name='fetch_storages'),
    re_path(r'^fetch-room-files/$', FetchRoomFiles.as_view(), name='fetch_room_files'),
]
