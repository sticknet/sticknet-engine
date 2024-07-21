from rest_framework import serializers

from .models import Album, Image, Note, Cipher, Blob
from groups.models import Group
from users.models import User
from users.serializers import UserSerializer
from groups.serializers import GroupSerializer, CipherSerializer
from notifications.push_notifications import PushNotification
from sticknet.dynamic_fields import DynamicFieldsModelSerializer
from django.db.models import Q
from stick_protocol.models import EncryptionSenderKey
from custom_storages import S3


def get_album_cover(album, request):
    # cover = Image.objects.filter(album=album, album_cover__isnull=False).first()
    # if (cover == None):
    cover = Blob.objects.filter(album_cover=album, album_cover__isnull=False).first()
    if (cover):
        cover.user = cover.image.user
        cover.stick_id = cover.image.stick_id
    cipher_noun = 'cipher'
    uri_noun = 'uri'
    cover_uri, cipher, id, user_id, name, stick_id, file_size, duration = None, None, None, None, None, None, None, None
    if (cover != None):
        if (cover.uri):
            cover_uri = request.build_absolute_uri(cover.uri.url)
            cipher = cover.cipher
        else:
            cipher_noun = 'thumb_cipher'
            uri_noun = 'thumbnail'
            cipher = cover.thumb_cipher
            cover_uri = request.build_absolute_uri(cover.thumbnail.url)
        id = cover.id
        user_id = cover.user.id
        name = cover.user.name
        stick_id = cover.stick_id
        file_size = cover.file_size
        duration = cover.duration
    return {uri_noun: cover_uri, 'id': id, cipher_noun: cipher, 'stick_id': stick_id, 'file_size': file_size,
            'duration': duration, 'user': {'id': user_id, 'name': name}}

class AlbumSerializer(DynamicFieldsModelSerializer):
    group_id = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), write_only=True)
    group = GroupSerializer(fields=('id', 'members_ids', 'owner'), read_only=True)
    title = CipherSerializer(required=False)
    description = CipherSerializer(allow_null=True, required=False)
    location = CipherSerializer(allow_null=True, required=False)
    date = CipherSerializer(allow_null=True, required=False)
    notes_count = serializers.SerializerMethodField()

    user_id = serializers.SerializerMethodField()
    name_of_user = serializers.SerializerMethodField()
    reaction = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()
    images_count = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = [
            'id',
            'title',
            'description',
            'group_id',
            'group',
            'timestamp',
            'date',
            'location',
            'notes_count',
            'user_id',
            'name_of_user',
            'reaction',
            'cover',
            'likes_count',
            'liked',
            'images_count']

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('group', 'title', 'description', 'location', 'date')
        return queryset

    def create(self, data):
        request = self.context['request']
        title = Cipher.objects.create(text=request.data['title_text'], user=request.user, stick_id=request.data['stick_id'])
        date = Cipher.objects.create(text=request.data['date_text'], user=request.user,
                                     stick_id=request.data['stick_id'])
        album = Album.objects.create(
            title=title,
            group=data['group_id'],
            date=date,
            user=self.context['request'].user
        )
        if 'description' in data:
            description = Cipher.objects.create(text=data['description']['text'], user=request.user,
                                          stick_id=request.data['stick_id'])
            album.description = description
        if 'location' in data:
            album.location = Cipher.objects.create(text=data['location']['text'], user=request.user,
                                                stick_id=request.data['stick_id'])
        album.groups.set([data['group_id']])
        album.save()
        return album

    def update(self, instance, data):
        stick_id = self.context['request'].data['stick_id']
        if 'title' in data:
            instance.title.text = data.pop('title')['text']
            instance.title.stick_id = stick_id
            instance.title.user = self.context['request'].user
            instance.title.save()
        if 'description' in data:
            if instance.description:
                instance.description.text = data.pop('description')['text']
                instance.description.stick_id = stick_id
                instance.description.user = self.context['request'].user
                instance.description.save()
            else:
                instance.description = Cipher.objects.create(text=data.pop('description')['text'],
                                                             stick_id=self.context['request'].data['stick_id'],
                                                             user=self.context['request'].user)
        if 'location' in data:
            if instance.location:
                instance.location.text = data.pop('location')['text']
                instance.location.stick_id = stick_id
                instance.location.user = self.context['request'].user
                instance.location.save()
            else:
                instance.location = Cipher.objects.create(text=data.pop('location')['text'],
                                                             stick_id=stick_id,
                                                             user=self.context['request'].user)
        if 'date' in data:
            if instance.date:
                instance.date.text = data.pop('date')['text']
                instance.date.stick_id = stick_id
                instance.date.user = self.context['request'].user
                instance.date.save()
            else:
                instance.date = Cipher.objects.create(text=data.pop('date')['text'],
                                                          stick_id=stick_id,
                                                          user=self.context['request'].user)
        instance.save()

        # UPDATE CHAIN STEP
        party_id = stick_id[:36]
        chain_id = stick_id[36:]
        key = EncryptionSenderKey.objects.get(party_id=party_id, chain_id=chain_id, user=self.context['request'].user)
        key.step = self.context['request'].data['chain_step']
        key.save()
        return instance


    def get_notes_count(self, obj):
        return obj.album_notes.all().exclude(user__is_active=False).count()

    def get_user_id(self, obj):
        return obj.user.id

    def get_name_of_user(self, obj):
        return obj.user.name


    def get_cover(self, obj):
        return get_album_cover(obj, self.context['request'])

    def get_images_count(self, obj):
        return obj.images.all().count()

    def get_likes_count(self, obj):
        return obj.likes.all().exclude(is_active=False).count()

    def get_liked(self, obj):
        return self.context['request'].user in obj.likes.all()


    def get_reaction(self, obj):
        note = Note.objects.filter(Q(user=self.context['request'].user, album=obj, is_reply=False) &
                                      (Q(reaction__isnull=False))).first()
        if note:
            return {'type': note.reaction, 'stick_id': note.stick_id}
        return None


