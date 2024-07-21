from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

PRODUCTS = (('com.stiiick.premium.1', 'Sticknet Premium (monthly)'),)

PLATFORMS = (('ios', 'iOS'), ('android', 'Android'), ('web', 'Web'))


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='transactions')
    platform = models.CharField(max_length=10, choices=PLATFORMS, null=True)
    product_id = models.CharField(max_length=100, choices=PRODUCTS, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_id = models.CharField(max_length=56, blank=True, null=True)
    original_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    purchase_date_ms = models.CharField(max_length=100, null=True)
    expires_date_ms = models.CharField(max_length=100, null=True)
    success = models.BooleanField()
    error = models.CharField(max_length=1000, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)
