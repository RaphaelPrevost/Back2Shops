from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from countries.models import Country

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    work_for = models.ForeignKey("Brand", related_name="employee")
    shops = models.ManyToManyField('shops.Shop', verbose_name=_('shops'), null=True, blank=True)
    language = models.CharField(max_length=2, verbose_name=_('language'), choices=settings.LANGUAGES)

    def __str__(self):
        return self.user.username

class Brand(models.Model):
    name = models.CharField(max_length=50)
    logo = models.ImageField(upload_to="brand_logos")
    address = models.CharField(verbose_name=_("Address"), max_length=250, blank=True, null=True)
    zipcode = models.IntegerField(verbose_name=_("Postal code"), blank=True, null=True)
    city = models.CharField(verbose_name=_("City"), max_length=100)
    country = models.ForeignKey(Country, verbose_name=_('Country'), blank=True, null=True)
    province_code = models.CharField(verbose_name=_('Province'), max_length=2, blank=True, null=True)

    def __str__(self):
        return self.name

    def clean_city(self):
        return self.city.upper()


