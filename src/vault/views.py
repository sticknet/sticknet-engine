from rest_framework import permissions, generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from sticknet.settings import TESTING
from .models import File, VaultAlbum, VaultNote
from .serializers import FileSerializer, VaultAlbumSerializer, VaultNoteSerializer
if not TESTING:
    from custom_storages import S3
else:
    from mock_custom_storages import S3
from django.db.models import F, Func
from photos.pagination import DynamicPagination


class FileViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileSerializer

    def get_queryset(self):
        qs = File.objects.filter(user=self.request.user)
        files = FileSerializer.setup_eager_loading(qs)
        return files


class VaultNoteViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VaultNoteSerializer

    def get_queryset(self):
        qs = VaultNote.objects.filter(user=self.request.user)
        return FileSerializer.setup_eager_loading(qs)


def trim_file_name(input_string):
    if len(input_string) > 100:
        last_dot_index = input_string.rfind('.')
        if last_dot_index != -1:
            characters_to_remove = len(input_string) - 100
            trimmed_string = input_string[:last_dot_index - characters_to_remove] + input_string[last_dot_index:]
        else:
            trimmed_string = input_string[:100]
    else:
        trimmed_string = input_string
    return trimmed_string

class UploadFiles(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        files = request.data['files']
        folder_id = request.data['folder_id']
        if 'is_camera_uploads' in request.data and request.data['is_camera_uploads']:
            folder = File.objects.get(user=request.user, folder_type='camera_uploads', name='Camera Uploads')
        elif folder_id == 'home':
            folder = File.objects.get(user=request.user, folder_type='home')
        else:
            folder = File.objects.get(user=request.user, id=folder_id)
        filesList = []
        album = None
        for i in range(len(files)):
            file = files[i]
            name = trim_file_name(file['name'])
            fileObject = File.objects.create(uri_key=file['uri_key'],
                                             cipher=file['cipher'],
                                             file_size=file['file_size'],
                                             name=name,
                                             type=file['type'],
                                             duration=file['duration'],
                                             folder=folder,
                                             album=album,
                                             is_photo=file['is_photo'],
                                             created_at=file['created_at'],
                                             user=request.user)
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
                    'is_photo': file['is_photo'],
                    'created_at': file['created_at'],
                    'timestamp': fileObject.timestamp,
                    'folder': folder.id}
            if 'timestamp' in file:
                item['client_timestamp'] = file['timestamp']
            if 'preview_uri_key' in file:
                item['preview_uri_key'] = file['preview_uri_key']
                item['preview_cipher'] = file['preview_cipher']
                item['preview_file_size'] = file['preview_file_size']
                item['width'] = file['width']
                item['height'] = file['height']
            filesList.append(item)
            request.user.vault_storage += file['file_size']
            if 'preview_uri_key' in file:
                request.user.vault_storage += file['preview_file_size']
        request.user.save()
        return Response(filesList)


