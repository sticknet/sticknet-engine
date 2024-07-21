import datetime
import json, os, requests, time, stripe

from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt

from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from django.utils import timezone

from .models import Transaction
from users.models import User
from vault.models import File
from sticknet.settings import DEBUG
from django.db.models import Q

ONE_DAY = 60 * 60 * 24
GRACE_PERIOD = ONE_DAY * 15
NOTIFY_GRACE_PERIOD = ONE_DAY


def ios_verify_receipt(request, attempts):
    success = False
    receipt_info = {}
    is_sandbox = False
    url_prod = 'https://buy.itunes.apple.com/verifyReceipt'
    url_sandbox = 'https://sandbox.itunes.apple.com/verifyReceipt'
    body = {'receipt-data': request.data['receipt'], 'password': os.environ['IAP_IOS_KEY'],
            'exclude-old-transactions': True}
    response = requests.post(url_prod, data=json.dumps(body))
    if response.json()['status'] == 21007:
        is_sandbox = True
        response = requests.post(url_sandbox, data=json.dumps(body))
    status_code = response.json()['status']
    error = status_code
    if status_code == 0:  # success
        receipt_info = response.json()['latest_receipt_info'][0]
        expires = int(response.json()['latest_receipt_info'][0]['expires_date_ms'])
        current_time = int(timezone.now().timestamp() * 1000)
        if expires < current_time:
            error = 'expired'
        else:
            success = True
    else:
        if attempts < 3:
            return ios_verify_receipt(request, attempts + 1)
    return {'success': success, 'error': error, 'receipt_info': receipt_info, 'is_sandbox': is_sandbox}


def android_verify_receipt(request, attempts):
    success = False
    receipt_info = {}
    SCOPES = ['https://www.googleapis.com/auth/androidpublisher']
    SERVICE_ACCOUNT_FILE = os.environ['IAP_ANDROID_KEY']
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    api_version = 'v3'
    service = build('androidpublisher', api_version, credentials=credentials)
    subscription_id = request.data['product_id']
    token = request.data['token']
    try:
        result = service.purchases().subscriptions().get(
            packageName='com.stiiick', subscriptionId=subscription_id, token=token).execute()
        receipt_info['purchase_date_ms'] = result['startTimeMillis']
        receipt_info['expires_date_ms'] = result['expiryTimeMillis']
        receipt_info['transaction_id'] = result['orderId']
        receipt_info['product_id'] = request.data['product_id']
        receipt_info['original_transaction_id'] = None
        expires = int(result['expiryTimeMillis'])
        current_time = int(timezone.now().timestamp() * 1000)
        if expires < current_time:
            success = False
            error = "expired"
        elif result['paymentState'] != 1:
            success = False
            error = "Payment state: " + str(result['paymentState'])
        else:
            success = True
            error = 0
    except HttpError as e:
        error = e
        if attempts < 3:
            return android_verify_receipt(request, attempts + 1)
    return {'success': success, 'error': error, 'receipt_info': receipt_info, 'is_sandbox': False}


class VerifyReceipt(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.data['platform'] == 'ios':
            response = ios_verify_receipt(request, 1)
        else:
            response = android_verify_receipt(request, 1)

        receipt_info = response['receipt_info']
        transaction_id = None
        test_prod = False
        if len(receipt_info):
            transaction_id = receipt_info['transaction_id']
            test_prod = not DEBUG and response['is_sandbox']
            if not test_prod:
                if not Transaction.objects.filter(transaction_id=receipt_info['transaction_id']).exists():
                    Transaction.objects.create(user=request.user,
                                               platform=request.data['platform'],
                                               product_id=receipt_info['product_id'],
                                               success=response['success'],
                                               error=response['error'],
                                               transaction_id=receipt_info['transaction_id'],
                                               original_transaction_id=receipt_info['original_transaction_id'],
                                               expires_date_ms=receipt_info['expires_date_ms'],
                                               purchase_date_ms=receipt_info['purchase_date_ms'])
                    request.user.subscription = 'premium'
                    request.user.subscription_expiring = False
                    request.user.save()
        else:
            Transaction.objects.create(user=request.user,
                                       platform=request.data['platform'],
                                       product_id=request.data['product_id'],
                                       success=response['success'],
                                       error=response['error'])
        return Response({'success': response['success'], 'transaction_id': transaction_id, 'error': response['error'],
                         'test_prod': test_prod})


class CheckUserGracePeriod(APIView):
    def get(self, request):
        current_time = int(time.time())
        users = User.objects.exclude(whitelist_premium=True)
        one_gb = 1073741824
        for user in users:
            try:
                latest_transaction = user.transactions.latest('timestamp')
                expiry_time = int(latest_transaction.expires_date_ms[:-3])
            except ObjectDoesNotExist:
                expiry_time = 0
            is_expired = current_time > expiry_time
            if is_expired:
                timesince_expiry = current_time - expiry_time
                if timesince_expiry >= GRACE_PERIOD:
                    if user.storage_used() > one_gb:
                        files = File.objects.filter(user=user, is_folder=False).order_by('-timestamp')
                        for file in files:
                            file.delete()
                            if user.storage_used() <= one_gb:
                                break
                    user.subscription = 'basic'
                    user.save()
                else:
                    user.subscription_expiring = True
                    user.save()
                    if user.storage_used() > one_gb:
                        dt_object = datetime.datetime.utcfromtimestamp(
                            int(latest_transaction.expires_date_ms[:-3]) + GRACE_PERIOD - ONE_DAY)
                        formatted_date = dt_object.strftime('%d %B %Y')
                        html_content = render_to_string('grace_period.html',
                                                        {'name_of_user': user.name, 'end_date': formatted_date})
                        text_content = strip_tags(html_content)
                        mail = EmailMultiAlternatives('Sticknet: Premium subscription expired', text_content,
                                                      'support@sticknet.org',
                                                      [user.email])
                        mail.attach_alternative(html_content, "text/html")
                        mail.send()
        return Response({'success': True})


stripe.api_key = os.environ['STRIPE_TEST_KEY'] if DEBUG else os.environ['STRIPE_LIVE_KEY']
WH_SECRET = os.environ['STRIPE_TEST_WH_SECRET'] if DEBUG else os.environ['STRIPE_LIVE_WH_SECRET']
YOUR_DOMAIN = 'http://127.0.0.1:8000' if DEBUG else 'https://www.stiiick.com'
PRICE_ID = 'price_1O1qseEQNuAuV5UyDgHbip6C' if DEBUG else 'price_1OIle5EQNuAuV5UygXgYDHFY'

class WebCheckout(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price': PRICE_ID,
                        'quantity': 1,
                    },
                ],
                customer=request.user.stripe_customer_id,
                customer_email=request.user.email if not request.user.stripe_customer_id else None,
                mode='subscription',
                success_url=YOUR_DOMAIN + '/welcome-to-premium',
                cancel_url=YOUR_DOMAIN + '/premium',
                subscription_data={'metadata': {'user_id': request.user.id},
                                   "trial_settings": {"end_behavior": {"missing_payment_method": "cancel"}},
                                   "trial_period_days": 30}

            )
        except Exception as e:
            print('EXCEPTIONX', e)
            return Response({'success': False})
        return Response({'success': True, 'url': checkout_session.url})

