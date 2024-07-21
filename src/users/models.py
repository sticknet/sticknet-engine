import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from django.db.models import Q
from knox.models import AuthToken

from custom_storages import S3
from sticknet.settings import DEFAULT_APP, FIREBASE_REF, FIREBASE_REF_DEV, TESTING
from firebase_admin import db, auth

from groups.models import Group, Cipher
from sticknet.settings import DEBUG

class ProfilePicture(models.Model):
    uri = models.FileField(upload_to='ProfilePictures/')
    self_uri = models.FileField(upload_to='SelfProfilePictures/', blank=True, null=True)
    uri_key = models.CharField(unique=True, blank=True, null=True, max_length=36)
    self_uri_key = models.CharField(unique=True, blank=True, null=True, max_length=36)
    cipher = models.CharField(max_length=1000, default='')
    self_cipher = models.CharField(max_length=1000, default='', blank=True, null=True)
    file_size = models.IntegerField(default=0)
    stick_id = models.CharField(max_length=100, default='')
    resize_mode = models.CharField(max_length=100, default='cover', blank=True, null=True)
    width = models.IntegerField(default=1000)
    height = models.IntegerField(default=1000)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    preview_uri_key = models.CharField(unique=True, blank=True, null=True, max_length=36)
    preview_cipher = models.CharField(blank=True, null=True, max_length=1000)
    preview_file_size = models.IntegerField(default=0)
    name = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return str(self.id)

    def delete(self, using=None, keep_parents=False):
        if self.uri_key:
            S3().delete_file(self.uri_key)
        if self.preview_uri_key:
            S3().delete_file(self.preview_uri_key)
        if self.self_uri_key:
            S3().delete_file(self.self_uri_key)
        super(ProfilePicture, self).delete(using, keep_parents)


class ProfileCover(models.Model):
    uri = models.FileField(upload_to='ProfileCovers/')
    uri_key = models.CharField(unique=True, blank=True, null=True, max_length=36)
    cipher = models.CharField(max_length=1000)
    file_size = models.IntegerField(default=0)
    stick_id = models.CharField(max_length=100)
    resize_mode = models.CharField(max_length=100, default='cover')
    width = models.IntegerField(default=1000)
    height = models.IntegerField(default=1000)
    name = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return str(self.id)


    def delete(self, using=None, keep_parents=False):
        if self.uri_key:
            S3().delete_file(self.uri_key)
        super(ProfileCover, self).delete(using, keep_parents)