class GetUploadUrls(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        one_gb = 1073741824
        max_space = one_gb if request.user.subscription == 'basic' else one_gb * 2000
        uploading_size = 0
        if 'uploading_size' in request.data:
            uploading_size = request.data['uploading_size']
        if request.user.vault_storage + request.user.chat_storage + uploading_size >= max_space:
            return Response({'limit_reached': True})
        uri_keys_list = request.data['uri_keys']
        total = len(uri_keys_list)
        response = {}
        for i in range(total):
            preview_uri = None
            uri = None
            map_key = None
            if uri_keys_list[i]['uri_key']:
                uri_key = uri_keys_list[i]['uri_key']
                uri = S3().get_presigned_url(uri_key)
                map_key = uri_key
            if uri_keys_list[i]['preview_uri_key']:
                preview_uri_key = uri_keys_list[i]['preview_uri_key']
                preview_uri = S3().get_presigned_url(preview_uri_key)
                if map_key == None:
                    map_key = preview_uri_key
            response[map_key] = {'uri': uri,
                                 'preview_uri': preview_uri}
        return Response(response)


class CreateFolder(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        folder_id = request.data['parent_folder_id']
        if folder_id == 'home':
            parent_folder = File.objects.get(user=request.user, folder_type='home')
        else:
            parent_folder = File.objects.get(user=request.user, id=folder_id)
        folder = File.objects.create(name=request.data['name'], folder=parent_folder, is_folder=True, user=request.user)
        return Response({'id': folder.id, 'timestamp': folder.timestamp, 'name': folder.name})


class RenameFile(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file = File.objects.get(user=request.user, id=request.data['id'])
        file.name = trim_file_name(request.data['name'])
        file.save()
        return Response({'name': file.name})


class CreateVaultAlbum(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        album = VaultAlbum.objects.create(name=request.data['name'], user=request.user)
        return Response({'id': album.id, 'timestamp': album.timestamp})


class FetchFiles(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = FileSerializer

    def get_queryset(self):
        folder_id = self.request.GET.get("folder_id")
        if folder_id is not None:
            if folder_id == 'home':
                folder = File.objects.get(user=self.request.user, folder_type='home')
            else:
                folder = File.objects.get(user=self.request.user, id=folder_id)
        else:
            folder_name = self.request.GET.get("folder_name")
            folder = File.objects.get(user=self.request.user, name=folder_name)
        files = File.objects.filter(folder=folder).annotate(lower_name=Func(F('name'), function='LOWER')).order_by(
            '-is_folder', 'lower_name')
        return files


class FetchPhotos(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = FileSerializer

    def get_queryset(self):
        album_id = self.request.GET.get("album_id")
        if album_id != 'recents':
            album = VaultAlbum.objects.get(id=album_id)
            photos = File.objects.filter(user=self.request.user, is_photo=True, album=album).order_by('-timestamp')
        else:
            photos = File.objects.filter(user=self.request.user, is_photo=True).order_by('-timestamp')
        return photos


class FetchVaultAlbums(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    serializer_class = VaultAlbumSerializer

    def get_queryset(self):
        return VaultAlbum.objects.filter(user=self.request.user)


class FetchVaultNotes(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VaultNoteSerializer

    def get_queryset(self):
        return VaultNote.objects.filter(user=self.request.user).order_by('-timestamp')


class CreateVaultNote(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if VaultNote.objects.filter(user=request.user).count() >= 50 and request.user.subscription == 'basic':
            return Response({'limit_reached': True})
        note = VaultNote.objects.create(user=request.user, cipher=request.data['cipher'])
        return Response({'id': note.id, 'timestamp': note.timestamp})


class UpdateVaultNote(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        note = VaultNote.objects.get(user=request.user, id=request.data['id'])
        note.cipher = request.data['cipher']
        note.save()
        return Response(status=status.HTTP_200_OK)


class DeleteFiles(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        files = File.objects.filter(id__in=request.data['ids'])
        for file in files:
            if file.user == request.user:
                file.delete()
        return Response(status=status.HTTP_200_OK)


class FetchHomeItems(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        files = File.objects.filter(user=self.request.user, is_folder=False).order_by('-timestamp')[:3]
        photos = File.objects.filter(user=self.request.user, is_photo=True).order_by('-timestamp')[:5]
        notes = VaultNote.objects.filter(user=self.request.user).order_by('-timestamp')[:3]
        file_serializer = FileSerializer(files, many=True)
        photo_serializer = FileSerializer(photos, many=True)
        note_serializer = VaultNoteSerializer(notes, many=True)
        response_data = {
            'files': file_serializer.data,
            'photos': photo_serializer.data,
            'notes': note_serializer.data,
        }
        return Response(response_data, status=status.HTTP_200_OK)

class FetchLatestFiles(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        files = File.objects.filter(user=self.request.user, is_folder=False).order_by('-timestamp')[:8]
        file_serializer = FileSerializer(files, many=True)
        return Response({'files': file_serializer.data}, status=status.HTTP_200_OK)


class SearchFiles(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = FileSerializer

    def get_queryset(self, *args, **kwargs):
        query = self.request.GET.get("q").lower()
        qs = File.objects.filter(user=self.request.user, name__icontains=query).order_by('-timestamp')
        return qs


class MoveFile(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file = File.objects.get(id=request.data['file_id'], user=request.user)
        folder_id = request.data['folder_id']
        if folder_id == 'home':
            folder = File.objects.get(user=request.user, folder_type='home')
        else:
            folder = File.objects.get(user=request.user, id=folder_id)
        file.folder = folder
        file.save()
        return Response(status=status.HTTP_200_OK)


class FetchAllVaultCipher(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        files_cipher = []
        notes_cipher = []
        for file in request.user.files.filter(is_folder=False):
            entry = {'id': file.id, 'cipher': file.cipher}
            if file.preview_cipher:
                entry['preview_cipher'] = file.preview_cipher
            files_cipher.append(entry)
        for note in request.user.vault_notes.all():
            notes_cipher.append({'id': note.id, 'cipher': note.cipher})
        profile = {}
        if request.user.profile_picture:
            profile['profile_picture_cipher'] = request.user.profile_picture.self_cipher
        return Response({'files_cipher': files_cipher,
                         'notes_cipher': notes_cipher,
                         'profile': profile})
