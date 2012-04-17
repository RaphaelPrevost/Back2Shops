# coding:UTF-8
from django.db import models
from django.utils.translation import ugettext_lazy as _
from accounts.models import Brand
from sorl.thumbnail import ImageField

class Shop(models.Model):
    mother_brand = models.ForeignKey(Brand, related_name="shops")
    gestion_name = models.CharField(verbose_name=_("Internal name"), max_length=100, blank=True, null=True)
    upc = models.CharField(verbose_name=_("Barcode"), max_length=50, blank=True, null=True)
    address = models.CharField(verbose_name=_("Address"), max_length=250, blank=True, null=True)
    zipcode = models.IntegerField(verbose_name=_("Postal code"), blank=True, null=True)
    city = models.CharField(verbose_name=_("City"), max_length=100)
    country = models.CharField(verbose_name=_("Country"), max_length=100)
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