class ImageAudioUriSerializer(serializers.ModelSerializer):

    class Meta:
        model = Image
        fields = ['audio_uri']


class BlobUriSerializer(serializers.ModelSerializer):

    class Meta:
        model = Blob
        fields = ['uri', 'thumbnail', 'video_uri']


class BlobSerializer(DynamicFieldsModelSerializer):
    id = serializers.SerializerMethodField()
    presigned_url = serializers.SerializerMethodField()
    preview_presigned_url = serializers.SerializerMethodField()

    class Meta:
        model = Blob
        fields = '__all__'

    def get_id(self, obj):
        return str(obj.id)

    def get_presigned_url(self, object):
        if not object.uri_key:
            return None
        return S3().get_file(object.uri_key)


    def get_preview_presigned_url(self, object):
        if not object.preview_uri_key:
            return None
        return S3().get_file(object.preview_uri_key)

class ImageSerializer(DynamicFieldsModelSerializer):
    user = UserSerializer(fields=('id', 'name', 'username', 'profile_picture', 'party_id', 'subscription'), read_only=True)
    album = AlbumSerializer(fields=('id', 'title', 'location', 'images_count'), read_only=True)
    notes_count = serializers.SerializerMethodField()
    album_id = serializers.PrimaryKeyRelatedField(queryset=Album.objects.all(), write_only=True, required=False,
                                                  allow_null=True)
    group_id = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), write_only=True, required=False)
    groups_ids = serializers.SerializerMethodField()
    connections_ids = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    reaction = serializers.SerializerMethodField()
    blobs = BlobSerializer(many=True, read_only=True)
    id = serializers.SerializerMethodField()


    class Meta:
        model = Image
        fields = [
            'id',
            'user',
            'uri',
            'video_uri',
            'thumbnail',
            'album',
            'album_id',
            'group_id',
            'album_cover',
            'caption',
            'location',
            'group',
            'timestamp',
            # 'groups_id',
            # 'connections_id',
            'notes_count',
            'likes_count',
            'liked',
            'reaction',
            'size',
            'groups_ids',
            'connections_ids',
            'width',
            'height',
            'duration',
            'youtube',
            'youtube_thumbnail',
            'audio_uri',
            'audio_duration',
            'cipher',
            'thumb_cipher',
            'audio_cipher',
            'stick_id',
            'party_id',
            'file_size',
            'index',
            'of_total',
            'is_profile',
            'text_photo',
            'blobs'
        ]

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('user', 'album')
        return queryset


    def update(self, instance, data):
        if 'thumbnail' in data:
            instance.thumbnail = data['thumbnail']
            instance.thumb_cipher = data['thumb_cipher']
        elif 'caption' in data:
            instance.caption = data['caption']
        elif 'location' in data:
            instance.location = data['location']
        elif 'groups_id' in data:
            instance.groups.set(data['groups_id'])
        else:
            album_id = instance.album.id
            current_cover = Image.objects.get(album=album_id, album_cover__isnull=False)
            current_cover.album_cover = None
            current_cover.save()
            album = Album.objects.get(id=album_id)
            instance.album_cover = album
        instance.save()

        # UPDATE CHAIN STEP
        if 'chain_step' in self.context['request'].data:
            stick_id = self.context['request'].data['stick_id']
            party_id = stick_id[:36]
            chain_id = stick_id[36:]
            key = EncryptionSenderKey.objects.get(party_id=party_id, chain_id=chain_id, user=self.context['request'].user)
            key.step = self.context['request'].data['chain_step']
            key.save()
        return instance

    def get_id(self, obj):
        return str(obj.id)

    def get_notes_count(self, obj):
        return obj.notes.all().exclude(user__is_active=False).count()


    def get_reaction(self, obj):
        note = Note.objects.filter(Q(user=self.context['request'].user, image=obj, is_reply=False) &
                                      (Q(reaction__isnull=False))).first()
        if note:
            return {'type': note.reaction, 'stick_id': note.stick_id}
        return None

    def get_groups_ids(self, obj):
        ids = []
        for group in obj.groups.all():
            ids.append(group.id)
        return ids

    def get_connections_ids(self, obj):
        ids = []
        for connection in obj.connections.all():
            ids.append(connection.id)
        return ids

    def get_likes_count(self, obj):
        return obj.likes.all().exclude(is_active=False).count()


    def get_liked(self, obj):
        return self.context['request'].user in obj.likes.all()

    # def get_shared_to(self, obj):
    #     if obj.album == None and obj.groups.all().count() == 1:
    #         return obj.groups.all().first().display_name_cipher
    #     return None



    # def get_likes_count(self, obj):
    #     return obj.notes.filter(reaction='H' or 'K' or 'A').count()
    #
    # def get_text_count(self, obj):
    #     return obj.notes.filter(text__isnull=False).count()
    #
    # def get_audio_count(self, obj):
    #     return obj.notes.filter(audio__isnull=False).count()


