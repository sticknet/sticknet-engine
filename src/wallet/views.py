from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from users.models import User
from users.views import user_verified
from sticknet.permissions import LimitedAccessPermission

class GenerateNonce(APIView):
    def get(self, request):
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
            request.data['ethereum_address'] = siwe_message.address
            return Response(user_verified(request))
        except Exception as e:
            return Response({'correct': False}, status=400)

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


# class GetAccountSecret(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     def post(self, request):
#         return Response({'account_secret': request.user.account_secret})
#
# class WalletVerified(APIView):
#     def post(self, request):
#         return Response(user_verified(request))
