from rest_framework import serializers

from sticknet.settings import TESTING
from .models import File, VaultAlbum, VaultNote
if not TESTING:
    from custom_storages import S3
else:
    from mock_custom_storages import S3


class FileSerializer(serializers.ModelSerializer):
    presigned_url = serializers.SerializerMethodField()
    preview_presigned_url = serializers.SerializerMethodField()
    uri_key = serializers.SerializerMethodField()
    class Meta:
        model = File
        fields = '__all__'

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('user')
        return queryset

    def get_presigned_url(self, object):
        if object.is_folder:
            return None
        return S3().get_file(object.uri_key)

    def get_preview_presigned_url(self, object):
        if object.is_folder or not object.preview_uri_key:
            return None
        return S3().get_file(object.preview_uri_key)

    def get_uri_key(self, object):
        return object.uri_key if not object.is_folder else str(object.id)


class VaultAlbumSerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()
    class Meta:
        model = VaultAlbum
        fields = '__all__'

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('user')
        return queryset

    def get_cover(self, object):
        cover = File.objects.filter(album=object).last()
        if cover:
            return {'preview_uri_key': cover.preview_uri_key,
                    'preview_file_size': cover.preview_file_size,
                    'preview_cipher': cover.preview_cipher,
                    'preview_presigned_url': S3().get_file(cover.preview_uri_key)}
        return None


class VaultNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = VaultNote
        fields = ['id', 'cipher', 'timestamp']

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('user')
        return queryset