class LimitedAccessToken(models.Model):
    """
    After a user verified their phone number, a LimitedAccessToken object associated with that user's phone number should
    be created and returned to the user. This token should be used to authorize Login, Register and UploadPreKeyBundle
    requests.
    """
    hash = models.CharField(max_length=128, primary_key=True)
    salt = models.CharField(max_length=16, unique=True)
    auth_id = models.CharField(unique=True, max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.auth_id



test_numbers = ['+971551111110', '+971551111111', '+971551111112', '+971551111113', '+971551111114',
            '+971551111115', '+971551111116', '+971551111117', '+971551111118', '+16501119999']

COLOR_CHOICES = (
    ('rgb(255,0,0)', 'red'), ('rgb(0,0,255)', 'blue'), ('rgb(0,128,0)', 'green'), ('rgb(255,165,0)', 'orange'), ('rgb(128,0,128)', 'purple'),
    ('rgb(50,205,50)', 'limegreen'), ('rgb(255,20,147)', 'deeppink'), ('rgb(139,0,0)', 'darkred'), ('rgb(0,191,255)', 'deepskyblue'),
    ('rgb(147,112,219)', 'mediumpurple'))

BACKUP_CHOICES = (('never', 'never'), ('weekly', 'weekly'))

SUBSCRIPTION_CHOICES = (('basic', 'Basic'), ('premium', 'Premium'))

PHOTO_BACKUP_CHOICES = (('all', 'all'), ('new', 'new'))
FOLDER_ICON_CHOICES = (('blue', 'blue'), ('yellow', 'yellow'), ('orange', 'orange'))
PLATFORM_CHOICES = (('ios', 'ios'), ('android', 'android'))

class EmailVerification(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    trials = models.IntegerField(default=0)
    block_time = models.DateTimeField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class User(AbstractUser):
    id = models.CharField(primary_key=True, unique=True, max_length=1000)
    one_time_id = models.CharField(max_length=1000, blank=True, null=True)
    local_id = models.IntegerField(blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=30, blank=True, null=True)
    password = models.CharField(max_length=1000, blank=True, null=True)
    password_salt = models.CharField(max_length=44, blank=True, null=True)
    phone = models.CharField(unique=True, max_length=50, blank=True, null=True)
    phone_hash = models.CharField(unique=True, max_length=44, blank=True, null=True)
    connections = models.ManyToManyField('User', blank=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    dial_code = models.CharField(max_length=5, blank=True, null=True)
    profile_picture = models.OneToOneField(ProfilePicture, on_delete=models.SET_NULL, blank=True, null=True)
    cover = models.OneToOneField(ProfileCover, on_delete=models.SET_NULL, blank=True, null=True)
    status = models.ForeignKey(Cipher, on_delete=models.SET_NULL, blank=True, null=True, related_name='users_statuses')
    name = models.CharField(max_length=23, blank=True, null=True)
    birth_day = models.ForeignKey(Cipher, on_delete=models.SET_NULL, blank=True, null=True,
                                  related_name='users_birth_days')
    birth_day_hidden = models.BooleanField(default=False)
    groups = models.ManyToManyField(Group, blank=True)
    invited_groups = models.ManyToManyField(Group, blank=True, related_name='invited_members')
    email = models.EmailField(_('email address'), blank=True, null=True)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, blank=True, null=True)
    password_trials = models.IntegerField(default=0)
    password_block_time = models.DateTimeField(blank=True, null=True)
    blocked = models.ManyToManyField('User', related_name='blocked_by', blank=True)
    hidden_images = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True)
    next_pre_key_id = models.IntegerField(default=0)
    finished_registration = models.BooleanField(default=False)
    highlights_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True)
    categories = models.ForeignKey(Cipher, on_delete=models.SET_NULL, blank=True, null=True, related_name='categories')
    chat_backup = models.ForeignKey(Cipher, on_delete=models.SET_NULL, blank=True, null=True, related_name='chat_backup')
    backup_frequency = models.CharField(max_length=20, choices=BACKUP_CHOICES, blank=True, null=True)
    website_link = models.CharField(max_length=100, blank=True, null=True)
    password_key = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    subscription = models.CharField(max_length=100, choices=SUBSCRIPTION_CHOICES, default='basic')
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, blank=True, null=True)
    subscription_expiring = models.BooleanField(default=False)
    vault_storage = models.BigIntegerField(default=0)
    chat_storage = models.BigIntegerField(default=0)
    whitelist_premium = models.BooleanField(default=False)

    def __str__(self):
        return str(self.username) + ' - ' + str(self.email or self.phone)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4()
        super(User, self).save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        # TODO: delete firebase user
        if not TESTING:
            firebase_ref = FIREBASE_REF_DEV if DEBUG else FIREBASE_REF
            db.reference('users/' + str(self.id), DEFAULT_APP, firebase_ref).delete()
            try:
                user = auth.get_user_by_email(self.email)
                auth.delete_user(user.uid)
            except:
                print('no firebase user')
        if self.profile_picture:
            self.profile_picture.delete()
        if self.cover:
            self.cover.delete()
        for file in self.files.all():
            file.delete()
        for file in self.chat_files.all():
            file.delete()
        for file in self.chat_audios.all():
            file.delete()
        super(User, self).delete(using, keep_parents)

    def get_groups(self):
        return self.groups.all()

    def get_groups_ids(self):
        ids = []
        for group in self.groups.all():
            ids.append(group.id)
        return ids

    def storage_used(self):
        return self.vault_storage + self.chat_storage

    def get_connections_parties_ids(self):  # todo exclude maybe redundant
        if not DEBUG:
            connections = User.objects.filter(
                Q(groups__in=self.groups.all()) | Q(connections__in=[self])).distinct().exclude(
                Q(id=self.id) | Q(is_active=False) | Q(finished_registration=False) | Q(phone__in=test_numbers))
        else:
            connections = User.objects.filter(
                Q(groups__in=self.groups.all()) | Q(connections__in=[self])).distinct().exclude(
                Q(id=self.id) | Q(is_active=False) | Q(finished_registration=False))
        ids = []
        for connection in connections:
            ids.append(connection.parties.get(individual=False).id)
        return ids

    def chat_parties(self):
        return self.party_connections.all() | self.parties.filter(individual=True)

    def has_party(self):
        has_party = False
        try:
            has_party = (self.parties.all().count() > 0)
        except:
            pass
        return has_party

    def get_all_connections(self): # phone update
        connections = self.connections.all().exclude(
            Q(id=self.id) | Q(is_active=False) | Q(finished_registration=False) |
            Q(id__in=self.blocked.all()) |
            Q(blocked__in=[self])
        )
        return connections

    def get_connections_ids(self): # contacts update
        connections = User.objects.filter(
            Q(groups__in=self.groups.all()) | Q(connections__in=[self])).distinct().exclude(
            Q(id=self.id) | Q(is_active=False) | Q(finished_registration=False) |
            Q(id__in=self.blocked.all()) |
            Q(blocked__in=[self])
        ).only('id')
        ids = []
        for connection in connections:
            ids.append(connection.id)
        return ids

class Device(models.Model):
    device_id = models.CharField(max_length=1000)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='devices')
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    chat_id = models.CharField(max_length=1000, blank=True, null=True)
    auth_token = models.OneToOneField(AuthToken, on_delete=models.CASCADE, blank=True, null=True)

class Preferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE if DEBUG else models.PROTECT, related_name='preferences')
    chat_device = models.OneToOneField(Device, on_delete=models.SET_NULL, blank=True, null=True)
    favorites_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True)
    photo_backup_setting = models.CharField(max_length=10, choices=PHOTO_BACKUP_CHOICES, default='all')
    folder_icon = models.CharField(max_length=10, choices=FOLDER_ICON_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.user.username


class AppSettings(models.Model):
    minViableIOSVersion = models.CharField(max_length=10, blank=True, null=True)
    minViableAndroidVersion = models.CharField(max_length=10, blank=True, null=True)

