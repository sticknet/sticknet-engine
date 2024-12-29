import asyncio

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from users.models import User
from users.views import user_verified
from sticknet.permissions import LimitedAccessPermission

class GenerateNonce(APIView):
    def get(self, request):
        asyncio.set_event_loop(asyncio.new_event_loop())
        from siwe import generate_nonce
        nonce = generate_nonce()
        request.session['nonce'] = nonce
        return Response(nonce, content_type='text/plain')

class VerifySiwe(APIView):
    def post(self, request):
        from siwe import SiweMessage
        message = request.data['message']
        signature = request.data['signature']
        try:
            siwe_message = SiweMessage(message)
            request.session['address'] = siwe_message.address
            request.session['chain_id'] = siwe_message.chain_id
            siwe_message.verify(signature=signature)
            return Response(True)
        except Exception as e:
            return Response(False, status=400)

class GetSession(APIView):
    def get(self, request):
        if not 'address' in request.session:
            return Response({'exists': False})
        return Response({'exists': True, 'address': request.session['address'], 'chain_id': request.session['chain_id']})

class FlushSession(APIView):
    def get(self, request):
        request.session.flush()
        return Response(status=status.HTTP_200_OK)


class SetAccountSecret(APIView):
    permission_classes = [LimitedAccessPermission]
    def post(self, request):
        user = User.objects.get(ethereum_address=request.data['ethereum_address'])
        user.account_secret = request.data['account_secret']
        user.save()
        return Response(status=status.HTTP_200_OK)


class WalletVerified(APIView):
    def post(self, request):
        return Response(user_verified(request))
