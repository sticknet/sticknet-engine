from django.conf.urls import url, include
from rest_framework import routers
from .views import UploadChatFiles, FetchChatFiles, FetchChatAlbums, \
    FetchAlbumPhotos, FetchSingleChatAlbum, UploadChatAudio, FetchChatAudio, DeleteChatFiles, DeleteChatAudio, \
    RenameAlbum, DeleteChatAlbum, FetchStorages, FetchRoomFiles

app_name = "chat"
router = routers.SimpleRouter()

urlpatterns = [
    url("^", include(router.urls)),
    url(r'^upload-chat-files/$', UploadChatFiles.as_view(), name='upload_chat_files'),
    url(r'^fetch-chat-files/$', FetchChatFiles.as_view(), name='fetch_chat_files'),
    url(r'^fetch-chat-albums/$', FetchChatAlbums.as_view(), name='fetch_chat_albums'),
    url(r'^fetch-album-photos/$', FetchAlbumPhotos.as_view(), name='fetch_album_photos'),
    url(r'^fetch-single-chat-album/$', FetchSingleChatAlbum.as_view(), name='fetch_single_chat_album'),
    url(r'^upload-chat-audio/$', UploadChatAudio.as_view(), name='upload_chat_audio'),
    url(r'^fetch-chat-audio/$', FetchChatAudio.as_view(), name='fetch_chat_audio'),
    url(r'^delete-chat-files/$', DeleteChatFiles.as_view(), name='delete_chat_files'),
    url(r'^delete-chat-audio/$', DeleteChatAudio.as_view(), name='delete_chat_audio'),
    url(r'^rename-album/$', RenameAlbum.as_view(), name='rename_album'),
    url(r'^delete-chat-album/$', DeleteChatAlbum.as_view(), name='delete_chat_album'),
    url(r'^fetch-storages/$', FetchStorages.as_view(), name='fetch_storages'),
    url(r'^fetch-room-files/$', FetchRoomFiles.as_view(), name='fetch_room_files'),
]
