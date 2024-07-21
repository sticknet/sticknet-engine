from rest_framework import serializers

from sticknet.settings import TESTING
if not TESTING:
    from custom_storages import S3
else:
    from mock_custom_storages import S3
from .models import ProfilePicture, User, ProfileCover
from notifications.models import ConnectionRequest
from stick_protocol.models import EncryptionSenderKey
from groups.serializers import GroupSerializer, CipherSerializer
from sticknet.dynamic_fields import DynamicFieldsModelSerializer
from groups.models import Cipher, GroupRequest
from photos.models import Blob
from stick_protocol.models import Party
import hashlib


class ProfilePictureSerializer(serializers.ModelSerializer):
    presigned_url = serializers.SerializerMethodField()
    preview_presigned_url = serializers.SerializerMethodField()
    self_presigned_url = serializers.SerializerMethodField()
    class Meta:
        model = ProfilePicture
        fields = '__all__'

    def get_presigned_url(self, object):
        if not object.uri_key:
            return None
        return S3().get_file(object.uri_key)

    def get_preview_presigned_url(self, object):
        if not object.preview_uri_key:
            return None
        return S3().get_file(object.preview_uri_key)

    def get_self_presigned_url(self, object):
        if not object.self_uri_key:
            return None
        return S3().get_file(object.self_uri_key)




class ProfileCoverSerializer(serializers.ModelSerializer):
    presigned_url = serializers.SerializerMethodField()
    class Meta:
        model = ProfileCover
        fields = '__all__'

    def get_presigned_url(self, object):
        if not object.uri_key:
            return None
        return S3().get_file(object.uri_key)


class UserBaseSerializer(DynamicFieldsModelSerializer):
    is_connected = serializers.SerializerMethodField()
    requested = serializers.SerializerMethodField()
    profile_picture = ProfilePictureSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'color', 'one_time_id', 'username', 'name', 'dial_code', 'phone', 'phone_hash', 'is_connected',
                  'requested', 'profile_picture', 'subscription']

    def get_is_connected(self, obj):
        try:
            # is_connected = self.context['request'].user in obj.connections.all()
            is_connected = obj in self.context['request'].user.connections.all()
            return is_connected
        except:
            return False

    def get_requested(self, obj):
        try:
            requested = ConnectionRequest.objects.filter(from_user=self.context['request'].user, to_user=obj).exists()
            return requested
        except:
            return False

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('profile_picture')
        return queryset


class GroupMemberSerializer(UserBaseSerializer):
    class Meta:
        model = User
        fields = ['id', 'one_time_id', 'username', 'name', 'dial_code', 'phone', 'phone_hash', 'color',
                  'profile_picture', 'subscription']

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('profile_picture')
        return queryset


class UserPublicSerializer(UserBaseSerializer):
    day_joined = serializers.SerializerMethodField()
    room_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'one_time_id', 'username', 'name', 'dial_code', 'phone', 'phone_hash', 'website_link',
                  'day_joined', 'subscription', 'color', 'room_id']

    def get_day_joined(self, obj):
        return obj.date_joined.strftime("%B") + ' ' + str(obj.date_joined.year)

    def get_room_id(self, obj):
        connections_ids = [self.context['request'].user.id, obj.id]
        connections_ids.sort()
        ids = ''.join(connections_ids)
        h = hashlib.sha256()
        h.update(ids.encode())
        party_hash = h.hexdigest()
        party = Party.objects.filter(party_hash=party_hash).first()
        if party:
            return party.id
        return None


class UserBaseConnectionSerializer(UserPublicSerializer):
    new_posts_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'one_time_id', 'username', 'name', 'color', 'dial_code', 'phone', 'phone_hash',
                  'profile_picture',
                  'is_connected', 'requested', 'subscription', 'new_posts_count', 'room_id']

    # VIP TODO: to be removed
    def get_new_posts_count(self, obj):
        return 0

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('profile_picture')
        return queryset


