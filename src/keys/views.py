import json, datetime
from rest_framework import permissions, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from stick_protocol.stick_protocol import StickProtocol
from knox.models import AuthToken

from sticknet.settings import TESTING
from users.models import User, Device, LimitedAccessToken
from groups.models import Group
from sticknet.permissions import LimitedAccessPermission
from users.serializers import UserSerializer
from stick_protocol.models import DecryptionSenderKey, PendingKey
from django.utils.timesince import timesince
from vault.models import File, VaultNote
from firebase_admin import auth

stick_protocol = StickProtocol(User, Device, Group, 300)

class UploadPreKeyBundle(APIView):
    permission_classes = [LimitedAccessPermission]

    def post(self, request):
        if 'phone' in request.data:
            auth_id = request.data['phone']
            user = User.objects.get(phone=auth_id)
        else:
            auth_id = request.data['email'].lower()
            user = User.objects.get(email=auth_id)
        stick_protocol.process_pre_key_bundle(request.data, user)
        LimitedAccessToken.objects.get(auth_id=auth_id).delete()
        party = user.parties.get(individual=False)
        self_party = user.parties.get(individual=True)
        auth_token = AuthToken.objects.create(user)
        device = Device.objects.get(user=user)
        device.auth_token = auth_token[0]
        device.save()
        firebase_token = auth.create_custom_token(user.id, {'email': user.email}) if not TESTING else 'firebase_token'
        return Response({'party_id': party.id, 'self_party_id': self_party.id, "token": auth_token[1], 'firebase_token': firebase_token})


class UploadPreKeys(APIView):
    """
    A user would need to refill their PreKeys on the server every while whenever it goes below a certain N value.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        stick_protocol.process_pre_keys(request.data, request.user)
        return Response(status=status.HTTP_200_OK)


class FetchPreKeyBundle(APIView):
    """
    The following get method is used to fetch the PreKeyBundle of user to create a pairwise signal session. The request must contain
    a boolean `is_sticky` to know whether this bundle would be used to communicate a SenderKey or not. If it will be used to
    communicate a SenderKey, then the PreKey must be marked as used, otherwise the PreKey is deleted from the server.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_id = request.GET.get("id")
        if request.GET.get('is_sticky') == None or json.loads(request.GET.get('is_sticky')):
            is_sticky = True
        else:
            is_sticky = False
        data = {'user_id': user_id, 'is_sticky': is_sticky}
        PKB = stick_protocol.get_pre_key_bundle(data)
        return Response(PKB)


class FetchPreKeyBundles(APIView):
    """
    Similar to the above method, but fetches PreKeyBundles of several users at once. This method allows a user to
    communicate their SenderKey to multiple members of a party at once.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # You can either provide in the request a list of `users_id` or just a `group_id`.
        if "users_id" in request.data:
            users_id = request.data["users_id"]
        else:
            users_id = Group.objects.get(id=request.data["group_id"]).get_all_users_ids()
        response = stick_protocol.get_pre_key_bundles(request.user, users_id) # TODO: method can be refactored to be reusable
        return Response(response)


class FetchSenderKey(APIView):
    """
    The following method is used to fetch the SenderKey of a stickySession.
    The body should contain the following fields:
        * stick_id - String
        * member_id - String
        * is_sticky - Boolean (are you fetching the SenderKey of a Sticky session or a standard session)
        * is_invitation - Boolean
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        response = stick_protocol.get_sender_key(request.data, request.user)
        if 'authorized' in response and not response['authorized']:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if not 'party_exists' in response or not response['party_exists']:
            return Response({'party_exists': False})
        return Response(
            {'sender_key': response['sender_key'], 'party_exists': response['party_exists']})


class FetchStandardSenderKeys(APIView):
    """
    The following method is used to fetch the standard session sender keys of a group.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group_id = request.data['group_id']
        group = Group.objects.get(id=group_id)
        response = stick_protocol.get_standard_sender_keys(request.data, request.user, group)
        if not response['authorized']:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response({'sender_keys': response['sender_keys']})


class FetchUploadedSenderKeys(APIView):
    """
    Before a user makes an upload they need to know which stick_id to use (whether the current sticky session has expired).
    Also, they need to know which members of the target party does not have their SenderKey for that sticky session.
    This following method expects these arguments in the request body:
    * groups_ids - a list of groups ids
    * connections_ids - a list of users ids
    * is_sticky - boolean, indicates whether the user is intending to use a sticky session
    * isProfile - boolean, indicates whether the user is sharing to their profile (includes all their connections)
    * party_id (optional) - boolean, the party_id of a user
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        response = stick_protocol.get_stick_id(request.data, request.user) # TODO: still more cases to test
        return Response(response)


