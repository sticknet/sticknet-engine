from django.urls import include, re_path
from rest_framework import routers

from .views import ImageViewSet, AlbumViewSet, \
    AlbumDetailAPIView, SharedImages, LatestShared, DeleteReactionNote, FetchNotes, \
    FetchAlbumNotes, SharedByOthers, YoutubeShare, AlbumImagesUris, ReactionsCount, HighlightedImages, ToggleLike, UploadImages, \
    HiddenImages, IsProfileImages, FetchSingleAlbum, DeleteAlbum, DeleteNote, NoteViewSet, FetchImageAudioUri, \
    GroupSharedImages, EditNote, ToggleFavorite, FavoriteImages, SelectedBlobsView, \
    DeleteBlob, ChangeAlbumCover, FetchBlobUri, YoutubeRestick, SelectedBlobsImageView, ConnectionImages

app_name = "photos"


router = routers.SimpleRouter()
router.register('images', ImageViewSet, basename='images')
router.register('albums', AlbumViewSet, basename='albums')
router.register('notes', NoteViewSet, basename='notes')

urlpatterns = [
    re_path("^", include(router.urls)),
    re_path(r'^shared-images/$', SharedImages.as_view(), name='shared_images'),
    re_path(r'^shared-by-others/$', SharedByOthers.as_view(), name='shared_by_others'),
    re_path(r'^latest-shared/$', LatestShared.as_view(), name='latest_shared'),
    re_path(r'^is-profile-images/$', IsProfileImages.as_view(), name='isProfile_images'),
    re_path(r'^highlighted-images/$', HighlightedImages.as_view(), name='highlighted_images'),
    re_path(r'^album-images-uris/$', AlbumImagesUris.as_view(), name='album-images-uris'),
    re_path(r'^album-detail/$', AlbumDetailAPIView.as_view(), name='album-detail'),
    re_path(r'^single-album/$', FetchSingleAlbum.as_view(), name='single_album'),
    re_path(r'^delete-album/$', DeleteAlbum.as_view(), name='delete_album'),
    re_path(r'^delete-blob/$', DeleteBlob.as_view(), name='delete_blob'),
    re_path(r'^delete-reaction-note/$', DeleteReactionNote.as_view(), name='delete-reaction-note'),
    re_path(r'^delete-note/$', DeleteNote.as_view(), name='delete-note'),
    re_path(r'^fetch-notes/$', FetchNotes.as_view(), name='fetch-notes'),
    re_path(r'^fetch-album-notes/$', FetchAlbumNotes.as_view(), name='fetch-album-notes'),
    re_path(r'^youtube-share/$', YoutubeShare.as_view(), name='youtube-share'),
    re_path(r'^youtube-restick/$', YoutubeRestick.as_view(), name='youtube_restick'),
    re_path(r'^selected-blobs/$', SelectedBlobsView.as_view(), name='selected-blobs'),
    re_path(r'^selected-blobs-image/$', SelectedBlobsImageView.as_view(), name='selected-blobs-image'),
    re_path(r'^reactions-count/$', ReactionsCount.as_view(), name='reactions_count'),
    re_path(r'^like/$', ToggleLike.as_view(), name='toggle_like'),
    re_path(r'^upload-images/$', UploadImages.as_view(), name='upload_images'),
    re_path(r'^fetch-hidden-images/$', HiddenImages.as_view(), name='fetch_hidden_images'),
    re_path(r'^fetch-image-audio-uri/$', FetchImageAudioUri.as_view(), name='fetch_image_audio_uri'),
    re_path(r'^fetch-blob-uri/$', FetchBlobUri.as_view(), name='fetch_blob_uri'),
    re_path(r'^group-shared-images/$', GroupSharedImages.as_view(), name='group_shared_images'),
    re_path(r'^edit-note/$', EditNote.as_view(), name='edit_note'),
    re_path(r'^toggle-favorite/$', ToggleFavorite.as_view(), name='toggle_favorite'),
    re_path(r'^favorite-images/$', FavoriteImages.as_view(), name='favorite_images'),
    re_path(r'^change-album-cover/$', ChangeAlbumCover.as_view(), name='change_album_cover'),
    re_path(r'^connection-images/$', ConnectionImages.as_view(), name='connection_images'),
    # re_path(r'^fetch-likes-count/$', FetchLikesCount.as_view(), name='fetch_likes_count')
]
