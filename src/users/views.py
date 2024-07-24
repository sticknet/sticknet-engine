import random, re, names
from random import randrange

from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives

from rest_framework import generics, viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from knox.crypto import create_token_string, hash_token, create_salt_string

from firebase_admin import auth
from django.utils import timezone

from .serializers import UserSerializer, UserPublicSerializer, UserBaseSerializer, UserConnectionSerializer, \
    ProfilePictureSerializer, ProfileCoverSerializer
from .models import ProfilePicture, User, ProfileCover, LimitedAccessToken, Device, Preferences, AppSettings, \
    EmailVerification
from photos.models import Image, Blob
from vault.models import File
from stick_protocol.models import PreKey, EncryptionSenderKey
from photos.pagination import DynamicPagination
from groups.models import Cipher, Group
from notifications.models import ConnectionRequest
from sticknet.settings import DEBUG
from sticknet.permissions import LimitedAccessPermission
from django.core.cache import cache
from groups.serializers import CipherSerializer

class CheckUsername(APIView):

    def post(self, request):
        user = User.objects.filter(username=request.data['username'])
        valid = True
        if user:
            valid = False
        return Response({'valid': valid})


class UserViewSet(viewsets.GenericViewSet, mixins.UpdateModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)


class ProfilePictureViewSet(viewsets.GenericViewSet, mixins.DestroyModelMixin, mixins.CreateModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfilePictureSerializer

    def get_queryset(self):
        return ProfilePicture.objects.filter(user__id=self.request.user.id)


class ProfileCoverViewSet(viewsets.GenericViewSet, mixins.DestroyModelMixin, mixins.CreateModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileCoverSerializer

    def get_queryset(self):
        return ProfileCover.objects.filter(user__id=self.request.user.id)


class FetchSingleUser(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        id = request.GET.get('id')
        if id:
            user = User.objects.get(id=id)
        else:
            username = request.GET.get('username')
            user = User.objects.get(username=username)
        connected = False
        self.serializer_class = UserPublicSerializer
        requested = None
        if request.user in user.connections.all():
            connected = True
            self.serializer_class = UserConnectionSerializer
        else:
            requested = ConnectionRequest.objects.filter(from_user=request.user, to_user_id=id).exists()
        return Response({
            'is_connected': connected,
            'requested': requested,
            'user': self.serializer_class(user, context=self.get_serializer_context()).data
        })


class UserSearch(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = UserBaseSerializer

    def get_queryset(self, *args, **kwargs):
        query = self.request.GET.get("q").lower()
        qs = User.objects.filter(
            (Q(username__istartswith=query) | Q(name__istartswith=query)) & Q(finished_registration=True)).exclude(
            Q(blocked__in=[self.request.user]) | Q(id=self.request.user.id)).order_by('-timestamp')
        return qs


def getUniqueUsername(username):
    clean_username = re.sub(r"[^a-z0-9_]", "", username.lower())
    user = User.objects.filter(username=clean_username)
    num = 1
    temp_username = clean_username
    while user:
        temp_username = clean_username + str(num)
        user = User.objects.filter(username=temp_username)
        num += 1
    return temp_username


def code_verified(request):
    token = create_token_string()
    salt = create_salt_string()
    hash = hash_token(token, salt)
    if 'phone' in request.data:
        auth_id = request.data['phone']
        user = User.objects.filter(phone=auth_id).first()
    else:
        auth_id = request.data['email'].lower()
        user = User.objects.filter(email=auth_id).first()
    if LimitedAccessToken.objects.filter(auth_id=auth_id).exists():
        LimitedAccessToken.objects.get(auth_id=auth_id).delete()
    LimitedAccessToken.objects.create(hash=hash, salt=salt, auth_id=auth_id)
    if user:
        if 'phone' in request.data or (not request.data['email'].endswith('@test.com') or request.data['email'] == 'e2e_1@test.com'):
            return Response({
                "correct": True,
                "exists": True,
                "limited_access_token": token,
                "user_id": user.id,
                "username": user.username,
                "finished_registration": user.finished_registration,
                "password_salt": user.password_salt,
                "password_key": user.password_key
            })
        else:
            delete_user(user)
    return Response({"exists": False, "limited_access_token": token, "correct": True})


class PhoneVerified(generics.GenericAPIView):

    def post(self, request):
        id_token = request.data['id_token']
        auth.verify_id_token(id_token)
        return code_verified(request)


class CheckUserPhoneExists(APIView):
    def get(self, request):
        phone = request.GET.get("phone")
        phone = phone.strip()
        if not phone.startswith('+'):
            phone = str("+" + phone)
        exists = User.objects.filter(phone=phone).exists()
        return Response({'exists': exists})


class Register(generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [LimitedAccessPermission]

    def post(self, request):
        data = request.data
        exists = User.objects.filter(
            Q(username=data.get('username')) |
            Q(email=data.get('email'))
        ).exists()
        if not exists:
            if 'phone' in data:
                user = User.objects.create(phone=data['phone'], phone_hash=data['phone_hash'],
                                           username=data['username'].lower(),
                                           name=data['name'], dial_code=data['dial_code'], country=data['country'],
                                           platform=data['platform'])
            else:
                user = User.objects.create(email=data['email'].lower(), username=data['username'].lower(),
                                           name=data['name'], platform=data['platform'])
            user.color = random.choice([choice[0] for choice in COLOR_CHOICES])
            user.save()
            folder_icon = 'blue' if data['platform'] == 'ios' else 'yellow'
            Preferences.objects.create(user=user, folder_icon=folder_icon)
            home_folder = File.objects.create(folder_type='home', is_folder=True, user=user)
            File.objects.create(folder_type='camera_uploads', is_folder=True, folder=home_folder, user=user,
                                name='Camera Uploads')
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "success": True
            })
        return Response({
            "success": False
        })


class CreateE2EUser(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request):
        email = "e2e@test.com"
        user = User.objects.filter(email=email).first()
        if user:
            delete_user(user)
        name = names.get_full_name()
        name_list = name.split()
        username = name_list[0].lower() + '_' + name_list[1][:3].lower() + str(randrange(0, 1000))
        params = {'email': email, 'name': name, 'username': username}
        token = create_token_string()
        salt = create_salt_string()
        hash = hash_token(token, salt)
        if LimitedAccessToken.objects.filter(auth_id=email).exists():
            LimitedAccessToken.objects.get(auth_id=email).delete()
        LimitedAccessToken.objects.create(hash=hash, salt=salt, auth_id=email)
        return Response({
            'params': params,
            'limited_access_token': token,
            "success": True
        })


class RefreshUser(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        user = request.user
        user.last_login = timezone.now()
        user.save()
        pre_keys_count = PreKey.objects.filter(user=user, used=False).count()
        notifications = user.notifications.all()
        unread_count = 0
        for notification in notifications:
            if notification.read == False:
                unread_count += 1
        firebase_token = None
        if "should_get_firebase_token" in request.GET:
            should_get_firebase_token = json.loads(request.GET.get("should_get_firebase_token"))
            if should_get_firebase_token:
                firebase_token = auth.create_custom_token(user.id, {'email': user.email})
        data = {
            'user': self.serializer_class(user, context=self.get_serializer_context()).data,
            'pre_keys_count': pre_keys_count,
            'unread_count': unread_count,
            'firebase_token': firebase_token
        }
        return Response(data)


class FetchPreferences(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        preferences = request.user.preferences
        chat_device_id = None
        if preferences.chat_device:
            chat_device_id = preferences.chat_device.device_id
        return Response({'favorites_ids': preferences.favorites_ids,
                         'chat_device_id': chat_device_id,
                         'photo_backup_setting': preferences.photo_backup_setting,
                         'folder_icon': preferences.folder_icon})


class SetFolderIcon(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.preferences.folder_icon = request.data['folder_icon']
        request.user.preferences.save()
        return Response(status=status.HTTP_200_OK)


class SetPlatform(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.platform = request.data['platform']
        request.user.save()
        request.user.preferences.folder_icon = 'blue' if request.data['platform'] == 'ios' else 'yellow'
        request.user.preferences.save()
        return Response(status=status.HTTP_200_OK)


class PingServer(APIView):
    def get(self, request):
        return Response(status=status.HTTP_200_OK)


class GetAppSettings(APIView):
    def get(self, request):
        appSettings = AppSettings.objects.get(id=1)
        return Response({'minViableIOSVersion': appSettings.minViableIOSVersion,
                         'minViableAndroidVersion': appSettings.minViableAndroidVersion})


class TestEndPoint(APIView):

    def get(self, request):
        cache_key = 'xxx'
        # data = cache.get(cache_key)
        # if data:
        #     return Response(data)
        data = {'someData': 'responseData'}
        cache.set(cache_key, data)
        return Response(data)


class UpdateContacts(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # contacts = User.objects.filter(phone_hash__in=request.data['hashed_nums'])
        # request.user.connections.add(*contacts)
        return Response(status=status.HTTP_200_OK)


class UpdateDonationReminder(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.donation_reminder = request.data['donation_reminder']
        request.user.save()
        return Response(status=status.HTTP_200_OK)


class HighlightImage(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        image = Image.objects.get(id=request.data['image_id'])
        if image.user.id != request.user.id:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user = request.user
        highlighted = True
        for blob_id in request.data['blobs_ids']:
            id = str(request.data['image_id']) + '-' + str(blob_id)
            if not user.highlights_ids:
                user.highlights_ids = [id]
            else:
                if not id in user.highlights_ids:
                    user.highlights_ids.append(id)
                else:
                    user.highlights_ids.remove(id)
                    highlighted = False
        user.save()
        return Response({'highlighted': highlighted})


class ToggleHideImage(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        id = request.data['image_id']
        if request.data['hide'] and id not in request.user.hidden_images:
            request.user.hidden_images.append(id)
        elif id in request.user.hidden_images:
            request.user.hidden_images.remove(id)
        request.user.save()
        return Response(status=status.HTTP_200_OK)


class UploadCategories(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        stick_id = request.data['stick_id']
        if request.user.categories:
            categories = request.user.categories
            categories.stick_id = stick_id
            categories.text = request.data['text']
            categories.uri = request.data['uri']
            categories.file_size = request.data['file_size']
            categories.text_length = request.data['text_length']
            categories.save()
        else:
            categories = Cipher.objects.create(user=request.user, stick_id=stick_id,
                                               text=request.data['text'],
                                               uri=request.data['uri'], file_size=request.data['file_size'],
                                               text_length=request.data['text_length'])
            request.user.categories = categories
            request.user.save()
        # UPDATE CHAIN STEP
        party_id = stick_id[:36]
        chain_id = stick_id[36:]
        key = EncryptionSenderKey.objects.get(party_id=party_id, chain_id=chain_id, user=request.user)
        key.step = request.data['chain_step']
        key.save()
        return Response(status=status.HTTP_200_OK)


class BackupChats(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        stick_id = request.data['stick_id']
        if request.user.chat_backup:
            request.user.chat_backup.delete()
        chat_backup = Cipher.objects.create(user=request.user, stick_id=stick_id,
                                            text=request.data['text'],
                                            uri=request.data['uri'], file_size=request.data['file_size'],
                                            text_length=request.data['text_length'])
        request.user.chat_backup = chat_backup
        request.user.save()
        # UPDATE CHAIN STEP
        party_id = stick_id[:36]
        chain_id = stick_id[36:]
        key = EncryptionSenderKey.objects.get(party_id=party_id, chain_id=chain_id, user=request.user)
        key.step = request.data['chain_step']
        key.save()
        return Response(status=status.HTTP_200_OK)


class DeleteChatBackup(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.chat_backup.delete()
        request.user.chat_backup = None
        request.user.save()
        return Response(status=status.HTTP_200_OK)


class UpdateBackupFreq(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.backup_frequency = request.data['freq']
        request.user.save()
        return Response(status=status.HTTP_200_OK)


class BlockUser(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = User.objects.get(id=request.data['id'])
        self.request.user.blocked.add(user.id)
        self.request.user.connections.remove(user.id)
        user.connections.remove(self.request.user.id)
        return Response(status.HTTP_200_OK)


class UnblockUser(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        self.request.user.blocked.remove(request.data['id'])
        return Response(status.HTTP_200_OK)


class FetchBlockedAccounts(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserPublicSerializer
    pagination_class = None

    def get_queryset(self, *args, **kwargs):
        users = self.request.user.blocked.all()
        return users


class FetchDevices(APIView):
    permission_classes = [LimitedAccessPermission]

    def post(self, request):
        if 'phone' in request.data and request.data['phone'] != None:
            devices = Device.objects.filter(user__phone=request.data['phone'])
        else:
            devices = Device.objects.filter(user__email=request.data['email'].lower())
        devices_list = []
        current_device_id = request.data['current_device_id']
        for device in devices:
            if device.device_id != current_device_id:
                devices_list.append({'id': device.device_id, 'name': device.name})
        return Response(devices_list)


class FetchUserDevices(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        devices = request.user.devices.all()
        devices_list = []
        for device in devices:
            devices_list.append({'id': device.device_id, 'name': device.name})
        return Response(devices_list)


class UpdateChatDevice(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        device_id = request.data['device_id']
        device = request.user.devices.get(device_id=device_id)
        request.user.one_time_id = device.chat_id
        if request.data['latest']:
            request.user.preferences.chat_device = None
        else:
            request.user.preferences.chat_device = device
        request.user.preferences.save()
        request.user.save()
        return Response(status=status.HTTP_200_OK)


class UploadPasswordKey(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.password_key = request.data['password_key']
        request.user.save()
        return Response(status=status.HTTP_200_OK)


class CreateDevUsersBulk(APIView):

    def get(self, request):
        if not DEBUG:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        color_choices = ['red', 'blue', 'green', 'orange', 'purple', 'limegreen', 'deeppink', 'darkred',
                         'deepskyblue',
                         'mediumpurple']
        # group = Group.objects.get(id='81041269-ce90-45a1-95f3-fc8affbaa1c0')
        for i in range(50):
            phone = str(random.randint(10000, 999999999))
            name = names.get_full_name()
            name_list = name.split()
            username = name_list[0].lower() + '_' + name_list[1][:3].lower() + str(randrange(0, 1000))
            user = User.objects.create(phone=phone, username=username, name=name,
                                       dial_code='+971', country='AE', finished_registration=True)
            user.color = random.choice(color_choices)
            user.save()
            # user.groups.add(group)
            # users.append(user)
        # group.me
        # user = User.objects.get(id='93d01f5e-edb7-428c-85dd-9f970d6fe20a')
        # user.added_connections.add(*users)
        return Response(status=status.HTTP_200_OK)


class VerifyPassword(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        verified = False
        if request.user.check_password(request.data['password']):
            verified = True
        return Response({'verified': verified})


class DeactivateAccount(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        user.auth_token_set.all().delete()
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_200_OK)


class CodeConfirmedDeleteAccount(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        email = request.user.email
        object = EmailVerification.objects.filter(email=email).first()
        if not object or object.code != request.data['code']:
            return Response({'correct': False})
        token = create_token_string()
        salt = create_salt_string()
        hash = hash_token(token, salt)
        if LimitedAccessToken.objects.filter(auth_id=email).exists():
            LimitedAccessToken.objects.get(auth_id=email).delete()
        LimitedAccessToken.objects.create(hash=hash, salt=salt, auth_id=email)
        return Response({"delete_account_token": token, 'correct': True})


def delete_user(user):
    groups = user.get_groups()
    for group in groups:
        if group.owner == user:
            members = group.get_members().exclude(id=user.id)
            if (members.count() == 0):
                group.delete()
            else:
                group.owner = members.first()
                group.admins.add(members.first())
                group.save()
    try:
        if user.preferences:
            user.preferences.delete()
    except:
        pass
    if user.profile_picture:
        user.profile_picture.delete()
    if user.cover:
        user.cover.delete()
    user.delete()


class DeleteAccount(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        success = False
        correct_password = False
        correct_token = False
        token = request.data['delete_account_token']
        user = request.user
        limited_access_token = LimitedAccessToken.objects.get(auth_id=user.email)
        hashed_token = hash_token(token, limited_access_token.salt)
        if hashed_token == limited_access_token.hash:
            correct_token = True
            if user.check_password(request.data['password']):
                correct_password = True
                delete_user(user)
                success = True
        return Response({'success': success, 'correct_password': correct_password, 'correct_token': correct_token})


class RecreateUser(generics.GenericAPIView):
    permission_classes = [LimitedAccessPermission]
    serializer_class = UserSerializer

    def post(self, request):
        user = User.objects.get(id=request.data['user_id'])
        username = user.username
        name = user.name
        dial_code = user.dial_code
        country = user.country
        phone = user.phone
        color = user.color
        delete_user(user)
        user = User.objects.create(phone=phone, username=username, name=name,
                                   dial_code=dial_code, country=country, color=color)
        Preferences.objects.create(user=user)
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "success": True
        })


class FetchUserCategories(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = CipherSerializer

    def get_queryset(self):
        if not self.request.user.categories:
            return Cipher.objects.none()
        return Cipher.objects.filter(id=self.request.user.categories.id)


class FetchUserChatBackup(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPagination
    serializer_class = CipherSerializer

    def get_queryset(self):
        if not self.request.user.chat_backup:
            return Cipher.objects.none()
        return Cipher.objects.filter(id=self.request.user.chat_backup.id)


class SetPhotoBackupSetting(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.preferences.photo_backup_setting = request.data['setting']
        request.user.preferences.save()
        return Response(status=status.HTTP_200_OK)


class RequestEmailCode(APIView):
    def post(self, request):
        email = request.data['email'].lower()
        registered = User.objects.filter(email=email).exists()
        if 'platform' in request.data and request.data['platform'] == 'web' and not registered:
            return Response({'registered': registered})
        if DEBUG or email == 'apple@test.com' or email == 'google@test.com' or email.endswith('@test.com'):
            code = 123456
            EmailVerification.objects.create(email=email, code=code)
            return Response({'registered': registered})
        code = random.randint(100000, 999999)
        EmailVerification.objects.filter(email=email).all().delete()
        EmailVerification.objects.create(email=email, code=code)
        html_content = render_to_string('email_code.html', {'code': code})
        text_content = strip_tags(html_content)
        mail = EmailMultiAlternatives('Sticknet: Email verification', text_content, 'no-reply@sticknet.org',
                                      [email])
        mail.attach_alternative(html_content, "text/html")
        mail.send()
        return Response({'registered': registered})


class VerifyEmailCode(APIView):
    def post(self, request):
        email = request.data['email'].lower()
        object = EmailVerification.objects.filter(email=email).first()
        if not object or object.code != request.data['code']:
            return Response({'correct': False})
        else:
            object.delete()
        return code_verified(request)

############################################################################################################


from sticknet.permissions import ServerAdminPermission


## TODO: next time email title should be "Sticknet" not "no-reply"
# Desktop UI can be improved
class EmailReminder(APIView):
    permission_classes = [ServerAdminPermission]

    def get(self, request):
        for user in User.objects.all():
            if user.email:
                html_content = render_to_string('update.html')
                text_content = strip_tags(html_content)
                mail = EmailMultiAlternatives('Sticknet: Reworked chatting experience!', text_content,
                                              'no-reply@sticknet.org',
                                              [user.email])
                mail.attach_alternative(html_content, "text/html")
                mail.send()
        return Response({})

import requests
from socket import gethostname, gethostbyname
class TestIP(APIView):

    def get(self, request):
        url = "http://169.254.169.254/latest/meta-data/public-ipv4"
        r = requests.get(url)
        instance_ip = r.text
        instance_ip2 = gethostbyname(gethostname())
        html_content = render_to_string('test.html', {'ip1': instance_ip, 'ip2': instance_ip2})
        text_content = strip_tags(html_content)
        mail = EmailMultiAlternatives('IP', text_content, 'founder@sticknet.org', ['founder@sticknet.org'])
        mail.attach_alternative(html_content, "text/html")
        mail.send()
        return Response(status=status.HTTP_200_OK)
