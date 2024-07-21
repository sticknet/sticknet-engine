from django.db import models
from django.contrib.auth import get_user_model

from photos.models import Image, Note, Album
from groups.models import Group, Cipher


User = get_user_model()


class PNToken(models.Model):
    fcm_token = models.CharField(max_length=500, null=True)
    device_id = models.CharField(max_length=100, null=True)
    PLATFORMS = (('ios', 'ios'), ('android', 'android'))
    platform = models.CharField(max_length=10, choices=PLATFORMS, default='android')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pn_tokens', null=True)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)

class Notification(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_sent', null=True)
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True)
    body = models.CharField(max_length=1000)
    image = models.ForeignKey(Image, on_delete=models.CASCADE, blank=True, null=True, related_name='notification')
    shared_photos = models.ManyToManyField(Image, blank=True, related_name='share_notification')
    album = models.ForeignKey(Album, on_delete=models.CASCADE, blank=True, null=True)
    note = models.ForeignKey(Note,on_delete=models.CASCADE, blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    read = models.BooleanField(default=False)
    stick_id = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    channel = models.CharField(max_length=100)
    is_like = models.BooleanField(default=False)


    def __str__(self):
        return str(self.id)


class Invitation(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations')
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    display_name = models.OneToOneField(Cipher, on_delete=models.SET_NULL, blank=True, null=True, related_name='invitation_display_names')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class ConnectionRequest(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connection_requests')
    timestamp = models.DateTimeField(auto_now_add=True)
