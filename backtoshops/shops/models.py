# coding:UTF-8
from django.db import models
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from accounts.models import Brand
from common.cache_invalidation import post_delete_handler
from common.cache_invalidation import post_save_handler
from countries.models import Country
from shippings.models import Shipping
from sorl.thumbnail import ImageField


class Shop(models.Model):
    mother_brand = models.ForeignKey(Brand, related_name="shops")
    gestion_name = models.CharField(verbose_name=_("Internal name"), max_length=100, blank=True, null=True)
    upc = models.CharField(verbose_name=_("Barcode"), max_length=50, blank=True, null=True)
    address = models.CharField(verbose_name=_("Address"), max_length=250, blank=True, null=True)
    zipcode = models.IntegerField(verbose_name=_("Postal code"), blank=True, null=True)
    city = models.CharField(verbose_name=_("City"), max_length=100)
    country = models.ForeignKey(Country, verbose_name=_('Country'), blank=True, null=True)
    province_code = models.CharField(verbose_name=_('Province'), max_length=2, blank=True, null=True)
    phone = models.CharField(verbose_name=_("Phone number"), max_length=50, blank=True, null=True)
    name = models.CharField(verbose_name=_("Shop name"), max_length=50)
    catcher = models.CharField(verbose_name=_("Caption"), max_length=250, blank=True, null=True)
    image = ImageField(verbose_name=_("Shop picture"), upload_to="shop_images", blank=True, null=True)
    description = models.CharField(verbose_name=_("Description"), max_length=500, blank=True, null=True)
    opening_hours = models.CharField(max_length=1000, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def clean_city(self):
        return self.city.upper()

    def save(self, *args, **kwargs):
        self.city = self.city.upper()
        super(Shop, self).save(*args, **kwargs)

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