class UserConnectionSerializer(UserBaseConnectionSerializer):
    status = CipherSerializer(required=False)
    groups_count = serializers.SerializerMethodField()
    profile_photos_count = serializers.SerializerMethodField()
    birth_day = CipherSerializer(required=False)
    connections_count = serializers.SerializerMethodField()
    highlights_ids = serializers.SerializerMethodField()
    cover = ProfileCoverSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'one_time_id', 'username', 'color', 'name', 'dial_code', 'phone', 'phone_hash', 'website_link',
                  'day_joined',
                  'status',
                  'groups_count', 'profile_photos_count', 'birth_day', 'birth_day_hidden', 'connections_count',
                  'highlights_ids', 'cover', 'profile_picture', 'new_posts_count', 'subscription', 'room_id']

    def get_groups_count(self, obj):
        return obj.get_groups().count()

    def get_profile_photos_count(self, obj):
        return obj.images.filter(is_profile=True).count()

    def get_connections_count(self, obj):
        if not obj.connections:
            return 0
        return obj.connections.all().count()

    def get_highlights_ids(self, obj):
        if obj.highlights_ids:
            return obj.highlights_ids
        return []

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('profile_picture', 'cover', 'status', 'birth_day')
        return queryset


class UserSerializer(UserConnectionSerializer):
    groups = GroupSerializer(many=True, required=False)

    profile_picture_id = serializers.PrimaryKeyRelatedField(queryset=ProfilePicture.objects.all(), write_only=True,
                                                            required=False)
    cover_id = serializers.PrimaryKeyRelatedField(queryset=ProfileCover.objects.all(), write_only=True,
                                                  required=False)
    images_count = serializers.SerializerMethodField()  # TODO: should be removed
    shared_count = serializers.SerializerMethodField()  # TODO: should be removed
    photos_count = serializers.SerializerMethodField()
    notes_count = serializers.SerializerMethodField()
    albums_count = serializers.SerializerMethodField()
    invitations_count = serializers.SerializerMethodField()
    cr_count = serializers.SerializerMethodField()
    blocked_ids = serializers.SerializerMethodField()
    has_password = serializers.SerializerMethodField()
    has_password_key = serializers.SerializerMethodField()
    party_id = serializers.SerializerMethodField()
    room_id = serializers.SerializerMethodField()
    pnt_devices = serializers.SerializerMethodField()
    group_requests = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'one_time_id',
            'username',
            'name',
            'groups',
            'profile_picture',
            'profile_picture_id',
            'cover',
            'cover_id',
            'status',
            'color',
            'birth_day',
            'birth_day_hidden',
            'groups_count',
            'email',
            'password',
            'images_count',
            'shared_count',
            'photos_count',
            'notes_count',
            'albums_count',
            'invitations_count',
            'cr_count',
            'profile_photos_count',
            'blocked_ids',
            'connections_count',
            'date_joined',
            'has_password',
            'has_password_key',
            'phone',
            'phone_hash',
            'email',
            'dial_code',
            'country',
            'next_pre_key_id',
            'highlights_ids',
            'party_id',
            'room_id',
            'pnt_devices',
            'hidden_images',
            'website_link',
            'day_joined',
            'group_requests',
            'backup_frequency',
            'vault_storage',
            'chat_storage',
            'subscription',
            'subscription_expiring',
            'platform'
        ]
        extra_kwargs = {'password': {'write_only': True}, 'id': {'read_only': True}}

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('profile_picture', 'cover', 'status', 'birth_day')
        queryset = queryset.prefetch_related('groups')
        return queryset

    def update(self, instance, data):
        instance.name = data.pop('name')
        instance.username = data.pop('username')
        instance.birth_day_hidden = data.pop('birth_day_hidden')
        # TODO: profile_picture_id to be removed
        if 'profile_picture_id' in data.keys():
            if instance.profile_picture != None:
                instance.profile_picture.delete()
            instance.profile_picture = data.pop('profile_picture_id')
        if 'profile_picture' in self.context['request'].data:
            picture = self.context['request'].data['profile_picture']
            instance.profile_picture = ProfilePicture.objects.create(uri_key=picture['uri_key'],
                                                                     preview_uri_key=picture['preview_uri_key'],
                                                                     self_uri_key=picture['self_uri_key'],
                                                                     cipher=picture['cipher'],
                                                                     preview_cipher=picture['preview_cipher'],
                                                                     self_cipher=picture['self_cipher'],
                                                                     file_size=picture['file_size'],
                                                                     preview_file_size=picture[
                                                                         'preview_file_size'],
                                                                     width=picture['width'],
                                                                     height=picture['height'],
                                                                     name=picture['name'],
                                                                     type=picture['type'],
                                                                     stick_id=self.context['request'].data['stick_id'],
                                                                     resize_mode=picture['resize_mode'])
        if 'cover' in self.context['request'].data:
            cover = self.context['request'].data['cover']
            instance.cover = ProfileCover.objects.create(uri_key=cover['uri_key'],
                                                         cipher=cover['cipher'],
                                                         file_size=cover['file_size'],
                                                         width=cover['width'],
                                                         height=cover['height'],
                                                         name=cover['name'],
                                                         type=cover['type'],
                                                         stick_id=self.context['request'].data['stick_id'],
                                                         resize_mode=cover['resize_mode'])
        if 'cover_id' in data.keys():
            if instance.cover != None:
                instance.cover.delete()
            instance.cover = data.pop('cover_id')
            instance.cover.save()
        if 'cover_resize_mode' in self.context['request'].data:
            if instance.cover != None:
                instance.cover.resize_mode = self.context['request'].data['cover_resize_mode']
                instance.cover.save()
        if 'pp_resize_mode' in self.context['request'].data:
            if instance.profile_picture != None:
                instance.profile_picture.resize_mode = self.context['request'].data['pp_resize_mode']
                instance.profile_picture.save()
        if 'status' in data.keys():
            stick_id = self.context['request'].data['stick_id']
            if instance.status:
                instance.status.text = data.pop('status')['text']
                instance.status.stick_id = stick_id
                instance.status.user = self.context['request'].user
                instance.status.save()
            else:
                instance.status = Cipher.objects.create(text=data.pop('status')['text'],
                                                        stick_id=stick_id,
                                                        user=self.context['request'].user)

        if 'birth_day' in data.keys():
            stick_id = self.context['request'].data['stick_id']
            if instance.birth_day:
                instance.birth_day.text = data.pop('birth_day')['text']
                instance.birth_day.stick_id = stick_id
                instance.birth_day.user = self.context['request'].user
                instance.birth_day.save()
            else:
                instance.birth_day = Cipher.objects.create(text=data.pop('birth_day')['text'],
                                                           stick_id=stick_id,
                                                           user=self.context['request'].user)

        if 'website_link' in data.keys():
            instance.website_link = data.pop('website_link')
        instance.save()

        # UPDATE CHAIN STEP
        if 'stick_id' in self.context['request'].data:
            stick_id = self.context['request'].data['stick_id']
            party_id = stick_id[:36]
            chain_id = stick_id[36:]
            key = EncryptionSenderKey.objects.get(party_id=party_id, chain_id=chain_id,
                                                  user=self.context['request'].user)
            key.step = self.context['request'].data['chain_step']
            key.save()
        return instance

    def get_images_count(self, obj):
        return obj.images.filter(group__isnull=False).count()

    def get_shared_count(self, obj):
        return obj.images.filter(group__isnull=True).count()

    def get_photos_count(self, obj):
        return Blob.objects.filter(image__user=obj).count()

    def get_notes_count(self, obj):
        return obj.notes.count()

    def get_albums_count(self, obj):
        return obj.albums.count()

    def get_invitations_count(self, obj):
        return obj.invitations.count()

    def get_cr_count(self, obj):
        return obj.connection_requests.count()

    def get_blocked_ids(self, obj):
        ids = []
        for user in obj.blocked.all():
            ids.append(user.id)
        return ids

    def get_has_password(self, obj):
        return obj.password != None

    def get_has_password_key(self, obj):
        return obj.password_key != None

    # Push Notification Tokens device ids
    def get_pnt_devices(self, obj):
        devices = []
        tokens = obj.pn_tokens.all()
        for token in tokens:
            devices.append(token.device_id)
        return devices

    def get_party_id(self, obj):
        if obj.has_party():
            party = obj.parties.get(individual=False)
            return party.id
        return None

    def get_room_id(self, obj):
        if obj.has_party():
            party = obj.parties.get(individual=True)
            return party.id
        return None

    def get_group_requests(self, obj):
        requests = GroupRequest.objects.filter(user=obj)
        group_requests = []
        for request in requests:
            group_requests.append({'id': request.group.id, 'display_name': request.display_name.text,
                                   'stick_id': request.display_name.stick_id})
        return group_requests
