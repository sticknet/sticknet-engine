import traceback

from rest_framework import status
from rest_framework.utils import json
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response

from groups.models import Group
from sticknet.permissions import ServerAdminPermission
from users.models import User
from .models import PNToken
from stick_protocol.models import EncryptionSenderKey

from firebase_admin import messaging

import requests


# multicastChannels = ['message_channel', 'post_channel', 'album_channel'], and sometimes group_channel

class PushNotification(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data['data']

        # UPDATE CHAIN STEP
        if 'chain_step' in request.data:
            stick_id = data['stick_id']
            party_id = stick_id[:36]
            chain_id = stick_id[36:]
            key = EncryptionSenderKey.objects.get(party_id=party_id, chain_id=chain_id, user=request.user)
            key.step = request.data['chain_step']
            key.save()

        android_config = messaging.AndroidConfig(priority='high')
        aps = messaging.Aps(content_available=True, sound='default', mutable_content=True)
        apns_payload = messaging.APNSPayload(aps=aps)
        apns_config = messaging.APNSConfig(payload=apns_payload)
        notification = messaging.Notification(title=data['title'], body=data['body'])

        if 'to_user' in request.data:
            users = request.data['to_user']

        if data['channel_id'] == 'request_channel':
            if 'group_id' in data:
                group = Group.objects.get(id=data['group_id'])
                users = group.admins.all()

        users = list(set(users))
        for user_id in users:
            if user_id != request.user.id:
                if isinstance(user_id, str):
                    try:
                        user = User.objects.get(id=user_id)
                    except:
                        continue
                else:
                    user = user_id
                    if user.id == request.user.id:
                        continue
                sendPN(user, data, notification, android_config, apns_config)
        return Response(status=status.HTTP_200_OK)


class PushNotificationMulticast(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data['data']

        # UPDATE CHAIN STEP
        if 'chain_step' in request.data:
            stick_id = data['stick_id']
            party_id = stick_id[:36]
            chain_id = stick_id[36:]
            key = EncryptionSenderKey.objects.get(party_id=party_id, chain_id=chain_id, user=request.user)
            key.step = request.data['chain_step']
            key.save()

        android_config = messaging.AndroidConfig(priority='high')
        aps = messaging.Aps(content_available=True, sound='default', mutable_content=True)
        apns_payload = messaging.APNSPayload(aps=aps)
        apns_config = messaging.APNSConfig(payload=apns_payload)
        notification = messaging.Notification(title=data['title'], body=data['body'])

        users = []
        if 'to_user' in request.data:
            users = request.data['to_user']

        tokens, apns_tokens = [], []
        users = list(set(users))
        for user_id in users:
            if user_id != request.user.id:
                if isinstance(user_id, str):
                    try:
                        user = User.objects.get(id=user_id)
                    except:
                        continue
                else:
                    user = user_id
                    if user.id == request.user.id:
                        continue
                for token in user.pn_tokens.all():
                    tokens.append(token.fcm_token)
                    if token.platform == 'ios':
                        apns_tokens.append(token.fcm_token)
        sendMulticastPN(tokens, apns_tokens, data, notification, android_config, apns_config)
        return Response(status=status.HTTP_200_OK)


class CustomPushNotification(APIView):
    """
{"data": {"title": "title",
          "body": "body",
          "channelId": "other_channel"}}
    """
    permission_classes = [ServerAdminPermission]

    def post(self, request):
        data = request.data['data']
        android_config = messaging.AndroidConfig(priority='high')
        aps = messaging.Aps(content_available=True, sound='default', mutable_content=True)
        apns_payload = messaging.APNSPayload(aps=aps)
        apns_config = messaging.APNSConfig(payload=apns_payload)
        notification = messaging.Notification(title=data['title'], body=data['body'])
        tokens, apns_tokens = [], []
        for user in User.objects.all():
            for token in user.pn_tokens.all():
                tokens.append(token.fcm_token)
                if token.platform == 'ios':
                    apns_tokens.append(token.fcm_token)
        sendMulticastPN(tokens, apns_tokens, data, notification, android_config, apns_config)
        return Response(status=status.HTTP_200_OK)


def sendMulticastPN(tokens, apns_tokens, data, notification, android_config, apns_config):
    message = messaging.MulticastMessage(
        tokens=tokens,
        data=data,
        android=android_config
    )
    messaging.send_multicast(message)
    apnsMessage = messaging.MulticastMessage(
        tokens=apns_tokens,
        data=data,
        notification=notification,
        apns=apns_config
    )
    messaging.send_multicast(apnsMessage)
    return


def sendPN(user, data, notification, android_config, apns_config):
    # send the notification to all user's devices
    for token in user.pn_tokens.all():
        message = messaging.Message(
            data=data,
            android=android_config,
            token=token.fcm_token
        )
        try:
            messaging.send(message)
        except Exception:
            if 'Requested entity was not found' in traceback.format_exc():
                token.delete()
            continue

        # ios BACKGROUND/KILLED notification
        if token.platform == 'ios':
            apnsMessage = messaging.Message(
                data=data,
                notification=notification,
                apns=apns_config,
                token=token.fcm_token
            )
            try:
                messaging.send(apnsMessage)
            except Exception:
                if 'Requested entity was not found' in traceback.format_exc():
                    token.delete()
                continue
    return


class SetPushToken(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        current_token = PNToken.objects.filter(device_id=data['device_id'])
        if not current_token:
            PNToken.objects.create(fcm_token=data['fcm_token'], platform=data['platform'], device_id=data['device_id'],
                                   user=request.user)
        else:
            current_token.update(fcm_token=data['fcm_token'], user=request.user)
        return Response(status=status.HTTP_200_OK)
