import os
from rest_framework import permissions

from sticknet import settings
from users.models import LimitedAccessToken
from knox.crypto import hash_token

from django.utils.timesince import timesince

class ServerAdminPermission():
    def has_permission(self, request, view):
        request_token = request.META['HTTP_AUTHORIZATION'].split()[-1]
        admin_token = os.environ['SERVER_ADMIN_TOKEN_DEBUG'] if settings.DEBUG else os.environ['SERVER_ADMIN_TOKEN_PROD']
        return request_token == admin_token

class LimitedAccessPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        token = request.META['HTTP_AUTHORIZATION']
        if 'phone' in request.data and request.data['phone'] != None:
            auth_id = request.data['phone']
        else:
            auth_id = request.data['email'].lower()
        limited_access_token = LimitedAccessToken.objects.get(auth_id=auth_id)

        is_valid = is_token_valid(limited_access_token.timestamp)
        if not is_valid:
            limited_access_token.delete()
            return False
        hashed_token = hash_token(token, limited_access_token.salt)
        verified = hashed_token == limited_access_token.hash
        if not verified:
            limited_access_token.delete()
        return verified


def is_token_valid(timestamp):
    age = timesince(timestamp)
    l = age.split('\xa0')
    if l[1] != 'minutes' and l[1] != 'minute':
        return False
    return True