class BlobImageSerializer(DynamicFieldsModelSerializer):
    id = serializers.SerializerMethodField()
    image = ImageSerializer(fields=('id', 'user', 'album', 'caption', 'audio_uri', 'audio_duration', 'audio_cipher', 'location', 'timestamp', 'group', 'groups_ids', 'connections_ids', 'notes_count', 'likes_count', 'liked', 'reaction', 'stick_id', 'party_id', 'is_profile', 'index', 'of_total'), read_only=True)

    class Meta:
        model = Blob
        fields = '__all__'

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('image')
        return queryset

    def get_id(self, obj):
        return str(obj.id)

class ReplySerializer(serializers.ModelSerializer):
    user = UserSerializer(fields=('id', 'name', 'profile_picture'), read_only=True)
    likes_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            'id',
            'user',
            'reaction',
            'text',
            'timestamp',
            'audio',
            'duration',
            'sketch',
            'cipher',
            'stick_id',
            'file_size',
            'likes_count',
            'liked',
            'is_reply'
        ]

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('user')
        return queryset

    def get_likes_count(self, obj):
        return obj.likes.all().exclude(is_active=False).count()

    def get_liked(self, obj):
        return self.context['request'].user in obj.likes.all()




class NoteSerializer(serializers.ModelSerializer):
    replies = ReplySerializer(many=True, required=False)
    image_id = serializers.PrimaryKeyRelatedField(queryset=Image.objects.all(), required=False)
    album_id = serializers.PrimaryKeyRelatedField(queryset=Album.objects.all(), required=False)
    user = UserSerializer(fields=('id', 'name', 'profile_picture'), read_only=True)
    reply_to_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, allow_null=True,
                                                   required=False)
    reply_id = serializers.PrimaryKeyRelatedField(queryset=Note.objects.all(), write_only=True, allow_null=True,
                                                  required=False)
    likes_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            'id',
            'user',
            'reaction',
            'text',
            'audio',
            'duration',
            'sketch',
            'image_id',
            'album_id',
            'timestamp',
            'replies',
            'reply_id',
            'is_reply',
            'reply_to_id',
            'cipher',
            'stick_id',
            'file_size',
            'likes_count',
            'liked',
        ]

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('user')
        queryset = queryset.prefetch_related('replies')
        return queryset

    def create(self, data):
        if 'audio' in data:
            note = Note.objects.create(
                user=self.context['request'].user,
                audio=data['audio'],
                duration=data['duration'],
                is_reply=data['is_reply'],
                stick_id=data['stick_id']
            )
        elif 'text' in data:
            note = Note.objects.create(
                user=self.context['request'].user,
                text=data['text'],
                is_reply=data['is_reply'],
                stick_id=data['stick_id']
            )
        elif 'sketch' in data:
            note = Note.objects.create(
                user=self.context['request'].user,
                sketch=data['sketch'],
                is_reply=data['is_reply'],
                stick_id=data['stick_id']
            )
        else:
            note = Note.objects.create(
                user=self.context['request'].user,
                reaction=data['reaction'],
                is_reply=data['is_reply'],
                stick_id=data['stick_id']
            )
        if 'reply_to_id' in data:
            note.reply_to = data['reply_to_id']
            note.save()
        if 'image_id' in data:
            if 'reaction' in data and not data['is_reply']:
                oldNote = Note.objects.filter(Q(user=self.context['request'].user, image=data['image_id'], is_reply=False) &
                                              (Q(reaction__isnull=False))).first()
                if oldNote:
                    oldNote.replies.all().delete()
                    oldNote.delete()
            note.image = data['image_id']
            kwargs = {'image': data['image_id'], 'note': note}
        else:
            if 'reaction' in data and not data['is_reply']:
                oldNote = Note.objects.filter(Q(user=self.context['request'].user, album=data['album_id'], is_reply=False) &
                                              (Q(reaction__isnull=False))).first()
                if oldNote:
                    oldNote.replies.all().delete()
                    oldNote.delete()
            note.album = data['album_id']
            kwargs = {'album': data['album_id'], 'note': note}
        if 'reply_id' in data:
            data['reply_id'].replies.add(note.id)
        if 'audio' in data or 'sketch' in data:
            note.cipher = data['cipher']
            note.file_size = data['file_size']
        note.save()
        PushNotification.post(self, self.context['request'], **kwargs)
        return note

    def get_likes_count(self, obj):
        return obj.likes.all().exclude(is_active=False).count()

    def get_liked(self, obj):
        return self.context['request'].user in obj.likes.all()


