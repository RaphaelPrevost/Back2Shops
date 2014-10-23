# coding:UTF-8
from django.db import models

from accounts.models import Brand
from sales.models import Sale
from shops.models import Shop
from attributes.models import BrandAttribute


class Visitors(models.Model):
    sid = models.CharField(max_length=36, primary_key=True)
    users_id = models.IntegerField(blank=True, null=True)
    visit_time = models.DateTimeField(blank=False, null=False)

    def __unicode__(self):
        return str(self.sid) + '-' + str(self.users_id)

class Incomes(models.Model):
    sale = models.ForeignKey(Sale)
    shop = models.ForeignKey(Shop)
    variant = models.ForeignKey(BrandAttribute)
    price = models.FloatField(null=False, blank=False)
    quantity = models.IntegerField(null=False, blank=False)
    users_id = models.IntegerField(null=False, blank=False)
    up_time = models.DateTimeField(null=False, blank=False)

class Orders(models.Model):
    users_id = models.IntegerField()
    order_id = models.IntegerField()
    brand = models.ForeignKey(Brand)
    shop = models.ForeignKey(Shop, null=True, blank=True)
    pending_date = models.DateField(null=True, blank=True)
    waiting_payment_date = models.DateField(null=True, blank=True)
    waiting_shipping_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)

class BoughtHistory(models.Model):
    sale = models.ForeignKey(Sale, null=False, blank=False)
    users = models.TextField(null=False, blank=False)
