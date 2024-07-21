from django.conf.urls import url

from .views import VerifyReceipt, CheckUserGracePeriod, WebCheckout, stripe_webhook, CancelWebSubscription, FetchSubscriptionDetails, WebBillingPortal


app_name = 'iap'
urlpatterns = [
    url(r'^verify-receipt/$', VerifyReceipt.as_view(), name='verify_receipt'),
    url(r'^grace-period/$', CheckUserGracePeriod.as_view(), name='grace_period'),
    url(r'^web-checkout/$', WebCheckout.as_view(), name='web_checkout'),
    url(r'^stripe-web-hook/$', stripe_webhook, name='web_hook'),
    url(r'^cancel-web-subscription/$', CancelWebSubscription.as_view(), name='cancel_web_subscription'),
    url(r'^fetch-subscription-details/$', FetchSubscriptionDetails.as_view(), name='fetch_subscription_details'),
    url(r'^web-billing-portal/$', WebBillingPortal.as_view(), name='web_billing_portal'),
]
