from django.db import models
from django.contrib.auth.models import User

from accounts.models import Brand

SETTING_KEY_CHOICES = (
                       ('default_currency', 'default currency'),
                       ('default_shipment_period', 'default shipment period'),
                       ('default_payment_period', 'default payment period'),
                       ('starting_invoice_number', 'starting invoice number'),
                       )

# Create your models here.
class BrandSettings(models.Model):
    key = models.CharField(max_length=200, choices=SETTING_KEY_CHOICES)
    value = models.CharField(max_length=200)
    brand = models.ForeignKey(Brand)
    shopowner = models.ForeignKey(User, blank=True, null=True)

    class Meta:
        unique_together = (("key", "value", "brand", "shopowner"),)

    def __unicode__(self):
        return self.key

