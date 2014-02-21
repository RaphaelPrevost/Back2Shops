from django.db import models
from django.utils.translation import ugettext_lazy as _
from countries.models import Country

class Address(models.Model):
    address = models.CharField(verbose_name=_("Address"), max_length=250, blank=True, null=True)
    zipcode = models.IntegerField(verbose_name=_("Postal code"), blank=True, null=True)
    city = models.CharField(verbose_name=_("City"), max_length=100)
    country = models.ForeignKey(Country, verbose_name=_('Country'), blank=True, null=True)
    province_code = models.CharField(verbose_name=_('Province'), max_length=2, blank=True, null=True)

    def __unicode__(self):
        return ('%s %s %s %s (%s)'
                % (self.country,
                   self.province_code,
                   self.city,
                   self.address,
                   self.zipcode))

    def clean_city(self):
        return self.city.upper()

    def save(self, *args, **kwargs):
        self.city = self.city.upper()
        super(Address, self).save(*args, **kwargs)
