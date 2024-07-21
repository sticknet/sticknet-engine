import os
from django.db import models
from django.contrib.auth import get_user_model
from photos.models import Image
from sticknet.settings import DEBUG
from custom_storages import PublicStorage
from django.core.files.storage import FileSystemStorage

User = get_user_model()


class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField(blank=True, null=True)
    text = models.CharField(max_length=10000)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField(blank=True, null=True)
    text = models.CharField(max_length=10000)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class Question(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    email = models.EmailField(blank=True, null=True)
    text = models.CharField(max_length=10000)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class Error(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    string = models.CharField(max_length=10000)
    native = models.BooleanField(default=False)
    is_fatal = models.BooleanField(default=True, blank=True, null=True)
    PLATFORMS = (('I', 'ios'), ('A', 'android'))
    platform = models.CharField(max_length=1, choices=PLATFORMS, default='I')
    model = models.CharField(max_length=100)
    system_version = models.CharField(max_length=50)
    app_version = models.CharField(max_length=50)
    screen = models.CharField(max_length=30, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.timestamp)

class UserReport(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_reports')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reports')
    REASONS = (('A', 'Fake account'), ('B', 'Posting inappropriate things'), ('C', 'Harassment or Bullying'), ('Z', 'Something else'))
    reason = models.CharField(max_length=1, choices=REASONS)
    timestamp = models.DateTimeField(auto_now=True)


class PostReport(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_post_reports')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_post_reports')
    post = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='reports', blank=True, null=True)
    REASONS = (('A', 'Fake account'), ('B', 'Posting inappropriate things'), ('C', 'Harassment or Bullying'), ('Z', 'Something else'))
    reason = models.CharField(max_length=1, choices=REASONS)
    timestamp = models.DateTimeField(auto_now=True)


fs = FileSystemStorage(location=os.environ['LOCAL_PUBLIC_STORAGE'], base_url='/public/')
storage = fs if DEBUG else PublicStorage()


class PublicFile(models.Model):
    name = models.CharField(max_length=100)
    uri = models.FileField(upload_to='PDFs/', storage=storage)
