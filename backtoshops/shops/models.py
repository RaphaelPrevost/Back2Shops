# coding:UTF-8
from django.db import models
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from accounts.models import Brand
from address.models import Address
from common.cache_invalidation import post_delete_handler
from common.cache_invalidation import post_save_handler
from shippings.models import Shipping
from sorl.thumbnail import ImageField


class Shop(models.Model):
    mother_brand = models.ForeignKey(Brand, related_name="shops")
    gestion_name = models.CharField(verbose_name=_("Internal name"), max_length=100, blank=True, null=True)
    upc = models.CharField(verbose_name=_("Barcode"), max_length=50, blank=True, null=True)
    phone = models.CharField(verbose_name=_("Phone number"), max_length=50, blank=True, null=True)
    name = models.CharField(verbose_name=_("Shop name"), max_length=50)
    catcher = models.CharField(verbose_name=_("Caption"), max_length=250, blank=True, null=True)
    image = ImageField(verbose_name=_("Shop picture"), upload_to="shop_images", blank=True, null=True)
    description = models.CharField(verbose_name=_("Description"), max_length=500, blank=True, null=True)
    opening_hours = models.CharField(max_length=1000, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.ForeignKey(Address, unique=True)


    def __unicode__(self):
        return self.name

@receiver(post_save, sender=Shop, dispatch_uid='shops.models.Shop')
def on_shop_saved(sender, **kwargs):
    post_save_handler('shop', sender, **kwargs)

@receiver(post_delete, sender=Shop, dispatch_uid='shops.models.Shop')
def on_shop_deleted(sender, **kwargs):
    post_delete_handler('shop', sender, **kwargs)


class DefaultShipping(models.Model):
    shop = models.ForeignKey(Shop)
    shipping = models.ForeignKey(Shipping)
