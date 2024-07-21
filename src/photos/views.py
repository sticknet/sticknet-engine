import json
from rest_framework import permissions, viewsets, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from notifications.push_notifications import PushNotification
from .models import Album, Image, Note, TestImage, Blob
from groups.models import Group
from .serializers import ImageSerializer, BlobImageSerializer, ImageAudioUriSerializer, BlobUriSerializer, \
    AlbumSerializer, NoteSerializer, \
    get_album_cover
from .pagination import DynamicPagination
from notifications.models import Notification
from sticknet.dynamic_fields import DynamicFieldsViewMixin
from django.db.models import Q
from stick_protocol.models import EncryptionSenderKey
from users.models import User
from django.utils import timezone


class ImageViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ImageSerializer

    def get_queryset(self):
        connections_parties_ids = self.request.user.get_connections_parties_ids()
        my_groups = self.request.user.groups.all()
        qs = Image.objects.filter(
            Q(groups__in=my_groups) |
            Q(connections__in=[self.request.user]) |
            Q(party_id__in=connections_parties_ids) |
            Q(user=self.request.user)) \
            .exclude(
            Q(user__is_active=False) |
            Q(user__in=self.request.user.blocked.all()) |
            Q(user__blocked__in=[self.request.user]) |
            Q(id__in=self.request.user.hidden_images)) \
            .distinct().order_by("-timestamp")
        images = ImageSerializer.setup_eager_loading(qs)
        return images

    def destroy(self, request, *args, **kwargs):
        image = self.get_object()
        if image.user.id != request.user.id:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        blobs_ids = request.user.highlights_ids
        highlights_ids = []
        for id in blobs_ids:
            if str(image.id) != id.split('-')[0]:
                highlights_ids.append(id)
        request.user.highlights_ids = highlights_ids
        request.user.save()

        blobs_ids = request.user.preferences.favorites_ids
        favorites_ids = []
        for id in blobs_ids:
            if str(image.id) != id.split('-')[0]:
                favorites_ids.append(id)
        request.user.preferences.favorites_ids = favorites_ids
        request.user.preferences.save()
        if image.album_cover != None:
            album = Album.objects.get(id=image.album.id)
            image.delete()
            new_cover = Image.objects.filter(album=album).first()
            if new_cover != None:
                new_cover.album_cover = album
                blob = new_cover.blobs.first()
                blob.album_cover = album
                new_cover.save()
                blob.save()
                cover = get_album_cover(album, request)
                return Response({'cover_updated': True, 'cover': cover})
            else:
                album.delete()
                return Response({'album_deleted': True})
        return super(ImageViewSet, self).destroy(request, *args, **kwargs)


