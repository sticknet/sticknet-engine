import json
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ChatFile, ChatAlbum, ChatAudio
from .serializers import ChatAlbumSerializer, \
    ChatAudioSerializer
from rest_framework import permissions, generics, status

from groups.models import Group, Cipher
from stick_protocol.models import Party
from .serializers import ChatFileSerializer, get_album_cover
from django.db.models import Q
from photos.pagination import DynamicPagination
from django.utils import timezone
from vault.views import trim_file_name

class UploadChatFiles(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        files = request.data['files']
        response = {}
        filesList = []
        group = None
        party = None
        album = None
        if 'group_id' in request.data:
            group = Group.objects.get(id=request.data['group_id'])
        if 'party_id' in request.data:
            party = Party.objects.get(id=request.data['party_id'])
        if 'encrypted_album_title' in request.data:
            title = Cipher.objects.create(text=request.data['encrypted_album_title'], user=request.user,
                                          stick_id=request.data['stick_id'])
            album = ChatAlbum.objects.create(user=request.user,
                                             title=title,
                                             group=group,
                                             party=party)
        elif 'album_id' in request.data and request.data['album_id']:
            album = ChatAlbum.objects.get(id=request.data['album_id'])
        elif request.data['is_media']:
            curr_month = timezone.now().strftime("%b %Y")
            album = ChatAlbum.objects.filter(group=group, party=party, auto_month=curr_month).first()
            if not album:
                album = ChatAlbum.objects.create(group=group,
                                                 party=party,
                                                 auto_month=curr_month)
        for i in range(len(files)):
            file = files[i]
            name = trim_file_name(file['name'])
            fileObject = ChatFile.objects.create(uri_key=file['uri_key'],
                                                 cipher=file['cipher'],
                                                 file_size=file['file_size'],
                                                 name=name,
                                                 type=file['type'],
                                                 duration=file['duration'],
                                                 created_at=file['created_at'],
                                                 stick_id=request.data['stick_id'],
                                                 message_id=request.data['message_id'],
                                                 party=party,
                                                 user=request.user,
                                                 group=group,
                                                 album=album)
            if album:
                if fileObject.duration == 0:
                    album.photos_count += 1
                else:
                    album.videos_count += 1
                album.save()
            if i == len(files) - 1:
                fileObject.is_album_cover = True
            if 'preview_uri_key' in file:
                fileObject.preview_uri_key = file['preview_uri_key']
                fileObject.preview_cipher = file['preview_cipher']
                fileObject.preview_file_size = file['preview_file_size']
                fileObject.width = file['width']
                fileObject.height = file['height']
                fileObject.save()

            item = {'id': fileObject.id,
                    'uri_key': file['uri_key'],
                    'cipher': file['cipher'],
                    'file_size': file['file_size'],
                    'name': fileObject.name,
                    'type': file['type'],
                    'duration': file['duration'],
                    'created_at': file['created_at'],
                    'timestamp': fileObject.timestamp,
                    'user': fileObject.user.id,
                    'messageId': request.data['message_id']}
            if 'timestamp' in file:
                item['client_timestamp'] = file['timestamp']
            if 'preview_uri_key' in file:
                item['preview_uri_key'] = file['preview_uri_key']
                item['preview_cipher'] = file['preview_cipher']
                item['preview_file_size'] = file['preview_file_size']
                item['width'] = file['width']
                item['height'] = file['height']
            filesList.append(item)
            request.user.chat_storage += file['file_size']
            if 'preview_uri_key' in file:
                request.user.chat_storage += file['preview_file_size']
        request.user.save()
        response['files'] = filesList
        if album:
            response['album'] = {'id': album.id,
                                 'timestamp': album.timestamp,
                                 'cover': get_album_cover(album),
                                 'photos_count': album.photos_count,
                                 'videos_count': album.videos_count,
                                 'auto_month': album.auto_month}
        return Response(response)


class UploadChatAudio(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        audio = request.data['audio']
        group = None
        party = None
        if 'group_id' in request.data:
            group = Group.objects.get(id=request.data['group_id'])
        if 'party_id' in request.data:
            party = Party.objects.get(id=request.data['party_id'])
        audioObject = ChatAudio.objects.create(uri_key=audio['uri_key'],
                                               cipher=audio['cipher'],
                                               file_size=audio['file_size'],
                                               duration=audio['duration'],
                                               stick_id=request.data['stick_id'],
                                               party=party,
                                               user=request.user,
                                               group=group)
        item = {'id': audioObject.id,
                'uri_key': audio['uri_key'],
                'cipher': audio['cipher'],
                'file_size': audio['file_size'],
                'duration': audio['duration'],
                'timestamp': audioObject.timestamp}
        request.user.chat_storage += audio['file_size']
        request.user.save()
        return Response({'audio': item})


class FetchChatFiles(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatFileSerializer
    pagination_class = None

    def get_queryset(self):
        ids = self.request.GET.get("ids")
        ids_list = ids.split(',')
        ids_list = list(map(int, ids_list))
        my_groups = self.request.user.groups.all()
        my_parties = self.request.user.chat_parties()
        qs = ChatFile.objects.filter(Q(id__in=ids_list) & (Q(group__in=my_groups) |
                                                           Q(party__in=my_parties) |
                                                           Q(user=self.request.user)))
        files = ChatFileSerializer.setup_eager_loading(qs)
        return files


class FetchChatAudio(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatAudioSerializer

    def get(self, request):
        id = request.GET.get("id")
        audio = ChatAudio.objects.get(id=id)
        if audio.group not in request.user.groups.all() and audio.party not in request.user.chat_parties():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response({
            'audio': self.serializer_class(audio, context=self.get_serializer_context()).data,
        })


class FetchChatAlbums(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatAlbumSerializer

    def get_queryset(self):
        room_id = self.request.GET.get("room_id")
        is_group = json.loads(self.request.GET.get("is_group"))
        if is_group:
            group = Group.objects.get(id=room_id)
            qs = ChatAlbum.objects.filter(group=group).order_by('-timestamp')
        else:
            party = Party.objects.get(id=room_id)
            qs = ChatAlbum.objects.filter(party=party).order_by('-timestamp')
        albums = ChatAlbumSerializer.setup_eager_loading(qs)
        return albums


class FetchSingleChatAlbum(generics.GenericAPIView):
    serializer_class = ChatAlbumSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        id = request.GET.get('id')
        album = ChatAlbum.objects.get(id=id)
        if album.group not in request.user.groups.all() and album.party not in request.user.chat_parties():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response({
            'album': self.serializer_class(album, context=self.get_serializer_context()).data,
        })


class FetchAlbumPhotos(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatFileSerializer
    pagination_class = DynamicPagination

    def get_queryset(self):
        album_id = self.request.GET.get("q")
        album = ChatAlbum.objects.get(id=album_id)
        if album.group not in self.request.user.groups.all() and album.party not in self.request.user.chat_parties():
            return ChatFile.objects.none()
        qs = ChatFile.objects.filter(album=album_id).exclude(
            Q(user__is_active=False) |
            Q(user__in=self.request.user.blocked.all()) |
            Q(user__blocked__in=[self.request.user])).order_by('-timestamp').distinct()
        photos = ChatFileSerializer.setup_eager_loading(qs)
        return photos


class DeleteChatFiles(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        files = ChatFile.objects.filter(id__in=request.data['ids'])
        album_timestamp = None
        is_album_deleted = False
        re_fetch_cover = True
        album = None
        cover = None
        for file in files:
            if file.user == request.user:
                album_timestamp = file.album.timestamp
                if file.album and file.album.photos_count == 1:
                    is_album_deleted = True
                    re_fetch_cover = False
                    file.album.delete()
                else:
                    album = file.album
                    file.delete()
        if re_fetch_cover:
            cover = get_album_cover(album)
        return Response({'album_timestamp': album_timestamp,
                         'is_album_deleted': is_album_deleted,
                         'cover': cover})

class DeleteChatAudio(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        audio = ChatAudio.objects.get(id=request.data['id'])
        if audio.user == request.user:
            audio.delete()
        return Response(status=status.HTTP_200_OK)


class RenameAlbum(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        album = ChatAlbum.objects.get(id=request.data['album_id'])
        if album.group not in self.request.user.groups.all() and album.party not in self.request.user.chat_parties():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        album.title.text = request.data['encrypted_album_title']
        album.title.stick_id = request.data['stick_id']
        album.title.user = request.user
        album.title.save()
        return Response(status=status.HTTP_200_OK)

class DeleteChatAlbum(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        album = ChatAlbum.objects.get(id=request.data['album_id'])
        if album.group not in self.request.user.groups.all() and album.party not in self.request.user.chat_parties():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if album.user == request.user and not album.auto_month:
            album.delete()
        return Response(status=status.HTTP_200_OK)

def get_storage_usage(queryset, user):
    total_storage = 0
    chat_files = ChatFile.objects.filter(user=user, **queryset)
    for chat_file in chat_files:
        total_storage += chat_file.file_size
        if chat_file.preview_file_size:
            total_storage += chat_file.preview_file_size
    chat_audios = ChatAudio.objects.filter(user=user, **queryset)
    for chat_audio in chat_audios:
        total_storage += chat_audio.file_size
    return total_storage

class FetchStorages(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        groups = user.groups.all()
        parties = user.chat_parties()
        group_storages = [{'id': group.id, 'storage': get_storage_usage({'group': group}, user)} for group in groups]
        party_storages = [{'id': party.id, 'storage': get_storage_usage({'party': party}, user)} for party in parties]
        return Response({'group_storages': group_storages, 'party_storages': party_storages})


class FetchRoomFiles(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatFileSerializer
    pagination_class = DynamicPagination

    def get_queryset(self):
        room_id = self.request.GET.get("room_id")
        is_group = json.loads(self.request.GET.get("is_group"))
        if is_group:
            group = Group.objects.get(id=room_id)
            qs = ChatFile.objects.filter(user=self.request.user, group=group).order_by('-timestamp')
        else:
            party = Party.objects.get(id=room_id)
            qs = ChatFile.objects.filter(user=self.request.user, party=party).order_by('-timestamp')
        files = ChatFileSerializer.setup_eager_loading(qs)
        return files


