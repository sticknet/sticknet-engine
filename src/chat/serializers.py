from rest_framework import serializers

from sticknet.settings import TESTING

if not TESTING:
    from custom_storages import S3
else:
    from mock_custom_storages import S3

from .models import ChatFile, ChatAlbum, ChatAudio
from groups.serializers import CipherSerializer

class ChatFileSerializer(serializers.ModelSerializer):
    presigned_url = serializers.SerializerMethodField()
    preview_presigned_url = serializers.SerializerMethodField()
    class Meta:
        model = ChatFile
        fields = '__all__'

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('user', 'group', 'party')
        return queryset

    def get_presigned_url(self, object):
        return S3().get_file(object.uri_key)

    def get_preview_presigned_url(self, object):
        if not object.preview_uri_key:
            return None
        return S3().get_file(object.preview_uri_key)

class ChatAudioSerializer(serializers.ModelSerializer):
    presigned_url = serializers.SerializerMethodField()
    class Meta:
        model = ChatAudio
        fields = '__all__'

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('user', 'group', 'party')
        return queryset

    def get_presigned_url(self, object):
        return S3().get_file(object.uri_key)


def get_album_cover(album):
    cover = ChatFile.objects.filter(album=album).last()
    if cover:
        return {
            'uri_key': cover.uri_key,
            'preview_uri_key': cover.preview_uri_key,
            'presigned_url': S3().get_file(cover.uri_key),
            'preview_presigned_url': S3().get_file(cover.preview_uri_key),
            'type': cover.type,
            'file_size': cover.file_size,
            'preview_file_size': cover.preview_file_size,
            'cipher': cover.cipher,
            'preview_cipher': cover.preview_cipher,
            'duration': cover.duration,
            'stick_id': cover.stick_id,
            'party_id': cover.party_id,
            'name': cover.name,
            'user': cover.user.id
        }
    return None

class ChatAlbumSerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()
    title = CipherSerializer(required=False)
    class Meta:
        model = ChatAlbum
        fields = '__all__'

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('user', 'group', 'party')
        return queryset

    def get_cover(self, obj):
        return get_album_cover(obj)