class GetActiveStickId(APIView):
    """
    The following method gets the active sticky session stick_id associated with a particular party_id that already exists.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        response = stick_protocol.get_active_stick_id(request.data, request.user)
        return Response(response)


class UploadSenderKey(APIView):
    """
    The following method is used to upload a SenderKey of a sticky session for a user. Typically used when a user
    receives a `PendingKey` request.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        stick_protocol.process_sender_key(request.data, request.user)
        return Response(status=status.HTTP_200_OK)


class UploadSenderKeys(APIView):
    """
    The following method is used to upload SenderKeys of multiple users at once. Before making an upload, and after
    the user has made a request to get the UploadedSenderKeys, and now knows which users does not have SenderKeys for
    a particular sticky session, the user can upload those SenderKeys through this method.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        stick_protocol.process_sender_keys(request.data, request.user)
        return Response({"success": True})


class UploadStandardSenderKeys(APIView):
    """
    The following method is used to upload the SenderKeys of a standard session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        stick_protocol.process_standard_sender_keys(request.data, request.user)
        return Response(status=status.HTTP_200_OK)


class UpdateActiveSPK(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        stick_protocol.update_active_spk(request.data, request.user)
        return Response(status=status.HTTP_200_OK)


class UpdateActiveIK(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        stick_protocol.update_active_ik(request.data, request.user)
        return Response(status=status.HTTP_200_OK)


class Login(generics.GenericAPIView):
    """
    This Login method should be called after the user have verified their phone number and got their LimitedAccessToken.
    As a 2FA mechanism, the user need to provide their password. If the password is correct, return to the user their keys:
        * Identity Key
        * Signed Pre Key
        * Pre Keys
        * Encrypting Sender Keys
    On the client-side, the password will be used to decrypt the private keys of the IdentityKey, SignedPreKey
    and PreKeys (using a secret key derived from the password through Argon2).
    The user will be able to re-establish their pairwise signal sessions. After that, the user can decrypt their ESKs
    as well as any of the DSKs the was sent to them, which they can fetch again from the server as needed.
    """
    permission_classes = [LimitedAccessPermission]

    def post(self, request):
        blocked = False
        if 'phone' in request.data:
            auth_id = request.data['phone']
            user = User.objects.get(phone=auth_id)
        else:
            auth_id = request.data['email'].lower()
            user = User.objects.get(email=auth_id)
        if user.password_block_time:
            age = timesince(user.password_block_time)
            l = age.split('\xa0')
            if (l[1] == 'minute' or l[1] == 'minutes') and int(l[0]) < 10:
                blocked = True
                return Response({"correct": False, "blocked": blocked, "block_time": 10 - int(l[0])})
        response = stick_protocol.verify_password_and_get_keys(request.data, user)
        if response['verify']:
            user.password_trials = 0
            user.password_block_time = None
            user.is_active = True
            user.save()
            DSKs = []
            DSKs_ids = []
            for group in user.groups.all():
                if group.display_name.user.id != user.id:
                    dsk = DecryptionSenderKey.objects.filter(stick_id=group.display_name.stick_id,
                                                             of_user=group.display_name.user, for_user=user).first()
                    if dsk:
                        DSKs.append(
                            {'key': dsk.key, 'identity_key_id': dsk.identity_key.key_id, 'pre_key_id': dsk.pre_key.key_id,
                             'sender_id': group.display_name.user.id, 'stick_id': group.display_name.stick_id})
                        DSKs_ids.append(dsk.id)
                if group.cover and group.cover.user.id != user.id:
                    dsk = DecryptionSenderKey.objects.filter(stick_id=group.cover.stick_id,
                                                             of_user=group.cover.user, for_user=user).first()
                    if dsk:
                        DSKs.append(
                            {'key': dsk.key, 'identity_key_id': dsk.identity_key.key_id, 'pre_key_id': dsk.pre_key.key_id,
                             'sender_id': group.cover.user.id, 'stick_id': group.cover.stick_id})
                        DSKs_ids.append(dsk.id)
            response['bundle']['DSKs'] = DSKs
            LimitedAccessToken.objects.get(auth_id=auth_id).delete()
            devices_count = user.devices.all().count()
            auth_token = AuthToken.objects.create(user)
            device = Device.objects.get(user=user, device_id=request.data['device_id'])
            if device.auth_token:
                device.auth_token.delete()
            device.auth_token = auth_token[0]
            device.save()
            firebase_token = auth.create_custom_token(user.id, {'email': user.email}) if not TESTING else 'firebase_token'
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "token": auth_token[1],
                "firebase_token": firebase_token,
                "bundle": response['bundle'],
                "correct": True,
                "devices_count": devices_count,
                "chat_backup_timestamp": 0
            })
        user.password_trials += 1
        if user.password_trials == 15:
            blocked = True
            user.password_block_time = datetime.datetime.now()
        user.save()
        return Response({"correct": False, "blocked": blocked, 'block_time': 10})