class WebBillingPortal(APIView):
    def post(self, request):
        billing_portal_session = stripe.billing_portal.Session.create(
            customer=request.user.stripe_customer_id,
            return_url=YOUR_DOMAIN + '/vault/files',
        )
        return Response({'success': True, 'url': billing_portal_session.url})


# stripe listen --forward-to http://127.0.0.1:8000/api/stripe-web-hook/
# This is your Stripe CLI webhook secret for testing your endpoint locally.
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WH_SECRET)
    except ValueError as e:
        html_content = render_to_string('server_error.html', {'error': str(e), 'error_type': 'ValueError'})
        text_content = strip_tags(html_content)
        mail = EmailMultiAlternatives('Server error', text_content, 'no-reply@sticknet.org',
                                      [os.environ['ERRORS_EMAIL']])
        mail.attach_alternative(html_content, "text/html")
        mail.send()
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        html_content = render_to_string('server_error.html', {'error': str(e), 'error_type': 'SignatureVerificationError'})
        text_content = strip_tags(html_content)
        mail = EmailMultiAlternatives('Server error', text_content, 'no-reply@sticknet.org',
                                      [os.environ['ERRORS_EMAIL']])
        mail.attach_alternative(html_content, "text/html")
        mail.send()
        return HttpResponse(status=400)

    if event.type == 'customer.subscription.updated':
        object = json.loads(payload)['data']['object']
        user = User.objects.get(stripe_customer_id=object['customer'])
        if object['cancel_at'] == None:
            user.subscription_expiring = False
            user.save()
        else:
            user.subscription_expiring = True
            user.save()
            latest_transaction = user.transactions.latest('timestamp')
            dt_object = datetime.datetime.utcfromtimestamp(int(latest_transaction.expires_date_ms[:-3]))
            formatted_date = dt_object.strftime('%d %B %Y')
            html_content = render_to_string('subscription_cancelled.html',
                                            {'name_of_user': user.name, 'end_date': formatted_date})
            text_content = strip_tags(html_content)
            mail = EmailMultiAlternatives('Sticknet: Premium subscription cancelled', text_content,
                                          'support@sticknet.org',
                                          [user.email])
            mail.attach_alternative(html_content, "text/html")
            mail.send()
    if event.type == 'invoice.payment_succeeded':
        object = json.loads(payload)['data']['object']
        item = object['lines']['data'][0]
        period = item['period']
        user_id = item['metadata']['user_id']
        user = User.objects.get(id=user_id)
        Transaction.objects.create(user=user,
                                   platform='web',
                                   product_id='com.stiiick.premium.1',
                                   subscription_id=object['subscription'],
                                   transaction_id=object['payment_intent'],
                                   expires_date_ms=period['end'] * 1000,
                                   purchase_date_ms=period['start'] * 1000,
                                   success=True,
                                   error=0)
        if not user.stripe_customer_id:
            user.stripe_customer_id = object['customer']
        user.subscription = 'premium'
        user.subscription_expiring = False
        user.save()
    return HttpResponse(status=200)


class CancelWebSubscription(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        transaction = Transaction.objects.filter(user=request.user, platform='web').latest('timestamp')
        stripe.Subscription.delete(transaction.subscription_id)
        request.user.subscription_expiring = True
        request.user.save()
        return Response({'success': True})


class FetchSubscriptionDetails(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user)
        if not transactions.exists():
            return Response({'subscription': request.user.subscription})
        transaction = transactions.latest('timestamp')
        return Response({'subscription': request.user.subscription,
                         'subscription_expiring': request.user.subscription_expiring,
                         'platform': transaction.platform,
                         'expires': transaction.expires_date_ms})