# if image.duration and 'compress' in self.context['request'].data:
#     if settings.DEBUG:
#         os.system('ffmpeg -ss 0 -to 60 -i ' + image.video_uri.path + ' -c copy -f mp4 -y -codec:v libx264 -b:v 1M -maxrate 1M -bufsize 2M -vf "scale=trunc(oh*a/2)*2:720" -threads 0 -c:a copy -progress -movflags frag_keyframe+empty_moov /Users/mymac/Dev/STiiiCK/src/media/videos/' + str(image.id) + '.mp4')
#     else:
#         os.system('/opt/ffmpeg/ffmpeg-4.2.2-amd64-static/ffmpeg -ss 0 -to 60 -i ' + settings.MEDIA_PATH + str(image.video_uri) + ' -c copy -f mp4 -y -codec:v libx264 -b:v 1M -maxrate 1M -bufsize 2M -vf "scale=trunc(oh*a/2)*2:720" -threads 0 -c:a copy -preset veryfast -movflags frag_keyframe+empty_moov pipe:1 | AWS_ACCESS_KEY_ID=' + settings.AWS_ACCESS_KEY_ID + ' AWS_SECRET_ACCESS_KEY=' + settings.AWS_SECRET_ACCESS_KEY + ' aws s3 cp - s3://stiiick/media/videos/' + str(image.id) + '.mp4')
#     image.video_uri.delete()
#     image.video_uri = 'videos/' + str(image.id) + '.mp4'
#     image.save()
