from django.db import models

from countries.models import Country
from sales.models import ProductCategory


class Rate(models.Model):
    name = models.CharField(max_length=50)
    region = models.ForeignKey(Country, related_name='region')
    province = models.CharField(max_length=50, null=True, blank=True)
    applies_to = models.ForeignKey(ProductCategory, null=True, blank=True)
    shipping_to_region = models.ForeignKey(Country, null=True, blank=True,
                                           related_name='shipping_to_region')
    shipping_to_province = models.CharField(max_length=50, null=True, blank=True)
    rate = models.FloatField()
    apply_after = models.IntegerField(null=True, blank=True)
    enabled = models.BooleanField()
    display_on_front = models.NullBooleanField(null=True, blank=True)
    taxable = models.NullBooleanField(null=True, blank=True)

    def __unicode__(self):
        return '%s - %s - %s%%' % (self.name, self.region, self.rate)
