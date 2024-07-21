from rest_framework import serializers

from sticknet.settings import TESTING
from .models import Notification, Invitation, ConnectionRequest
from users.models import User
from users.serializers import UserConnectionSerializer
from photos.serializers import ImageSerializer, AlbumSerializer
from groups.serializers import GroupSerializer, CipherSerializer
if not TESTING:
    from custom_storages import S3
else:
    from mock_custom_storages import S3


class ConnectionRequestSerializer(serializers.ModelSerializer):
    from_user =  UserConnectionSerializer(fields=('id', 'name', 'username', 'phone', 'profile_picture','color', 'room_id'),
                               read_only=True)

    class Meta:
        model = ConnectionRequest
        fields = ['id', 'from_user', 'timestamp']

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('from_user')
        return queryset


class NotificationSerializer(serializers.ModelSerializer):
    from_user = UserConnectionSerializer(fields=('id', 'phone', 'name', 'profile_picture', 'color'), read_only=True)
    to_user = UserConnectionSerializer(fields=('id'), read_only=True)
    image = ImageSerializer(fields=(
    'id', 'cipher', 'thumb_cipher', 'stick_id', 'uri', 'thumbnail', 'album', 'user', 'duration', 'groups_ids', 'file_size',
    'youtube_thumbnail', 'text_photo'), read_only=True)
    album = AlbumSerializer(fields=('id', 'title', 'coverUri'), read_only=True)
    group = GroupSerializer(fields=('id', 'cover', 'display_name'))
    to_user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    reaction = serializers.SerializerMethodField()
    is_reply = serializers.SerializerMethodField()
    reply_to = serializers.SerializerMethodField()
    node_id = serializers.SerializerMethodField()
    images_ids = serializers.SerializerMethodField()
    blob = serializers.SerializerMethodField()
    blobs_length = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'from_user',
            'to_user',
            'image',
            'album',
            'group',
            'reaction',
            'channel',
            'to_user_id',
            'body',
            'read',
            'is_reply',
            'reply_to',
            'node_id',
            'timestamp',
            'images_ids',
            'stick_id',
            'is_like',
            'blob',
            'blobs_length'
        ]

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('from_user', 'to_user', 'image', 'album', 'group')
        return queryset

    def get_reaction(self, obj):
        note = obj.note
        if note != None:
            if note.reaction:
                reaction = note.reaction
            elif note.text:
                reaction = 'Comment'
            elif note.audio:
                reaction = 'Audio'
            else:
                reaction = 'Sketch'
            return reaction
        return None

    def get_is_reply(self, obj):
        if obj.note != None:
            return obj.note.is_reply
        return None

    def get_reply_to(self, obj):
        if obj.note != None:
            if obj.note.is_reply:
                return {'id': obj.note.reply_to.id, 'name': obj.note.reply_to.name}
        return None

    def get_node_id(self, obj):
        if not obj.note:
            return None
        return obj.note.id

    def get_images_ids(self, obj):
        list = []
        if obj.shared_photos.count() > 0:
            for image in obj.shared_photos.all():
                list.insert(0, image.id)
        return list

    def get_blob(self, obj):
        if obj.image != None and obj.image.blobs and obj.image.blobs.count() > 0:
            blob = obj.image.blobs.first()
            youtube_thumbnail = None
            if blob.uri_key:
                uri = S3().get_file(blob.uri_key)
            elif blob.preview_uri_key:
                uri = S3.get_file(blob.preview_uri_key)
            elif blob.uri:
                uri = self.context['request'].build_absolute_uri(blob.uri.url)
            elif blob.thumbnail:
                uri = self.context['request'].build_absolute_uri(blob.thumbnail.url)
            else:
                uri = ''
                youtube_thumbnail = blob.youtube_thumbnail
            return {'id': blob.id, 'uri': uri, 'thumbnail': uri, 'youtube_thumbnail': youtube_thumbnail,
                    'cipher': blob.cipher, 'thumb_cipher': blob.thumb_cipher, 'duration': blob.duration,
                    'file_size': blob.file_size, 'text_photo': blob.text_photo}
        return None

    def get_blobs_length(self, obj):
        if obj.image and obj.image.blobs:
            return obj.image.blobs.count()
        return 0

class InvitationSerializer(serializers.ModelSerializer):
    from_user = UserConnectionSerializer(fields=('id', 'name', 'profile_picture', 'color'), read_only=True)
    group = GroupSerializer(read_only=True)
    display_name = CipherSerializer()

    class Meta:
        model = Invitation
        fields = ['id', 'from_user', 'group', 'display_name', 'timestamp']

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('from_user', 'group', 'display_name')
        return queryset


class InvitedMembersSerializer(serializers.ModelSerializer):
    to_user = UserConnectionSerializer(fields=('id', 'username', 'name', 'profile_picture', 'color'), read_only=True)

    class Meta:
        model = Invitation
        fields = ['to_user', 'id']

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('to_user')
        return queryset