class FetchImageAudioUri(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = ImageAudioUriSerializer

    def get_queryset(self):
        id = self.request.GET.get("id")
        my_groups = self.request.user.groups.all()
        connections_parties_ids = self.request.user.get_connections_parties_ids()
        image = Image.objects.filter(Q(id=id) & (Q(groups__in=my_groups) |
                                                 Q(connections__in=[self.request.user]) |
                                                 Q(party_id__in=connections_parties_ids) |
                                                 Q(user=self.request.user))) \
            .exclude(
            Q(user__is_active=False) |
            Q(user__in=self.request.user.blocked.all()) |
            Q(user__blocked__in=[self.request.user]) |
            Q(id__in=self.request.user.hidden_images))
        if not image:
            return Image.objects.none()
        return image


class FetchBlobUri(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = BlobUriSerializer

    def get_queryset(self):
        id = self.request.GET.get("id")
        blob = Blob.objects.filter(id=id)
        try:
            id = blob.first().image.id
        except:
            return Image.objects.none()
        my_groups = self.request.user.groups.all()
        connections_parties_ids = self.request.user.get_connections_parties_ids()
        image = Image.objects.filter(Q(id=id) & (Q(groups__in=my_groups) |
                                                 Q(connections__in=[self.request.user]) |
                                                 Q(party_id__in=connections_parties_ids) |
                                                 Q(user=self.request.user))) \
            .exclude(
            Q(user__is_active=False) |
            Q(user__in=self.request.user.blocked.all()) |
            Q(user__blocked__in=[self.request.user]) |
            Q(id__in=self.request.user.hidden_images))
        if not image:
            return Image.objects.none()
        return blob


class DeleteBlob(APIView):
    permissions_classes = [permissions.IsAuthenticated]

    def post(self, request):
        blob = Blob.objects.get(id=request.data['blob_id'])
        image = blob.image
        if image.user.id != request.user.id:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        id = str(image.id) + '-' + str(blob.id)
        if id in request.user.highlights_ids:
            request.user.highlights_ids.remove(id)
            request.user.save()
        if id in request.user.preferences.favorites_ids:
            request.user.preferences.favorites_ids.remove(id)
            request.user.preferences.save()

        if blob.album_cover != None:
            blob.delete()
            new_cover = image.blobs.first()
            new_cover.album_cover = image.album
            new_cover.save()
            cover = get_album_cover(image.album, request)
            return Response({'cover_updated': True, 'cover': cover})
        blob.delete()
        return Response(status=status.HTTP_200_OK)


class ChangeAlbumCover(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        blob = Blob.objects.get(id=request.data['blob_id'])
        album_id = blob.image.album.id
        current_cover = Blob.objects.get(album_cover=album_id, album_cover__isnull=False)
        current_cover.album_cover = None
        current_cover.save()
        album = Album.objects.get(id=album_id)
        blob.album_cover = album
        blob.save()

        if blob.image.id != current_cover.image.id:
            current_cover.image.album_cover = None
            current_cover.image.save()
            blob.image.album_cover = album
            blob.image.save()
        return Response(status=status.HTTP_200_OK)


class ToggleFavorite(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        my_groups = self.request.user.groups.all()
        connections_parties_ids = self.request.user.get_connections_parties_ids()
        image = Image.objects.filter(
            Q(id=request.data['image_id']) &
            (Q(groups__in=my_groups) |
             Q(connections__in=[self.request.user]) |
             Q(party_id__in=connections_parties_ids) |
             Q(user=self.request.user))) \
            .exclude(
            Q(user__is_active=False) |
            Q(user__in=self.request.user.blocked.all()) |
            Q(user__blocked__in=[self.request.user]) |
            Q(id__in=self.request.user.hidden_images)) \
            .order_by("-timestamp").first()
        if not image:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if 'blob_id' in request.data and request.data['blob_id'] != None:
            id = str(request.data['image_id']) + '-' + str(request.data['blob_id'])
            if not id in request.user.preferences.favorites_ids:
                faved = True
                request.user.preferences.favorites_ids.append(id)
            else:
                faved = False
                request.user.preferences.favorites_ids.remove(id)

        else:
            blobs = image.blobs.all()
            faved = not request.data['is_fav']
            for blob in blobs:
                id = str(request.data['image_id']) + '-' + str(blob.id)
                if not request.data['is_fav'] and not id in request.user.preferences.favorites_ids:
                    request.user.preferences.favorites_ids.append(id)
                elif request.data['is_fav'] and id in request.user.preferences.favorites_ids:
                    request.user.preferences.favorites_ids.remove(id)
        request.user.preferences.save()
        return Response({'faved': faved})


class SelectedBlobsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = ImageSerializer

    def get_queryset(self):
        ids = self.request.GET.get("ids")
        ids_list = ids.split(',')
        ids_list = list(map(int, ids_list))
        my_groups = self.request.user.groups.all()
        connections_parties_ids = self.request.user.get_connections_parties_ids()
        qs = Image.objects.filter(Q(blobs__id__in=ids_list) & (Q(groups__in=my_groups) |
                                                               Q(connections__in=[self.request.user]) |
                                                               Q(party_id__in=connections_parties_ids) |
                                                               Q(user=self.request.user))) \
            .exclude(
            Q(user__is_active=False) |
            Q(user__in=self.request.user.blocked.all()) |
            Q(user__blocked__in=[self.request.user]) |
            Q(id__in=self.request.user.hidden_images)) \
            .distinct().order_by("-timestamp")
        images = ImageSerializer.setup_eager_loading(qs)
        return images


class SelectedBlobsImageView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = BlobImageSerializer

    def get_queryset(self):
        ids = self.request.GET.get("ids")
        ids_list = ids.split(',')
        ids_list = list(map(int, ids_list))
        my_groups = self.request.user.groups.all()
        connections_parties_ids = self.request.user.get_connections_parties_ids()
        qs = Blob.objects.filter(Q(id__in=ids_list) & (Q(image__groups__in=my_groups) |
                                                       Q(image__connections__in=[self.request.user]) |
                                                       Q(image__party_id__in=connections_parties_ids) |
                                                       Q(image__user=self.request.user))) \
            .exclude(
            Q(image__user__is_active=False) |
            Q(image__user__in=self.request.user.blocked.all()) |
            Q(image__user__blocked__in=[self.request.user]) |
            Q(image__id__in=self.request.user.hidden_images)) \
            .distinct()
        blobs = BlobImageSerializer.setup_eager_loading(qs)
        return blobs


class FavoriteImages(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = ImageSerializer

    def get_queryset(self):
        my_groups = self.request.user.groups.all()
        connections_parties_ids = self.request.user.get_connections_parties_ids()
        blobs_ids = self.request.user.preferences.favorites_ids
        ids = []
        for id in blobs_ids:
            ids.append(id.split('-')[0])
        qs = Image.objects.filter(Q(id__in=ids) & (Q(groups__in=my_groups) | Q(connections__in=[self.request.user]) |
                                                   Q(party_id__in=connections_parties_ids) |
                                                   Q(user=self.request.user))) \
            .exclude(
            Q(user__is_active=False) |
            Q(user__in=self.request.user.blocked.all()) |
            Q(user__blocked__in=[self.request.user]) |
            Q(id__in=self.request.user.hidden_images)) \
            .distinct().order_by("-timestamp")
        images = ImageSerializer.setup_eager_loading(qs)
        return images


class HiddenImages(DynamicFieldsViewMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ImageSerializer
    pagination_class = None

    def get_queryset(self):
        my_groups = self.request.user.groups.all()
        connections_parties_ids = self.request.user.get_connections_parties_ids()
        qs = Image.objects.filter(Q(id__in=self.request.user.hidden_images) & (Q(groups__in=my_groups) |
                                                                               Q(connections__in=[self.request.user]) |
                                                                               Q(party_id__in=connections_parties_ids) |
                                                                               Q(user=self.request.user))) \
            .exclude(
            Q(user__is_active=False) |
            Q(user__in=self.request.user.blocked.all()) |
            Q(user__blocked__in=[self.request.user])) \
            .distinct().order_by("-timestamp")
        images = ImageSerializer.setup_eager_loading(qs)
        return images


def create_youtube_post(request):
    data = request.data
    thumbnail = data['youtube_thumbnail'].rstrip("\n\r")
    image = Image.objects.create(caption=data['caption'],
                                 stick_id=data['stick_id'], party_id=data['party_id'],
                                 duration=1, user=request.user)
    Blob.objects.create(image=image, youtube=data['youtube'], youtube_thumbnail=thumbnail, duration=1)
    if 'groups_id' in data:
        image.groups.set(data['groups_id'])
    if 'connections_id' in data:
        image.connections.set(data['connections_id'])
    return image


class YoutubeShare(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        image = create_youtube_post(request)
        return Response({"id": image.id})


class YoutubeRestick(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ImageSerializer

    def create(self, request, *args, **kwargs):
        image = create_youtube_post(request)
        serializer = self.get_serializer(data=[image], many=True)
        serializer.is_valid()
        return Response(serializer.data)


class LatestShared(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ImageSerializer

    def get_queryset(self):
        my_groups = self.request.user.groups.all()
        connections_parties_ids = self.request.user.get_connections_parties_ids()
        qs = Image.objects.filter(Q(album__isnull=True) & (Q(groups__in=my_groups) |
                                                           Q(connections__in=[self.request.user]) |
                                                           Q(party_id__in=connections_parties_ids) |
                                                           Q(user=self.request.user))).exclude(
            Q(user__is_active=False) |
            Q(user__in=self.request.user.blocked.all()) |
            Q(user__blocked__in=[self.request.user]) | Q(id__in=self.request.user.hidden_images)).distinct().order_by(
            "-timestamp")[:4]
        images = ImageSerializer.setup_eager_loading(qs)
        return images


class HighlightedImages(generics.ListAPIView):  # TODO: use BlobImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ImageSerializer

    def get_queryset(self):
        blobs_ids = self.request.user.highlights_ids
        ids = []
        for id in blobs_ids:
            ids.append(id.split('-')[0])
        qs = Image.objects.filter(id__in=ids).distinct().order_by('-timestamp')
        images = ImageSerializer.setup_eager_loading(qs)
        return images


class IsProfileImages(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ImageSerializer

    def get_queryset(self):
        id = self.request.GET.get('id')
        if id == None:
            id = self.request.user.id
            qs = Image.objects.filter(user__id=id, is_profile=True).distinct().order_by('-timestamp')
        else:
            my_groups = self.request.user.groups.all()
            connections_parties_ids = self.request.user.get_connections_parties_ids()
            qs = Image.objects.filter(Q(user__id=id) & Q(is_profile=True) & (Q(groups__in=my_groups) |
                                                                             Q(connections__in=[self.request.user]) |
                                                                             Q(party_id__in=connections_parties_ids) |
                                                                             Q(user=self.request.user))).distinct().order_by(
                '-timestamp')
        images = ImageSerializer.setup_eager_loading(qs)
        return images

class ConnectionImages(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ImageSerializer

    def get_queryset(self):
        id = self.request.GET.get('id')
        connection = User.objects.get(id=id)
        qs = Image.objects.filter(Q(user=connection, connections__in=[self.request.user]) | Q(user=self.request.user, connections__in=[connection])).distinct().order_by('-timestamp')
        for image in qs:
            image.seen_by.add(self.request.user)
        images = ImageSerializer.setup_eager_loading(qs)
        return images


class GroupSharedImages(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ImageSerializer

    def get_queryset(self, *args, **kwargs):
        group_id = self.request.GET.get("id")
        group = Group.objects.get(id=group_id)
        if not group in self.request.user.groups.all():
            return Image.objects.none()
        qs = Image.objects.filter(groups__in=[group], album__isnull=True) \
            .exclude(
            Q(user__is_active=False) |
            Q(user__in=self.request.user.blocked.all()) |
            Q(user__blocked__in=[self.request.user]) |
            Q(id__in=self.request.user.hidden_images)
        ).distinct().order_by('-timestamp')
        for image in qs:
            image.seen_by.add(self.request.user)
        images = ImageSerializer.setup_eager_loading(qs)
        return images


class SharedImages(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = ImageSerializer

    def get_queryset(self):
        user = self.request.user.id
        qs = Image.objects.filter(user=user, album__isnull=True).distinct().order_by("-timestamp")
        images = ImageSerializer.setup_eager_loading(qs)
        return images


class SharedByOthers(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = ImageSerializer

    def get_queryset(self):
        user = self.request.user
        connections_parties_ids = self.request.user.get_connections_parties_ids()
        qs = Image.objects.filter(
            ~Q(user=user) &
            Q(album__isnull=True) &
            (Q(groups__in=user.get_groups()) |
             Q(connections__in=[user]) |
             Q(party_id__in=connections_parties_ids))
        ).exclude(
            Q(user__is_active=False) |
            Q(user__in=self.request.user.blocked.all()) |
            Q(user__blocked__in=[self.request.user]) |
            Q(id__in=self.request.user.hidden_images)).distinct().order_by(
            "-timestamp")

        images = ImageSerializer.setup_eager_loading(qs)
        return images


class AlbumViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AlbumSerializer

    def get_queryset(self):
        group_id = self.request.GET.get('q')
        group = Group.objects.get(id=group_id)
        if not group in self.request.user.groups.all():
            return Album.objects.none()
        qs = Album.objects.filter(group=group).distinct().order_by("-timestamp")
        albums = AlbumSerializer.setup_eager_loading(qs)
        return albums

class DeleteAlbum(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        album = Album.objects.get(id=request.data['id'])
        if album.user.id != request.user.id and album.group.owner.id != request.user.id:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        has_cover = Image.objects.filter(album=album, album_cover__isnull=False).first()
        if has_cover:
            Notification.objects.filter(image=album.cover).all().delete()
        album.delete()
        return Response(status=status.HTTP_200_OK)


class FetchSingleAlbum(generics.GenericAPIView):
    serializer_class = AlbumSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        id = request.GET.get('id')
        album = Album.objects.get(id=id)
        if not album.group in request.user.groups.all():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response({
            'album': self.serializer_class(album, context=self.get_serializer_context()).data,
        })

class AlbumImagesUris(DynamicFieldsViewMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = ImageSerializer

    def get_queryset(self):
        album_id = self.request.GET.get('q')
        album = Album.objects.get(id=album_id)
        if not album.group in self.request.user.groups.all():
            return Image.objects.none()
        qs = Image.objects.filter(album=album_id)
        images = ImageSerializer.setup_eager_loading(qs)
        return images


class AlbumDetailAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ImageSerializer

    def get_queryset(self, *args, **kwargs):
        album_id = self.request.GET.get("q")
        album = Album.objects.get(id=album_id)
        if not album.group in self.request.user.groups.all():
            return Image.objects.none()
        timestamp = self.request.GET.get('timestamp')
        qs = Image.objects.filter(album=album_id).exclude(
            Q(user__is_active=False) |
            Q(user__in=self.request.user.blocked.all()) |
            Q(user__blocked__in=[self.request.user]) |
            Q(id__in=self.request.user.hidden_images)).distinct().order_by(timestamp)
        images = ImageSerializer.setup_eager_loading(qs)
        return images

class UploadImages(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ImageSerializer

    def create(self, request, *args, **kwargs):
        one_gb = 1073741824
        max_space = one_gb if request.user.subscription == 'basic' else one_gb * 2000
        if request.user.vault_storage >= max_space:
            return Response({'limit_reached': True})
        uri_key_list = request.data.getlist('uri_key')
        total = len(uri_key_list) if 'uri_key' in request.data else 1

        # if current_count + total > BASIC_LIMIT and request.user.subscription == 'basic':
        #     return Response({'limit_reached': True})
        type = request.data['type']
        is_profile = json.loads(request.data['is_profile'])
        group, album = None, None

        # Validate authorization
        if type == 'create' or type == 'more':
            group = Group.objects.get(id=request.data['group_id'])
            album = Album.objects.get(id=request.data['album_id'])
            if not group in request.user.groups.all():
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            if type == 'more' and album.group.id != group.id:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        elif type == 'share' and not is_profile:
            if 'groups_id' in request.data:
                groups_ids = request.user.get_groups_ids()
                for id in request.data.getlist('groups_id'):
                    if not id in groups_ids:
                        return Response(status=status.HTTP_401_UNAUTHORIZED)
                    else:
                        group = Group.objects.get(id=id)
                        group.last_activity = timezone.now()
                        group.save()
            if 'connections_id' in request.data:
                connections_ids = request.user.get_connections_ids()
                for id in request.data.getlist('connections_id'):
                    if not id in connections_ids:
                        return Response(status=status.HTTP_401_UNAUTHORIZED)

        stick_id = request.data['stick_id']
        party_id = request.data['party_id']
        caption = request.data['caption']
        share_ext = json.loads(request.data['share_ext'])
        cipher_list = request.data.getlist('cipher')
        size_list = request.data.getlist('size')
        width_list = request.data.getlist('width')
        height_list = request.data.getlist('height')
        duration_list = request.data.getlist('duration')
        asset_size_list = request.data.getlist('asset_size')
        media_type_list = request.data.getlist('media_type')
        preview_uri_key_list = request.data.getlist('preview_uri_key')
        thumb_cipher_list = request.data.getlist('thumb_cipher')
        thumb_size_list = request.data.getlist('thumb_size')
        text_photo_list = request.data.getlist('text_photo')
        location_list = request.data.getlist('location')
        album_cover_list = request.data.getlist('album_cover')
        is_video_list = request.data.getlist('is_video')

        image = Image.objects.create(stick_id=stick_id,
                                     party_id=party_id,
                                     is_profile=is_profile,
                                     caption=caption,
                                     user=request.user,
                                     share_ext=share_ext)
        image.seen_by.set([request.user])
        if 'audio_uri' in request.data:
            image.audio_uri = request.data['audio_uri']
            image.audio_cipher = request.data['audio_cipher']
            image.audio_duration = request.data['audio_duration']
            image.file_size = [request.data['audio_size']]
        if 'location' in request.data and location_list[0] != '':
            image.location = location_list[0]

        if type == 'share':
            image.index = 0
            image.of_total = total
        else:
            image.album = album
            image.group = group
            if type == 'create':
                image.groups.set([request.data['group_id']])
                image.album_cover = album
        image.save()
        if 'groups_id' in request.data:
            image.groups.set(request.data.getlist('groups_id'))
        if 'connections_id' in request.data:
            image.connections.set(request.data.getlist('connections_id'))

        for i in range(total):
            blob = Blob.objects.create(
                image=image,
                cipher=cipher_list[i],
                size=size_list[i],
                width=json.loads(width_list[i]),
                height=json.loads(height_list[i]),
                duration=json.loads(duration_list[i]),
                file_size=[json.loads(asset_size_list[i])],
            )

            request.user.vault_storage += json.loads(asset_size_list[i])

            if not share_ext:
                media_type = media_type_list[i]
            else:
                media_type = "video" if json.loads(is_video_list[i]) else "image"
            if media_type.startswith('image'):
                blob.uri_key = uri_key_list[i]
            elif media_type.startswith('video'):
                blob.uri_key = uri_key_list[i]
                if 'preview_uri_key' in request.data:
                    blob.preview_uri_key = preview_uri_key_list.pop(0)
                    blob.thumb_cipher = thumb_cipher_list.pop(0)
                    blob.file_size.append(json.loads(thumb_size_list.pop(0)))
                    request.user.vault_storage += blob.file_size[1]
            else:
                blob.text_photo = text_photo_list.pop(0)

            if type == 'create':
                if json.loads(album_cover_list[i]):
                    blob.album_cover = Album.objects.get(id=album_cover_list[i])
            blob.save()

        request.user.save()
        serializer = self.get_serializer(data=[image], many=True)
        serializer.is_valid()
        return Response(serializer.data)

class NoteViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NoteSerializer


class DeleteNote(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        note = Note.objects.get(id=request.data['id'])
        if note.user.id != request.user.id:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        Notification.objects.filter(note=note).all().delete()
        note.replies.all().delete()
        note.delete()
        return Response(status=status.HTTP_200_OK)


class DeleteReactionNote(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if 'image' in request.data:
            note = Note.objects.get(user=request.user, image=request.data['image'], is_reply=False,
                                    reaction__isnull=False)
        else:
            note = Note.objects.get(user=request.user, album=request.data['album'], is_reply=False,
                                    reaction__isnull=False)
        note_id = note.id
        Notification.objects.filter(note=note).all().delete()
        note.replies.all().delete()
        note.delete()
        return Response({'note_id': note_id})


class EditNote(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        note = Note.objects.get(id=request.data['note_id'])
        if note.user.id != request.user.id:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        note.text = request.data['cipher_text']
        note.save()
        stick_id = note.stick_id
        party_id = stick_id[:36]
        chain_id = stick_id[36:]
        key = EncryptionSenderKey.objects.get(party_id=party_id, chain_id=chain_id, user=request.user)
        key.step = request.data['chain_step']
        key.save()
        return Response(status=status.HTTP_200_OK)


class FetchNotes(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NoteSerializer

    def get_queryset(self):
        image_id = self.request.GET.get("q")
        connections_parties_ids = self.request.user.get_connections_parties_ids()
        my_groups = self.request.user.groups.all()
        image = Image.objects.filter(Q(id=image_id) & (Q(groups__in=my_groups) |
                                                       Q(connections__in=[self.request.user]) |
                                                       Q(party_id__in=connections_parties_ids) |
                                                       Q(user=self.request.user))).first()
        if not image:
            return Note.objects.none()
        qs = image.get_notes().order_by("-timestamp")
        notes = NoteSerializer.setup_eager_loading(qs)
        return notes


class FetchAlbumNotes(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NoteSerializer

    def get_queryset(self):
        album_id = self.request.GET.get("q")
        album = Album.objects.get(id=album_id)
        if not album.group in self.request.user.groups.all():
            return Note.objects.none()
        qs = album.get_notes().order_by("-timestamp")
        notes = NoteSerializer.setup_eager_loading(qs)
        return notes


class ReactionsCount(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        id = request.GET.get("q")
        type = request.GET.get('type')
        if type == 'image':
            connections_parties_ids = self.request.user.get_connections_parties_ids()
            my_groups = self.request.user.groups.all()
            image = Image.objects.filter(Q(id=id) & (Q(groups__in=my_groups) |
                                                     Q(connections__in=[self.request.user]) |
                                                     Q(party_id__in=connections_parties_ids) |
                                                     Q(user=self.request.user))).first()
            if not image:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            notifications = Notification.objects.filter(image=image, to_user=request.user)
            likes_count = image.likes.all().exclude(is_active=False).count()
            users = []
            for user in image.likes.all():
                users.append({'id': user.id, 'name': user.name, 'username': user.username})
            notes_count = image.notes.all().exclude(user__is_active=False).count()
        elif type == 'album':
            album = Album.objects.get(id=id)
            if not album.group in self.request.user.groups.all():
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            notifications = Notification.objects.filter(album=album, to_user=request.user)
            likes_count = album.likes.all().exclude(is_active=False).count()
            users = []
            for user in album.likes.all():
                users.append({'id': user.id, 'name': user.name, 'username': user.username})
            notes_count = album.album_notes.all().exclude(user__is_active=False).count()
        else:  # note
            note = Note.objects.get(id=id)
            notifications = Notification.objects.filter(note=note, to_user=request.user)
            likes_count = note.likes.all().exclude(is_active=False).count()
            users = []
            for user in note.likes.all():
                users.append({'id': user.id, 'name': user.name, 'username': user.username})
            notes_count = 0
        count = 0
        ids = []
        for notification in notifications:
            if notification.read == False:
                count += 1
                notification.read = True
                ids.append(notification.id)
                notification.save()
        return Response(
            {"count": count, "ids": ids, 'likes_count': likes_count, 'notes_count': notes_count, 'liked_by': users})


class ToggleLike(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        type = request.data['type']
        if type == 'image':
            connections_parties_ids = self.request.user.get_connections_parties_ids()
            my_groups = request.user.groups.all()
            content = Image.objects.filter(Q(id=request.data['id']) & (Q(groups__in=my_groups) |
                                                                       Q(connections__in=[self.request.user]) |
                                                                       Q(party_id__in=connections_parties_ids) |
                                                                       Q(user=self.request.user))).first()
            if not content:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            content = Image.objects.get(id=request.data['id'])
            noun = 'image'
        elif type == 'album':
            content = Album.objects.get(id=request.data['id'])
            if not content.group in request.user.groups.all():
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            noun = 'album'
        else:
            content = Note.objects.get(id=request.data['id'])
            noun = 'note'
        if not request.user in content.likes.all():
            content.likes.add(request.user)
            if content.user.id != request.user.id:
                kwargs = {noun: content}
                if type == 'note':
                    if json.loads(request.data['data']['is_image']):
                        kwargs['image'] = content.image
                    else:
                        kwargs['album'] = content.album
                PushNotification.post(self, request, **kwargs)
        else:
            content.likes.remove(request.user)
            if type == 'image':
                notification = Notification.objects.filter(image=content, from_user=request.user,
                                                           channel='comment_channel', note=None).first()
            elif type == 'album':
                notification = Notification.objects.filter(album=content, from_user=request.user,
                                                           channel='comment_channel', note=None).first()
            else:
                notification = Notification.objects.filter(note=content, is_like=True, from_user=request.user,
                                                           channel='comment_channel').first()
            if notification:
                notification.delete()
        content.save()
        return Response(status=status.HTTP_200_OK)




##################################################################################################################################


class CipherImageView(APIView):

    def post(self, request):
        # print(request.data)
        # print("HEADER", request.headers)
        TestImage.objects.create(uri=request.data["file"])
        # TestImage.objects.create(uri=request.data["file1"])
        # TestImage.objects.create(uri=request.data["file2"])
        # TestImage.objects.create(uri=request.data["file3"])
        return Response(status=status.HTTP_200_OK)


class CipherImageView2(APIView):

    def post(self, request):
        # print(request.data)
        # print("HEADER", request.headers)
        # TestImage.objects.create(uri=request.data["file"])
        TestImage.objects.create(uri=request.data["file1"])
        TestImage.objects.create(uri=request.data["file2"])
        # TestImage.objects.create(uri=request.data["file3"])
        return Response(status=status.HTTP_200_OK)


# class WorkingDir(APIView):
#
#     def get(self, request):
#         return Response({"dir": str(pathlib.Path(__file__).parent.absolute())})


class Test(APIView):

    def post(self, request):
        return Response({'allDone': 'YES'})


class TestHost(APIView):

    def post(self, request):
        import requests

        ########## ALLOWED_HOSTS
        from requests.exceptions import ConnectionError

        url = "http://169.254.169.254/latest/meta-data/public-ipv4"
        ALLOWED_HOSTS = []

        r = requests.get(url)
        instance_ip = r.text
        ALLOWED_HOSTS += [instance_ip]
        from socket import gethostname, gethostbyname
        ALLOWED_HOSTS += [gethostname(), gethostbyname(gethostname())]

        return Response({'hosts': ALLOWED_HOSTS})
        # except ConnectionError:
        #     error_msg = "You can only run production settings on an AWS EC2 instance"
        # raise ImproperlyConfigured(error_msg)
        ########## END ALLOWED_HOSTS




from custom_storages import S3
class GetPresignedUrl(APIView):

    def post(self, request):
        url = S3().get_presigned_url(request.data['uri_key'])
        return Response({'url': url})