class WebLogin(generics.GenericAPIView):
    permission_classes = [LimitedAccessPermission]

    def post(self, request):
        blocked = False
        if 'phone' in request.data and request.data['phone'] != None:
            auth_id = request.data['phone']
            user = User.objects.get(phone=auth_id)
        else:
            auth_id = request.data['email'].lower()
            user = User.objects.get(email=auth_id)
        if user.password_block_time:
            age = timesince(user.password_block_time)
            l = age.split('\xa0')
            if (l[1] == 'minute' or l[1] == 'minutes') and int(l[0]) < 10:
                blocked = True
                return Response({"correct": False, "blocked": blocked, "block_time": 10 - int(l[0])})
        if user.check_password(request.data['password_hash']):
            user.password_trials = 0
            user.password_block_time = None
            user.is_active = True
            user.save()
            LimitedAccessToken.objects.get(auth_id=auth_id).delete()
            auth_token = AuthToken.objects.create(user)
            # device = Device.objects.get(user=user, device_id=request.data['device_id'])
            # if device.auth_token:
            #     device.auth_token.delete()
            # device.auth_token = auth_token[0]
            # device.save()
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "token": auth_token[1],
                "correct": True,
            })
        user.password_trials += 1
        if user.password_trials == 15:
            blocked = True
            user.password_block_time = datetime.datetime.now()
        user.save()
        return Response({"correct": False, "blocked": blocked, 'block_time': 10})



class FetchOneTimeId(APIView):
    """
    The following method is used to fetch the OneTimeId of a user.
    An example of usage is when entering a chat room a user need to know
    the current one_time_id of the recipient.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        id = request.GET.get("id")
        user = User.objects.get(id=id)
        is_blocked = request.user in user.blocked.all()
        return Response({'one_time_id': user.one_time_id, 'name': user.name, 'is_blocked': is_blocked})


class ChangePassword(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        vault_cipher = request.data['vault_cipher']
        for entry in vault_cipher['files_cipher']:
            file = File.objects.get(id=entry['id'], user=request.user)
            file.cipher = entry['cipher']
            if 'preview_cipher' in entry:
                file.preview_cipher = entry['preview_cipher']
            file.save()
        for entry in vault_cipher['notes_cipher']:
            note = VaultNote.objects.get(id=entry['id'], user=request.user)
            note.cipher = entry['cipher']
            note.save()
        if 'profile_picture_cipher' in vault_cipher['profile']:
            request.user.profile_picture.self_cipher = vault_cipher['profile']['profile_picture_cipher']
            request.user.profile_picture.save()
        response = stick_protocol.process_reencrypted_keys(request.data['keys'], request.user)
        tokens = AuthToken.objects.filter(user=request.user)
        device = Device.objects.get(device_id=request.data['device_id'], user=request.user)
        for token in tokens:
            if token.token_key != device.auth_token.token_key:
                token.delete()
        return Response({'success': response['success']})


class FetchPendingKeys(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        pending_keys = PendingKey.objects.filter(owner=request.user)
        pending_keys_list = []
        for key in pending_keys:
            pending_keys_list.append({'stick_id': key.stick_id, 'sender_id': key.owner.id, 'receiver_id': key.user.id})
        pending_keys.all().delete()
        return Response({'pending_keys': pending_keys_list})
