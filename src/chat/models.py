import os
from django.db import models
from custom_storages import StaticStorage
from django.core.files.storage import FileSystemStorage
from sticknet.settings import DEBUG, TESTING
from django.contrib.auth import get_user_model
from groups.models import Group, Cipher
from stick_protocol.models import Party
if not TESTING:
    from custom_storages import S3
else:
    from mock_custom_storages import S3

User = get_user_model()


def insert_counter_in_filename(file_name, counter):
    base_name, extension = os.path.splitext(file_name)
    return f"{base_name}({counter}){extension}"


class ChatAlbum(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='chat_albums')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='chat_albums', blank=True, null=True)
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='chat_albums', blank=True, null=True)
    title = models.ForeignKey(Cipher, on_delete=models.SET_NULL, blank=True, null=True, related_name='chat_albums')
    photos_count = models.IntegerField(default=0)
    videos_count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    auto_month = models.CharField(max_length=20, blank=True, null=True)

    def delete(self, using=None, keep_parents=False):
        for file in self.chatfile_set.all():
            file.delete()
        super(ChatAlbum, self).delete(using, keep_parents)


class ChatFile(models.Model):
    uri_key = models.CharField(unique=True, blank=True, null=True, max_length=36)
    preview_uri_key = models.CharField(unique=True, blank=True, null=True, max_length=36)
    name = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.BigIntegerField(default=0, blank=True, null=True)
    preview_file_size = models.IntegerField(default=0, blank=True, null=True)
    album = models.ForeignKey(ChatAlbum, on_delete=models.CASCADE, blank=True, null=True)
    is_album_cover = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='chat_files')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='chat_files', blank=True, null=True)
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='chat_files', blank=True, null=True)
    cipher = models.CharField(max_length=1000, blank=True, null=True)
    preview_cipher = models.CharField(max_length=1000, blank=True, null=True)
    created_at = models.FloatField(blank=True, null=True)
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    duration = models.FloatField(default=0)
    stick_id = models.CharField(max_length=100)
    message_id = models.CharField(max_length=20, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def delete(self, using=None, keep_parents=False):
        if self.uri_key:
            S3().delete_file(self.uri_key)
            self.user.chat_storage -= self.file_size
        if self.preview_uri_key:
            S3().delete_file(self.preview_uri_key)
            self.user.chat_storage -= self.preview_file_size
        if self.album:
            if self.duration == 0:
                self.album.photos_count -= 1
            else:
                self.album.videos_count -= 1
            self.album.save()
        super(ChatFile, self).delete(using, keep_parents)


class ChatAudio(models.Model):
    uri_key = models.CharField(unique=True, blank=True, null=True, max_length=36)
    file_size = models.IntegerField(default=0, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='chat_audios')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='chat_audios', blank=True, null=True)
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='chat_audios', blank=True, null=True)
    stick_id = models.CharField(max_length=100)
    cipher = models.CharField(max_length=1000, blank=True, null=True)
    duration = models.FloatField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def delete(self, using=None, keep_parents=False):
        if self.uri_key:
            S3().delete_file(self.uri_key)
            self.user.chat_storage -= self.file_size
        super(ChatAudio, self).delete(using, keep_parents)

#####

fs = FileSystemStorage(location='../media/', base_url='/media/')
storage = fs if DEBUG else StaticStorage()
