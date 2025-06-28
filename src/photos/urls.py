from django.conf.urls import url, include
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
    url("^", include(router.urls)),
    url(r'^shared-images/$', SharedImages.as_view(), name='shared_images'),
    url(r'^shared-by-others/$', SharedByOthers.as_view(), name='shared_by_others'),
    url(r'^latest-shared/$', LatestShared.as_view(), name='latest_shared'),
    url(r'^is-profile-images/$', IsProfileImages.as_view(), name='isProfile_images'),
    url(r'^highlighted-images/$', HighlightedImages.as_view(), name='highlighted_images'),
    url(r'^album-images-uris/$', AlbumImagesUris.as_view(), name='album-images-uris'),
    url(r'^album-detail/$', AlbumDetailAPIView.as_view(), name='album-detail'),
    url(r'^single-album/$', FetchSingleAlbum.as_view(), name='single_album'),
    url(r'^delete-album/$', DeleteAlbum.as_view(), name='delete_album'),
    url(r'^delete-blob/$', DeleteBlob.as_view(), name='delete_blob'),
    url(r'^delete-reaction-note/$', DeleteReactionNote.as_view(), name='delete-reaction-note'),
    url(r'^delete-note/$', DeleteNote.as_view(), name='delete-note'),
    url(r'^fetch-notes/$', FetchNotes.as_view(), name='fetch-notes'),
    url(r'^fetch-album-notes/$', FetchAlbumNotes.as_view(), name='fetch-album-notes'),
    url(r'^youtube-share/$', YoutubeShare.as_view(), name='youtube-share'),
    url(r'^youtube-restick/$', YoutubeRestick.as_view(), name='youtube_restick'),
    url(r'^selected-blobs/$', SelectedBlobsView.as_view(), name='selected-blobs'),
    url(r'^selected-blobs-image/$', SelectedBlobsImageView.as_view(), name='selected-blobs-image'),
    url(r'^reactions-count/$', ReactionsCount.as_view(), name='reactions_count'),
    url(r'^like/$', ToggleLike.as_view(), name='toggle_like'),
    url(r'^upload-images/$', UploadImages.as_view(), name='upload_images'),
    url(r'^fetch-hidden-images/$', HiddenImages.as_view(), name='fetch_hidden_images'),
    url(r'^fetch-image-audio-uri/$', FetchImageAudioUri.as_view(), name='fetch_image_audio_uri'),
    url(r'^fetch-blob-uri/$', FetchBlobUri.as_view(), name='fetch_blob_uri'),
    url(r'^group-shared-images/$', GroupSharedImages.as_view(), name='group_shared_images'),
    url(r'^edit-note/$', EditNote.as_view(), name='edit_note'),
    url(r'^toggle-favorite/$', ToggleFavorite.as_view(), name='toggle_favorite'),
    url(r'^favorite-images/$', FavoriteImages.as_view(), name='favorite_images'),
    url(r'^change-album-cover/$', ChangeAlbumCover.as_view(), name='change_album_cover'),
    url(r'^connection-images/$', ConnectionImages.as_view(), name='connection_images'),
    # url(r'^fetch-likes-count/$', FetchLikesCount.as_view(), name='fetch_likes_count')
]
