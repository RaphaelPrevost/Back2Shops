# coding:UTF-8
from django.db import models
from django.utils.translation import ugettext_lazy as _

from accounts.models import Brand
from sales.models import ProductType
from sales.models import Sale
from shops.models import Shop

class Group(models.Model):
    name = models.CharField(verbose_name=_("Group Name"), max_length=50)
    types = models.ManyToManyField(ProductType, blank=True, null=True, through="TypesInGroup")
    sales = models.ManyToManyField(Sale, blank=True, null=True, through="SalesInGroup")
    brand = models.ForeignKey(Brand)
    shop = models.ForeignKey(Shop, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

class TypesInGroup(models.Model):
    group = models.ForeignKey(Group)
    type = models.ForeignKey(ProductType)

class SalesInGroup(models.Model):
    group = models.ForeignKey(Group)
    sale = models.ForeignKey(Sale)


