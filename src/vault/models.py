import os
from django.db import models
from django.contrib.auth import get_user_model
from sticknet.settings import TESTING
if not TESTING:
    from custom_storages import S3
else:
    from mock_custom_storages import S3


User = get_user_model()

FOLDER_TYPES = (('normal', 'Normal'), ('home', 'Home'), ('camera_uploads', 'Camera Uploads'))


def insert_counter_in_filename(file_name, counter):
    base_name, extension = os.path.splitext(file_name)
    return f"{base_name}({counter}){extension}"

class VaultAlbum(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='vault_albums')
    name = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

# A model that represents a file object and a folder object
class File(models.Model):
    uri_key = models.CharField(unique=True, blank=True, null=True, max_length=36)
    preview_uri_key = models.CharField(unique=True, blank=True, null=True, max_length=36)
    name = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.BigIntegerField(default=0, blank=True, null=True)
    preview_file_size = models.IntegerField(default=0, blank=True, null=True)
    folder = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True, related_name='files')
    album = models.ForeignKey(VaultAlbum, on_delete=models.PROTECT, blank=True, null=True, related_name='photos')
    is_photo = models.BooleanField(default=False)
    is_folder = models.BooleanField(default=False)
    folder_type = models.CharField(max_length=20, choices=FOLDER_TYPES, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='files')
    cipher = models.CharField(max_length=1000, blank=True, null=True)
    preview_cipher = models.CharField(max_length=1000, blank=True, null=True)
    created_at = models.FloatField(blank=True, null=True)
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    duration = models.FloatField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def delete(self, using=None, keep_parents=False):
        for file in self.files.all():
            file.delete()
        if self.uri_key:
            S3().delete_file(self.uri_key)
            self.user.vault_storage -= self.file_size
        if self.preview_uri_key:
            S3().delete_file(self.preview_uri_key)
            self.user.vault_storage -= self.preview_file_size
        self.user.save()
        super(File, self).delete(using, keep_parents)


    def save(self, *args, **kwargs):
        exists = File.objects.filter(user=self.user, folder=self.folder, name=self.name).exclude(id=self.id).exists()
        increment = 2
        file_name = self.name
        while exists:
            file_name = insert_counter_in_filename(self.name, increment)
            exists = File.objects.filter(user=self.user, folder=self.folder, name=file_name).exists()
            increment += 1
        self.name = file_name
        super(File, self).save(*args, **kwargs)


class VaultNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='vault_notes')
    cipher = models.CharField(max_length=3000)
    timestamp = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return self.name + ' - ' + self.user.username

