# coding:UTF-8
from django.db import models

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
