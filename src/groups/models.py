import uuid

from django.db import models
from django.contrib.auth import settings
from django.db.models import Q
from sticknet.settings import TESTING
if not TESTING:
    from custom_storages import S3
else:
    from mock_custom_storages import S3
from sticknet.settings import DEBUG, DEFAULT_APP, FIREBASE_REF, FIREBASE_REF_DEV, TESTING
from firebase_admin import db


User = settings.AUTH_USER_MODEL


class Cipher(models.Model):
    text = models.CharField(max_length=10000, blank=True, null=True)
    uri = models.FileField(upload_to='CipherFiles/', blank=True, null=True)
    file_size = models.IntegerField(default=0, blank=True, null=True)
    text_length = models.IntegerField(default=0, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='ciphers')
    stick_id = models.CharField(max_length=1000, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)

class GroupCover(models.Model):
    stick_id = models.CharField(max_length=100)
    uri = models.FileField(upload_to='GroupsCovers/')
    resize_mode = models.CharField(max_length=100, default='cover')
    cipher = models.CharField(max_length=1000)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    file_size = models.IntegerField(default=0)
    width = models.IntegerField(default=1000)
    height = models.IntegerField(default=1000)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    uri_key = models.CharField(unique=True, blank=True, null=True, max_length=36)
    preview_uri_key = models.CharField(unique=True, blank=True, null=True, max_length=36)
    preview_cipher = models.CharField(blank=True, null=True, max_length=1000)
    preview_file_size = models.IntegerField(default=0)
    name = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)

    def delete(self, using=None, keep_parents=False):
        if self.uri_key:
            S3().delete_file(self.uri_key)
        if self.preview_uri_key:
            S3().delete_file(self.preview_uri_key)
        super(GroupCover, self).delete(using, keep_parents)

class GroupManager(models.Manager):

    def members(self, group):
        return group.user_set.all()


class Group(models.Model):
    id = models.CharField(primary_key=True, unique=True, max_length=1000)
    chat_id = models.CharField(unique=True, max_length=1000)
    display_name = models.ForeignKey(Cipher, on_delete=models.SET_NULL, blank=True, null=True, related_name='display_names')
    status = models.ForeignKey(Cipher, on_delete=models.SET_NULL, blank=True, null=True, related_name='statuses')
    cover = models.OneToOneField(GroupCover, on_delete=models.SET_NULL, blank=True, null=True, related_name='group')
    owner = models.ForeignKey(User, on_delete=models.CASCADE if DEBUG else models.PROTECT, blank=True, null=True, related_name='group_owner')
    admins = models.ManyToManyField(User, blank=True, related_name='group_admin')
    verification_id = models.CharField(max_length=1000, blank=True, null=True)
    link = models.ForeignKey(Cipher, on_delete=models.SET_NULL, blank=True, null=True,
                                     related_name='group_links')
    link_enabled = models.BooleanField(default=False)
    link_approval = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(blank=True, null=True)
    storage = models.IntegerField(default=0)
    objects = GroupManager()

    def delete(self, using=None, keep_parents=False):
        if not TESTING:
            firebase_ref = FIREBASE_REF_DEV if DEBUG else FIREBASE_REF
            db.reference('rooms/' + str(self.id), DEFAULT_APP, firebase_ref).delete()
        if self.cover:
            self.cover.delete()
        super(Group, self).delete(using, keep_parents)

    def save(self, *args, **kwargs):
        if not self.chat_id:
            # self.id = uuid.uuid4()
            self.chat_id = uuid.uuid4()
        super(Group, self).save(*args, **kwargs)

    def __str__(self):
        return  str(self.timestamp) + ' - ' + self.id

    def get_members(self):
        members = self.user_set.all().exclude(Q(is_active=False) | Q(finished_registration=False))
        return members

    def get_invited_members(self):
        invited_members = self.invited_members.all().exclude(Q(is_active=False) | Q(finished_registration=False))
        return invited_members

    def get_members_ids(self):
        members = self.user_set.all().exclude(Q(is_active=False) | Q(finished_registration=False))
        members_ids=[]
        for member in members:
            members_ids.append(member.id)
        return members_ids

    def get_members_otids(self):
        members = self.user_set.all().exclude(Q(is_active=False) | Q(finished_registration=False))
        members_ids=[]
        for member in members:
            members_ids.append(member.one_time_id)
        return members_ids

    def get_all_users_ids(self):
        members = self.user_set.all().exclude(Q(is_active=False) | Q(finished_registration=False))
        invited_members = self.invited_members.all().exclude(is_active=False)
        users_ids=[]
        for member in members:
            users_ids.append(member.id)
        for member in invited_members:
            users_ids.append(member.id)
        return users_ids

    def get_all_users_ids_and_otids(self):
        members = self.user_set.all().exclude(Q(is_active=False) | Q(finished_registration=False))
        invited_members = self.invited_members.all().exclude(is_active=False)
        users_ids=[]
        for member in members:
            users_ids.append({'id': member.id, 'one_time_id': member.one_time_id})
        for member in invited_members:
            users_ids.append({'id': member.id, 'one_time_id': member.one_time_id})
        return users_ids

    def get_members_count(self):
        return self.user_set.all().exclude(is_active=False).count()


class TempDisplayName(models.Model):
    stick_id = models.CharField(max_length=100)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='tdn')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='my_tdn')
    cipher = models.CharField(max_length=1000)


class GroupRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_requests')
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    display_name = models.OneToOneField(Cipher, on_delete=models.SET_NULL, blank=True, null=True,
                                        related_name='request_display_names')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)
