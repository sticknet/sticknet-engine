from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.postgres.fields import ArrayField
from groups.models import Cipher
from custom_storages import S3


from groups.models import Group

User = get_user_model()


class Album(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='albums')
    title = models.OneToOneField(Cipher, on_delete=models.SET_NULL, blank=True, null=True, related_name='titles')
    description = models.ForeignKey(Cipher, on_delete=models.SET_NULL, blank=True, null=True, related_name='descriptions') # FK to allow null
    timestamp = models.DateTimeField(auto_now_add=True)
    date = models.ForeignKey(Cipher, on_delete=models.SET_NULL, blank=True, null=True, related_name='dates')
    location = models.ForeignKey(Cipher, on_delete=models.SET_NULL, blank=True, null=True, related_name='locations')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='album_group', blank=True, null=True)
    groups = models.ManyToManyField(Group, related_name='album_groups', blank=True)
    likes = models.ManyToManyField(User)

    def __str__(self):
        return str(self.timestamp)

    def get_notes(self):
        return self.album_notes.all().filter(album=self, is_reply=False).exclude(user__is_active=False)

    def get_absolute_url(self):
        return reverse("album:detail", kwargs={"pk": self.pk})


class ImageManager(models.Manager):

    def dislikes_count(self, image):
        return image.dislikes.all().count()

    def kisses_count(self, image):
        return image.kisses.all().count()

    def adores_count(self, image):
        return image.adores.all().count()



SIZES = (('S', 'square'), ('V', 'vertical'), ('H', 'horizontal'), ('C', 'contain'))

class Image(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='images', blank=True, null=True)
    album_cover = models.OneToOneField(Album, on_delete=models.CASCADE, related_name='cover', blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='images', blank=True, null=True)
    groups = models.ManyToManyField(Group, related_name='shared_images', blank=True)
    connections = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='connected_images', blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='images')
    video_uri = models.FileField(upload_to='videos/', blank=True, null=True)
    uri = models.FileField(upload_to='photos/', blank=True, null=True)
    audio_uri = models.FileField(upload_to='audio/images/', blank=True, null=True)
    audio_duration = models.FloatField(default=0)
    thumbnail = models.FileField(upload_to='thumbnails/', blank=True, null=True)
    youtube = models.CharField(max_length=1000, null=True, blank=True)
    youtube_thumbnail = models.CharField(max_length=1000, null=True, blank=True)
    caption = models.CharField(max_length=1000, null=True, blank=True)
    text_photo = models.CharField(max_length=1000, null=True, blank=True)
    location = models.CharField(max_length=1000, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    size = models.CharField(max_length=1, choices=SIZES, default='S')
    duration = models.FloatField(default=0)
    width = models.IntegerField(default=1000)
    height = models.IntegerField(default=1000)
    cipher = models.CharField(max_length=1000, null=True, blank=True)
    thumb_cipher = models.CharField(max_length=1000, null=True, blank=True)
    audio_cipher = models.CharField(max_length=1000, null=True, blank=True)
    stick_id = models.CharField(max_length=100)
    party_id = models.CharField(max_length=100)
    file_size = ArrayField(models.IntegerField(default=0), blank=True, null=True)
    index = models.IntegerField(default=1)
    of_total = models.IntegerField(default=1)
    is_profile = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, blank=True, related_name='image_likes')
    share_ext = models.BooleanField(default=False)
    seen_by = models.ManyToManyField(User, blank=True, related_name='image_seen_by')
    objects = ImageManager()

    def __str__(self):
        return str(self.id)

    def get_notes(self):
        return self.notes.all().filter(image=self, is_reply=False).exclude(user__is_active=False)

    def delete(self, using=None, keep_parents=False):
        super(Image, self).delete(using, keep_parents)


class Blob(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='blobs', blank=True, null=True)
    uri = models.FileField(upload_to='photos/', blank=True, null=True)
    video_uri = models.FileField(upload_to='videos/', blank=True, null=True)
    thumbnail = models.FileField(upload_to='thumbnails/', blank=True, null=True)
    uri_key = models.CharField(unique=True, blank=True, null=True, max_length=100)
    preview_uri_key = models.CharField(unique=True, blank=True, null=True, max_length=100)
    size = models.CharField(max_length=1, choices=SIZES, default='S')
    duration = models.FloatField(default=0)
    width = models.IntegerField(default=1000)
    height = models.IntegerField(default=1000)
    cipher = models.CharField(max_length=1000, null=True, blank=True)
    thumb_cipher = models.CharField(max_length=1000, null=True, blank=True)
    file_size = ArrayField(models.IntegerField(default=0), blank=True, null=True)
    album_cover = models.OneToOneField(Album, on_delete=models.CASCADE, related_name='blob_cover', blank=True, null=True)
    text_photo = models.CharField(max_length=1000, null=True, blank=True)
    youtube = models.CharField(max_length=1000, null=True, blank=True)
    youtube_thumbnail = models.CharField(max_length=1000, null=True, blank=True)


    def __str__(self):
        return str(self.id)



class Note(models.Model):
    replies = models.ManyToManyField('Note',  related_name='parent_note', blank=True)
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='notes', blank=True, null=True)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='album_notes', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='notes')
    reaction = models.CharField(max_length=1000, blank=True, null=True)
    text = models.CharField(max_length=10000, blank=True)
    audio = models.FileField(blank=True, null=True, upload_to='audio/comments/')
    duration = models.FloatField(blank=True, null=True)
    sketch = models.FileField(upload_to='sketches/', blank=True)
    uri_key = models.CharField(unique=True, blank=True, null=True, max_length=100)
    is_reply = models.BooleanField(default=False)
    reply_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    cipher = models.CharField(max_length=1000, null=True, blank=True)
    file_size = models.IntegerField(default=0)
    stick_id = models.CharField(max_length=100, blank=True, null=True)
    likes = models.ManyToManyField(User, blank=True, related_name='liked_notes')


class TestImage(models.Model):
    uri = models.FileField(upload_to='test/', blank=True, null=True)


