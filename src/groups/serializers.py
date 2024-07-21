from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Group, GroupCover, TempDisplayName, Cipher, GroupRequest
from sticknet.dynamic_fields import DynamicFieldsModelSerializer
from stick_protocol.models import EncryptionSenderKey
from photos.models import Image
from custom_storages import S3

User = get_user_model()


class CipherSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    name_of_user = serializers.SerializerMethodField()

    class Meta:
        model = Cipher
        fields = ['id', 'text', 'stick_id', 'user_id', 'name_of_user', 'uri', 'file_size', 'text_length']

    def get_user_id(self, obj):
        return obj.user.id

    def get_name_of_user(self, obj):
        return obj.user.name


class GroupCoverSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    presigned_url = serializers.SerializerMethodField()
    preview_presigned_url = serializers.SerializerMethodField()

    class Meta:
        model = GroupCover
        fields = '__all__'

    def create(self, data):
        cover = GroupCover.objects.create(stick_id=data['stick_id'], uri=data["uri"], file_size=data['file_size'],
                                          resize_mode=data['resize_mode'], cipher=data["cipher"], width=data['width'],
                                          height=data['height'],
                                          user=self.context["request"].user)
        return cover

    def get_user(self, obj):
        return {"id": obj.user.id, "name": obj.user.name}

    def get_presigned_url(self, object):
        if not object.uri_key:
            return None
        return S3().get_file(object.uri_key)

    def get_preview_presigned_url(self, object):
        if not object.preview_uri_key:
            return None
        return S3().get_file(object.preview_uri_key)


class GroupSerializer(DynamicFieldsModelSerializer):
    cover = GroupCoverSerializer(read_only=True)
    cover_id = serializers.PrimaryKeyRelatedField(queryset=GroupCover.objects.all(), write_only=True, required=False)
    admin_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, required=False)
    display_name = CipherSerializer()
    status = CipherSerializer(required=False)
    link = CipherSerializer(required=False)
    members_count = serializers.SerializerMethodField()
    members_ids = serializers.SerializerMethodField()
    members_otids = serializers.SerializerMethodField()
    members_all_ids = serializers.SerializerMethodField()
    temp_display_name = serializers.SerializerMethodField()
    has_shared_photos = serializers.SerializerMethodField()
    requests_count = serializers.SerializerMethodField()
    new_posts_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id',
            'chat_id',
            'display_name',
            'status',
            'link',
            'link_approval',
            'link_enabled',
            'cover',
            'admins',
            'owner',
            'cover_id',
            'admin_id',
            'members_count',
            'members_ids',
            'members_otids',
            'members_all_ids',
            'temp_display_name',
            'has_shared_photos',
            'requests_count',
            'timestamp',
            'new_posts_count',
            'last_activity'
        ]
        extra_kwargs = {'chat_id': {'read_only': True}}

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('cover', 'display_name', 'status', 'link')
        return queryset

    def create(self, data):
        stick_id = data['id'] + '0'
        user = self.context['request'].user
        added_users = self.context['request'].data['added_users']
        invited_users = self.context['request'].data['invited_users']
        display_name = Cipher.objects.create(text=data['display_name']['text'], user=user, stick_id=stick_id)
        group = Group.objects.create(id=data['id'], display_name=display_name, owner=user)
        # TODO: cover_id to be removed
        if 'cover_id' in data:
            group.cover = data["cover_id"]
        if 'cover' in self.context['request'].data:
            cover = self.context['request'].data['cover']
            group.cover = GroupCover.objects.create(uri_key=cover['uri_key'],
                                                    preview_uri_key=cover['preview_uri_key'],
                                                    cipher=cover['cipher'],
                                                    preview_cipher=cover['preview_cipher'],
                                                    file_size=cover['file_size'],
                                                    preview_file_size=cover['preview_file_size'],
                                                    width=cover['width'],
                                                    height=cover['height'],
                                                    name=cover['name'],
                                                    type=cover['type'],
                                                    stick_id=stick_id,
                                                    resize_mode=cover['resize_mode'],
                                                    user=user)
        group.admins.add(user)
        user.groups.add(group)
        user.connections.add(*added_users)
        for user_id in added_users:
            added_user = User.objects.get(id=user_id)
            added_user.groups.add(group)
            added_user.connections.add(*added_users)
            added_user.connections.remove(added_user)
        for user_id in invited_users:
            invited_user = User.objects.get(id=user_id)
            invited_user.invited_groups.add(group)
        group.save()
        return group

    def update(self, instance, data):
        stick_id = self.context['request'].data['stick_id']
        if 'display_name' in data.keys():
            instance.display_name.text = data.pop('display_name')['text']
            instance.display_name.stick_id = stick_id
            instance.display_name.user = self.context['request'].user
            instance.display_name.save()
        if 'status' in data.keys():
            if instance.status:
                instance.status.text = data.pop('status')['text']
                instance.status.stick_id = stick_id
                instance.status.user = self.context['request'].user
                instance.status.save()
            else:
                instance.status = Cipher.objects.create(text=data.pop('status')['text'],
                                                        stick_id=stick_id,
                                                        user=self.context['request'].user)
        if 'cover_id' in data.keys():
            if instance.cover != None:
                instance.cover.delete()
            instance.cover = data.pop('cover_id')
            instance.cover.save()
        if 'cover' in self.context['request'].data:
            if instance.cover != None:
                instance.cover.delete()
            cover = self.context['request'].data['cover']
            instance.cover = GroupCover.objects.create(uri_key=cover['uri_key'],
                                                       preview_uri_key=cover['preview_uri_key'],
                                                       cipher=cover['cipher'],
                                                       preview_cipher=cover['preview_cipher'],
                                                       file_size=cover['file_size'],
                                                       preview_file_size=cover['preview_file_size'],
                                                       width=cover['width'],
                                                       height=cover['height'],
                                                       name=cover['name'],
                                                       type=cover['type'],
                                                       stick_id=stick_id,
                                                       resize_mode=cover['resize_mode'],
                                                       user=self.context['request'].user)
        if 'resize_mode' in self.context['request'].data:
            if instance.cover != None:
                instance.cover.resize_mode = self.context['request'].data['resize_mode']
                instance.cover.save()

        # UPDATE CHAIN STEP
        party_id = stick_id[:36]
        chain_id = stick_id[36:]
        key = EncryptionSenderKey.objects.get(party_id=party_id, chain_id=chain_id, user=self.context['request'].user)
        key.step = self.context['request'].data['chain_step']
        key.save()
        instance.save()
        return instance

    def get_members_count(self, obj):
        return obj.user_set.count()

    def get_members_ids(self, obj):
        return obj.get_members_ids()

    def get_members_otids(self, obj):
        return obj.get_members_otids()

    def get_members_all_ids(self, obj):
        return obj.get_all_users_ids_and_otids()

    def get_temp_display_name(self, obj):
        if not 'request' in self.context:
            return None
        temp_display_name = TempDisplayName.objects.filter(group=obj, to_user=self.context['request'].user).first()
        if temp_display_name:
            return {'text': temp_display_name.cipher, 'stick_id': temp_display_name.stick_id,
                    'member_id': temp_display_name.from_user.id}
        return None

    def get_has_shared_photos(self, obj):
        return Image.objects.filter(groups__in=[obj], album__isnull=True).count() > 0

    def get_requests_count(self, obj):
        if not 'request' in self.context:
            return 0
        if not self.context['request'].user in obj.admins.all():
            return 0
        group_requests = GroupRequest.objects.filter(group=obj)
        return group_requests.count()

    # VIP TODO: to be removed
    def get_new_posts_count(self, obj):
        return 0
