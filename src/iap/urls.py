from django.urls import re_path

from .views import VerifyReceipt, CheckUserGracePeriod, WebCheckout, stripe_webhook, CancelWebSubscription, FetchSubscriptionDetails, WebBillingPortal


app_name = 'iap'
urlpatterns = [
    re_path(r'^verify-receipt/$', VerifyReceipt.as_view(), name='verify_receipt'),
    re_path(r'^grace-period/$', CheckUserGracePeriod.as_view(), name='grace_period'),
    re_path(r'^web-checkout/$', WebCheckout.as_view(), name='web_checkout'),
    re_path(r'^stripe-web-hook/$', stripe_webhook, name='web_hook'),
    re_path(r'^cancel-web-subscription/$', CancelWebSubscription.as_view(), name='cancel_web_subscription'),
    re_path(r'^fetch-subscription-details/$', FetchSubscriptionDetails.as_view(), name='fetch_subscription_details'),
    re_path(r'^web-billing-portal/$', WebBillingPortal.as_view(), name='web_billing_portal'),
]
